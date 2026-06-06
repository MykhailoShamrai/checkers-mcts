"""Immutable game state: the unit the search algorithms and GUI operate on.

A :class:`GameState` bundles the board, the side to move, and the ply counter
(needed for the move-limit draw rule). It is treated as immutable: ``play``
returns a new state rather than mutating in place, which keeps MCTS/minimax
node expansion simple and bug-resistant.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from . import board as board_mod
from . import constants as C
from . import rules
from .move import Move


@dataclass(frozen=True)
class GameState:
    board: np.ndarray
    to_move: int = C.WHITE          # WHITE moves first
    ply: int = 0                    # number of plies played so far
    move_limit: int = C.MOVE_LIMIT

    @staticmethod
    def initial(move_limit: int = C.MOVE_LIMIT) -> "GameState":
        return GameState(board_mod.initial_board(), C.WHITE, 0, move_limit)

    def legal_moves(self) -> list[Move]:
        return rules.legal_moves(self.board, self.to_move)

    def play(self, move: Move) -> "GameState":
        """Return the successor state after ``move`` (does not mutate self)."""
        new_board = rules.apply_move(self.board, move)
        return GameState(new_board, -self.to_move, self.ply + 1, self.move_limit)

    def is_terminal(self) -> bool:
        return self.winner() is not None or self.is_draw()

    def is_draw(self) -> bool:
        """Draw by move limit (and later: any other draw rules we add)."""
        return self.ply >= self.move_limit and self.winner() is None

    def winner(self) -> int | None:
        """Return the winning color, or None if the game is not decided.

        A side with no legal move loses (it has no pieces or is blocked). Note
        this does not by itself capture the move-limit draw -- use
        :meth:`is_draw` / :meth:`result` for the full outcome.
        """
        if self.legal_moves():
            return None
        # Side to move has no moves -> it loses.
        return -self.to_move

    def result(self, perspective: int) -> float:
        """Terminal value in [-1, 1] from ``perspective``'s point of view.

        +1 win, -1 loss, 0 draw. Undefined (raises) if the state is not
        terminal; callers should guard with :meth:`is_terminal`.
        """
        if not self.is_terminal():
            raise ValueError("result() called on a non-terminal state")
        win = self.winner()
        if win is None:
            return 0.0
        return 1.0 if win == perspective else -1.0