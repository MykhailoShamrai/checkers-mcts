"""Pygame menu for selecting game mode and player parameters — polished version."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pygame

from checkers.gui.board_view import WINDOW_W, WINDOW_H, COLOR_BG, COLOR_TEXT, COLOR_PANEL_BG

# ------------------------------------------------------------------
# Menu data structures
# ------------------------------------------------------------------

PLAYER_OPTIONS = [
    "human",
    "uct",
    "uct_minimax",
    "uct_early_term",
    "alphabeta",
    "random",
]

PLAYER_LABELS = {
    "human": "Human",
    "uct": "UCT (basic)",
    "uct_minimax": "UCT + Minimax",
    "uct_early_term": "UCT + Early Term",
    "alphabeta": "Alpha-Beta",
    "random": "Random",
}


@dataclass
class PlayerConfig:
    kind: str = "human"
    iterations: int = 1000
    c: float = 1.4
    minimax_depth: int = 2
    playout_depth: int = 20
    alpha: float = 0.5
    max_depth: int = 6
    seed: Optional[int] = None


@dataclass
class GameConfig:
    white: PlayerConfig
    black: PlayerConfig
    move_limit: int = 150


# ------------------------------------------------------------------
# Polished menu
# ------------------------------------------------------------------

def _draw_gradient(surface: pygame.Surface, color_top: tuple, color_bottom: tuple) -> None:
    """Draw a vertical gradient background."""
    h = surface.get_height()
    for y in range(h):
        t = y / h
        r = int(color_top[0] * (1 - t) + color_bottom[0] * t)
        g = int(color_top[1] * (1 - t) + color_bottom[1] * t)
        b = int(color_top[2] * (1 - t) + color_bottom[2] * t)
        pygame.draw.line(surface, (r, g, b), (0, y), (WINDOW_W, y))


def _draw_mini_board(surface: pygame.Surface, x: int, y: int, size: int = 160) -> None:
    """Draw a decorative mini checkerboard."""
    sq = size // 8
    for row in range(8):
        for col in range(8):
            color = (139, 90, 43) if (row + col) % 2 == 1 else (245, 222, 179)
            pygame.draw.rect(surface, color, (x + col * sq, y + row * sq, sq, sq))


def _draw_selector(
    surface: pygame.Surface,
    y: int,
    label: str,
    value: str,
    active: bool,
    color_dot: tuple,
) -> None:
    """Draw a player selector row."""
    font = pygame.font.SysFont("Segoe UI", 20)
    label_font = pygame.font.SysFont("Segoe UI", 16)

    # Background card
    card_x = WINDOW_W // 2 - 200
    card_w = 400
    card_h = 56
    card_color = (60, 60, 70) if active else (50, 50, 56)
    border_color = (255, 215, 0) if active else (80, 80, 90)
    pygame.draw.rect(surface, card_color, (card_x, y, card_w, card_h), border_radius=8)
    pygame.draw.rect(surface, border_color, (card_x, y, card_w, card_h), 2, border_radius=8)

    # Color indicator dot
    pygame.draw.circle(surface, color_dot, (card_x + 24, y + card_h // 2), 10)
    pygame.draw.circle(surface, (200, 200, 200), (card_x + 24, y + card_h // 2), 10, 1)

    # Label
    lbl = label_font.render(label, True, (180, 180, 180))
    surface.blit(lbl, (card_x + 44, y + 6))

    # Value with arrows
    arrow_color = (255, 215, 0) if active else (120, 120, 120)
    arrow_l = font.render("◀", True, arrow_color)
    arrow_r = font.render("▶", True, arrow_color)

    val_text = font.render(value, True, COLOR_TEXT)
    val_x = WINDOW_W // 2 - val_text.get_width() // 2 + 20
    surface.blit(arrow_l, (val_x - 30, y + 26))
    surface.blit(val_text, (val_x, y + 28))
    surface.blit(arrow_r, (val_x + val_text.get_width() + 10, y + 26))


def run_menu(screen: pygame.Surface) -> GameConfig:
    """Display a polished interactive menu and return the chosen config."""
    title_font = pygame.font.SysFont("Segoe UI", 34, bold=True)
    subtitle_font = pygame.font.SysFont("Segoe UI", 15)
    btn_font = pygame.font.SysFont("Segoe UI", 22, bold=True)
    hint_font = pygame.font.SysFont("Segoe UI", 13)

    white_idx = 0  # human
    black_idx = 4  # alphabeta
    selected_field = 0  # 0=white, 1=black, 2=start

    # Pre-render gradient background
    bg_surface = pygame.Surface((WINDOW_W, WINDOW_H))
    _draw_gradient(bg_surface, (30, 30, 40), (20, 20, 28))

    clock = pygame.time.Clock()

    while True:
        screen.blit(bg_surface, (0, 0))

        # Decorative mini boards in corners
        _draw_mini_board(screen, 10, WINDOW_H - 170, 160)
        _draw_mini_board(screen, WINDOW_W - 170, WINDOW_H - 170, 160)
        # Dim them
        dim = pygame.Surface((160, 160), pygame.SRCALPHA)
        dim.fill((20, 20, 28, 180))
        screen.blit(dim, (10, WINDOW_H - 170))
        screen.blit(dim, (WINDOW_W - 170, WINDOW_H - 170))

        # Title
        title = title_font.render("♟  CHECKERS  ♟", True, (255, 215, 0))
        screen.blit(title, (WINDOW_W // 2 - title.get_width() // 2, 40))

        subtitle = subtitle_font.render("Monte Carlo Tree Search — Experiment Platform", True, (150, 150, 160))
        screen.blit(subtitle, (WINDOW_W // 2 - subtitle.get_width() // 2, 82))

        # Separator line
        pygame.draw.line(screen, (80, 80, 90), (WINDOW_W // 2 - 180, 115), (WINDOW_W // 2 + 180, 115))

        # Player selectors
        _draw_selector(screen, 140, "WHITE player", PLAYER_LABELS[PLAYER_OPTIONS[white_idx]],
                       selected_field == 0, (255, 250, 240))
        _draw_selector(screen, 220, "BLACK player", PLAYER_LABELS[PLAYER_OPTIONS[black_idx]],
                       selected_field == 1, (50, 50, 50))

        # Start button
        btn_y = 320
        btn_w = 220
        btn_h = 50
        btn_x = WINDOW_W // 2 - btn_w // 2
        btn_active = selected_field == 2
        btn_color = (34, 139, 34) if btn_active else (50, 100, 50)
        btn_border = (80, 255, 80) if btn_active else (60, 120, 60)
        pygame.draw.rect(screen, btn_color, (btn_x, btn_y, btn_w, btn_h), border_radius=10)
        pygame.draw.rect(screen, btn_border, (btn_x, btn_y, btn_w, btn_h), 2, border_radius=10)
        btn_text = btn_font.render("▶  START GAME", True, (240, 255, 240))
        screen.blit(btn_text, (btn_x + btn_w // 2 - btn_text.get_width() // 2, btn_y + 12))

        # Hint
        hint = hint_font.render("↑↓ select  |  ← → change  |  Enter confirm", True, (100, 100, 110))
        screen.blit(hint, (WINDOW_W // 2 - hint.get_width() // 2, WINDOW_H - 35))

        pygame.display.flip()
        clock.tick(30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN:
                    selected_field = min(selected_field + 1, 2)
                elif event.key == pygame.K_UP:
                    selected_field = max(selected_field - 1, 0)
                elif event.key == pygame.K_LEFT:
                    if selected_field == 0:
                        white_idx = (white_idx - 1) % len(PLAYER_OPTIONS)
                    elif selected_field == 1:
                        black_idx = (black_idx - 1) % len(PLAYER_OPTIONS)
                elif event.key == pygame.K_RIGHT:
                    if selected_field == 0:
                        white_idx = (white_idx + 1) % len(PLAYER_OPTIONS)
                    elif selected_field == 1:
                        black_idx = (black_idx + 1) % len(PLAYER_OPTIONS)
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if selected_field == 2:
                        return GameConfig(
                            white=PlayerConfig(kind=PLAYER_OPTIONS[white_idx]),
                            black=PlayerConfig(kind=PLAYER_OPTIONS[black_idx]),
                        )
                    else:
                        selected_field = 2  # jump to start
