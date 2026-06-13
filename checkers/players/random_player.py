"""Random player — picks a legal move uniformly at random (seeded)."""

from __future__ import annotations

import random as _random

from checkers.engine.game_state import GameState
from checkers.engine.move import Move
from checkers.players.base import Player


class RandomPlayer(Player):
    def __init__(self, seed: int | None = None) -> None:
        self._rng = _random.Random(seed)

    def choose_move(self, state: GameState) -> Move:
        moves = state.legal_moves()
        if not moves:
            raise RuntimeError("No legal moves available")
        return self._rng.choice(moves)
