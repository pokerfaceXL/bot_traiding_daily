# F006 — Hypothesis: entry-quality regime filter (ADX14 trend strength), Train 1 only

> Written up to and including "Falsification condition" BEFORE running the experiment script,
> per the ticket's requirement to state the predicted effect before looking at results. The
> "Method", "Run_id", "Result", and "Decision" sections below were filled in after the run.
> This is a TRAIN-only exploratory experiment. Per `spec/research/F005-validation-protocol.md`
> section 7.3, F006 does all its selection on train+validation and never opens holdout — this
> experiment does not touch Validation 1-4 or the Holdout window (2026-03-01 onward) at all.

## Observation

`spec/research/F006-hypothesis-stop-width.md` ruled out stop-width as a fix for the existing
catalog's negative edge: widening `max_sl_pct` from 0.03 to 0.12 improved mean win rate
monotonically (28.94% → 34.60%) but produced **zero** profitable runs out of 400 and no clear,
monotonic net PnL improvement in aggregate. That note's stated next step is to test trade
*selection* (fewer, higher-conviction entries) rather than another trade *exit-sizing* sweep,
since exit-sizing sweeps (that experiment, plus F005's leverage/cooldown sweeps) have both now
been tried without restoring positive edge.

## Hypothesis

A meaningful fraction of the existing catalog's entries fire during choppy/range-bound
conditions, where trend-following and momentum signals (7 of the catalog's families are
trend/momentum-based) are least reliable and most likely to whipsaw into a stop-out before any
real directional move develops. **Predicted effect**: gating new entries on `adx14` (already
computed by `strategy.add_indicators`) exceeding a threshold — i.e. only entering during
trending regimes, as identified in real time by `adx14` at signal time, not post-hoc — should,
holding signal logic, `leverage=1` (F006 research placeholder), `cooldown_candles=0`,
`max_sl_pct=0.03` (F005/F006 baseline value, held fixed to isolate this filter's effect from the
already-tested stop-width dimension) and costs fixed, reduce trade count and improve mean win
rate and/or net PnL as the ADX threshold rises from no filter to 30, by suppressing exactly the
low-conviction, high-noise entries the mechanism describes.

## Sources

This repo's own prior findings only: `spec/research/F006-hypothesis-stop-width.md`,
`spec/research/F005-leverage-sensitivity.md`, `spec/research/F005-baseline.md`,
`spec/research/F005-validation-protocol.md` (frozen window boundaries, section 3.2: Train 1 =
2024-03-01T00:00:00Z … 2025-03-01T00:00:00Z, warm-up back to 2024-01-26T00:00:00Z).

## Falsification condition (stated before running)

This hypothesis is **falsified** if mean net PnL across the sampled (symbol, interval, strategy)
combinations does not improve (does not become less negative or positive) as the ADX14 entry
threshold rises from "no filter" to 30, AND/OR mean win rate does not increase over the same
sweep. If both move the wrong way, move inconsistently with no clear trend, or the filter merely
reduces trade count to near-zero without any accompanying win-rate/PnL improvement (i.e. the
filter is just starving the strategy of trades rather than selecting better ones), the hypothesis
is not supported and an ADX-based entry-quality filter alone is not the fix.

## Method

Same continuous-run methodology, checksum-verification discipline, and 10-strategy sample as
`spec/research/F006-hypothesis-stop-width.md` (`scripts/f006_stop_width_experiment.py`),
restricted to Train 1 only, with the addition of `backtest_engine.run_backtest`'s new
`entry_regime_mask` parameter (added by this experiment; gates only new-entry queuing, leaves
stop-loss/trailing/signal-reversal exits untouched — see `backtest_engine.py`'s module
docstring). Existing 79 (81 after this addition) engine tests, including two new regression
tests confirming `entry_regime_mask=None`/all-True is a no-op and all-False blocks every entry,
pass before this experiment runs.

- **Sample**: same 10 strategies, same 5×2 symbol/interval basket, same checksummed
  `data_cache` load and Train 1 slice (`[2024-01-26T00:00:00Z, 2025-03-01T00:00:00Z)`) as
  `spec/research/F006-hypothesis-stop-width.md`.
- **Grid**: ADX14 entry threshold in {none, 15, 20, 25, 30} × 10 strategies × 5 symbols ×
  2 intervals = 500 runs. For each non-"none" threshold, the mask is
  `strategy.add_indicators(train1_df.copy())["adx14"] > threshold`, computed once per
  (symbol, interval) and reindexed onto the engine's own closed-candle frame inside
  `run_backtest`. Fixed: `leverage=1`, `cooldown_candles=0`, `max_sl_pct=0.03`,
  `atr_multiplier=1.5`, `activate_pct=0.03`, `trail_pct=0.02` (same defaults as the stop-width
  experiment), `initial_equity=500`, `stake=100`, `commission_rate_bps=10`, `half_spread_bps=5`,
  `slippage_bps=2`. `now` fixed to `2025-03-01T00:00:00Z` (Train 1 boundary).
- **Metrics recorded per run**: net PnL, win rate, number of trades, max drawdown_pct,
  `survived = final_equity >= $100`. `regularity.compute_regularity` is not invoked (Train-only
  exploration, per the frozen protocol).

## Run_id

Script: `scripts/f006_regime_filter_experiment.py`. `run_timestamp_utc = 2026-09-23`,
`git_commit_parent` = HEAD at the time this script ran (preceding this note's commit),
`elapsed_seconds ≈ 84.0`, `n_runs = 500`. Full parameters/checksums:
`output/f006_regime_filter/summary/manifest.json`. Full per-run results:
`output/f006_regime_filter/summary/results.csv` (500 rows, committed directly).

## Result

**Aggregate mean, across all 100 runs per threshold (10 strategies × 5 symbols × 2 intervals):**

| ADX threshold | Mean net PnL | Mean win rate | Mean n_trades | Mean max_drawdown_pct | Survived | Runs with positive net PnL |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| none | -$357.81 | 28.94% | 367.8 | 71.80% | 27/100 | 0/100 |
| 15 | -$357.46 | 29.00% | 367.4 | 71.73% | 27/100 | 0/100 |
| 20 | -$355.38 | 29.07% | 364.4 | 71.32% | 29/100 | 0/100 |
| 25 | -$350.51 | 29.02% | 353.3 | 70.36% | 34/100 | 0/100 |
| 30 | -$340.13 | 28.73% | 337.4 | 68.27% | 38/100 | 0/100 |

**Mean net PnL improves modestly and monotonically as the threshold rises** (-$357.81 →
-$340.13, a $17.68 swing, roughly 5% of the deficit), unlike the stop-width experiment's flat,
non-monotonic sweep. Per-strategy breakdown (`output/f006_regime_filter/summary/results.csv`)
shows this is a broad, consistent pattern: **9 of 10 strategies improve net PnL monotonically**
as the threshold rises from none to 30 (e.g. `BB_20_25_breakout` -$168.6 → -$132.5,
`RSI14_7030` -$362.8 → -$333.4, `BB_20_2_RSI14` -$306.2 → -$263.0); only `STOCH14_cross` is flat
to marginally worse. Survival count also rises (27/100 → 38/100).

**Mean win rate does NOT increase over the sweep** — it is flat and noisy (28.94% → 29.00% →
29.07% → 29.02% → 28.73%), a swing of about 0.3 percentage points with no clear direction,
and actually ends lower at threshold=30 than at threshold=20. Per-strategy win-rate figures
confirm this: most strategies show sub-1-point, non-monotonic wobble (e.g. `EMA_8_21` 28.68% →
28.83%, `MACD_RSI14_50` 28.40% → 27.90%) rather than the clear improvement the entry-quality
mechanism predicted.

**The net-PnL improvement tracks trade-count reduction, not selection quality.** Mean n_trades
falls from 367.8 to 337.4 (an 8.3% reduction) as the threshold tightens, and every strategy's
n_trades falls monotonically alongside its net-PnL improvement (e.g. `ADX14_DI_20` 438.2 → 390.4
trades while win rate is flat at ~25%; `MACD_12_26_hist` 423.1 → 405.5 trades, win rate flat at
~27%). Since win rate stays flat while PnL improves as trade count drops, the improvement is
consistent with simply paying fewer round-trip costs (commission/spread/slippage) on a smaller
number of similarly-unprofitable trades — not with the filter selecting higher-quality entries,
which would show up as a win-rate increase. **Zero of the 500 runs, at any threshold, produced a
positive net PnL.**

**Falsification check**: the stated condition requires mean win rate to increase alongside net
PnL improving; win rate does not clearly increase (flat/noisy, non-monotonic). Per that
condition, and per the explicit caveat about trade-count reduction without win-rate/PnL-quality
improvement, **the hypothesis is falsified at the aggregate level** — the small net-PnL gain is
best explained by reduced cost drag from trading less, not by the filter picking better trades.

## Decision

**Abandon the ADX14 entry-regime filter, on its own, as the fix for the existing catalog's
negative edge.** It produces a real but small ($17.68, ~5% of the deficit) and mechanistically
unconvincing net-PnL improvement — driven by fewer trades/lower cost drag rather than by higher
win rate — and, like the stop-width experiment, zero profitable (symbol, interval, strategy,
threshold) combinations out of 500 on Train 1. Combined with F006-hypothesis-stop-width.md, two
independent single-dimension entry/exit-tuning hypotheses (wider stops, ADX-gated entries) have
now both been tried and neither restores positive edge, though each moves a different metric
(win rate for stop-width, trade-count/cost-drag for the regime filter) without the other moving
together. Next F006 step: since both a pure exit-sizing change and a pure single-indicator
entry-quality gate have been ruled out individually, and neither showed win-rate improvement
from better trade selection (only from fewer premature stop-outs or fewer trades), the more
informative next experiment is likely a fundamentally different signal generator (not another
filter layered on the existing 79-strategy catalog's signal logic) — e.g. Lorentzian
Classification per `spec/build.md`'s stated F006 priority, or one of the not-yet-tried families
listed there (Donchian/pullback), rather than a third parameter sweep on the existing catalog.
