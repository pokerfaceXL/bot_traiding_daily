# F006 — Hypothesis: `activate_pct` × `trail_pct`, the exit geometry that sets reward:risk, Train 1 only

> Sections "Observation" … "Method" (including the falsification condition and the exact
> 8-name sample) were written and committed to this file BEFORE
> `scripts/f006_trailing_sweep_experiment.py` was written and before any backtest was run, per the
> same discipline as `spec/research/F006-hypothesis-donchian.md`,
> `spec/research/F006-hypothesis-one-shot-entry.md`, `spec/research/F006-hypothesis-cooldown.md`,
> `spec/research/F006-hypothesis-stop-width.md`, `spec/research/F006-hypothesis-entry-regime-filter.md`
> and `spec/research/F006-lorentzian-causality.md`. "Run_id", "Result", "Decision" and "Tests" were
> filled in after the run.
>
> TRAIN-1 ONLY. Per `spec/research/F005-validation-protocol.md` section 7.3, F006 selects on
> train+validation and never opens holdout; this slice restricts itself further, to Train 1
> (`[2024-03-01T00:00:00Z, 2025-03-01T00:00:00Z)`) plus the protocol's 35-day warm-up buffer from
> `2024-01-26T00:00:00Z`. Validation 1-4 and the Holdout window are not loaded, not sliced and not
> looked at by any script in this slice.

## Observation

`spec/research/F006-hypothesis-donchian.md`'s decomposition is the only F006 measurement that says
*why* per-trade expectancy is negative rather than restating that it is. Pooled across old catalog
names and the two new generators, on the same Train-1 sample:

| | Value |
| --- | ---: |
| average winner | **$1.46** |
| average losing trade | **-$2.55** |
| reward:risk | ~**0.57** (i.e. roughly 1 : 1.75) |
| win rate needed to break even | ~**63%** |
| best win rate any name achieves | **44.09%** (`DONCHIAN_PULLBACK_55`) |
| share of trades closed by the stop/trailing machinery | **86.2%** (39.2% `initial_sl` + 47.0% `trailing_sl`) |

Every name is 20-27 percentage points short of its own breakeven win rate, and the shortfall is the
same everywhere because the *shape* of the trade distribution is the same everywhere: winners are
about 0.55-0.60 of losers. That shape is not produced by the entry signal — 86% of trades never get
to find out what the signal thought, because the exit machinery closes them first.

And the exit machinery's two win-side parameters have **never been varied in F006**.
`activate_pct=0.03` / `trail_pct=0.02` are hard-coded identically in
`scripts/f006_stop_width_experiment.py`, `f006_regime_filter_experiment.py`,
`f006_cooldown_experiment.py`, `f006_lorentzian_experiment.py`, `f006_one_shot_experiment.py` and
`f006_donchian_experiment.py` — they are `backtest_engine.run_backtest`'s own function-signature
defaults, inherited by every slice without ever being questioned.
`spec/research/F006-hypothesis-stop-width.md` swept `max_sl_pct` — the **loss** side, the cap on how
bad a loser can be — and found nothing at any width from 0.01 to 0.12. The **win** side has not been
touched by any of the seven prior slices.

### What the engine actually does (read from the code, not the docstring)

`backtest_engine._update_trailing` (lines 93-110) and `_active_sl` (lines 113-116), for a long
position entered at `E` with `max_sl_pct = m`, `activate_pct = a`, `trail_pct = t`:

* `best_price` tracks the **intrabar high** (`max(best_price, bar.high)`), not the close.
* The trail arms the first bar `best_price >= E * (1 + a)`; on that bar `trailing_sl` is set to
  `best_price * (1 - t)`, and thereafter it ratchets: `trailing_sl = max(trailing_sl, best_price * (1 - t))`.
  It never loosens.
* The stop actually tested each bar is `_active_sl = max(initial_sl, trailing_sl)` (long), with
  `initial_sl = E * (1 - m)`. So **the trail only matters on bars where `best_price*(1-t) > E*(1-m)`**;
  below that the initial stop binds and the exit is labelled `initial_sl`, not `trailing_sl`.
* Shorts are the exact mirror (`min`, `low`, `1+t`, `1-a`).
* There is **no take-profit** anywhere in the engine. A winner is therefore ended by exactly one of:
  the ratcheting trail, a signal reversal, or end of data. Under the one-shot mask at
  `cooldown_candles=0` that is the whole win-side geometry.

Two derived quantities fall straight out of this and are what the grid really varies:

1. **Lock-in at arming**: `(1+a)(1-t)`. At the baseline 0.03/0.02 this is **1.0094** — the moment the
   trail arms, the position is guaranteed roughly +0.94% *if* the stop is hit immediately, against an
   initial stop at -3%. That single number is a 1 : 3.2 geometry on the arming bar, and it is a
   plausible mechanical origin of the measured 1 : 1.75.
2. **Trail-binding threshold**: the trail overtakes the initial stop only once
   `best_price >= E(1-m)/(1-t)`. Per cell (`m = 0.03`):

| lock-in `(1+a)(1-t)`, `a` \ `t` | 0.01 | 0.02 | 0.04 |
| --- | ---: | ---: | ---: |
| **a = 0.01** | 0.9999 | 0.9898 | 0.9696 |
| **a = 0.03** | 1.0197 | **1.0094** (baseline) | 0.9888 |
| **a = 0.06** | 1.0494 | 1.0388 | 1.0176 |
| **trail binds once `best` exceeds** | -2.02% | -1.02% | **+1.04%** |

