"""Tournament runner — plays N games between two players, alternates colors,
logs per-game metrics to a list of dicts (ready for CSV export).

Supports multiprocessing for significant speedup on multi-core machines.
"""

from __future__ import annotations

import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Optional

from checkers.engine import constants as C
from checkers.engine.game_state import GameState
from checkers.players.base import Player


@dataclass
class GameResult:
    game_id: int
    seed: int
    player_a: str
    player_b: str
    white_player: str  # which of a/b played white
    black_player: str
    winner: Optional[str]  # "a", "b", or None (draw)
    winner_color: Optional[int]
    num_plies: int
    avg_time_white: float  # seconds per move
    avg_time_black: float
    move_limit: int


@dataclass
class TournamentResult:
    games: list[GameResult] = field(default_factory=list)

    @property
    def a_wins(self) -> int:
        return sum(1 for g in self.games if g.winner == "a")

    @property
    def b_wins(self) -> int:
        return sum(1 for g in self.games if g.winner == "b")

    @property
    def draws(self) -> int:
        return sum(1 for g in self.games if g.winner is None)

    def summary(self) -> str:
        total = len(self.games)
        return (
            f"Games: {total} | A wins: {self.a_wins} ({self.a_wins/total*100:.1f}%) | "
            f"B wins: {self.b_wins} ({self.b_wins/total*100:.1f}%) | "
            f"Draws: {self.draws} ({self.draws/total*100:.1f}%)"
        )


def play_one_game(
    white_player: Player,
    black_player: Player,
    move_limit: int = C.MOVE_LIMIT,
) -> tuple[Optional[int], int, float, float]:
    """Play a single game to completion.

    Returns: (winner_color or None, num_plies, avg_time_white, avg_time_black)
    """
    state = GameState.initial(move_limit=move_limit)
    white_times: list[float] = []
    black_times: list[float] = []

    while not state.is_terminal():
        current = white_player if state.to_move == C.WHITE else black_player
        t0 = time.perf_counter()
        move = current.choose_move(state)
        elapsed = time.perf_counter() - t0

        if state.to_move == C.WHITE:
            white_times.append(elapsed)
        else:
            black_times.append(elapsed)

        state = state.play(move)

    winner_color = state.winner()
    avg_w = sum(white_times) / len(white_times) if white_times else 0.0
    avg_b = sum(black_times) / len(black_times) if black_times else 0.0
    return winner_color, state.ply, avg_w, avg_b


def _play_single_game_task(args: tuple) -> GameResult:
    """Top-level function for multiprocessing — plays one game and returns result."""
    (game_id, seed, player_a_spec, player_b_spec,
     player_a_name, player_b_name, swap_colors, move_limit) = args

    if swap_colors and game_id % 2 == 1:
        white_name, black_name = player_b_name, player_a_name
        white_p = _build_player_from_spec(player_b_spec, seed)
        black_p = _build_player_from_spec(player_a_spec, seed)
        a_is_white = False
    else:
        white_name, black_name = player_a_name, player_b_name
        white_p = _build_player_from_spec(player_a_spec, seed)
        black_p = _build_player_from_spec(player_b_spec, seed)
        a_is_white = True

    winner_color, num_plies, avg_w, avg_b = play_one_game(
        white_p, black_p, move_limit=move_limit
    )

    if winner_color is None:
        winner = None
    elif winner_color == C.WHITE:
        winner = "a" if a_is_white else "b"
    else:
        winner = "b" if a_is_white else "a"

    return GameResult(
        game_id=game_id,
        seed=seed,
        player_a=player_a_name,
        player_b=player_b_name,
        white_player=white_name,
        black_player=black_name,
        winner=winner,
        winner_color=winner_color,
        num_plies=num_plies,
        avg_time_white=avg_w,
        avg_time_black=avg_b,
        move_limit=move_limit,
    )


