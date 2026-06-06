"""Board representation helpers.

The board itself is just a plain ``numpy.int8`` array of shape (8, 8); we keep
the engine functional/stateless rather than wrapping the array in a class so
that copying for search (MCTS/minimax) stays cheap and explicit. The helpers
here build and inspect such arrays.
"""

from __future__ import annotations

import numpy as np

from . import constants as C


def initial_board() -> np.ndarray:
    """Return the starting position as an 8x8 int8 array.

    BLACK men fill the playable squares of rows 0-2, WHITE men fill the
    playable squares of rows 5-7. See ``constants`` for the encoding.
    """
    board = np.zeros((C.BOARD_SIZE, C.BOARD_SIZE), dtype=C.BOARD_DTYPE)
    for row in range(C.BOARD_SIZE):
        for col in range(C.BOARD_SIZE):
            if not C.is_playable(row, col):
                continue
            if row <= 2:
                board[row, col] = C.BLACK_MAN
            elif row >= 5:
                board[row, col] = C.WHITE_MAN
    return board


def count_material(board: np.ndarray) -> dict[str, int]:
    """Return counts of men and kings for each color.

    Keys: ``white_men``, ``white_kings``, ``black_men``, ``black_kings``.
    """
    return {
        "white_men": int(np.count_nonzero(board == C.WHITE_MAN)),
        "white_kings": int(np.count_nonzero(board == C.WHITE_KING)),
        "black_men": int(np.count_nonzero(board == C.BLACK_MAN)),
        "black_kings": int(np.count_nonzero(board == C.BLACK_KING)),
    }


def render_ascii(board: np.ndarray) -> str:
    """Return a human-readable ASCII rendering (handy for tests/debugging)."""
    glyphs = {
        C.EMPTY: ".",
        C.WHITE_MAN: "w",
        C.WHITE_KING: "W",
        C.BLACK_MAN: "b",
        C.BLACK_KING: "B",
    }
    lines = []
    for row in range(C.BOARD_SIZE):
        cells = []
        for col in range(C.BOARD_SIZE):
            if C.is_playable(row, col):
                cells.append(glyphs[int(board[row, col])])
            else:
                cells.append(" ")
        lines.append(f"{row} " + " ".join(cells))
    header = "  " + " ".join(str(c) for c in range(C.BOARD_SIZE))
    return header + "\n" + "\n".join(lines)