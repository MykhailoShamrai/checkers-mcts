"""Run experiments from the experiment matrix and write results to CSV.

Usage:
    python -m experiments.run_experiment [--output results/] [--games 50] [--quick]

The --quick flag runs a smaller subset for sanity checking.
"""

from __future__ import annotations

import argparse
import csv
import os
import time
from dataclasses import asdict
from pathlib import Path

from checkers.engine import constants as C
from checkers.players.alphabeta import AlphaBetaPlayer
from checkers.players.mcts.uct import UCTPlayer
from checkers.players.mcts.uct_minimax import UCTMinimaxPlayer
from checkers.players.mcts.uct_early_term import UCTEarlyTermPlayer
from checkers.players.random_player import RandomPlayer
from experiments.tournament import run_tournament, TournamentResult


# ------------------------------------------------------------------
# Player factories
# ------------------------------------------------------------------

def make_factory(kind: str, **kwargs):
    """Return a callable(seed) -> Player for the given kind and params."""

    def factory(seed: int):
        if kind == "uct":
            return UCTPlayer(
                iterations=kwargs.get("iterations", 1000),
                c=kwargs.get("c", 1.4),
                seed=seed,
            )
        elif kind == "uct_minimax":
            return UCTMinimaxPlayer(
                iterations=kwargs.get("iterations", 1000),
                c=kwargs.get("c", 1.4),
                minimax_depth=kwargs.get("minimax_depth", 2),
                seed=seed,
            )
        elif kind == "uct_early_term":
            return UCTEarlyTermPlayer(
                iterations=kwargs.get("iterations", 1000),
                c=kwargs.get("c", 1.4),
                playout_depth=kwargs.get("playout_depth", 20),
                alpha=kwargs.get("alpha", 0.5),
                seed=seed,
            )
        elif kind == "alphabeta":
            return AlphaBetaPlayer(
                max_depth=kwargs.get("max_depth", 6),
                seed=seed,
            )
        elif kind == "random":
            return RandomPlayer(seed=seed)
        else:
            raise ValueError(f"Unknown player kind: {kind}")

    return factory


# ------------------------------------------------------------------
# Experiment definitions (mirrors STEP0_MACIERZ_EKSPERYMENTOW.csv)
# ------------------------------------------------------------------

EXPERIMENTS = [
    # H1: UCT vs AlphaBeta — C sweep at 100 iterations
    {"id": "E01", "a": "uct", "b": "alphabeta", "a_kw": {"iterations": 100, "c": 0.1}, "b_kw": {"max_depth": 6}, "move_limit": 150},
    {"id": "E02", "a": "uct", "b": "alphabeta", "a_kw": {"iterations": 100, "c": 0.3}, "b_kw": {"max_depth": 6}, "move_limit": 150},
    {"id": "E03", "a": "uct", "b": "alphabeta", "a_kw": {"iterations": 100, "c": 0.7}, "b_kw": {"max_depth": 6}, "move_limit": 150},
    {"id": "E04", "a": "uct", "b": "alphabeta", "a_kw": {"iterations": 100, "c": 1.0}, "b_kw": {"max_depth": 6}, "move_limit": 150},
    {"id": "E05", "a": "uct", "b": "alphabeta", "a_kw": {"iterations": 100, "c": 1.4}, "b_kw": {"max_depth": 6}, "move_limit": 150},
    {"id": "E06", "a": "uct", "b": "alphabeta", "a_kw": {"iterations": 100, "c": 2.0}, "b_kw": {"max_depth": 6}, "move_limit": 150},
    {"id": "E07", "a": "uct", "b": "alphabeta", "a_kw": {"iterations": 100, "c": 3.0}, "b_kw": {"max_depth": 6}, "move_limit": 150},
    # H1: UCT vs AlphaBeta — budget sweep at c=1.4
    {"id": "E08", "a": "uct", "b": "alphabeta", "a_kw": {"iterations": 500, "c": 1.4}, "b_kw": {"max_depth": 6}, "move_limit": 150},
    {"id": "E09", "a": "uct", "b": "alphabeta", "a_kw": {"iterations": 1000, "c": 1.4}, "b_kw": {"max_depth": 6}, "move_limit": 150},
    {"id": "E10", "a": "uct", "b": "alphabeta", "a_kw": {"iterations": 5000, "c": 1.4}, "b_kw": {"max_depth": 6}, "move_limit": 150},
    {"id": "E11", "a": "uct", "b": "alphabeta", "a_kw": {"iterations": 10000, "c": 1.4}, "b_kw": {"max_depth": 6}, "move_limit": 150},
    # H2: UCT+minimax vs UCT
    {"id": "E12", "a": "uct_minimax", "b": "uct", "a_kw": {"iterations": 1000, "c": 1.4, "minimax_depth": 2}, "b_kw": {"iterations": 1000, "c": 1.4}, "move_limit": 150},
    {"id": "E13", "a": "uct_minimax", "b": "uct", "a_kw": {"iterations": 5000, "c": 1.4, "minimax_depth": 2}, "b_kw": {"iterations": 5000, "c": 1.4}, "move_limit": 150},
    # H3: UCT+early_term vs UCT
    {"id": "E14", "a": "uct_early_term", "b": "uct", "a_kw": {"iterations": 1000, "c": 1.4, "playout_depth": 20, "alpha": 0.5}, "b_kw": {"iterations": 1000, "c": 1.4}, "move_limit": 150},
    {"id": "E15", "a": "uct_early_term", "b": "uct", "a_kw": {"iterations": 5000, "c": 1.4, "playout_depth": 20, "alpha": 0.5}, "b_kw": {"iterations": 5000, "c": 1.4}, "move_limit": 150},
    # H4: move_limit=100 experiments
    {"id": "E16", "a": "uct", "b": "alphabeta", "a_kw": {"iterations": 1000, "c": 1.4}, "b_kw": {"max_depth": 6}, "move_limit": 100},
    {"id": "E17", "a": "uct_minimax", "b": "alphabeta", "a_kw": {"iterations": 1000, "c": 1.4, "minimax_depth": 2}, "b_kw": {"max_depth": 6}, "move_limit": 100},
    {"id": "E18", "a": "uct_early_term", "b": "alphabeta", "a_kw": {"iterations": 1000, "c": 1.4, "playout_depth": 20, "alpha": 0.5}, "b_kw": {"max_depth": 6}, "move_limit": 100},
]


def run_single_experiment(
    exp: dict,
    num_games: int,
    seeds: list[int],
    output_dir: Path,
    verbose: bool = True,
    workers: int | None = None,
) -> None:
    """Run one experiment config and append results to CSV."""
    exp_id = exp["id"]
    if verbose:
        print(f"{'='*60}")
        print(f"Running {exp_id}: {exp['a']}({exp['a_kw']}) vs {exp['b']}({exp['b_kw']}) "
              f"move_limit={exp['move_limit']} | workers={workers or 'all cores'}")
        print(f"{'='*60}")

    factory_a = make_factory(exp["a"], **exp["a_kw"])
    factory_b = make_factory(exp["b"], **exp["b_kw"])

    # Picklable specs for parallel mode
    spec_a = (exp["a"], exp["a_kw"])
    spec_b = (exp["b"], exp["b_kw"])

    t0 = time.perf_counter()
    result = run_tournament(
        player_a_factory=factory_a,
        player_b_factory=factory_b,
        player_a_name=exp["a"],
        player_b_name=exp["b"],
        num_games=num_games,
        seeds=seeds,
        move_limit=exp["move_limit"],
        swap_colors=True,
        verbose=verbose,
        workers=workers,
        player_a_spec=spec_a,
        player_b_spec=spec_b,
    )
    elapsed = time.perf_counter() - t0

    if verbose:
        print(f"  Elapsed: {elapsed:.1f}s")

    # Write to CSV
    csv_path = output_dir / f"{exp_id}.csv"
    _write_csv(result, exp, csv_path)
    if verbose:
        print(f"  Saved: {csv_path}")


def _write_csv(result: TournamentResult, exp: dict, path: Path) -> None:
    """Write tournament results to a CSV file."""
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "experiment_id", "game_id", "seed",
        "player_a", "player_b", "player_a_params", "player_b_params",
        "white_player", "black_player",
        "winner", "winner_color", "num_plies",
        "avg_time_white", "avg_time_black", "move_limit",
    ]

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for g in result.games:
            writer.writerow({
                "experiment_id": exp["id"],
                "game_id": g.game_id,
                "seed": g.seed,
                "player_a": g.player_a,
                "player_b": g.player_b,
                "player_a_params": str(exp["a_kw"]),
                "player_b_params": str(exp["b_kw"]),
                "white_player": g.white_player,
                "black_player": g.black_player,
                "winner": g.winner if g.winner else "draw",
                "winner_color": g.winner_color if g.winner_color else "draw",
                "num_plies": g.num_plies,
                "avg_time_white": f"{g.avg_time_white:.6f}",
                "avg_time_black": f"{g.avg_time_black:.6f}",
                "move_limit": g.move_limit,
            })


def main():
    parser = argparse.ArgumentParser(description="Run checkers MCTS experiments")
    parser.add_argument("--output", type=str, default="results", help="Output directory for CSV files")
    parser.add_argument("--games", type=int, default=50, help="Number of games per experiment")
    parser.add_argument("--seeds", type=int, default=20, help="Number of distinct seeds")
    parser.add_argument("--workers", type=int, default=None, help="Number of parallel processes (default: all CPU cores)")
    parser.add_argument("--quick", action="store_true", help="Quick mode: 4 games, subset of experiments")
    parser.add_argument("--experiments", type=str, nargs="*", help="Run only specific experiment IDs (e.g. E01 E02)")
    args = parser.parse_args()

    output_dir = Path(args.output)
    num_games = 4 if args.quick else args.games
    num_seeds = 4 if args.quick else args.seeds
    seeds = list(range(num_seeds))

    experiments = EXPERIMENTS
    if args.experiments:
        experiments = [e for e in EXPERIMENTS if e["id"] in args.experiments]
    elif args.quick:
        # In quick mode, run only E01 and E12 for sanity check
        experiments = [e for e in EXPERIMENTS if e["id"] in ("E01", "E12")]

    print(f"Output: {output_dir}")
    print(f"Games per experiment: {num_games}")
    print(f"Seeds: {seeds[:5]}{'...' if len(seeds) > 5 else ''}")
    print(f"Workers: {args.workers or 'all CPU cores'}")
    print(f"Experiments to run: {[e['id'] for e in experiments]}")
    print(f"Total experiments: {len(experiments)}")
    print()

    total_exp = len(experiments)
    total_start = time.perf_counter()

    for i, exp in enumerate(experiments, 1):
        print(f"\n[{i}/{total_exp}] ", end="")
        run_single_experiment(exp, num_games, seeds, output_dir, verbose=True, workers=args.workers)
        elapsed_total = time.perf_counter() - total_start
        avg_per_exp = elapsed_total / i
        remaining = avg_per_exp * (total_exp - i)
        mins_left = remaining / 60
        print(f"  ⏱ Total elapsed: {elapsed_total/60:.1f} min | "
              f"Est. remaining: {mins_left:.1f} min ({total_exp - i} experiments left)")

    total_elapsed = time.perf_counter() - total_start
    print(f"\n✓ All experiments complete in {total_elapsed/60:.1f} minutes.")


if __name__ == "__main__":
    main()