def _build_player_from_spec(spec: tuple, seed: int) -> Player:
    """Build a player from a picklable spec: (kind, kwargs_dict)."""
    from checkers.players.mcts.uct import UCTPlayer
    from checkers.players.mcts.uct_minimax import UCTMinimaxPlayer
    from checkers.players.mcts.uct_early_term import UCTEarlyTermPlayer
    from checkers.players.alphabeta import AlphaBetaPlayer
    from checkers.players.random_player import RandomPlayer

    kind, kwargs = spec
    if kind == "uct":
        return UCTPlayer(iterations=kwargs.get("iterations", 1000),
                         c=kwargs.get("c", 1.4), seed=seed)
    elif kind == "uct_minimax":
        return UCTMinimaxPlayer(iterations=kwargs.get("iterations", 1000),
                                c=kwargs.get("c", 1.4),
                                minimax_depth=kwargs.get("minimax_depth", 2), seed=seed)
    elif kind == "uct_early_term":
        return UCTEarlyTermPlayer(iterations=kwargs.get("iterations", 1000),
                                  c=kwargs.get("c", 1.4),
                                  playout_depth=kwargs.get("playout_depth", 20),
                                  alpha=kwargs.get("alpha", 0.5), seed=seed)
    elif kind == "alphabeta":
        return AlphaBetaPlayer(max_depth=kwargs.get("max_depth", 6), seed=seed)
    elif kind == "random":
        return RandomPlayer(seed=seed)
    else:
        raise ValueError(f"Unknown player kind: {kind}")


def run_tournament(
    player_a_factory,
    player_b_factory,
    player_a_name: str = "player_a",
    player_b_name: str = "player_b",
    num_games: int = 50,
    seeds: list[int] | None = None,
    move_limit: int = C.MOVE_LIMIT,
    swap_colors: bool = True,
    verbose: bool = True,
    workers: int | None = None,
    player_a_spec: tuple | None = None,
    player_b_spec: tuple | None = None,
) -> TournamentResult:
    """Run a tournament of ``num_games`` between two player factories.

    Args:
        player_a_factory: callable(seed) -> Player (used in sequential mode)
        player_b_factory: callable(seed) -> Player (used in sequential mode)
        player_a_spec: picklable (kind, kwargs) tuple for parallel mode
        player_b_spec: picklable (kind, kwargs) tuple for parallel mode
        seeds: list of seeds to use; if None, uses range(num_games).
        swap_colors: if True, alternate who plays white each game.
        workers: number of parallel processes (None = all CPU cores).
    """
    if seeds is None:
        seeds = list(range(num_games))
    if len(seeds) < num_games:
        seeds = [seeds[i % len(seeds)] for i in range(num_games)]

    if workers is None:
        workers = min(os.cpu_count() or 4, num_games)

    # Decide if we can use parallel mode (need specs for pickling)
    use_parallel = workers > 1 and player_a_spec is not None and player_b_spec is not None

    result = TournamentResult()

    if not use_parallel:
        # Sequential fallback
        for game_id in range(num_games):
            seed = seeds[game_id]
            if swap_colors and game_id % 2 == 1:
                white_name, black_name = player_b_name, player_a_name
                white_p = player_b_factory(seed)
                black_p = player_a_factory(seed)
                a_is_white = False
            else:
                white_name, black_name = player_a_name, player_b_name
                white_p = player_a_factory(seed)
                black_p = player_b_factory(seed)
                a_is_white = True

            winner_color, num_plies, avg_w, avg_b = play_one_game(
                white_p, black_p, move_limit=move_limit
            )

            if winner_color is None:
                winner = None
            elif winner_color == C.WHITE:
                winner = "a" if a_is_white else "b"
            else:
                winner = "b" if a_is_white else "a"

            gr = GameResult(
                game_id=game_id, seed=seed,
                player_a=player_a_name, player_b=player_b_name,
                white_player=white_name, black_player=black_name,
                winner=winner, winner_color=winner_color,
                num_plies=num_plies, avg_time_white=avg_w, avg_time_black=avg_b,
                move_limit=move_limit,
            )
            result.games.append(gr)
            if verbose:
                w_str = gr.winner if gr.winner else "draw"
                print(f"  Game {game_id+1}/{num_games} seed={gr.seed} "
                      f"white={gr.white_player} black={gr.black_player} → {w_str} "
                      f"({gr.num_plies} plies)")
    else:
        # Parallel execution
        tasks = [
            (game_id, seeds[game_id], player_a_spec, player_b_spec,
             player_a_name, player_b_name, swap_colors, move_limit)
            for game_id in range(num_games)
        ]

        completed = 0
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(_play_single_game_task, t): t[0] for t in tasks}
            for future in as_completed(futures):
                gr = future.result()
                result.games.append(gr)
                completed += 1
                if verbose:
                    w_str = gr.winner if gr.winner else "draw"
                    print(f"  [{completed}/{num_games}] Game {gr.game_id+1} seed={gr.seed} "
                          f"white={gr.white_player} black={gr.black_player} → {w_str} "
                          f"({gr.num_plies} plies)")

        # Sort by game_id for consistent ordering
        result.games.sort(key=lambda g: g.game_id)

    if verbose:
        print(result.summary())

    return result
