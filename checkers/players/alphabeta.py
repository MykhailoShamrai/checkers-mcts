"""Alpha-beta player with iterative deepening and Chinook-inspired evaluation.

This is the heuristic benchmark that MCTS variants are measured against.
Uses iterative deepening alpha-beta with a configurable maximum depth.
"""

from __future__ import annotations

import random as _random
from typing import Optional

from checkers.engine import constants as C
from checkers.engine.game_state import GameState
from checkers.engine.move import Move
from checkers.players.base import Player

import numpy as np


def chinook_eval(board: np.ndarray, perspective: int) -> float:
    """Chinook-inspired evaluation combining material, mobility proxies,
    center control, and promotion proximity. Returns value in approx [-1, 1].

    Features:
    - Material: man=1, king=3
    - Center control: pieces on center 4x4 get bonus
    - Promotion proximity: men closer to promotion row score higher
    - Back row defense: men on starting back row get small bonus
    """
    white_material = 0.0
    black_material = 0.0
    white_positional = 0.0
    black_positional = 0.0

    center_rows = {3, 4}
    center_cols = {3, 4}

    for row in range(C.BOARD_SIZE):
        for col in range(C.BOARD_SIZE):
            piece = int(board[row, col])
            if piece == C.EMPTY:
                continue

            color = C.color_of(piece)

            # Material
            mat = 3.0 if C.is_king(piece) else 1.0

            # Positional bonuses (only for men — kings are already powerful)
            pos = 0.0
            if not C.is_king(piece):
                # Promotion proximity: how far along toward promotion row
                if color == C.WHITE:
                    pos += (7 - row) * 0.05  # closer to row 0
                else:
                    pos += row * 0.05  # closer to row 7

                # Back row defense
                if color == C.WHITE and row == 7:
                    pos += 0.1
                elif color == C.BLACK and row == 0:
                    pos += 0.1

            # Center control
            if row in center_rows and col in center_cols:
                pos += 0.15

            if color == C.WHITE:
                white_material += mat
                white_positional += pos
            else:
                black_material += mat
                black_positional += pos

    white_score = white_material + white_positional
    black_score = black_material + black_positional

    total = white_score + black_score
    if total == 0:
        return 0.0

    my_score = white_score if perspective == C.WHITE else black_score
    opp_score = black_score if perspective == C.WHITE else white_score

    return (my_score - opp_score) / (white_material + black_material + 1e-9)


class AlphaBetaPlayer(Player):
    """Iterative-deepening alpha-beta player with Chinook-inspired eval."""

    def __init__(
        self,
        max_depth: int = 6,
        seed: int | None = None,
    ) -> None:
        self.max_depth = max_depth
        self._rng = _random.Random(seed)

    def choose_move(self, state: GameState) -> Move:
        moves = state.legal_moves()
        if not moves:
            raise RuntimeError("No legal moves available")
        if len(moves) == 1:
            return moves[0]

        # Shuffle to break ties randomly (deterministic given seed)
        self._rng.shuffle(moves)

        best_move: Optional[Move] = None
        best_value = -float("inf")

        # Iterative deepening up to max_depth
        for depth in range(1, self.max_depth + 1):
            current_best_move: Optional[Move] = None
            current_best_value = -float("inf")

            for move in moves:
                child = state.play(move)
                value = -self._alphabeta(
                    child, depth - 1, -float("inf"), -current_best_value, -state.to_move
                )
                if value > current_best_value:
                    current_best_value = value
                    current_best_move = move

            best_move = current_best_move
            best_value = current_best_value

        return best_move  # type: ignore[return-value]

    def _alphabeta(
        self,
        state: GameState,
        depth: int,
        alpha: float,
        beta: float,
        perspective: int,
    ) -> float:
        """Negamax formulation of alpha-beta."""
        if state.is_terminal():
            return state.result(perspective)
        if depth == 0:
            return chinook_eval(state.board, perspective)

        moves = state.legal_moves()
        value = -float("inf")

        for move in moves:
            child = state.play(move)
            value = max(
                value,
                -self._alphabeta(child, depth - 1, -beta, -alpha, -perspective),
            )
            alpha = max(alpha, value)
            if alpha >= beta:
                break  # pruning

        return value