The bottom row is `E(1-m)/(1-t)` expressed as a move from entry. For `t = 0.01` and `t = 0.02` it is
*below* the entry price, and `best_price` starts at the entry price and only ever moves in the
position's favour — so in those two columns the trail binds the instant it arms. Only in the
`t = 0.04` column is there a window (arming at `+a`, binding at `+1.04%`) where the trail is armed but
the initial stop still binds, and that window is non-empty only for the `a = 0.01, t = 0.04` cell.
So the nine cells differ almost entirely in *when the ratchet starts* and *how much of the best price
it gives back* — which is exactly the lever this hypothesis is about.

## Hypothesis

The 1 : 1.75 reward:risk ratio is a **property of the exit parameters**, not of the basket's price
action. A trail that arms early and trails tightly converts a position that has merely twitched in
the right direction into a small winner or a breakeven scratch, while every loser is free to run to
the full `max_sl_pct` = -3%. Moving `activate_pct` / `trail_pct` away from 0.03/0.02 in the
direction that lets winners run should raise `avg_winner` faster than it worsens `avg_loser`, and so
should **lower `breakeven_win_rate_pct`** — the win rate a name would need to break even.

Written as two separable directional sub-claims, because they can disagree and the grid can tell
them apart:

* **P1 — arm later.** At fixed `t`, raising `a` (0.01 → 0.03 → 0.06) means the trail cannot end a
  trade until the move has already proven itself by `a`. Winners that survive to arming are bigger
  by construction. Predicted: `avg_winner` rises monotonically in `a`; `breakeven_win_rate_pct` falls.
* **P2 — trail looser.** At fixed `a`, raising `t` (0.01 → 0.02 → 0.04) gives the position more room
  before the ratchet fires. Predicted: `avg_winner` rises in `t`.

**These two do not simply add, and that is the honest tension in this hypothesis.** Loosening the
trail also means more trades run all the way back to the -3% initial stop instead of being cut at a
small trailing loss, so `avg_loser` should get *worse* (more negative, toward the -$3 gross cap) as
`t` rises. The prediction being tested is not "winners get bigger" — that is nearly tautological —
but that **the ratio improves**: `avg_winner` grows faster than `|avg_loser|`, so
`breakeven_win_rate_pct = |avg_loser| / (avg_winner + |avg_loser|) × 100` falls. The predicted best
cell is `a=0.06, t=0.04` (latest arming, loosest trail, lock-in 1.0176) and the predicted worst is
`a=0.01, t=0.01` (lock-in 0.9999 — a trail that arms at +1% and immediately guarantees a scratch).

**Why the usual "trading less isn't trading better" confound should be structurally absent here, and
how that is checked.** Under the one-shot entry mask, an entry is queued only on the first bar of a
directional call (`entry_masks.one_shot_entry_mask`), and on such a bar any position from the
previous call has already been closed by the engine's step-3 signal reversal. Exit parameters
therefore change *when a position closes and at what price*, not *how many entries exist*.
Prediction, checked mechanically in the script: **`n_trades` is near-constant across all 9 cells for
a given (name, symbol, interval)**. If it is not, the reasoning above is wrong and the confound is
live; the check is reported either way.

## Falsification condition (stated before running)

Aggregated over the 8-name sample described below (5 symbols × 2 intervals, one-shot mask on,
`cooldown_candles=0`, `max_sl_pct=0.03` fixed), with all figures **pooled over every trade in the
cell** (not a mean of per-series means, since cells differ in trade count per series):

This hypothesis is **falsified** if **either**:

* **(a)** no cell in the 3×3 grid reduces pooled `breakeven_win_rate_pct` by at least **2.0
  percentage points** versus the 0.03/0.02 baseline cell on the same 8-name sample — i.e. the
  reward:risk ratio does not materially improve anywhere in the swept space, **OR**
* **(b)** every cell that does clear that bar fails the "not just trading less / not just a cost
  story" test, meaning at least one of:
  * pooled `n_trades` in that cell is more than **10%** below the baseline cell's (the confound the
    cooldown and Donchian notes had to apply to themselves — structurally not expected here, see
    above, but checked rather than assumed), **or**
  * pooled net PnL **per trade** does not improve versus the baseline cell (a better ratio that does
    not translate into better per-trade expectancy is a bookkeeping artefact), **or**
  * pooled **gross** PnL per trade (pre-cost) does not improve versus the baseline cell (i.e. the
    entire gain is a cost effect from shorter/cheaper trades rather than trade geometry).

Surviving therefore requires a cell that genuinely improves the per-trade reward:risk ratio, on
roughly the same number of trades, in both gross and net terms. Either clause alone falsifies.

Reported either way, not by itself falsifying: the full 9-cell table of `avg_winner`, `avg_loser`,
`breakeven_win_rate_pct`, actual win rate, the **gap** (breakeven − actual), net and gross PnL per
trade, exit-reason mix and `n_trades`; the per-name breakdown at the best and baseline cells; and
whether P1 and P2 hold individually (monotonicity in `a` at fixed `t`, and in `t` at fixed `a`).

