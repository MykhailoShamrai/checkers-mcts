"""Players package — re-exports for convenience."""

from checkers.players.base import Player
from checkers.players.random_player import RandomPlayer
from checkers.players.mcts.uct import UCTPlayer

__all__ = ["Player", "RandomPlayer", "UCTPlayer"]
