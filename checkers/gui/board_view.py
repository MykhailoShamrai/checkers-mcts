"""Board rendering and click-to-square mapping for the Pygame GUI.

Redesigned for a polished, modern look with:
- Wooden board texture colors with subtle bevels
- 3D-style pieces with highlights and shadows
- Captured pieces panels on both sides
- Smooth highlights and legal move indicators
"""

from __future__ import annotations

from typing import Optional

import pygame

from checkers.engine import constants as C
from checkers.engine.move import Move

# ------------------------------------------------------------------
# Layout constants
# ------------------------------------------------------------------
SQUARE_SIZE = 72
BOARD_PX = SQUARE_SIZE * C.BOARD_SIZE  # 576
PANEL_W = 100  # side panels for captured pieces
MARGIN_TOP = 60  # top status bar
MARGIN_BOTTOM = 40  # bottom info bar
BOARD_OFFSET_X = PANEL_W
BOARD_OFFSET_Y = MARGIN_TOP
WINDOW_W = BOARD_PX + 2 * PANEL_W
WINDOW_H = BOARD_PX + MARGIN_TOP + MARGIN_BOTTOM

# ------------------------------------------------------------------
# Color palette
# ------------------------------------------------------------------
COLOR_LIGHT = (245, 222, 179)  # wheat
COLOR_DARK = (139, 90, 43)  # saddle brown
COLOR_DARK_HOVER = (160, 110, 60)
COLOR_HIGHLIGHT = (255, 215, 0, 120)  # gold semi-transparent
COLOR_LAST_MOVE = (100, 180, 255, 80)  # blue hint for last move
COLOR_LEGAL_FILL = (50, 205, 50, 100)  # green semi-transparent
COLOR_LEGAL_RING = (34, 139, 34)

COLOR_WHITE_PIECE = (255, 250, 240)  # floral white
COLOR_WHITE_DARK = (200, 195, 185)
COLOR_WHITE_HIGHLIGHT = (255, 255, 255)
COLOR_BLACK_PIECE = (50, 50, 50)
COLOR_BLACK_DARK = (20, 20, 20)
COLOR_BLACK_HIGHLIGHT = (90, 90, 90)
COLOR_KING_CROWN = (255, 215, 0)  # gold crown
COLOR_KING_CROWN_DARK = (184, 134, 11)

COLOR_BG = (32, 32, 36)
COLOR_PANEL_BG = (42, 42, 48)
COLOR_BORDER = (80, 60, 40)
COLOR_TEXT = (240, 240, 240)
COLOR_TEXT_DIM = (160, 160, 160)
COLOR_TEXT_GOLD = (255, 215, 0)
COLOR_TEXT_RED = (255, 80, 80)
COLOR_TEXT_GREEN = (80, 255, 80)


# ------------------------------------------------------------------
# Drawing functions
# ------------------------------------------------------------------

