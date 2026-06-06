"""Core constants and encodings for the 8x8 checkers engine.

Board encoding
--------------
The board is an 8x8 ``numpy.int8`` array. Each cell holds one of:

    EMPTY      =  0
    WHITE_MAN  =  1
    WHITE_KING =  2
    BLACK_MAN  = -1
    BLACK_KING = -2

The *sign* encodes the color (positive = WHITE, negative = BLACK) and the
*absolute value* encodes the rank (1 = man, 2 = king). This makes common
queries cheap, e.g. ``np.sign(cell)`` gives the owning color and
``abs(cell) == 2`` tests for a king.

Geometry / orientation
----------------------
* Rows are indexed 0 (top) .. 7 (bottom), columns 0 (left) .. 7 (right).
* Only *dark* squares are playable. A square ``(r, c)`` is playable iff
  ``(r + c) % 2 == 1``. This yields exactly 12 playable squares in each
  block of three rows.
* BLACK starts on rows 0, 1, 2 and moves *down* (increasing row index).
* WHITE starts on rows 5, 6, 7 and moves *up* (decreasing row index).
* A WHITE man promotes on reaching row 0; a BLACK man on reaching row 7.

These conventions are relied upon throughout the engine; do not change them
without updating ``board.initial_board`` and the move generator together.
"""

from __future__ import annotations

import numpy as np

BOARD_SIZE = 8

# Cell values.
EMPTY = 0
WHITE_MAN = 1
WHITE_KING = 2
BLACK_MAN = -1
BLACK_KING = -2

# Colors (also used as the sign of a cell value).
WHITE = 1
BLACK = -1

# Default rule parameters (see the project konspekt / CLAUDE.md).
MOVE_LIMIT = 150  # plies after which the game is declared a draw

# Diagonal directions as (d_row, d_col).
DIRECTIONS = ((-1, -1), (-1, 1), (1, -1), (1, 1))
# Men capture in all four diagonal directions but step only "forward":
WHITE_FORWARD = ((-1, -1), (-1, 1))  # toward row 0
BLACK_FORWARD = ((1, -1), (1, 1))    # toward row 7

# Dtype used for the board array.
BOARD_DTYPE = np.int8


def is_playable(row: int, col: int) -> bool:
    """Return True if (row, col) is on the board and a dark (playable) square."""
    return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE and (row + col) % 2 == 1


def color_of(cell: int) -> int:
    """Return WHITE, BLACK, or 0 (empty) for a cell value."""
    return int(np.sign(cell))


def is_king(cell: int) -> bool:
    return abs(cell) == 2