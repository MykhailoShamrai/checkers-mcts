"""Statistical analysis and visualization of experiment results.

Reads CSV files from results/ directory, computes aggregated statistics
(mean, std, 95% CI), and generates comparative plots for the report.

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

# Polish-friendly style
matplotlib.rcParams.update({
    'font.size': 11,
    'axes.titlesize': 13,
    'axes.labelsize': 11,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.dpi': 150,
    'savefig.dpi': 150,
    'savefig.bbox': 'tight',
})


def load_all_results(input_dir: Path) -> pd.DataFrame:
    """Load all experiment CSV files into a single DataFrame."""
    frames = []
    for csv_file in sorted(input_dir.glob("E*.csv")):
        df = pd.read_csv(csv_file)
        frames.append(df)
    if not frames:
        raise FileNotFoundError(f"No experiment CSV files found in {input_dir}")
    return pd.concat(frames, ignore_index=True)


def wilson_ci(wins: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score 95% confidence interval for a proportion."""
    if n == 0:
        return 0.0, 0.0
    p = wins / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2*n)) / denom
    margin = z * np.sqrt(p*(1-p)/n + z**2/(4*n**2)) / denom
    return max(0, center - margin), min(1, center + margin)


def compute_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Compute per-experiment aggregate statistics."""
    records = []
    for exp_id, group in df.groupby("experiment_id"):
        n = len(group)
        a_wins = int((group["winner"] == "a").sum())
        b_wins = int((group["winner"] == "b").sum())
        draws = n - a_wins - b_wins

        a_win_rate = a_wins / n
        b_win_rate = b_wins / n
        draw_rate = draws / n

        # Wilson CI
        lo, hi = wilson_ci(a_wins, n)
        a_ci_low = a_win_rate - lo
        a_ci_high = hi - a_win_rate

        avg_plies = group["num_plies"].mean()
        std_plies = group["num_plies"].std()

        avg_time_w = group["avg_time_white"].mean()
        avg_time_b = group["avg_time_black"].mean()

        records.append({
            "experiment_id": exp_id,
            "n_games": n,
            "player_a": group["player_a"].iloc[0],
            "player_b": group["player_b"].iloc[0],
            "player_a_params": group["player_a_params"].iloc[0] if "player_a_params" in group.columns else "",
            "player_b_params": group["player_b_params"].iloc[0] if "player_b_params" in group.columns else "",
            "move_limit": group["move_limit"].iloc[0],
            "a_wins": a_wins,
            "b_wins": b_wins,
            "draws": draws,
            "a_win_rate": a_win_rate,
            "b_win_rate": b_win_rate,
            "draw_rate": draw_rate,
            "a_ci_low": a_ci_low,
            "a_ci_high": a_ci_high,
            "avg_game_length": avg_plies,
            "std_game_length": std_plies,
            "avg_time_white": avg_time_w,
            "avg_time_black": avg_time_b,
        })

    return pd.DataFrame(records)


def plot_c_sweep(df: pd.DataFrame, stats: pd.DataFrame, output_dir: Path) -> None:
    """H1a: UCT win rate vs exploration constant C (E01-E07, 100 iterations)."""
    c_values = [0.1, 0.3, 0.7, 1.0, 1.4, 2.0, 3.0]
    exp_ids = ['E01', 'E02', 'E03', 'E04', 'E05', 'E06', 'E07']

    win_rates = []
    ci_low = []
    ci_high = []
    draw_rates = []

    for exp_id in exp_ids:
        sub = df[df.experiment_id == exp_id]
        n = len(sub)
        a_wins = int((sub.winner == 'a').sum())
        draws = n - a_wins - int((sub.winner == 'b').sum())
        wr = a_wins / n
        lo, hi = wilson_ci(a_wins, n)
        win_rates.append(wr)
        ci_low.append(wr - lo)
        ci_high.append(hi - wr)
        draw_rates.append(draws / n)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.errorbar(c_values, win_rates, yerr=[ci_low, ci_high],
                fmt='o-', capsize=5, color='#2196F3', linewidth=2, markersize=8,
                label='Win rate UCT')
    ax.bar(c_values, draw_rates, width=0.08, alpha=0.3, color='gray', label='Remisy')
    ax.axhline(0.5, color='gray', linestyle='--', alpha=0.5, label='50%')
    ax.set_xlabel('Stała eksploracji C')
    ax.set_ylabel('Win rate UCT')
    ax.set_title('H1a: Wpływ stałej eksploracji C na siłę gry UCT\n(100 iteracji vs Alpha-Beta depth=6, N=50 gier)')
    ax.set_ylim(-0.05, 1.05)
    ax.set_xticks(c_values)
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_dir / 'h1a_c_sweep.png')
    plt.close(fig)
    print('  Saved h1a_c_sweep.png')


def plot_budget_sweep(df: pd.DataFrame, stats: pd.DataFrame, output_dir: Path) -> None:
    """H1b: UCT win rate vs iteration budget (E05, E08-E11, all c=1.4)."""
    budgets = [100, 500, 1000, 5000, 10000]
    exp_ids = ['E05', 'E08', 'E09', 'E10', 'E11']

    win_rates = []
    ci_low = []
    ci_high = []
    avg_times = []

    for exp_id in exp_ids:
        sub = df[df.experiment_id == exp_id]
        n = len(sub)
        a_wins = int((sub.winner == 'a').sum())
        wr = a_wins / n
        lo, hi = wilson_ci(a_wins, n)
        win_rates.append(wr)
        ci_low.append(wr - lo)
        ci_high.append(hi - wr)
        # Average time for UCT player (player_a)
        avg_t = sub.apply(
            lambda r: r['avg_time_white'] if r['white_player'] == r['player_a'] else r['avg_time_black'],
            axis=1
        ).mean()
        avg_times.append(avg_t)

    fig, ax1 = plt.subplots(figsize=(8, 5))

    color1 = '#2196F3'
    ax1.errorbar(budgets, win_rates, yerr=[ci_low, ci_high],
                 fmt='o-', capsize=5, color=color1, linewidth=2, markersize=8, label='Win rate UCT')
    ax1.axhline(0.5, color='gray', linestyle='--', alpha=0.5)
    ax1.set_xlabel('Budżet iteracji MCTS')
    ax1.set_ylabel('Win rate UCT (vs Alpha-Beta depth=6)', color=color1)
    ax1.set_ylim(-0.05, 1.05)
    ax1.set_xscale('log')
    ax1.set_xticks(budgets)
    ax1.set_xticklabels([str(b) for b in budgets])
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.grid(True, alpha=0.3)

    # Secondary axis: time per move
    color2 = '#FF5722'
    ax2 = ax1.twinx()
    ax2.plot(budgets, avg_times, 's--', color=color2, linewidth=1.5, markersize=6, label='Czas/ruch [s]')
    ax2.set_ylabel('Średni czas na ruch [s]', color=color2)
    ax2.tick_params(axis='y', labelcolor=color2)

    # Combined legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='center left')

    ax1.set_title('H1b: Wpływ budżetu iteracji na siłę gry UCT (C=1.4)\n(vs Alpha-Beta depth=6, N=50 gier)')
    fig.tight_layout()
    fig.savefig(output_dir / 'h1b_budget_sweep.png')
    plt.close(fig)
    print('  Saved h1b_budget_sweep.png')


def plot_variants_comparison(df: pd.DataFrame, stats: pd.DataFrame, output_dir: Path) -> None:
    """H2+H3: Stacked bar chart comparing UCT variants head-to-head."""
    experiments = [
        ('E12', 'UCT+Minimax\n(1000 iter)'),
        ('E13', 'UCT+Minimax\n(5000 iter)'),
        ('E14', 'UCT+EarlyTerm\n(1000 iter)'),
        ('E15', 'UCT+EarlyTerm\n(5000 iter)'),
    ]

    labels = []
    a_rates = []
    b_rates = []
    d_rates = []

    for exp_id, label in experiments:
        sub = df[df.experiment_id == exp_id]
        n = len(sub)
        a_w = (sub.winner == 'a').sum() / n
        b_w = (sub.winner == 'b').sum() / n
        d_w = 1.0 - a_w - b_w
        labels.append(label)
        a_rates.append(a_w)
        b_rates.append(b_w)
        d_rates.append(d_w)

    x = np.arange(len(labels))
    width = 0.6

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(x, a_rates, width, label='Wariant (A) wygrywa', color='#4CAF50', alpha=0.85)
    ax.bar(x, d_rates, width, bottom=a_rates, label='Remis', color='#9E9E9E', alpha=0.7)
    ax.bar(x, b_rates, width, bottom=[a+d for a, d in zip(a_rates, d_rates)],
           label='Basic UCT (B) wygrywa', color='#F44336', alpha=0.85)

    ax.set_xlabel('Eksperyment')
    ax.set_ylabel('Proporcja wyników')
    ax.set_title('H2 & H3: Porównanie wariantów UCT vs Basic UCT\n(N=50 gier na eksperyment)')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend(loc='upper right')
    ax.set_ylim(0, 1.05)
    ax.axhline(0.5, color='black', linestyle=':', alpha=0.3)
    ax.grid(True, alpha=0.2, axis='y')

    # Percentage annotations
    for i in range(len(labels)):
        if a_rates[i] > 0.05:
            ax.text(i, a_rates[i]/2, f'{a_rates[i]:.0%}', ha='center', va='center', fontsize=10, fontweight='bold')
        if b_rates[i] > 0.05:
            ax.text(i, a_rates[i] + d_rates[i] + b_rates[i]/2, f'{b_rates[i]:.0%}',
                    ha='center', va='center', fontsize=10, fontweight='bold', color='white')
        if d_rates[i] > 0.05:
            ax.text(i, a_rates[i] + d_rates[i]/2, f'{d_rates[i]:.0%}',
                    ha='center', va='center', fontsize=9)

    fig.tight_layout()
    fig.savefig(output_dir / 'h2_h3_variants.png')
    plt.close(fig)
    print('  Saved h2_h3_variants.png')


def plot_move_limit_comparison(df: pd.DataFrame, stats: pd.DataFrame, output_dir: Path) -> None:
    """H4: Effect of move limit — compare ml=150 vs ml=100."""
    # E09: UCT 1000 iter vs AB, ml=150
    # E16: UCT 1000 iter vs AB, ml=100
    # E17: UCT+Minimax 1000 iter vs AB, ml=100
    # E18: UCT+EarlyTerm 1000 iter vs AB, ml=100
    configs = [
        ('E09', 'UCT\n(ml=150)'),
        ('E16', 'UCT\n(ml=100)'),
        ('E17', 'UCT+Minimax\n(ml=100)'),
        ('E18', 'UCT+EarlyTerm\n(ml=100)'),
    ]

    labels = []
    a_rates = []
    b_rates = []
    d_rates = []

    for exp_id, label in configs:
        sub = df[df.experiment_id == exp_id]
        n = len(sub)
        a_w = (sub.winner == 'a').sum() / n
        b_w = (sub.winner == 'b').sum() / n
        d_w = 1.0 - a_w - b_w
        labels.append(label)
        a_rates.append(a_w)
        b_rates.append(b_w)
        d_rates.append(d_w)

    x = np.arange(len(labels))
    width = 0.25

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(x - width, a_rates, width, label='MCTS wygrywa', color='#2196F3', alpha=0.85)
    ax.bar(x, b_rates, width, label='Alpha-Beta wygrywa', color='#FF9800', alpha=0.85)
    ax.bar(x + width, d_rates, width, label='Remis', color='#9E9E9E', alpha=0.7)

    ax.set_xlabel('Konfiguracja (1000 iteracji, C=1.4)')
    ax.set_ylabel('Proporcja wyników')
    ax.set_title('H4: Wpływ limitu ruchów i wariantu MCTS vs Alpha-Beta (depth=6)\n(N=50 gier)')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()
    ax.set_ylim(0, 1.05)
    ax.axhline(0.5, color='gray', linestyle='--', alpha=0.4)
    ax.grid(True, alpha=0.3, axis='y')

    # Percentage labels
    for i in range(len(labels)):
        for val, offset in [(a_rates[i], -width), (b_rates[i], 0), (d_rates[i], width)]:
            if val > 0.03:
                ax.text(i + offset, val + 0.02, f'{val:.0%}', ha='center', va='bottom', fontsize=9)

    fig.tight_layout()
    fig.savefig(output_dir / 'h4_move_limit.png')
    plt.close(fig)
    print('  Saved h4_move_limit.png')


def plot_game_lengths(df: pd.DataFrame, output_dir: Path) -> None:
    """Box plot of game lengths by experiment."""
    fig, ax = plt.subplots(figsize=(12, 5))

    exp_ids = sorted(df.experiment_id.unique())
    data = [df[df.experiment_id == eid].num_plies.values for eid in exp_ids]

    bp = ax.boxplot(data, tick_labels=exp_ids, patch_artist=True)

    # Color by group
    group_colors = {
        'E01': '#2196F3', 'E02': '#2196F3', 'E03': '#2196F3', 'E04': '#2196F3',
        'E05': '#2196F3', 'E06': '#2196F3', 'E07': '#2196F3',
        'E08': '#FF9800', 'E09': '#FF9800', 'E10': '#FF9800', 'E11': '#FF9800',
        'E12': '#4CAF50', 'E13': '#4CAF50',
        'E14': '#9C27B0', 'E15': '#9C27B0',
        'E16': '#F44336', 'E17': '#F44336', 'E18': '#F44336',
    }
    for patch, eid in zip(bp['boxes'], exp_ids):
        patch.set_facecolor(group_colors.get(eid, '#888888'))
        patch.set_alpha(0.6)

    ax.set_xlabel('Eksperyment')
    ax.set_ylabel('Liczba półruchów (plies)')
    ax.set_title('Rozkład długości gier w poszczególnych eksperymentach')
    ax.grid(True, alpha=0.3, axis='y')
    plt.xticks(rotation=45)
    ax.axhline(150, color='red', linestyle=':', alpha=0.5, label='Limit ruchów (150)')
    ax.legend()

    fig.tight_layout()
    fig.savefig(output_dir / 'game_lengths_boxplot.png')
    plt.close(fig)
    print('  Saved game_lengths_boxplot.png')


def plot_time_per_move(df: pd.DataFrame, stats: pd.DataFrame, output_dir: Path) -> None:
    """Time per move comparison across budget sweep."""
    budgets = [100, 500, 1000, 5000, 10000]
    exp_ids = ['E05', 'E08', 'E09', 'E10', 'E11']

    uct_times = []
    ab_times = []

    for exp_id in exp_ids:
        sub = df[df.experiment_id == exp_id]
        uct_t = sub.apply(
            lambda r: r['avg_time_white'] if r['white_player'] == r['player_a'] else r['avg_time_black'],
            axis=1
        ).mean()
        ab_t = sub.apply(
            lambda r: r['avg_time_white'] if r['white_player'] == r['player_b'] else r['avg_time_black'],
            axis=1
        ).mean()
        uct_times.append(uct_t)
        ab_times.append(ab_t)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(budgets, uct_times, 'o-', color='#2196F3', linewidth=2, markersize=8, label='UCT')
    ax.plot(budgets, ab_times, 's--', color='#FF9800', linewidth=2, markersize=8, label='Alpha-Beta (depth=6)')
    ax.set_xlabel('Budżet iteracji MCTS')
    ax.set_ylabel('Średni czas na ruch [s]')
    ax.set_title('Czas obliczeniowy na ruch vs budżet iteracji')
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xticks(budgets)
    ax.set_xticklabels([str(b) for b in budgets])
    ax.legend()
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(output_dir / 'time_per_move.png')
    plt.close(fig)
    print('  Saved time_per_move.png')


def plot_full_overview(df: pd.DataFrame, stats: pd.DataFrame, output_dir: Path) -> None:
    """Combined overview: win rates for all 18 experiments as a horizontal bar chart."""
    fig, ax = plt.subplots(figsize=(10, 8))

    exp_ids = list(stats['experiment_id'])
    y = np.arange(len(exp_ids))

    a_rates = stats['a_win_rate'].values
    b_rates = stats['b_win_rate'].values
    d_rates = stats['draw_rate'].values

    ax.barh(y, a_rates, height=0.7, label='Gracz A wygrywa', color='#4CAF50', alpha=0.85)
    ax.barh(y, d_rates, height=0.7, left=a_rates, label='Remis', color='#9E9E9E', alpha=0.6)
    ax.barh(y, b_rates, height=0.7, left=a_rates + d_rates, label='Gracz B wygrywa',
            color='#F44336', alpha=0.85)

    # Labels on the right side
    for i, eid in enumerate(exp_ids):
        row = stats[stats.experiment_id == eid].iloc[0]
        label = f"{row['player_a']} vs {row['player_b']}"
        ax.text(1.02, i, label, ha='left', va='center', fontsize=8, transform=ax.get_yaxis_transform())

    ax.set_yticks(y)
    ax.set_yticklabels(exp_ids)
    ax.set_xlabel('Proporcja wyników')
    ax.set_title('Przegląd wszystkich eksperymentów (N=50 gier każdy)')
    ax.axvline(0.5, color='black', linestyle=':', alpha=0.4)
    ax.set_xlim(0, 1)
    ax.legend(loc='lower right')
    ax.grid(True, alpha=0.2, axis='x')

    fig.tight_layout()
    fig.subplots_adjust(right=0.72)
    fig.savefig(output_dir / 'full_overview.png')
    plt.close(fig)
    print('  Saved full_overview.png')


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
    print(f"Loaded {len(df)} game records from {df['experiment_id'].nunique()} experiments\n")

    stats = compute_stats(df)
    print("Summary statistics:")
    print(stats[["experiment_id", "player_a", "player_b", "a_win_rate", "draw_rate",
                 "avg_game_length", "avg_time_white"]].to_string(index=False))

    generate_summary_table(stats, output_dir)
    print(f"\nSaved summary_stats.csv\n")

    # Generate plots
    print("Generating plots...")
    plot_c_sweep(df, stats, output_dir)
    plot_budget_sweep(df, stats, output_dir)
    plot_variants_comparison(df, stats, output_dir)
    plot_move_limit_comparison(df, stats, output_dir)
    plot_game_lengths(df, output_dir)
    plot_time_per_move(df, stats, output_dir)
    plot_full_overview(df, stats, output_dir)

    print(f"\nAll plots saved to: {output_dir}")
    print("Done.")


if __name__ == "__main__":
    main()