A secondary, non-falsifying question this grid answers for free: whether any cell makes any
(name, symbol, interval) series **profitable** on Train 1. Seven prior slices have produced 0 of
~1,500 profitable runs; this one adds 720 more chances.

## Sample (fixed before running, 8 names)

Eight signal names × 5 symbols (`SOLUSDT`, `ETHUSDT`, `BTCUSDT`, `XRPUSDT`, `DOGEUSDT`) × 2
intervals (`240`, `60`) = 80 series per cell, 720 runs over the 9 cells.

| Name | Family | Why it is in the sample |
| --- | --- | --- |
| `EMA_8_21` | EMA | the catalog's canonical persistent momentum state; also a harness-control name in `spec/research/F006-hypothesis-donchian.md`, so its baseline-cell rows are stored and cross-checkable |
| `MACD_12_26_hist` | MACD | the other plain smoothed-momentum family, no RSI combo |
| `RSI14_7030` | RSI | the only plain **mean-reversion** entry in the sample — its winners are shaped differently from a trend name's, which is the one place the exit-geometry claim could behave differently |
| `BB_20_25_breakout` | Bollinger | the catalog's least-bad name (-$143.32 one-shot, `F006-hypothesis-one-shot-entry.md`) and the second stored harness-control name |
| `ADX14_DI_20` | ADX | the trend-strength family; the entry-regime-filter slice's lever, included so this grid is not read only through crossover names |
| `LORENTZIAN_default` | kNN classifier (new generator) | the causal Lorentzian adapter, per the ticket; needs the Python 3.11 `.venv_lorentzian` pass |
| `DONCHIAN_55` | Donchian breakout (new generator) | best raw-breakout variant by net PnL in `F006-hypothesis-donchian.md` (-$48.26) |
| `DONCHIAN_PULLBACK_55` | Donchian pullback (new generator) | best variant overall in that note (-$33.07, 7.35% max DD, 44.09% pooled win rate — the highest win rate ever measured in F006, so the name with the least distance to close to its breakeven) |

Deliberately excluded and why: the three **combo** variants of the 10-strategy sample
(`EMA_13_34_RSI14_55`, `MACD_RSI14_50`, `BB_20_2_RSI14`) duplicate families already represented, and
this hypothesis is about the exit machinery that is identical across all of them;
`TS_13_34_200_14` is a composite of EMA+MACD+RSI, all three already present; `STOCH14_cross` is a
bounded oscillator crossing fixed thresholds, the same shape as `RSI14_7030`, which is kept instead
because it is the sample's mean-reversion representative. `LORENTZIAN_raw` is dropped (the ticket
asks for one Lorentzian entry, and `_default` is the better of the two: -$384.99 vs -$401.03).
`DONCHIAN_20` / `DONCHIAN_PULLBACK_20` are dropped in favour of their 55-bar siblings, which the
Donchian note measured as the better pair on net PnL, drawdown and win rate.

The five catalog names are a strict subset of `spec/research/F006-hypothesis-stop-width.md`'s
10-strategy sample, so their baseline-cell rows are directly comparable to that note, to the
cooldown note and to the one-shot note without re-derivation.

## Method

Same continuous-run methodology, fixed parameter block, data slice and checksum discipline as
`scripts/f006_donchian_experiment.py` (itself `f006_one_shot_experiment.py`, itself
`f006_cooldown_experiment.py`, itself `f006_stop_width_experiment.py`). **No engine change**, and no
existing module changed: one new script, one new helper module, one new test file.

- **Script**: `scripts/f006_trailing_sweep_experiment.py`. Two passes, one schema, same split as the
  one-shot and cooldown experiments because advanced-ta (`lorentzian.py`) needs Python ≥ 3.10:
  `--catalog` (7 names × 10 series × 9 cells = 630 runs) on Python 3.9 `.venv_test`, `--lorentzian`
  (1 name × 10 × 9 = 90 runs) on the standalone Python 3.11 `.venv_lorentzian`, then `--merge`.
- **Grid**: `activate_pct ∈ {0.01, 0.03, 0.06}` × `trail_pct ∈ {0.01, 0.02, 0.04}` = 9 cells. The
  0.03/0.02 cell is re-run from scratch rather than lifted from the stored notes, so every figure in
  the comparison comes out of one process over one set of frames — and is then *also* diffed against
  the stored rows (see check 2).
- **Fixed**: one-shot `entry_regime_mask` **on** for every run (per the board's recorded decision to
  evaluate new work with it from now on), `cooldown_candles=0`, `leverage=1`, `max_sl_pct=0.03`,
  `atr_multiplier=1.5`, `initial_equity=500`, `stake=100`, `commission_rate_bps=10`,
  `half_spread_bps=5`, `slippage_bps=2`, `now` pinned to `2025-03-01T00:00:00Z`.
- **Masks**: built by `entry_masks.one_shot_entry_mask` over `entry_masks.strategy_signal_series(...)`
  — the merged helper, reused unmodified. The mask is a function of the signal only, so it is
  computed once per (name, symbol, interval) and shared by all 9 cells; that is also what makes the
  `n_trades`-invariance prediction testable.
