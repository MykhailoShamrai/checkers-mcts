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


# Optional rule switch kept for experiments; default variant does not require
# selecting a longest capture sequence.
MAX_CAPTURE_RULE = False


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
    new_board = board.copy()

    origin_r, origin_c = move.origin
    dest_r, dest_c = move.destination

    piece = int(new_board[origin_r, origin_c])
    if piece == C.EMPTY:
        raise ValueError("Cannot apply move from an empty origin square")

    new_board[origin_r, origin_c] = C.EMPTY
    for cap_r, cap_c in move.captured:
        new_board[cap_r, cap_c] = C.EMPTY

    # Promotion is checked on final landing square (not mid-sequence).
    color = C.color_of(piece)
    if abs(piece) == 1 and dest_r == _promotion_row(color):
        piece = C.WHITE_KING if color == C.WHITE else C.BLACK_KING

    new_board[dest_r, dest_c] = piece
    return new_board


def _simple_moves(board: np.ndarray, color: int) -> list[Move]:
    """Non-capturing moves for ``color`` (men: one step forward; kings: slide)."""
    moves: list[Move] = []

    for row, col in _pieces_of_color(board, color):
        piece = int(board[row, col])
        if C.is_king(piece):
            for d_row, d_col in C.DIRECTIONS:
                r, c = row + d_row, col + d_col
                while C.is_playable(r, c) and board[r, c] == C.EMPTY:
                    moves.append(Move(squares=((row, col), (r, c))))
                    r += d_row
                    c += d_col
        else:
            forward_dirs = C.WHITE_FORWARD if color == C.WHITE else C.BLACK_FORWARD
            for d_row, d_col in forward_dirs:
                r, c = row + d_row, col + d_col
                if C.is_playable(r, c) and board[r, c] == C.EMPTY:
                    moves.append(Move(squares=((row, col), (r, c))))

    return moves


def _capture_moves(board: np.ndarray, color: int) -> list[Move]:
    """All maximal capture sequences for ``color``.

    Typically implemented as a recursive search from each of ``color``'s pieces,
    extending the jump as long as another capture is available.
    """
    all_moves: list[Move] = []
    for row, col in _pieces_of_color(board, color):
        piece = int(board[row, col])
        all_moves.extend(
            _capture_sequences_from(
                board=board,
                pos=(row, col),
                piece=piece,
                path=((row, col),),
                captured=(),
                captured_set=frozenset(),
            )
        )

    if not all_moves:
        return []

    if MAX_CAPTURE_RULE:
        max_captures = max(m.num_captured for m in all_moves)
        return [m for m in all_moves if m.num_captured == max_captures]

    return all_moves


def _promotion_row(color: int) -> int:
    """Return the back-row index on which a man of ``color`` promotes."""
    return 0 if color == C.WHITE else C.BOARD_SIZE - 1


def _pieces_of_color(board: np.ndarray, color: int) -> list[Square]:
    pieces: list[Square] = []
    for row in range(C.BOARD_SIZE):
        for col in range(C.BOARD_SIZE):
            if C.color_of(int(board[row, col])) == color:
                pieces.append((row, col))
    return pieces


def _capture_sequences_from(
    board: np.ndarray,
    pos: Square,
    piece: int,
    path: tuple[Square, ...],
    captured: tuple[Square, ...],
    captured_set: frozenset[Square],
) -> list[Move]:
    if C.is_king(piece):
        jumps = _king_jump_options(board, pos, C.color_of(piece), captured_set)
    else:
        jumps = _man_jump_options(board, pos, C.color_of(piece), captured_set)

    if not jumps:
        return [Move(squares=path, captured=captured)] if captured else []

    results: list[Move] = []
    for victim, landing in jumps:
        next_board = board.copy()
        pos_r, pos_c = pos
        land_r, land_c = landing
        next_board[pos_r, pos_c] = C.EMPTY
        next_board[land_r, land_c] = piece

        results.extend(
            _capture_sequences_from(
                board=next_board,
                pos=landing,
                piece=piece,
                path=path + (landing,),
                captured=captured + (victim,),
                captured_set=captured_set | {victim},
            )
        )

    return results


def _man_jump_options(
    board: np.ndarray,
    pos: Square,
    color: int,
    captured_set: frozenset[Square],
) -> list[tuple[Square, Square]]:
    pos_r, pos_c = pos
    options: list[tuple[Square, Square]] = []

    for d_row, d_col in C.DIRECTIONS:
        mid_r, mid_c = pos_r + d_row, pos_c + d_col
        land_r, land_c = pos_r + 2 * d_row, pos_c + 2 * d_col

        if not C.is_playable(mid_r, mid_c) or not C.is_playable(land_r, land_c):
            continue
        if board[land_r, land_c] != C.EMPTY:
            continue

        victim = (mid_r, mid_c)
        mid_piece = int(board[mid_r, mid_c])
        if mid_piece == C.EMPTY or C.color_of(mid_piece) != -color:
            continue
        if victim in captured_set:
            continue

        options.append((victim, (land_r, land_c)))

    return options


def _king_jump_options(
    board: np.ndarray,
    pos: Square,
    color: int,
    captured_set: frozenset[Square],
) -> list[tuple[Square, Square]]:
    pos_r, pos_c = pos
    options: list[tuple[Square, Square]] = []

    for d_row, d_col in C.DIRECTIONS:
        r, c = pos_r + d_row, pos_c + d_col

        # Traverse empty approach squares to find first blocker.
        while C.is_playable(r, c) and board[r, c] == C.EMPTY:
            r += d_row
            c += d_col

        if not C.is_playable(r, c):
            continue

        blocker_piece = int(board[r, c])
        blocker_sq = (r, c)

        # Own piece blocks. Already-captured piece also blocks (it stays on
        # board until sequence end and cannot be jumped again).
        if blocker_piece == C.EMPTY:
            continue
        if C.color_of(blocker_piece) == color:
            continue
        if blocker_sq in captured_set:
            continue

        # Enemy piece found: every empty square beyond is a valid landing.
        land_r, land_c = r + d_row, c + d_col
        while C.is_playable(land_r, land_c) and board[land_r, land_c] == C.EMPTY:
            options.append((blocker_sq, (land_r, land_c)))
            land_r += d_row
            land_c += d_col

    return options