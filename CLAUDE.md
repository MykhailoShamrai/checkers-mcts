# CLAUDE.md — Checkers + MCTS project guide

Guide for developing this project across sessions. Read this first.

## What this project is

An 8×8 checkers (draughts) program used as a testbed for **Monte Carlo Tree
Search (MCTS / UCT)** and its variants, compared against an alpha-beta
heuristic player. It ships a **Pygame GUI** supporting human-vs-human,
human-vs-bot, and bot-vs-bot play (you can pick each bot's algorithm), plus an
**experiment harness** for automated tournaments and analysis.

Source spec: `msi2_mcts_konspekt.pdf` (Polish). Key points distilled below — if
in doubt, the PDF wins.

## Game rules (the exact variant — do not deviate)

- **Board**: 8×8, pieces on **dark squares** only. 12 men per side on the first
  three rows. BLACK on rows 0–2, WHITE on rows 5–7. **WHITE moves first.**
- **Men**: move one diagonal step forward (WHITE toward row 0, BLACK toward
  row 7). They **capture forward and backward**.
- **Mandatory capture**: if any capture is available, the side to move *must*
  capture. Only capturing moves are legal that turn.
- **Multi-capture**: a capture sequence must continue as long as further jumps
  are possible with the same piece. Captured pieces are removed only when the
  whole sequence ends and may not be jumped twice.
- **Flying kings (damki)**: a man reaching the opponent's back row becomes a
  king. A king slides any number of empty squares along a diagonal, and
  captures along the **whole diagonal** — it may jump one enemy piece at any
  distance (only empty squares between) and land on any empty square beyond it.
  Kings must also perform multi-captures.
- **King weight**: a king is worth ~3 men (it captures along the full diagonal).
- **End of game**: a side with **no legal move** (no pieces or fully blocked)
  **loses**. To avoid endless games there is a **move limit (default 150
  plies)**; reaching it is a **draw**.
- "Maximum capture" rule (must choose the longest capture) is **NOT** required —
  any complete capture sequence is legal. Keep a flag for it (default OFF).

## The four computer players (to implement in Phase 2)

1. **Basic UCT** — standard UCT, random playouts to game end (or move limit).
   Selection uses formula (1): `a* = argmax[ Q(s,a) + C·sqrt(ln N(s) / N(s,a)) ]`.
2. **UCT + minimax hybrid** (Baier & Winands [1]) — replace the random playout
   with a shallow **minimax** search of configurable depth `d` from the leaf.
   Minimax needs no eval if it reaches a terminal state; otherwise it backs up
   leaf evaluations.
3. **UCT + early termination** (Lorentz [3], Lanctot [2]) — cut the simulation
   off after a fixed number of moves and evaluate with the **material
   heuristic** (formula (3), normalized to [-1,1]). Optionally blend via
   formula (2): `Q̂ = (1-α)·(r/n) + α·v`.
4. **Alpha-beta heuristic player** — iterative-deepening alpha-beta with a
   Chinook-inspired eval: material (man=1, king=3), center control, mobility,
   promotion proximity. The benchmark the MCTS variants are measured against.

All players implement the `Player` interface (`choose_move(state) -> Move`).

### Tunable parameters (must be CLI/config inputs)

player variant, computational budget (MCTS iterations), exploration constant
`C` (sweep range 0.1–3.0), minimax/early-termination depth, **RNG seed**.

## Architecture & layout

Modular by design: stateless-ish engine, pluggable players, thin GUI, separate
experiment scripts.

```
checkers/
  engine/        board + rules + state. The ONLY place game rules live.
    constants.py   cell encoding, geometry, directions  [done]
    board.py       initial_board, material counts, ASCII render  [done]
    move.py        Move dataclass (squares + captured)  [done]
    rules.py       legal_moves / apply_move  ← Phase 1 core, STUBBED
    game_state.py  immutable GameState (play/terminal/winner)  [done]
  players/
    base.py        Player ABC  [done]
    random_player.py, human.py  [done]
    heuristics.py  material_heuristic [done], chinook_eval [stub]
    alphabeta.py   AlphaBetaPlayer  [stub]
    mcts/
      node.py      shared UCT Node  [done]
      uct.py            basic UCT       [stub — TODO]
      uct_minimax.py    hybrid          [stub — TODO]
      uct_early_term.py early termination [stub — TODO]
  gui/
    app.py         Pygame loop + turn handling  [stub — TODO]
    board_view.py  rendering, click→square mapping, highlights  [stub — TODO]
    menu.py        choose seats/algorithms/params  [stub — TODO]
  config.py        config dataclasses + defaults  [TODO]
experiments/
  tournament.py    run N games between two players  [TODO]
  run_experiment.py  C-sweep, budget-sweep; write CSV  [TODO]
  analysis.py      pandas/matplotlib from CSV  [TODO]
tests/             pytest — engine first, then players  [TODO]
main.py            entry point → launches GUI  [TODO]
results/           CSV/plot output (gitignored)
```

### Board encoding (memorize this)

8×8 `numpy.int8`. `EMPTY=0`, `WHITE_MAN=1`, `WHITE_KING=2`, `BLACK_MAN=-1`,
`BLACK_KING=-2`. **Sign = color** (positive WHITE, negative BLACK), **abs = rank**
(2 = king). Playable square iff `(r+c) % 2 == 1`. `WHITE=1`, `BLACK=-1` double as
color constants. See `engine/constants.py`.

### Move encoding

`Move(squares, captured)`. `squares` = ordered occupied squares from origin to
final landing (`len==2` for a simple step, `n+1` for an n-capture). `captured` =
squares of removed enemy pieces. Frozen/hashable so it can key search trees.

### Conventions

- The engine is **functional**: `apply_move` returns a **new** board; never
  mutate in place. `GameState` is frozen — `play()` returns a new state. This
  keeps MCTS/minimax node expansion safe.
- Game rules live **only** in `engine/`. Players and GUI must not re-implement
  any rule; they call `state.legal_moves()` / `state.play(move)`.
- Players must be **deterministic given a seed** (reproducibility requirement).

## Build order / TODO roadmap

### Phase 1 — Engine + engine tests + GUI (human-vs-human)
- [ ] `engine/rules.py`: `_simple_moves`, `_capture_moves` (recursive
      multi-capture for both men and flying kings), `apply_move` (move,
      remove captures, promote). Decide & document mid-sequence promotion rule.
- [ ] Tests **alongside** the engine (see invariants below). This is the
      bug-prone heart of the project — do not defer these to Phase 3.
- [ ] `gui/board_view.py` + `gui/app.py`: render board/pieces, map clicks to
      squares, highlight selected piece + legal targets, enforce mandatory
      capture in the UI, animate/step multi-captures, detect game over.
- [ ] `main.py`: launch GUI in human-vs-human mode.

### Phase 2 — Players (bots) + menu
- [ ] `players/mcts/uct.py`: 4 MCTS phases (select/expand/simulate/backprop),
      `iterations` and `c` params, seeded RNG.
- [ ] `players/mcts/uct_minimax.py`: replace playout with depth-`d` minimax.
- [ ] `players/mcts/uct_early_term.py`: cut playout, use `material_heuristic`;
      optional α-blend (formula (2)).
- [ ] `players/heuristics.py::chinook_eval` + `players/alphabeta.py`.
- [ ] `config.py`: dataclasses mapping CLI/menu choices → constructed players.
- [ ] `gui/menu.py`: pick each seat (human / which bot) and bot params; wire
      human-vs-bot and bot-vs-bot into `app.py`.

### Phase 3 — Experiment infrastructure + broader tests
- [ ] `experiments/tournament.py`: play N games between two players, alternate
      colors, per-game seed; collect win/loss/draw, game length, time/move.
- [ ] `experiments/run_experiment.py`: C-sweep (0.1–3.0, ≥50 games each),
      budget-sweep (100/500/1000/5000/10000 iters); write **CSV** to `results/`.
- [ ] `experiments/analysis.py`: pandas aggregation + matplotlib plots
      (win rate, avg length, avg time/move, with mean/std/CI).
- [ ] Player-level tests; reproducibility test (same seed → same game).

## Engine invariants to test (Phase 1)

- `initial_board` has 12 WHITE and 12 BLACK men, all on playable squares.
- A side with a capture available is given **only** captures by `legal_moves`.
- Single, double, and triple man captures generate correctly; captured pieces
  removed only at sequence end; no piece jumped twice.
- Flying king: slides over multiple empties; captures at a distance and can land
  on any empty square beyond the victim; multi-capture with direction changes.
- Promotion on reaching the back row; documented mid-capture-promotion behavior.
- `winner()` returns the right side when a player is blocked / has no pieces.
- Move-limit draw triggers at `move_limit` plies.
- `apply_move` never mutates its input board (assert array unchanged).

## Tooling & commands

Python 3.12, venv at `.venv`. Libraries (PDF): **NumPy, Pygame, Matplotlib,
Pandas**; **pytest** for tests.

```bash
.venv/bin/pip install numpy pygame matplotlib pandas pytest   # first-time setup
# (create requirements.txt with these once pinned)

.venv/bin/python main.py            # launch the GUI
.venv/bin/pytest                    # run the test suite
.venv/bin/pytest tests/test_captures.py -q   # a single test file
```

## References (from the konspekt)

[1] Baier & Winands, *MCTS-Minimax Hybrids*, 2014.
[2] Lanctot et al., *MCTS with Heuristic Evaluations using Implicit Minimax
    Backups*, CIG 2014. (formula (2))
[3] Lorentz, *Using Evaluation Functions in MCTS*, 2016. (early termination)
[4] Schaeffer, *One Jump Ahead: ... Checkers*, 1997. (Chinook eval inspiration)
[5] Świechowski et al., *MCTS: a review of recent modifications and
    applications*, AI Review 2023. (UCT formula (1))