- **Data**: `data_contract.load_dataset("data_cache", …, "2024-01-26T00:00:00Z",
  "2026-09-01T00:00:00Z")`, all ten checksums verified in-script against
  `spec/research/F005-validation-protocol.md` section 6 (same `EXPECTED_CHECKSUMS` table as every
  other F006 script, duplicated rather than imported so the verification is independent), then
  sliced to `[2024-01-26T00:00:00Z, 2025-03-01T00:00:00Z)` — warm-up + Train 1 only — before
  `run_backtest` sees it. No network fetch.
- **Recorded per run**: net PnL, **gross PnL (pre-cost)**, total costs, win rate, `n_trades`,
  `n_calls`, `max_drawdown_pct`, `final_equity`, `survived`, `avg_winner`, `avg_loser`,
  `breakeven_win_rate_pct`, `sum_wins`/`n_wins`/`sum_losses`/`n_losses` (so cells can be pooled
  correctly rather than averaged over ratios), exit-reason counts and mean bars held.
- **New computation logic, in its own module**: `trade_stats.py` —
  `win_loss_decomposition(trades)` and `breakeven_win_rate_pct(avg_winner, avg_loser)`. It reuses
  `result.trades["net_pnl"]` and the engine's own win convention (`net_pnl > 0` is a win, `<= 0` is a
  loss — exactly `backtest_engine`'s `win_rate = (net_pnl > 0).mean() * 100`, asserted in the tests)
  rather than reimplementing any metric the engine already produces.

**Discriminating checks, run before and alongside the grid:**

