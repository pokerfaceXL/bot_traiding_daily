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
