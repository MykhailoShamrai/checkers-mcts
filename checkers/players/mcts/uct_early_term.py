"""UCT + Early Termination player (Lorentz 2016, Lanctot et al. 2014).

Instead of playing the simulation to a terminal state, the playout is cut off
after a fixed number of moves (``playout_depth``) and the position is evaluated
with the material heuristic.

Optionally uses blending (formula (2) from Lanctot et al.):
    Q_hat = (1 - alpha) * (r / n) + alpha * v
where v is the heuristic evaluation of the node's state.  When alpha=0 this
reduces to pure UCT with early-terminated playouts.
"""

from __future__ import annotations

import random as _random

from checkers.engine.game_state import GameState
from checkers.engine.move import Move
from checkers.players.base import Player
from checkers.players.heuristics import material_heuristic
from checkers.players.mcts.node import UCTNode


class UCTEarlyTermPlayer(Player):
    """UCT with playout depth limit and optional heuristic blending."""

    def __init__(
        self,
        iterations: int = 1000,
        c: float = 1.4,
        playout_depth: int = 20,
        alpha: float = 0.0,
        seed: int | None = None,
    ) -> None:
        self.iterations = iterations
        self.c = c
        self.playout_depth = playout_depth
        self.alpha = alpha  # blending weight for heuristic value at node
        self._rng = _random.Random(seed)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def choose_move(self, state: GameState) -> Move:
        root = UCTNode(state)
        root_color = state.to_move

        for _ in range(self.iterations):
            node = self._select(root)
            node = self._expand(node)
            result = self._simulate(node, root_color)

            # Optional blending: mix playout result with node heuristic.
            if self.alpha > 0.0 and not node.is_terminal:
                v = material_heuristic(node.state.board, root_color)
                result = (1.0 - self.alpha) * result + self.alpha * v

            self._backpropagate(node, result)

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
        """Random playout with early termination after playout_depth moves."""
        state = node.state
        depth = 0
        while not state.is_terminal() and depth < self.playout_depth:
            moves = state.legal_moves()
            move = moves[self._rng.randrange(len(moves))]
            state = state.play(move)
            depth += 1

        if state.is_terminal():
            return state.result(root_color)
        # Early termination: evaluate with heuristic.
        return material_heuristic(state.board, root_color)

    def _backpropagate(self, node: UCTNode, result: float) -> None:
        while node is not None:
            node.visits += 1
            node.value += result
            result = -result
            node = node.parent
