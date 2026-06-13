"""UCT + Minimax hybrid player (Baier & Winands, 2014).

Instead of a random playout to terminal, the simulation phase runs a
depth-limited minimax search from the leaf node. If the minimax reaches a
terminal state it returns the exact game result; otherwise it evaluates the
position with the material heuristic.

This reduces playout variance compared to pure random simulations.
"""

from __future__ import annotations

import random as _random

from checkers.engine.game_state import GameState
from checkers.engine.move import Move
from checkers.players.base import Player
from checkers.players.heuristics import material_heuristic
from checkers.players.mcts.node import UCTNode


class UCTMinimaxPlayer(Player):
    """UCT with shallow minimax replacing the random playout."""

    def __init__(
        self,
        iterations: int = 1000,
        c: float = 1.4,
        minimax_depth: int = 2,
        seed: int | None = None,
    ) -> None:
        self.iterations = iterations
        self.c = c
        self.minimax_depth = minimax_depth
        self._rng = _random.Random(seed)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def choose_move(self, state: GameState) -> Move:
        root = UCTNode(state)

        for _ in range(self.iterations):
            node = self._select(root)
            node = self._expand(node)
            result = self._simulate(node, root.state.to_move)
            self._backpropagate(node, result, root.state.to_move)

        return root.best_move_child().move

    # ------------------------------------------------------------------
    # MCTS phases
    # ------------------------------------------------------------------

    def _select(self, node: UCTNode) -> UCTNode:
        while not node.is_terminal and node.is_fully_expanded:
            node = node.best_child(self.c)
        return node

    def _expand(self, node: UCTNode) -> UCTNode:
        if node.is_terminal:
            return node
        untried = node.untried_moves
        move = untried.pop(self._rng.randrange(len(untried)))
        child_state = node.state.play(move)
        child = UCTNode(state=child_state, move=move, parent=node)
        node.children.append(child)
        return child

    def _simulate(self, node: UCTNode, root_color: int) -> float:
        """Evaluate the leaf using depth-limited minimax instead of random playout."""
        if node.state.is_terminal():
            return node.state.result(root_color)
        maximizing = (node.state.to_move == root_color)
        return self._minimax(node.state, self.minimax_depth, root_color, maximizing)

    def _backpropagate(self, node: UCTNode, result: float, root_color: int) -> None:
        # Adjust initial perspective: if leaf's to_move == root_color,
        # the parent is opponent, so negate to store from parent's perspective.
        if node.state.to_move == root_color:
            result = -result
        while node is not None:
            node.visits += 1
            node.value += result
            result = -result
            node = node.parent

    # ------------------------------------------------------------------
    # Minimax with alpha-beta pruning
    # ------------------------------------------------------------------

    def _minimax(
        self,
        state: GameState,
        depth: int,
        root_color: int,
        maximizing: bool,
    ) -> float:
        if state.is_terminal():
            return state.result(root_color)
        if depth == 0:
            return material_heuristic(state.board, root_color)

        moves = state.legal_moves()
        if maximizing:
            value = -2.0
            for move in moves:
                child = state.play(move)
                value = max(value, self._minimax(child, depth - 1, root_color, False))
            return value
        else:
            value = 2.0
            for move in moves:
                child = state.play(move)
                value = min(value, self._minimax(child, depth - 1, root_color, True))
            return value
