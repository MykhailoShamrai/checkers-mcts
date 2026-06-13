"""Heuristic evaluation functions for checkers positions.

Used by alpha-beta player and as leaf evaluator in MCTS variants.
"""

from __future__ import annotations

import numpy as np

from checkers.engine import constants as C


def material_heuristic(board: np.ndarray, perspective: int) -> float:
    """Simple material count normalized to [-1, 1].

    Formula (from konspekt, formula (3)):
        h = (my_material - opp_material) / (my_material + opp_material)

    where man=1, king=3.  Returns value from ``perspective``'s point of view.
    """
    white_score = (
        int(np.count_nonzero(board == C.WHITE_MAN)) * 1
        + int(np.count_nonzero(board == C.WHITE_KING)) * 3
    )
    black_score = (
        int(np.count_nonzero(board == C.BLACK_MAN)) * 1
        + int(np.count_nonzero(board == C.BLACK_KING)) * 3
    )

    my_score = white_score if perspective == C.WHITE else black_score
    opp_score = black_score if perspective == C.WHITE else white_score

    total = my_score + opp_score
    if total == 0:
        return 0.0
    return (my_score - opp_score) / total
