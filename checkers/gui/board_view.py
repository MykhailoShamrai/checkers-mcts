"""Board rendering and click-to-square mapping for the Pygame GUI."""

from __future__ import annotations

from typing import Optional

import pygame

from checkers.engine import constants as C
from checkers.engine.move import Move

# ------------------------------------------------------------------
# Visual constants
# ------------------------------------------------------------------
SQUARE_SIZE = 80
BOARD_PX = SQUARE_SIZE * C.BOARD_SIZE  # 640
MARGIN_TOP = 50  # space for status text
WINDOW_W = BOARD_PX
WINDOW_H = BOARD_PX + MARGIN_TOP

COLOR_LIGHT = (240, 217, 181)
COLOR_DARK = (181, 136, 99)
COLOR_HIGHLIGHT = (255, 255, 100, 150)
COLOR_LEGAL_DOT = (80, 200, 80)
COLOR_WHITE_PIECE = (255, 255, 255)
COLOR_BLACK_PIECE = (30, 30, 30)
COLOR_KING_MARKER = (220, 50, 50)
COLOR_BG = (40, 40, 40)
COLOR_TEXT = (255, 255, 255)


def draw_board(surface: pygame.Surface) -> None:
    """Draw the 8x8 board squares."""
    for row in range(C.BOARD_SIZE):
        for col in range(C.BOARD_SIZE):
            x = col * SQUARE_SIZE
            y = row * SQUARE_SIZE + MARGIN_TOP
            color = COLOR_DARK if (row + col) % 2 == 1 else COLOR_LIGHT
            pygame.draw.rect(surface, color, (x, y, SQUARE_SIZE, SQUARE_SIZE))


def draw_pieces(surface: pygame.Surface, board) -> None:
    """Draw pieces on the board from a numpy array."""
    for row in range(C.BOARD_SIZE):
        for col in range(C.BOARD_SIZE):
            piece = int(board[row, col])
            if piece == C.EMPTY:
                continue
            cx = col * SQUARE_SIZE + SQUARE_SIZE // 2
            cy = row * SQUARE_SIZE + MARGIN_TOP + SQUARE_SIZE // 2
            radius = SQUARE_SIZE // 2 - 8

            color = COLOR_WHITE_PIECE if C.color_of(piece) == C.WHITE else COLOR_BLACK_PIECE
            pygame.draw.circle(surface, color, (cx, cy), radius)
            # Outline
            pygame.draw.circle(surface, (100, 100, 100), (cx, cy), radius, 2)

            # King marker
            if C.is_king(piece):
                pygame.draw.circle(surface, COLOR_KING_MARKER, (cx, cy), radius // 3)


def draw_highlight(surface: pygame.Surface, square: tuple[int, int]) -> None:
    """Highlight a selected square."""
    row, col = square
    x = col * SQUARE_SIZE
    y = row * SQUARE_SIZE + MARGIN_TOP
    highlight_surf = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
    highlight_surf.fill(COLOR_HIGHLIGHT)
    surface.blit(highlight_surf, (x, y))


def draw_legal_targets(
    surface: pygame.Surface,
    moves: list[Move],
    selected: tuple[int, int],
) -> None:
    """Draw dots on squares that are legal destinations from `selected`."""
    for move in moves:
        if move.origin == selected:
            dest_row, dest_col = move.destination
            cx = dest_col * SQUARE_SIZE + SQUARE_SIZE // 2
            cy = dest_row * SQUARE_SIZE + MARGIN_TOP + SQUARE_SIZE // 2
            pygame.draw.circle(surface, COLOR_LEGAL_DOT, (cx, cy), 12)


def draw_status(surface: pygame.Surface, text: str) -> None:
    """Draw status text at the top."""
    font = pygame.font.SysFont("Arial", 22)
    rendered = font.render(text, True, COLOR_TEXT)
    surface.fill(COLOR_BG, (0, 0, WINDOW_W, MARGIN_TOP))
    surface.blit(rendered, (10, 12))


def pixel_to_square(pos: tuple[int, int]) -> Optional[tuple[int, int]]:
    """Convert pixel (x, y) to board (row, col), or None if outside board."""
    x, y = pos
    y -= MARGIN_TOP
    if y < 0 or x < 0 or x >= BOARD_PX or y >= BOARD_PX:
        return None
    col = x // SQUARE_SIZE
    row = y // SQUARE_SIZE
    return (row, col)
