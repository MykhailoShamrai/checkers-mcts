"""UCT Node used by all MCTS variants."""

from __future__ import annotations

import math
from typing import Optional

from checkers.engine.game_state import GameState
from checkers.engine.move import Move


class UCTNode:
    """A single node in the MCTS search tree."""

    __slots__ = (
        "state",
        "move",
        "parent",
        "children",
        "visits",
        "value",
        "_untried_moves",
    )

    def __init__(
        self,
        state: GameState,
        move: Optional[Move] = None,
        parent: Optional["UCTNode"] = None,
    ) -> None:
        self.state = state
        self.move = move  # move that led to this node
        self.parent = parent
        self.children: list["UCTNode"] = []
        self.visits: int = 0
        self.value: float = 0.0  # total reward from perspective of node's *parent* mover
        self._untried_moves: list[Move] | None = None

    @property
    def untried_moves(self) -> list[Move]:
        if self._untried_moves is None:
            self._untried_moves = self.state.legal_moves()
        return self._untried_moves

    @property
    def is_fully_expanded(self) -> bool:
        return len(self.untried_moves) == 0

    @property
    def is_terminal(self) -> bool:
        return self.state.is_terminal()

    def ucb1(self, c: float) -> float:
        """UCB1 score from the parent's perspective."""
        if self.visits == 0:
            return float("inf")
        exploitation = self.value / self.visits
        exploration = c * math.sqrt(math.log(self.parent.visits) / self.visits)
        return exploitation + exploration

    def best_child(self, c: float) -> "UCTNode":
        return max(self.children, key=lambda ch: ch.ucb1(c))

    def best_move_child(self) -> "UCTNode":
        """Return the child with the most visits (robust child selection)."""
        return max(self.children, key=lambda ch: ch.visits)
