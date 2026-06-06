"""Move generation and rule enforcement.

This is the heart of the engine and the single most correctness-critical
module in the project. Implement it carefully and pair every rule with a unit
test in ``tests/`` (see CLAUDE.md, "Engine invariants").

Rules to enforce (from the project konspekt)
--------------------------------------------
1. Men move one diagonal step forward to an empty square (WHITE toward row 0,
   BLACK toward row 7).
2. Kings ("flying kings") slide any number of empty squares along a diagonal.
3. Captures are MANDATORY. If any capturing move exists for the side to move,
   only capturing moves are legal.
4. Men capture by jumping an adjacent enemy piece to the empty square
   immediately beyond it; capture direction may be forward OR backward.
5. King captures along the whole diagonal: it may jump a single enemy piece
   located any distance away (with only empty squares in between) and land on
   any empty square beyond it.
6. Multi-captures are mandatory and must be played to completion: after each
   jump, if the same piece can capture again it must continue. Captured pieces
   are removed only after the whole sequence ends and may not be jumped twice.
7. (Optional / configurable) "maximum capture" rule is NOT required by the
   konspekt -- any complete capture sequence is legal. Keep this flag so we can
   experiment, but default to OFF.
8. Promotion: a man that ends its move on the opposing back row becomes a king.
   Per standard draughts, if a man reaches the back row mid-capture it promotes
   only if the sequence ends there; otherwise it continues as a man. (Decide
   and document the chosen convention; cover it with a test.)

Public API (keep these signatures stable -- the players depend on them)
----------------------------------------------------------------------
    legal_moves(board, color) -> list[Move]
    apply_move(board, move) -> np.ndarray          # returns a NEW board
"""

from __future__ import annotations

import numpy as np

from . import constants as C
from .move import Move, Square


def legal_moves(board: np.ndarray, color: int) -> list[Move]:
    """Return all legal moves for ``color`` in ``board``.

    Honors the mandatory-capture rule: if any capture exists, only captures are
    returned.
    """
    captures = _capture_moves(board, color)
    if captures:
        return captures
    return _simple_moves(board, color)


def apply_move(board: np.ndarray, move: Move) -> np.ndarray:
    """Return a NEW board with ``move`` applied (input board is not mutated).

    Handles piece relocation, removal of captured pieces, and promotion.
    """
    raise NotImplementedError("Phase 1: implement apply_move")


def _simple_moves(board: np.ndarray, color: int) -> list[Move]:
    """Non-capturing moves for ``color`` (men: one step forward; kings: slide)."""
    raise NotImplementedError("Phase 1: implement non-capturing move generation")


def _capture_moves(board: np.ndarray, color: int) -> list[Move]:
    """All maximal capture sequences for ``color``.

    Typically implemented as a recursive search from each of ``color``'s pieces,
    extending the jump as long as another capture is available.
    """
    raise NotImplementedError("Phase 1: implement capture (incl. multi) generation")


def _promotion_row(color: int) -> int:
    """Return the back-row index on which a man of ``color`` promotes."""
    return 0 if color == C.WHITE else C.BOARD_SIZE - 1