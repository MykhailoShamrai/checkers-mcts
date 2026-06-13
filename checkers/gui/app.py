"""Main Pygame application loop — handles turns, input, and bot integration."""

from __future__ import annotations

import threading
from typing import Optional

import numpy as np
import pygame

from checkers.engine import constants as C
from checkers.engine.game_state import GameState
from checkers.engine.move import Move
from checkers.gui.board_view import (
    WINDOW_W,
    WINDOW_H,
    COLOR_BG,
    draw_board,
    draw_pieces,
    draw_highlight,
    draw_legal_targets,
    draw_captured_pieces,
    draw_status,
    draw_bottom_bar,
    pixel_to_square,
    animate_move,
)
from checkers.gui.menu import GameConfig, PlayerConfig, run_menu
from checkers.players.base import Player
from checkers.players.random_player import RandomPlayer
from checkers.players.mcts.uct import UCTPlayer
from checkers.players.mcts.uct_minimax import UCTMinimaxPlayer
from checkers.players.mcts.uct_early_term import UCTEarlyTermPlayer
from checkers.players.alphabeta import AlphaBetaPlayer


def _build_player(cfg: PlayerConfig) -> Optional[Player]:
    """Construct a Player from config, or None for human."""
    if cfg.kind == "human":
        return None
    elif cfg.kind == "random":
        return RandomPlayer(seed=cfg.seed)
    elif cfg.kind == "uct":
        return UCTPlayer(iterations=cfg.iterations, c=cfg.c, seed=cfg.seed)
    elif cfg.kind == "uct_minimax":
        return UCTMinimaxPlayer(
            iterations=cfg.iterations, c=cfg.c,
            minimax_depth=cfg.minimax_depth, seed=cfg.seed,
        )
    elif cfg.kind == "uct_early_term":
        return UCTEarlyTermPlayer(
            iterations=cfg.iterations, c=cfg.c,
            playout_depth=cfg.playout_depth, alpha=cfg.alpha, seed=cfg.seed,
        )
    elif cfg.kind == "alphabeta":
        return AlphaBetaPlayer(max_depth=cfg.max_depth, seed=cfg.seed)
    else:
        raise ValueError(f"Unknown player kind: {cfg.kind}")


def run_app() -> None:
    """Launch the full GUI application (menu → game loop)."""
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("Checkers — MCTS Project")

    config = run_menu(screen)

    white_player = _build_player(config.white)
    black_player = _build_player(config.black)

    state = GameState.initial(move_limit=config.move_limit)

    # Game loop state
    selected: Optional[tuple[int, int]] = None
    legal_moves: list[Move] = state.legal_moves()
    bot_thinking = False
    bot_move_result: Optional[Move] = None
    game_over = False
    status_text = _status_text(state, config, game_over)

    # Track captured pieces
    white_men_captured = 0
    white_kings_captured = 0
    black_men_captured = 0
    black_kings_captured = 0

    clock = pygame.time.Clock()

    def _draw_frame(surface, board):
        """Draw a full frame with a given board (used by animation)."""
        surface.fill(COLOR_BG)
        draw_board(surface)
        draw_pieces(surface, board)
        draw_captured_pieces(surface,
                            white_men_captured, white_kings_captured,
                            black_men_captured, black_kings_captured)
        draw_status(surface, status_text, game_over)
        draw_bottom_bar(surface, state.ply, state.move_limit)

    while True:
        # --- Event handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    # Restart
                    state = GameState.initial(move_limit=config.move_limit)
                    legal_moves = state.legal_moves()
                    selected = None
                    game_over = False
                    bot_thinking = False
                    bot_move_result = None
                    white_men_captured = 0
                    white_kings_captured = 0
                    black_men_captured = 0
                    black_kings_captured = 0
                    status_text = _status_text(state, config, game_over)
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    return

            if event.type == pygame.MOUSEBUTTONDOWN and not game_over and not bot_thinking:
                current_player = white_player if state.to_move == C.WHITE else black_player
                if current_player is None:  # human turn
                    sq = pixel_to_square(event.pos)
                    if sq is not None:
                        # Check if this click completes a move
                        move_to_play = None
                        if selected is not None:
                            for move in legal_moves:
                                if move.origin == selected and move.destination == sq:
                                    move_to_play = move
                                    break

                        if move_to_play is not None:
                            # Animate then play
                            animate_move(screen, state.board, move_to_play,
                                         duration_ms=200, draw_frame_callback=_draw_frame)
                            old_board = state.board.copy()
                            state = state.play(move_to_play)
                            _update_captures(old_board, state.board, locals_dict := {})
                            white_men_captured += locals_dict.get("wm", 0)
                            white_kings_captured += locals_dict.get("wk", 0)
                            black_men_captured += locals_dict.get("bm", 0)
                            black_kings_captured += locals_dict.get("bk", 0)
                            legal_moves = state.legal_moves() if not state.is_terminal() else []
                            selected = None
                            game_over = state.is_terminal()
                        else:
                            # Select a piece that has legal moves
                            piece = int(state.board[sq[0], sq[1]])
                            if piece != C.EMPTY and C.color_of(piece) == state.to_move:
                                has_moves = any(m.origin == sq for m in legal_moves)
                                if has_moves:
                                    selected = sq
                                else:
                                    selected = None
                            else:
                                selected = None
                        status_text = _status_text(state, config, game_over)

        # --- Bot turn ---
        if not game_over and not bot_thinking:
            current_player = white_player if state.to_move == C.WHITE else black_player
            if current_player is not None:
                bot_thinking = True
                status_text = f"{'WHITE' if state.to_move == C.WHITE else 'BLACK'} ({_player_name(state, config)}) thinking..."

                def _bot_work(player=current_player, st=state):
                    nonlocal bot_move_result
                    bot_move_result = player.choose_move(st)

                thread = threading.Thread(target=_bot_work, daemon=True)
                thread.start()

        # Check if bot finished
        if bot_thinking and bot_move_result is not None:
            # Animate the bot's move
            animate_move(screen, state.board, bot_move_result,
                         duration_ms=250, draw_frame_callback=_draw_frame)
            old_board = state.board.copy()
            state = state.play(bot_move_result)
            # Count captures from bot move
            _update_captures(old_board, state.board, locals_dict := {})
            white_men_captured += locals_dict.get("wm", 0)
            white_kings_captured += locals_dict.get("wk", 0)
            black_men_captured += locals_dict.get("bm", 0)
            black_kings_captured += locals_dict.get("bk", 0)

            legal_moves = state.legal_moves() if not state.is_terminal() else []
            selected = None
            bot_move_result = None
            bot_thinking = False
            game_over = state.is_terminal()
            status_text = _status_text(state, config, game_over)

        # --- Drawing ---
        screen.fill(COLOR_BG)
        draw_board(screen)
        draw_pieces(screen, state.board)
        draw_captured_pieces(screen,
                            white_men_captured, white_kings_captured,
                            black_men_captured, black_kings_captured)

        if selected is not None:
            draw_highlight(screen, selected)
            draw_legal_targets(screen, legal_moves, selected)

        draw_status(screen, status_text, game_over)
        draw_bottom_bar(screen, state.ply, state.move_limit)
        pygame.display.flip()
        clock.tick(60)