1. **The new arithmetic is right against hand-calculated numbers** (`tests/test_trade_stats.py`):
   a fixture of seven trades with known net PnLs, hand-computed `avg_winner`, `avg_loser` and
   `breakeven_win_rate_pct`; the zero-PnL boundary (counts as a loss, matching the engine);
   the no-winners / no-losers / no-trades degenerate cells; pooling identity (decomposing a
   concatenation equals pooling the parts' sums and counts); and an end-to-end agreement test that
   the helper's win count over a real `run_backtest` result reproduces `result.metrics["win_rate"]`.
2. **The baseline cell reproduces the stored notes exactly.** All 80 rows of the 0.03/0.02 cell are
   diffed row by row against `output/f006_one_shot/summary/results.csv` (one-shot, `cd=0`, the six
   catalog + Lorentzian names) and `output/f006_donchian/summary/results.csv` (one-shot, the two
   Donchian names) on `net_pnl`, `win_rate`, `n_trades`, `max_drawdown_pct`, `final_equity` and
   `n_calls`. This is the harness-control pattern the Donchian note recommends every future F006
   script adopt; it is what makes "improves versus the baseline" a measured statement instead of an
   assumed one.
3. **The trade-count confound is measured, not assumed**: per-(name, symbol, interval) spread of
   `n_trades` across the 9 cells, and pooled `n_trades` per cell versus baseline, both reported.
4. **The one-shot rule still holds**: `n_trades <= n_calls` on every run in the grid.

## Run_id

`scripts/f006_trailing_sweep_experiment.py`, `git_commit_parent =
86afa1c9c63d1114783ed3308880146a30edc5e2` (the pre-registration commit above), `n_runs = 720`.
Catalog+Donchian pass: `run_timestamp_utc = 2026-09-23T12:34:18Z`, Python 3.9.25, 630 runs,
`elapsed_seconds = 125.8`. Lorentzian pass: `run_timestamp_utc = 2026-09-23T12:35:06Z`, Python
3.11.16 + advanced-ta 0.1.8, 90 runs, `elapsed_seconds = 43.9`. pandas 2.3.3 in both. Full
parameters, checksums, cross-checks and aggregate tables:
`output/f006_trailing_sweep/summary/manifest.json`. Per-run results, 720 rows:
`output/f006_trailing_sweep/summary/results.csv` (per-pass: `results_catalog.csv`,
`results_lorentzian.csv`).

**Rebuilding `.venv_lorentzian` in this worktree** took ~2 minutes rather than the ~20 the ticket
budgeted, because the standalone CPython 3.11.16 tarball from
`spec/research/F006-hypothesis-one-shot-entry.md`'s recipe was still cached at `/tmp/cpy311.tar.gz`
on this host, with the recorded sha256
`faa0758583a63f14c5eee516af82738403b59c13edda6fc0a21d953febd89eed` (verified before use). If it is
gone, the download is the slow part; the recipe itself is unchanged. `data_cache/*.csv` is
gitignored, so the ten `*_20240126T000000Z_20260901T000000Z.csv` files were copied from the main
checkout and both passes verified their checksums before use.

## Result

**The hypothesis is NOT falsified.** This is the first F006 hypothesis to survive its own
pre-registered condition. Six of the eight non-baseline cells clear both clauses.

**The 9-cell grid, pooled over all 17,399-18,420 trades in each cell** (80 series each: 8 names ×
5 symbols × 2 intervals, one-shot mask on, `cd=0`, `max_sl_pct=0.03`):

| cell (`a`/`t`) | lock-in | avg winner | avg loser | R:R | **breakeven win%** | actual win% | gap (pp) | net/trade | gross/trade | trades | profitable runs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.01 / 0.01 | 0.9999 | $0.306 | -$1.065 | 0.288 | **77.65** | 12.93 | 64.72 | -$0.887 | -$0.567 | 17,399 | 0/80 |
| 0.01 / 0.02 | 0.9898 | $1.012 | -$1.266 | 0.799 | 55.59 | 18.69 | 36.89 | -$0.841 | -$0.520 | 17,885 | 0/80 |
| 0.01 / 0.04 | 0.9696 | $2.256 | -$1.737 | 1.299 | 43.50 | 26.91 | 16.60 | -$0.663 | -$0.343 | 18,420 | 3/80 |
| 0.03 / 0.01 | 1.0197 | $1.304 | -$1.877 | 0.695 | 59.01 | 32.00 | 27.01 | -$0.859 | -$0.539 | 17,727 | 0/80 |
| **0.03 / 0.02 (baseline)** | 1.0094 | $1.333 | -$1.875 | 0.711 | **58.44** | 32.02 | 26.42 | -$0.848 | -$0.527 | 17,776 | 0/80 |
| 0.03 / 0.04 | 0.9888 | $2.248 | -$1.829 | 1.229 | 44.86 | 28.24 | 16.62 | -$0.678 | -$0.358 | 18,243 | 3/80 |
| 0.06 / 0.01 | 1.0494 | $2.540 | -$2.039 | 1.245 | 44.54 | 29.98 | 14.56 | -$0.667 | -$0.346 | 18,229 | 2/80 |
| 0.06 / 0.02 | 1.0388 | $2.521 | -$2.038 | 1.237 | 44.71 | 29.98 | 14.73 | -$0.672 | -$0.352 | 18,221 | 1/80 |
| **0.06 / 0.04 (best)** | 1.0176 | **$2.710** | -$2.036 | **1.331** | **42.90** | 29.95 | **12.94** | **-$0.614** | **-$0.294** | 18,302 | 4/80 |

**The headline: `breakeven_win_rate_pct` falls from 58.44% to 42.90%, a 15.54 pp improvement —
7.8× the 2.0 pp bar the falsification condition set.** The reward:risk ratio rises from 0.711 to
1.331: the average winner **overtakes** the average loser, which no F006 measurement has ever shown
before. The gap between what a name needs and what it gets narrows from 26.42 pp to 12.94 pp — the
exit parameters account for **51% of the shortfall** the Donchian note measured.

**Clause (b) — "not just trading less" — passes comfortably, and in the opposite direction from the
worry.** The best cell trades **more**, not less: 18,302 trades against the baseline's 17,776
(+3.0%), so the bar of "no more than a 10% drop" is not remotely approached. Net per-trade
expectancy improves (-$0.848 → -$0.614, +27.6%) and **gross** per-trade expectancy improves by the
same $0.233 (-$0.527 → -$0.294, +44.3%), since cost per trade is $0.320 in every cell of every
F006 run. The improvement is entirely trade geometry; none of it is a cost effect.

**The mechanism, which is sharper than the hypothesis predicted: the two parameters collapse into
one.** `avg_winner` is essentially a function of `max(activate_pct, trail_pct)` alone:

| `max(a, t)` | cells | avg winner | avg loser | breakeven win% | net/trade |
| ---: | --- | ---: | ---: | ---: | ---: |
| 0.01 | 0.01/0.01 | $0.306 | -$1.065 | 77.65 | -$0.887 |
| 0.02 | 0.01/0.02 | $1.012 | -$1.266 | 55.59 | -$0.841 |
| 0.03 | 0.03/0.01, 0.03/0.02 | $1.319 | -$1.876 | 58.72 | -$0.853 |
| 0.04 | 0.01/0.04, 0.03/0.04 | $2.252 | -$1.782 | 44.18 | -$0.670 |
| 0.06 | all three `a = 0.06` cells | $2.590 | -$2.038 | 44.03 | -$0.651 |

Cells sharing a `max(a, t)` agree to within a few cents on `avg_winner` while differing on both raw
parameters, and the two `a = 0.06` cells at `t = 0.01` and `t = 0.02` are indistinguishable (44.54%
vs 44.71% breakeven). The reason is in the engine (`backtest_engine._update_trailing`): a position
cannot be closed by the trail until `best_price >= entry * (1 + a)`, and the trail then sits at
`best_price * (1 - t)`, so the smallest trailing exit the machinery can produce is bounded below by
`(1+a)(1-t)` and the *binding* constraint is whichever of the two thresholds the price has to clear
last. `tests/test_trailing_geometry.py` pins that floor on the recorded stop levels.

**One correction to the mechanism as first written, left visible rather than edited away.** The
floor is a statement about the trailing stop **level**, not the realised exit price. On Train-1
BTCUSDT 1h `EMA_8_21` at `a=0.06, t=0.01` (lock-in floor +4.94%): **0 of 43** trailing exits had a
stop level below the floor, but **34 of 43 filled at a gap** and **24 of those realised below it** —
`execution.resolve_stop_take_within_bar` fills at the bar's open when the bar gaps through the stop.
The giveback is therefore larger than `(1+a)(1-t)` alone implies, which is one reason the improved
geometry still does not reach profitability. Both halves are now tests.

**P1 and P2 hold where they can and fail where the collapse predicts they must.**

| Claim | Series | avg winner rises? | breakeven falls? | net change |
| --- | --- | :-: | :-: | ---: |
| P1: raise `a`, `t = 0.01` | 0.306 → 1.304 → 2.540 | yes | yes | **-33.11 pp** |
| P1: raise `a`, `t = 0.02` | 1.012 → 1.333 → 2.521 | yes | no (55.59 → 58.44 → 44.71) | -10.88 pp |
| P1: raise `a`, `t = 0.04` | 2.256 → 2.248 → 2.710 | no | no | -0.61 pp |
| P2: raise `t`, `a = 0.01` | 0.306 → 1.012 → 2.256 | yes | yes | **-34.15 pp** |
| P2: raise `t`, `a = 0.03` | 1.304 → 1.333 → 2.248 | yes | yes | -14.15 pp |
| P2: raise `t`, `a = 0.06` | 2.540 → 2.521 → 2.710 | no | no | -1.64 pp |

Both sub-claims hold strongly wherever the swept parameter is the binding one, and go flat wherever
the *other* parameter already dominates `max(a, t)` — exactly what the collapse implies. The
predicted best cell (0.06/0.04) was correct and the predicted worst (0.01/0.01) was correct: the
tightest cell has a lock-in of 0.9999, arms at +1% and guarantees a scratch, producing an average
winner of **$0.31** against a -$1.07 loser and a **12.93%** win rate — it needs 77.65% of trades to
win and gets one in eight.

**The pre-registered `n_trades`-invariance prediction was partly wrong, and the failure is
informative.** Predicted: near-constant trade counts across cells. Measured: **43 of 80** series
have literally identical `n_trades` in all 9 cells; mean relative spread **10.2%**, max **67.7%**.
Two mechanisms, both measured, and neither helps the loose cells:

* **15 of 80 series hit the $100 margin floor** in at least one cell (`equity.InsufficientMarginError`
  skips the entry). All 15 have a nonzero spread, and every one of them is a series whose minimum
  final equity across cells is under $100. These are the *tight* cells running out of money and
  therefore stopping trading — which flatters the tight cells' per-trade figures, not the loose
  ones. Among the 65 series that stay solvent in all 9 cells, 43 are exactly invariant and the mean
  relative spread is 6.9%.
* **The remaining variation runs against the loose cells.** A position held longer can still be open
  when the same direction re-arms after a flat gap (`+1, 0, +1` is a new call under
  `entry_masks.one_shot_entry_mask`, but the engine cannot enter while `pos != 0`), so that call is
  skipped. `BB_20_25_breakout` loses 17% of its trades at the best cell (1,390 → 1,158) for this
  reason, while still improving its breakeven rate by 20.4 pp.

**Every one of the 8 names improves, including the mean-reversion name and both new generators.**

| Name | breakeven% @ baseline | breakeven% @ 0.06/0.04 | Δ | gap @ baseline | gap @ best | net/trade | mean net PnL | survived |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `EMA_8_21` | 55.36 | **37.50** | -17.86 | 25.83 | 11.22 | -$0.792 → -$0.540 | -$223.8 → -$154.5 | 9/10 → 10/10 |
| `MACD_12_26_hist` | 56.67 | 43.58 | -13.09 | 27.42 | 15.10 | -$0.795 → -$0.619 | -$319.1 → -$270.5 | 7/10 → 7/10 |
| `RSI14_7030` | 66.67 | 53.91 | -12.76 | 24.31 | 12.43 | -$1.025 → -$0.724 | -$250.2 → -$174.4 | 9/10 → 10/10 |
| `BB_20_25_breakout` | 63.13 | 42.77 | -20.36 | 26.94 | 12.46 | -$1.031 → -$0.814 | -$143.3 → -$94.3 | 10/10 → 10/10 |
| `ADX14_DI_20` | 53.60 | 41.08 | -12.52 | 27.92 | 15.24 | -$0.729 → -$0.562 | -$326.3 → -$273.8 | 6/10 → 7/10 |
| `DONCHIAN_55` | 63.81 | 41.48 | **-22.33** | 24.73 | **6.82** | -$1.014 → **-$0.501** | -$48.3 → -$23.9 | 10/10 → 10/10 |
| `DONCHIAN_PULLBACK_55` | 64.44 | 43.83 | -20.61 | 20.35 | **8.96** | -$0.889 → -$0.638 | -$33.1 → -$23.6 | 10/10 → 10/10 |
| `LORENTZIAN_default` | 61.77 | 43.95 | -17.82 | 25.52 | 11.34 | -$0.914 → -$0.613 | -$162.6 → -$109.1 | 10/10 → 10/10 |

The effect is not one family's: 8 of 8 improve, by 12.5 to 22.3 pp. `RSI14_7030`, the sample's
mean-reversion name, improves by 12.76 pp — in line with the weaker trend names (`ADX14_DI_20`
12.52, `MACD_12_26_hist` 13.09) but from a much worse starting point (66.67%) and stays the worst name in the sample — its winners are capped by the same trail while its
losers run to the same -3%.

**Risk and exit mix move with it, coherently.** Mean max drawdown falls 38.3% → 30.6%, survivors
rise 71/80 → 74/80, mean holding time rises 10.2 → 16.8 bars, and the exit mix shifts from
**23.3% `initial_sl` / 33.1% `trailing_sl` / 43.5% `signal_reverse`** at baseline to
**27.1% / 14.5% / 58.3%** at the best cell. At the baseline the machinery closed 56.4% of trades;
at the best cell it closes 41.6% and the *signal* closes most of them — which is what "letting the
signal be tested" means mechanically.

**The first profitable runs in F006: 13 of 720.** Across every prior F006 slice's stored results
— **2,220 runs** (stop-width 400, regime-filter 500, cooldown 600, Lorentzian 120, one-shot 480,
Donchian 120) — the count of runs with positive net PnL is **0**, re-counted from their CSVs for
this note rather than taken from their prose. All 13 here are Donchian names on BTCUSDT or ETHUSDT, all at
`trail_pct = 0.04` or `activate_pct = 0.06`, and all small:

| cell | name | symbol | interval | net PnL | gross | win rate | trades | max DD |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 0.06/0.04 | `DONCHIAN_PULLBACK_55` | BTCUSDT | 1h | **$15.16** | $34.11 | 42.37% | 59 | 5.65% |
| 0.03/0.04 | `DONCHIAN_PULLBACK_55` | BTCUSDT | 1h | $12.18 | $31.78 | 42.62% | 61 | 4.51% |
| 0.06/0.01 | `DONCHIAN_PULLBACK_55` | BTCUSDT | 1h | $11.84 | $30.79 | 42.37% | 59 | 4.16% |
| 0.06/0.04 | `DONCHIAN_55` | BTCUSDT | 1h | $11.00 | $35.31 | 36.84% | 76 | 5.93% |
| 0.01/0.04 | `DONCHIAN_PULLBACK_55` | BTCUSDT | 1h | $8.73 | $28.32 | 39.34% | 61 | 4.44% |
| 0.03/0.04 | `DONCHIAN_PULLBACK_55` | BTCUSDT | 4h | $8.32 | $12.14 | 50.00% | 12 | 2.51% |
| … 7 more, $0.69 to $7.36 | | | | | | | | |

Stated with the same caution the Donchian note applied to itself: **this is 13 of 720 (1.8%), on two
symbols out of five, with 12 to 76 trades each, and the largest is $15.16 on a $500 account over a
year.** `DONCHIAN_PULLBACK_55`/BTCUSDT/1h is positive in 5 of its 9 cells, which is the only one of
the 13 that is not a single-cell coincidence. None of this is an edge; it is recorded so that the
"0 profitable runs anywhere" statement from prior notes is not silently carried forward as still
true.

**4h vs 1h: the improvement is larger at 4h in percentage-point terms but 1h remains better.**
Breakeven at 4h falls 65.34% → 45.91% (-19.4 pp) and at 1h 56.32% → 41.80% (-14.5 pp); net per trade
at the best cell is -$0.923 (4h) against -$0.528 (1h). The Donchian note's finding that 4h has the
worse trade geometry survives the sweep — it is improved, not reversed.

**What did not change, and it is the important half.** Per-trade expectancy is **negative in every
one of the 9 cells**, and **gross** (pre-cost) per-trade expectancy is negative in every one of the
9 cells. Even at the best cell a name needs 42.90% of trades to win and gets 29.95%. And the
composition of the remaining loss has shifted: at baseline costs were 37.8% of the net loss per
trade, at the best cell they are **52.1%** ($0.320 of $0.614). The geometry problem is roughly half
solved; what is left is half cost drag and half a residual -$0.294 of gross edge.

## Decision

**The reward:risk ratio is a property of the exit parameters, not of this basket's price action —
the Donchian note's alternative explanation is rejected.** Moving two numbers that seven prior F006
slices inherited without questioning takes the pooled breakeven win rate from 58.44% to 42.90%, the
reward:risk ratio from 0.71 to 1.33, and the gap to breakeven from 26.4 pp to 12.9 pp, on 3% *more*
trades and with 44% better gross per-trade expectancy. That is the single largest effect any F006
lever has produced, and unlike `cooldown_candles` and the one-shot mask it is not a trade-count
effect.

**It is not enough to promote anything to Validation, and the protocol says so explicitly.**
`spec/research/F005-validation-protocol.md` section 7 (hard rejection criteria, quoting
`spec/build.md`): *"Ujemny PnL netto w dowolnym ocenianym miesiącu lub w całym okresie → brak
promocji, niezależnie od regularności"*. Every cell of this grid has negative net PnL over Train 1
on 80 of 80 series in aggregate; the best single name at the best cell (`DONCHIAN_PULLBACK_55`,
-$23.6 mean) is still losing. Spending Validation budget now would burn a window to confirm a
negative number. **Recommendation: do not promote; run one more Train-1 slice first.**

**Which is exactly what the data asks for, because the optimum is at the grid boundary.** The best
cell is the corner `a = 0.06, t = 0.04` — both parameters at their maximum. The sweep has found a
direction, not an optimum, and the `max(a, t)` collapse says what to vary next and why the current
grid is nearly one-dimensional. **The next slice should extend the same grid outward and add the two
variants this ticket's 3×3 could not contain:**

1. **`max(a, t)` beyond 0.06** — e.g. `a ∈ {0.06, 0.10, 0.15}` × `t ∈ {0.04, 0.08}`. The
   `max(a, t)` table is still improving at its right edge (44.18 → 44.03 breakeven from 0.04 to
   0.06, having come from 77.65), so the curve is flattening but has not turned. Where it turns is
   the question, and it is cheap: 720 runs took 170 seconds on two interpreters.
2. **No trailing stop at all** (the variant `spec/research/F006-hypothesis-donchian.md` asked for and
   this 3×3 grid could not express). It is the `t → ∞` limit of the collapse and the natural control:
   if "no trail" beats every cell, the trailing machinery is a pure cost and the finding is simpler
   than this note's.
3. **A take-profit at a multiple of the initial stop distance.** The engine supports
   `take_profit=None` only through `execution.resolve_stop_take_within_bar`'s existing parameter,
   which `run_backtest` never populates — so this one needs an engine change and should be scoped as
   such, not smuggled into a research script.
4. **`max_sl_pct` jointly with `max(a, t)`.** `spec/research/F006-hypothesis-stop-width.md` swept the
   loss side alone at a fixed, and now known to be badly chosen, 0.03/0.02 win side. Its conclusion
   ("nothing at any width") was measured inside the worst corner of this grid and deserves one
   re-test at `a = 0.06, t = 0.04`. This is the cheapest way to find out whether a prior F006
   negative result was an artefact of an unexamined default — and if it is, every entry-side slice
   deserves the same question asked of it.

**On the possibility this ticket asked to be named explicitly.** The ticket anticipated an eighth
consecutive falsification and asked whether that would mean catalog-and-parameter search cannot
reach the project's regularity target on this basket and timeframe range. **The data does not
support saying that, and it should not be said.** The invariant that motivated the question —
"every name needs ~63% and none gets past 44%" — was measured inside one arbitrary corner of the
exit-parameter space, and half of it dissolved the moment that corner was left. The honest
statement is narrower and more useful: **seven prior F006 slices measured the same
badly-parameterised exit machinery and attributed its signature to their own levers.** The entry
side may well be exhausted; the exit side demonstrably was not, and was never tested. Before any
claim about the limits of this approach, the exit space has to be swept to its actual boundary —
items 1 and 2 above — and `spec/research/F006-hypothesis-stop-width.md`'s negative result re-run
outside the corner.

**What is reusable regardless of that outcome:**

* `trade_stats.py` — `avg_winner` / `avg_loser` / `breakeven_win_rate_pct` with correct pooling, 7
  hand-calculated tests. Every future F006 script should report breakeven-gap, not net PnL: this run
  found a 15.5 pp geometry improvement that net PnL alone would have shown as "still losing money".
* The harness-control pattern, now at two notes: re-running the baseline cell inside the new
  experiment and diffing it against the stored rows (**80/80 exact**) is what makes "improves versus
  baseline" a measurement.
* `tests/test_trailing_geometry.py` — the lock-in floor and the gap-fill exception, for any later
  slice reasoning about what the trail can and cannot produce.
* The `max(a, t)` collapse: the exit parameter space is effectively **one**-dimensional in the region
  swept here, so the next grid should spend its cells on reach, not on resolution.

**Falsification verdict, restated for the record**: hypothesis **NOT falsified**. Clause (a) not met
— 6 of 8 non-baseline cells improve pooled `breakeven_win_rate_pct` by ≥ 2.0 pp, the best by 15.54
pp. Clause (b) not met — the best cell trades 3.0% *more* than baseline (bar: no worse than -10%),
improves net per trade by $0.234 and gross per trade by $0.233. Both sub-claims (P1, P2) hold
wherever the swept parameter binds and go flat exactly where `max(a, t)` predicts they must.

## Tests

`tests/test_trade_stats.py` (7 new tests) and `tests/test_trailing_geometry.py` (15 passed, 4
skipped) are described under "Method", check 1, and in the Result section's mechanism paragraph.

**Sabotage-and-restore, reported honestly including the mutation that was not caught:**

| Mutation | Effect |
| --- | --- |
| `breakeven_win_rate_pct` ratio inverted (`avg_winner / denom`) | **4 of 7** trade_stats tests fail |
| zero-PnL trade counted as a win (`net >= 0` / `net < 0`) | **2 of 7** fail |
| `pool_decompositions` averages the parts' `avg_winner` instead of summing sums | **1 of 7** fails (the pooling-identity test, by design) |
| `avg_winner` divided by trade count instead of winner count | **1 of 7** fails |
| `_update_trailing`'s activation gate removed (`(1 + activate_pct)` → `(1 + 0.0)`) | **17 of 19** trailing-geometry tests fail |
| `_update_trailing` ratchets from `entry_price` instead of `best_price` | **0 fail — not caught.** The lock-in floor is a one-sided bound that a frozen ratchet also satisfies, and at `t = 0.01` the trail fires so soon after arming that the ratchet rarely moves at all (max recorded stop level is identical, 3.4653%, with and without the mutation). Recorded rather than papered over: these tests pin the floor, not the ratchet. |

All mutations restored; `git diff` on `backtest_engine.py` and `trade_stats.py` is empty.

Full suite, before and after this slice, on both interpreters:

| | Baseline (this slice's two test files excluded) | With this slice |
| --- | --- | --- |
| Python 3.9 `.venv_test` | 112 passed, 5 skipped | **134 passed, 9 skipped** |
| Python 3.11 `.venv_lorentzian` | 115 passed, 2 skipped | **137 passed, 6 skipped** |

Exactly the 22 new tests on both, no behaviour change in any existing test. Both baselines were
measured in this worktree, not copied from a prior note. The 4 skips are trailing-exit cells the
600-bar fixture cannot produce (documented in the test module's docstring); the `a = 0.06 / t = 0.04`
cell the Result section calls best is covered on the amplified frame and is not among them.
