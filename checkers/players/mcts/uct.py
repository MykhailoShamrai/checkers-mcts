"""Basic UCT (Upper Confidence bounds applied to Trees) player.

Implements the standard four-phase MCTS loop:
1. Selection — walk down the tree using UCB1 until a non-fully-expanded node.
2. Expansion — add one child for an untried move.
3. Simulation — random playout from the new child to a terminal state.
4. Backpropagation — propagate the result back up the tree.

Deterministic for a given seed.
"""

from __future__ import annotations

import random as _random

from checkers.engine.game_state import GameState
from checkers.engine.move import Move
from checkers.players.base import Player
from checkers.players.mcts.node import UCTNode


class UCTPlayer(Player):
    """Pure UCT player with configurable iteration budget and exploration constant."""

    def __init__(
        self,
        iterations: int = 1000,
        c: float = 1.4,
        seed: int | None = None,
    ) -> None:
        self.iterations = iterations
        self.c = c
        self._rng = _random.Random(seed)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def choose_move(self, state: GameState) -> Move:
        root = UCTNode(state)

        for _ in range(self.iterations):
            node = self._select(root)
            node = self._expand(node)
            result = self._simulate(node)
            self._backpropagate(node, result)

        best = root.best_move_child()
        return best.move

    # ------------------------------------------------------------------
    # MCTS phases
    # ------------------------------------------------------------------

    def _select(self, node: UCTNode) -> UCTNode:
        """Descend through fully-expanded, non-terminal nodes using UCB1."""
        while not node.is_terminal and node.is_fully_expanded:
            node = node.best_child(self.c)
        return node

    def _expand(self, node: UCTNode) -> UCTNode:
        """Expand one untried move if possible, return the new child."""
        if node.is_terminal:
            return node
        untried = node.untried_moves
        move = untried.pop(self._rng.randrange(len(untried)))
        child_state = node.state.play(move)
        child = UCTNode(state=child_state, move=move, parent=node)
        node.children.append(child)
        return child

    def _simulate(self, node: UCTNode) -> float:
        """Random playout from node's state to terminal; return result for root player."""
        state = node.state
        while not state.is_terminal():
            moves = state.legal_moves()
            move = moves[self._rng.randrange(len(moves))]
            state = state.play(move)
        # Result from perspective of the root's to_move player.
        return state.result(self._root_color(node))

    def _backpropagate(self, node: UCTNode, result: float) -> None:
        """Propagate result up the tree, flipping perspective at each level.

        node.value accumulates reward from the perspective of the *parent's*
        side-to-move (the player who chose to enter this node). The simulation
        returns a result from root's perspective, so we must adjust the initial
        sign based on the leaf's depth parity.
        """
        # If the leaf's to_move == root_color, then the parent is the opponent
        # and we need to negate so the value is stored from opponent's perspective.
        root_color = self._root_color(node)
        if node.state.to_move == root_color:
            result = -result
        while node is not None:
            node.visits += 1
            node.value += result
            result = -result
            node = node.parent

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _root_color(node: UCTNode) -> int:
        """Walk up to root and return the root's to_move color."""
        while node.parent is not None:
            node = node.parent
        return node.state.to_move