def _handle_click(
    sq: tuple[int, int],
    selected: Optional[tuple[int, int]],
    state: GameState,
    legal_moves: list[Move],
) -> tuple[Optional[tuple[int, int]], GameState, list[Move], bool]:
    """Process a human click; return updated (selected, state, legal_moves, game_over)."""
    # If clicking on a legal destination of selected piece -> make the move
    if selected is not None:
        for move in legal_moves:
            if move.origin == selected and move.destination == sq:
                state = state.play(move)
                new_legal = state.legal_moves() if not state.is_terminal() else []
                return None, state, new_legal, state.is_terminal()

    # Select a piece that has legal moves
    piece = int(state.board[sq[0], sq[1]])
    if piece != C.EMPTY and C.color_of(piece) == state.to_move:
        has_moves = any(m.origin == sq for m in legal_moves)
        if has_moves:
            return sq, state, legal_moves, False

    return None, state, legal_moves, False


def _update_captures(old_board: np.ndarray, new_board: np.ndarray, out: dict) -> None:
    """Compare boards and count newly captured pieces."""
    wm = int(np.count_nonzero(old_board == C.WHITE_MAN)) - int(np.count_nonzero(new_board == C.WHITE_MAN))
    wk = int(np.count_nonzero(old_board == C.WHITE_KING)) - int(np.count_nonzero(new_board == C.WHITE_KING))
    bm = int(np.count_nonzero(old_board == C.BLACK_MAN)) - int(np.count_nonzero(new_board == C.BLACK_MAN))
    bk = int(np.count_nonzero(old_board == C.BLACK_KING)) - int(np.count_nonzero(new_board == C.BLACK_KING))
    # Only count positive differences (pieces that disappeared = captured)
    out["wm"] = max(0, wm)
    out["wk"] = max(0, wk)
    out["bm"] = max(0, bm)
    out["bk"] = max(0, bk)


def _player_name(state: GameState, config: GameConfig) -> str:
    cfg = config.white if state.to_move == C.WHITE else config.black
    return cfg.kind


def _status_text(state: GameState, config: GameConfig, game_over: bool) -> str:
    if game_over:
        winner = state.winner()
        if winner is None:
            return f"DRAW — move limit {state.move_limit} reached"
        name = "WHITE" if winner == C.WHITE else "BLACK"
        return f"{name} WINS!"
    to_move = "WHITE" if state.to_move == C.WHITE else "BLACK"
    kind = _player_name(state, config)
    return f"{to_move}'s turn  •  {kind}"
