"""Abstract base class for all players."""

from __future__ import annotations

from abc import ABC, abstractmethod

from checkers.engine.game_state import GameState
from checkers.engine.move import Move


class Player(ABC):
    """Interface that every player (human, random, AI) must implement."""

    @abstractmethod
    def choose_move(self, state: GameState) -> Move:
        """Return the move chosen for the current game state."""
        ...