def draw_board(surface: pygame.Surface) -> None:
    """Draw the 8x8 board with border and coordinate labels."""
    # Board border
    border_rect = (
        BOARD_OFFSET_X - 4, BOARD_OFFSET_Y - 4,
        BOARD_PX + 8, BOARD_PX + 8,
    )
    pygame.draw.rect(surface, COLOR_BORDER, border_rect, border_radius=3)

    for row in range(C.BOARD_SIZE):
        for col in range(C.BOARD_SIZE):
            x = col * SQUARE_SIZE + BOARD_OFFSET_X
            y = row * SQUARE_SIZE + BOARD_OFFSET_Y
            if (row + col) % 2 == 1:
                pygame.draw.rect(surface, COLOR_DARK, (x, y, SQUARE_SIZE, SQUARE_SIZE))
                # Subtle inner shadow on dark squares
                pygame.draw.rect(surface, (120, 75, 35), (x, y, SQUARE_SIZE, 2))
                pygame.draw.rect(surface, (120, 75, 35), (x, y, 2, SQUARE_SIZE))
            else:
                pygame.draw.rect(surface, COLOR_LIGHT, (x, y, SQUARE_SIZE, SQUARE_SIZE))

    # Coordinate labels
    font = pygame.font.SysFont("Consolas", 12)
    for i in range(C.BOARD_SIZE):
        # Row numbers (left side)
        label = font.render(str(i), True, COLOR_TEXT_DIM)
        surface.blit(label, (BOARD_OFFSET_X - 14, BOARD_OFFSET_Y + i * SQUARE_SIZE + SQUARE_SIZE // 2 - 6))
        # Column numbers (bottom)
        label = font.render(str(i), True, COLOR_TEXT_DIM)
        surface.blit(label, (BOARD_OFFSET_X + i * SQUARE_SIZE + SQUARE_SIZE // 2 - 4, BOARD_OFFSET_Y + BOARD_PX + 4))


def _draw_piece(surface: pygame.Surface, cx: int, cy: int, color: int, is_king: bool) -> None:
    """Draw a single piece with 3D shading and optional crown."""
    radius = SQUARE_SIZE // 2 - 8

    if color == C.WHITE:
        base_color = COLOR_WHITE_PIECE
        dark_color = COLOR_WHITE_DARK
        highlight_color = COLOR_WHITE_HIGHLIGHT
    else:
        base_color = COLOR_BLACK_PIECE
        dark_color = COLOR_BLACK_DARK
        highlight_color = COLOR_BLACK_HIGHLIGHT

    # Shadow
    pygame.draw.circle(surface, (0, 0, 0, 60), (cx + 2, cy + 3), radius)

    # Base (3D effect — darker bottom ring)
    pygame.draw.circle(surface, dark_color, (cx, cy + 2), radius)
    pygame.draw.circle(surface, base_color, (cx, cy), radius)

    # Top highlight (glossy effect)
    highlight_r = radius // 2
    pygame.draw.circle(surface, highlight_color, (cx - radius // 4, cy - radius // 4), highlight_r)

    # Outer ring
    pygame.draw.circle(surface, dark_color, (cx, cy), radius, 2)

    # King crown
    if is_king:
        crown_r = radius // 2 + 2
        pygame.draw.circle(surface, COLOR_KING_CROWN_DARK, (cx, cy), crown_r)
        pygame.draw.circle(surface, COLOR_KING_CROWN, (cx, cy), crown_r - 2)
        # Crown symbol: small star/triangle hints
        font = pygame.font.SysFont("Segoe UI Symbol", 18, bold=True)
        crown_text = font.render("♔" if color == C.WHITE else "♚", True, (60, 30, 0))
        surface.blit(crown_text, (cx - crown_text.get_width() // 2, cy - crown_text.get_height() // 2))


def draw_pieces(surface: pygame.Surface, board) -> None:
    """Draw all pieces on the board."""
    for row in range(C.BOARD_SIZE):
        for col in range(C.BOARD_SIZE):
            piece = int(board[row, col])
            if piece == C.EMPTY:
                continue
            cx = col * SQUARE_SIZE + SQUARE_SIZE // 2 + BOARD_OFFSET_X
            cy = row * SQUARE_SIZE + SQUARE_SIZE // 2 + BOARD_OFFSET_Y
            _draw_piece(surface, cx, cy, C.color_of(piece), C.is_king(piece))


def draw_highlight(surface: pygame.Surface, square: tuple[int, int]) -> None:
    """Highlight selected square with golden glow."""
    row, col = square
    x = col * SQUARE_SIZE + BOARD_OFFSET_X
    y = row * SQUARE_SIZE + BOARD_OFFSET_Y
    highlight_surf = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
    highlight_surf.fill(COLOR_HIGHLIGHT)
    surface.blit(highlight_surf, (x, y))
    pygame.draw.rect(surface, (255, 215, 0), (x, y, SQUARE_SIZE, SQUARE_SIZE), 3, border_radius=2)


def draw_legal_targets(
    surface: pygame.Surface,
    moves: list[Move],
    selected: tuple[int, int],
) -> None:
    """Draw legal move indicators — translucent circles with ring."""
    for move in moves:
        if move.origin == selected:
            dest_row, dest_col = move.destination
            cx = dest_col * SQUARE_SIZE + SQUARE_SIZE // 2 + BOARD_OFFSET_X
            cy = dest_row * SQUARE_SIZE + SQUARE_SIZE // 2 + BOARD_OFFSET_Y
            # Semi-transparent fill
            dot_surf = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            pygame.draw.circle(dot_surf, COLOR_LEGAL_FILL, (SQUARE_SIZE // 2, SQUARE_SIZE // 2), 16)
            surface.blit(dot_surf, (cx - SQUARE_SIZE // 2, cy - SQUARE_SIZE // 2))
            # Solid ring
            pygame.draw.circle(surface, COLOR_LEGAL_RING, (cx, cy), 16, 3)
            # If it's a capture, mark it red
            if move.is_capture:
                pygame.draw.circle(surface, (255, 60, 60), (cx, cy), 18, 3)


def draw_captured_pieces(
    surface: pygame.Surface,
    white_captured: int,
    white_kings_captured: int,
    black_captured: int,
    black_kings_captured: int,
) -> None:
    """Draw captured piece counts in side panels."""
    font = pygame.font.SysFont("Segoe UI", 14)
    title_font = pygame.font.SysFont("Segoe UI", 13, bold=True)

    # Left panel — pieces captured BY white (i.e. black pieces lost)
    panel_y = BOARD_OFFSET_Y + 10
    left_x = 12

    pygame.draw.rect(surface, COLOR_PANEL_BG, (4, BOARD_OFFSET_Y, PANEL_W - 8, BOARD_PX), border_radius=6)

    title = title_font.render("BLACK lost", True, COLOR_TEXT_DIM)
    surface.blit(title, (left_x, panel_y))
    panel_y += 28

    # Draw mini black pieces as captured trophies
    mini_r = 12
    for i in range(black_captured):
        row_i = i // 3
        col_i = i % 3
        mx = left_x + 16 + col_i * 28
        my = panel_y + 16 + row_i * 28
        pygame.draw.circle(surface, COLOR_BLACK_PIECE, (mx, my), mini_r)
        pygame.draw.circle(surface, (80, 80, 80), (mx, my), mini_r, 1)

    for i in range(black_kings_captured):
        row_i = (black_captured + i) // 3
        col_i = (black_captured + i) % 3
        mx = left_x + 16 + col_i * 28
        my = panel_y + 16 + row_i * 28
        pygame.draw.circle(surface, COLOR_BLACK_PIECE, (mx, my), mini_r)
        pygame.draw.circle(surface, COLOR_KING_CROWN, (mx, my), mini_r, 2)

    # Right panel — pieces captured BY black (i.e. white pieces lost)
    right_x = WINDOW_W - PANEL_W + 12
    panel_y = BOARD_OFFSET_Y + 10

    pygame.draw.rect(surface, COLOR_PANEL_BG,
                     (WINDOW_W - PANEL_W + 4, BOARD_OFFSET_Y, PANEL_W - 8, BOARD_PX), border_radius=6)

    title = title_font.render("WHITE lost", True, COLOR_TEXT_DIM)
    surface.blit(title, (right_x, panel_y))
    panel_y += 28

    for i in range(white_captured):
        row_i = i // 3
        col_i = i % 3
        mx = right_x + 16 + col_i * 28
        my = panel_y + 16 + row_i * 28
        pygame.draw.circle(surface, COLOR_WHITE_PIECE, (mx, my), mini_r)
        pygame.draw.circle(surface, (180, 180, 180), (mx, my), mini_r, 1)

    for i in range(white_kings_captured):
        row_i = (white_captured + i) // 3
        col_i = (white_captured + i) % 3
        mx = right_x + 16 + col_i * 28
        my = panel_y + 16 + row_i * 28
        pygame.draw.circle(surface, COLOR_WHITE_PIECE, (mx, my), mini_r)
        pygame.draw.circle(surface, COLOR_KING_CROWN, (mx, my), mini_r, 2)


def draw_status(surface: pygame.Surface, text: str, game_over: bool = False) -> None:
    """Draw status bar at the top."""
    pygame.draw.rect(surface, COLOR_PANEL_BG, (0, 0, WINDOW_W, MARGIN_TOP), border_radius=0)
    pygame.draw.line(surface, COLOR_BORDER, (0, MARGIN_TOP - 1), (WINDOW_W, MARGIN_TOP - 1))

    font = pygame.font.SysFont("Segoe UI", 20, bold=True)
    color = COLOR_TEXT_GOLD if game_over else COLOR_TEXT
    rendered = font.render(text, True, color)
    surface.blit(rendered, (WINDOW_W // 2 - rendered.get_width() // 2, 18))


def draw_bottom_bar(surface: pygame.Surface, ply: int, move_limit: int) -> None:
    """Draw bottom info bar with ply counter and controls hint."""
    y = WINDOW_H - MARGIN_BOTTOM
    pygame.draw.rect(surface, COLOR_PANEL_BG, (0, y, WINDOW_W, MARGIN_BOTTOM))
    pygame.draw.line(surface, COLOR_BORDER, (0, y), (WINDOW_W, y))

    font = pygame.font.SysFont("Segoe UI", 12)
    left_text = font.render(f"Ply: {ply}/{move_limit}", True, COLOR_TEXT_DIM)
    surface.blit(left_text, (12, y + 12))

    right_text = font.render("R: restart | ESC: quit", True, COLOR_TEXT_DIM)
    surface.blit(right_text, (WINDOW_W - right_text.get_width() - 12, y + 12))


def pixel_to_square(pos: tuple[int, int]) -> Optional[tuple[int, int]]:
    """Convert pixel (x, y) to board (row, col), or None if outside board."""
    x, y = pos
    x -= BOARD_OFFSET_X
    y -= BOARD_OFFSET_Y
    if y < 0 or x < 0 or x >= BOARD_PX or y >= BOARD_PX:
        return None
    col = x // SQUARE_SIZE
    row = y // SQUARE_SIZE
    return (row, col)


def _square_center(row: int, col: int) -> tuple[int, int]:
    """Get pixel center of a board square."""
    cx = col * SQUARE_SIZE + SQUARE_SIZE // 2 + BOARD_OFFSET_X
    cy = row * SQUARE_SIZE + SQUARE_SIZE // 2 + BOARD_OFFSET_Y
    return cx, cy


def animate_move(
    screen: pygame.Surface,
    board_before,
    move: "Move",
    duration_ms: int = 200,
    draw_frame_callback=None,
) -> None:
    """Animate a piece sliding from origin to destination.

    Args:
        screen: pygame display surface
        board_before: board state BEFORE the move (numpy array)
        move: the Move being played
        duration_ms: animation duration in milliseconds
        draw_frame_callback: callable(surface) that draws the full static frame
            (board, panels, status) WITHOUT the moving piece. If None, just draws board.
    """
    clock = pygame.time.Clock()

    origin = move.origin
    dest = move.destination
    piece = int(board_before[origin[0], origin[1]])
    if piece == C.EMPTY:
        return

    color = C.color_of(piece)
    is_king = C.is_king(piece)

    start_x, start_y = _square_center(origin[0], origin[1])
    end_x, end_y = _square_center(dest[0], dest[1])

    # For multi-step captures, animate through intermediate squares
    steps = list(move.squares)
    if len(steps) < 2:
        steps = [origin, dest]

    # Calculate total duration per segment
    num_segments = len(steps) - 1
    segment_ms = duration_ms // max(num_segments, 1)

    # Temporarily clear the moving piece from the board for rendering
    import numpy as np
    temp_board = board_before.copy()
    temp_board[origin[0], origin[1]] = C.EMPTY

    for seg_i in range(num_segments):
        seg_start = steps[seg_i]
        seg_end = steps[seg_i + 1]
        sx, sy = _square_center(seg_start[0], seg_start[1])
        ex, ey = _square_center(seg_end[0], seg_end[1])

        # If capture, remove the captured piece between seg_start and seg_end
        if move.is_capture and move.captured:
            mid_r = (seg_start[0] + seg_end[0]) // 2
            mid_c = (seg_start[1] + seg_end[1]) // 2
            if temp_board[mid_r, mid_c] != C.EMPTY:
                temp_board[mid_r, mid_c] = C.EMPTY

        elapsed = 0
        while elapsed < segment_ms:
            dt = clock.tick(60)
            elapsed += dt
            t = min(elapsed / segment_ms, 1.0)
            # Ease-out quad for smooth deceleration
            t_eased = 1.0 - (1.0 - t) ** 2

            cur_x = sx + (ex - sx) * t_eased
            cur_y = sy + (ey - sy) * t_eased

            # Draw full frame without the moving piece
            if draw_frame_callback:
                draw_frame_callback(screen, temp_board)
            else:
                screen.fill(COLOR_BG)
                draw_board(screen)
                draw_pieces(screen, temp_board)

            # Draw the moving piece at interpolated position
            _draw_piece(screen, int(cur_x), int(cur_y), color, is_king)

            pygame.display.flip()

            # Consume events to prevent freeze
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit
