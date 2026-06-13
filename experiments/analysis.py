"""Statistical analysis and visualization of experiment results.

Reads CSV files from results/ directory, computes aggregated statistics
(mean, std, 95% CI), and generates comparative plots.

Usage:
    python -m experiments.analysis [--input results/] [--output results/plots/]
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")  # non-interactive backend for saving plots


def load_all_results(input_dir: Path) -> pd.DataFrame:
    """Load all experiment CSV files into a single DataFrame."""
    frames = []
    for csv_file in sorted(input_dir.glob("E*.csv")):
        df = pd.read_csv(csv_file)
        frames.append(df)
    if not frames:
        raise FileNotFoundError(f"No experiment CSV files found in {input_dir}")
    return pd.concat(frames, ignore_index=True)


def compute_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Compute per-experiment aggregate statistics."""
    records = []
    for exp_id, group in df.groupby("experiment_id"):
        n = len(group)
        a_wins = (group["winner"] == "a").sum()
        b_wins = (group["winner"] == "b").sum()
        draws = (group["winner"] == "draw").sum()

        a_win_rate = a_wins / n
        b_win_rate = b_wins / n
        draw_rate = draws / n

        # 95% CI for win rate (binomial approximation)
        a_ci = 1.96 * np.sqrt(a_win_rate * (1 - a_win_rate) / n) if n > 1 else 0

        avg_plies = group["num_plies"].mean()
        std_plies = group["num_plies"].std()

        avg_time_w = group["avg_time_white"].mean()
        avg_time_b = group["avg_time_black"].mean()

        records.append({
            "experiment_id": exp_id,
            "n_games": n,
            "player_a": group["player_a"].iloc[0],
            "player_b": group["player_b"].iloc[0],
            "player_a_params": group["player_a_params"].iloc[0],
            "player_b_params": group["player_b_params"].iloc[0],
            "move_limit": group["move_limit"].iloc[0],
            "a_wins": a_wins,
            "b_wins": b_wins,
            "draws": draws,
            "a_win_rate": a_win_rate,
            "b_win_rate": b_win_rate,
            "draw_rate": draw_rate,
            "a_win_rate_ci95": a_ci,
            "avg_game_length": avg_plies,
            "std_game_length": std_plies,
            "avg_time_white": avg_time_w,
            "avg_time_black": avg_time_b,
        })

    return pd.DataFrame(records)


def plot_c_sweep(stats: pd.DataFrame, output_dir: Path) -> None:
    """Plot win rate vs exploration constant C (experiments E01-E07)."""
    c_exps = stats[stats["experiment_id"].isin([f"E0{i}" for i in range(1, 8)])]
    if c_exps.empty:
        return

    c_values = [0.1, 0.3, 0.7, 1.0, 1.4, 2.0, 3.0]
    if len(c_exps) != len(c_values):
        c_values = c_values[:len(c_exps)]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.errorbar(
        c_values[:len(c_exps)],
        c_exps["a_win_rate"].values,
        yerr=c_exps["a_win_rate_ci95"].values,
        marker="o", capsize=4, linewidth=2,
    )
    ax.set_xlabel("Exploration constant C")
    ax.set_ylabel("UCT Win Rate vs AlphaBeta")
    ax.set_title("H1: UCT Win Rate vs C (100 iterations)")
    ax.set_ylim(-0.05, 1.05)
    ax.axhline(0.5, color="gray", linestyle="--", alpha=0.5)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / "h1_c_sweep.png", dpi=150)
    plt.close()


def plot_budget_sweep(stats: pd.DataFrame, output_dir: Path) -> None:
    """Plot win rate vs iteration budget (experiments E05, E08-E11)."""
    budget_ids = ["E05", "E08", "E09", "E10", "E11"]
    b_exps = stats[stats["experiment_id"].isin(budget_ids)]
    if b_exps.empty:
        return

    budgets = [100, 500, 1000, 5000, 10000]
    budgets = budgets[:len(b_exps)]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.errorbar(
        budgets,
        b_exps["a_win_rate"].values,
        yerr=b_exps["a_win_rate_ci95"].values,
        marker="s", capsize=4, linewidth=2, color="tab:orange",
    )
    ax.set_xlabel("MCTS Iterations")
    ax.set_ylabel("UCT Win Rate vs AlphaBeta")
    ax.set_title("H1: UCT Win Rate vs Budget (C=1.4)")
    ax.set_xscale("log")
    ax.set_ylim(-0.05, 1.05)
    ax.axhline(0.5, color="gray", linestyle="--", alpha=0.5)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / "h1_budget_sweep.png", dpi=150)
    plt.close()


def plot_variants_comparison(stats: pd.DataFrame, output_dir: Path) -> None:
    """Bar chart comparing UCT variants (E12-E15)."""
    variant_ids = ["E12", "E13", "E14", "E15"]
    v_exps = stats[stats["experiment_id"].isin(variant_ids)]
    if v_exps.empty:
        return

    fig, ax = plt.subplots(figsize=(8, 5))
    labels = []
    win_rates = []
    cis = []
    for _, row in v_exps.iterrows():
        labels.append(f"{row['experiment_id']}\n{row['player_a']}")
        win_rates.append(row["a_win_rate"])
        cis.append(row["a_win_rate_ci95"])

    x = np.arange(len(labels))
    bars = ax.bar(x, win_rates, yerr=cis, capsize=5, color=["tab:blue", "tab:blue", "tab:green", "tab:green"])
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("Win Rate vs Pure UCT")
    ax.set_title("H2/H3: UCT Variants vs Pure UCT")
    ax.set_ylim(0, 1.05)
    ax.axhline(0.5, color="gray", linestyle="--", alpha=0.5)
    ax.grid(True, alpha=0.3, axis="y")
    plt.tight_layout()
    plt.savefig(output_dir / "h2_h3_variants.png", dpi=150)
    plt.close()


def plot_move_limit_comparison(stats: pd.DataFrame, output_dir: Path) -> None:
    """Compare results under different move limits (H4: E09 vs E16, E12 vs E17, E14 vs E18)."""
    pairs = [
        ("E09", "E16", "UCT"),
        ("E12", "E17", "UCT+Minimax"),
        ("E14", "E18", "UCT+EarlyTerm"),
    ]

    labels = []
    wr_150 = []
    wr_100 = []
    for id_150, id_100, name in pairs:
        row_150 = stats[stats["experiment_id"] == id_150]
        row_100 = stats[stats["experiment_id"] == id_100]
        if row_150.empty or row_100.empty:
            continue
        labels.append(name)
        wr_150.append(row_150["a_win_rate"].values[0])
        wr_100.append(row_100["a_win_rate"].values[0])

    if not labels:
        return

    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(len(labels))
    width = 0.35
    ax.bar(x - width / 2, wr_150, width, label="move_limit=150", color="tab:blue")
    ax.bar(x + width / 2, wr_100, width, label="move_limit=100", color="tab:red")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Win Rate vs AlphaBeta")
    ax.set_title("H4: Effect of Move Limit on Algorithm Ranking")
    ax.set_ylim(0, 1.05)
    ax.axhline(0.5, color="gray", linestyle="--", alpha=0.5)
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")
    plt.tight_layout()
    plt.savefig(output_dir / "h4_move_limit.png", dpi=150)
    plt.close()


def plot_time_per_move(stats: pd.DataFrame, output_dir: Path) -> None:
    """Bar chart of average time per move across experiments."""
    if stats.empty:
        return

    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(stats))
    ax.bar(x, stats["avg_time_white"].values, label="White avg time/move", alpha=0.7)
    ax.bar(x, stats["avg_time_black"].values, bottom=stats["avg_time_white"].values,
           label="Black avg time/move", alpha=0.7)
    ax.set_xticks(x)
    ax.set_xticklabels(stats["experiment_id"].values, rotation=45, fontsize=8)
    ax.set_ylabel("Time per move (s)")
    ax.set_title("Average Time per Move by Experiment")
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")
    plt.tight_layout()
    plt.savefig(output_dir / "time_per_move.png", dpi=150)
    plt.close()


def generate_summary_table(stats: pd.DataFrame, output_dir: Path) -> None:
    """Save a summary table as CSV."""
    stats.to_csv(output_dir / "summary_stats.csv", index=False)


def main():
    parser = argparse.ArgumentParser(description="Analyze checkers experiment results")
    parser.add_argument("--input", type=str, default="results", help="Directory with experiment CSVs")
    parser.add_argument("--output", type=str, default="results/plots", help="Output directory for plots")
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading results from: {input_dir}")
    df = load_all_results(input_dir)
    print(f"Loaded {len(df)} game records from {df['experiment_id'].nunique()} experiments")

    stats = compute_stats(df)
    print(f"\nSummary statistics:")
    print(stats[["experiment_id", "player_a", "player_b", "a_win_rate", "a_win_rate_ci95",
                 "avg_game_length", "avg_time_white"]].to_string(index=False))

    generate_summary_table(stats, output_dir)
    print(f"\nSaved summary_stats.csv")

    # Generate plots
    plot_c_sweep(stats, output_dir)
    plot_budget_sweep(stats, output_dir)
    plot_variants_comparison(stats, output_dir)
    plot_move_limit_comparison(stats, output_dir)
    plot_time_per_move(stats, output_dir)

    print(f"\nPlots saved to: {output_dir}")
    print("Done.")


if __name__ == "__main__":
    main()
