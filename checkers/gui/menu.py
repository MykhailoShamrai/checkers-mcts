"""Simple Pygame menu for selecting game mode and player parameters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pygame

from checkers.gui.board_view import WINDOW_W, WINDOW_H, COLOR_BG, COLOR_TEXT

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
# Text-based menu rendered in Pygame
# ------------------------------------------------------------------

def run_menu(screen: pygame.Surface) -> GameConfig:
    """Display a simple interactive menu and return the chosen config."""
    font = pygame.font.SysFont("Arial", 20)
    title_font = pygame.font.SysFont("Arial", 28, bold=True)

    white_idx = 0  # human
    black_idx = 1  # uct
    selected_field = 0  # 0=white, 1=black, 2=start

    clock = pygame.time.Clock()

    while True:
        screen.fill(COLOR_BG)

        # Title
        title = title_font.render("CHECKERS — Game Setup", True, COLOR_TEXT)
        screen.blit(title, (WINDOW_W // 2 - title.get_width() // 2, 30))

        # White player
        w_color = (255, 255, 100) if selected_field == 0 else COLOR_TEXT
        w_text = font.render(f"WHITE player: < {PLAYER_OPTIONS[white_idx]} >", True, w_color)
        screen.blit(w_text, (60, 120))

        # Black player
        b_color = (255, 255, 100) if selected_field == 1 else COLOR_TEXT
        b_text = font.render(f"BLACK player: < {PLAYER_OPTIONS[black_idx]} >", True, b_color)
        screen.blit(b_text, (60, 180))

        # Start button
        s_color = (100, 255, 100) if selected_field == 2 else COLOR_TEXT
        s_text = font.render("[ START GAME ]", True, s_color)
        screen.blit(s_text, (WINDOW_W // 2 - s_text.get_width() // 2, 280))

        # Instructions
        instr = font.render("Up/Down: select field | Left/Right: change | Enter: confirm", True, (150, 150, 150))
        screen.blit(instr, (WINDOW_W // 2 - instr.get_width() // 2, WINDOW_H - 60))

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
