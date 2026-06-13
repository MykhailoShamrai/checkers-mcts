"""Tournament runner — plays N games between two players, alternates colors,
logs per-game metrics to a list of dicts (ready for CSV export).
"""

from __future__ import annotations

import time
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
) -> TournamentResult:
    """Run a tournament of ``num_games`` between two player factories.

    Args:
        player_a_factory: callable(seed) -> Player
        player_b_factory: callable(seed) -> Player
        seeds: list of seeds to use; if None, uses range(num_games).
        swap_colors: if True, alternate who plays white each game.
    """
    if seeds is None:
        seeds = list(range(num_games))
    if len(seeds) < num_games:
        # Cycle seeds if fewer provided
        seeds = [seeds[i % len(seeds)] for i in range(num_games)]

    result = TournamentResult()

    for game_id in range(num_games):
        seed = seeds[game_id]

        # Determine color assignment
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

        # Map winner_color to "a"/"b"/None
        if winner_color is None:
            winner = None
        elif winner_color == C.WHITE:
            winner = "a" if a_is_white else "b"
        else:
            winner = "b" if a_is_white else "a"

        gr = GameResult(
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
        result.games.append(gr)

        if verbose:
            w_str = winner if winner else "draw"
            print(f"  Game {game_id+1}/{num_games} seed={seed} "
                  f"white={white_name} black={black_name} → {w_str} "
                  f"({num_plies} plies)")

    if verbose:
        print(result.summary())

    return result
