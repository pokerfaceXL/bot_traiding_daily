# F006 — Hypothesis: stop width, Train 1 only

> Written up to and including "Falsification condition" BEFORE running the experiment script,
> per the ticket's requirement to state the predicted effect before looking at results. The
> "Method", "Run_id", "Result", and "Decision" sections below were filled in after the run.
> This is a TRAIN-only exploratory experiment. Per `spec/research/F005-validation-protocol.md`
> section 7.3, F006 does all its selection on train+validation and never opens holdout — this
> experiment does not touch Validation 1-4 or the Holdout window (2026-03-01 onward) at all.

## Observation

`spec/research/F005-baseline.md` (wave 3, full 79-strategy catalog, leverage=10,
`max_sl_pct=0.03`) and `spec/research/F005-leverage-sensitivity.md` (10-strategy sample,
leverage in {1,2,3,5,10}, cooldown in {0,5,20}, `max_sl_pct=0.03` throughout) both find: every
tested combination of (symbol, interval, strategy, leverage, cooldown) in the existing
`strategy.STRATEGY_CATALOG` loses money and eventually gets stopped out repeatedly under
realistic costs, at `max_sl_pct=0.03` (3%). This holds regardless of leverage or cooldown — the
leverage-sensitivity addendum shows leverage/cooldown only change *how fast* an account burns
down to the $100 re-entry floor, not *whether* it does. `spec/research/F006-pipeline-positive-control.md`
independently confirms the backtest/costs/equity/regularity pipeline itself produces a correct,
positive result on favourable (synthetic, near-zero-noise) data — so this is not a pipeline bug;
the negative edge is a property of the signal+stop combination on real, noisy data. A 3% stop is
tight relative to typical 4h/1h crypto price noise on this basket.

## Hypothesis

The 3% stop (`max_sl_pct=0.03`) is too tight relative to normal noise on these symbols/intervals,
causing strategies to be stopped out by noise before any real directional move plays out —
independent of whether the underlying signal has real directional skill. **Predicted effect**:
widening `max_sl_pct` alone (holding signal logic, `leverage=1` — the F006 research placeholder
per `spec/build.md` — `cooldown_candles=0`, and costs fixed) should measurably reduce the
frequency/severity of stop-outs and could shift average trade expectancy less negative, or even
positive, for at least some strategies, without changing the signal logic itself.

## Sources

This repo's own prior findings only, no external sources needed for this internal hypothesis:
`spec/research/F005-baseline.md`, `spec/research/F005-leverage-sensitivity.md`,
`spec/research/F006-pipeline-positive-control.md`, `spec/research/F005-validation-protocol.md`
(frozen window boundaries, section 3.2: Train 1 = 2024-03-01T00:00:00Z … 2025-03-01T00:00:00Z).

## Falsification condition (stated before running)

This hypothesis is **falsified** if net PnL and win rate do not improve, on average across the
sampled (symbol, interval, strategy) combinations, as `max_sl_pct` increases from 0.03 to 0.12.
"Improve on average" means: mean net PnL across the sample at `max_sl_pct=0.12` is not higher
(less negative or more positive) than at `max_sl_pct=0.03`, AND mean win rate does not increase.
If both directions move the wrong way, or move inconsistently with no clear monotonic trend, the
hypothesis is not supported and stop-width alone is not the fix.

## Method

Same continuous-run methodology and checksum-verification discipline as
`scripts/f005d_leverage_sensitivity.py`, restricted to Train 1 only.

- **Sample**: the same 10 strategies as `spec/research/F005-leverage-sensitivity.md` (`EMA_8_21`,
  `EMA_13_34_RSI14_55`, `RSI14_7030`, `MACD_12_26_hist`, `MACD_RSI14_50`, `BB_20_25_breakout`,
  `BB_20_2_RSI14`, `ADX14_DI_20`, `STOCH14_cross`, `TS_13_34_200_14`) — all 7 families present in
  `strategy.STRATEGY_CATALOG` (ADX, BB, EMA, MACD, RSI, STOCH, TS) are covered, and reusing the
  exact same sample makes this experiment's numbers directly cross-referenceable against the
  leverage-sensitivity addendum's `max_sl_pct=0.03`/`leverage=1`/`cooldown=0` rows, rather than
  introducing a new, harder-to-compare sample.
- **Data**: `data_contract.load_dataset("data_cache", symbol, interval, "2024-01-26T00:00:00Z",
  "2026-09-01T00:00:00Z")` for all 5×2 basket combinations — the same full protocol-scoped
  cache and checksums as `F005-validation-protocol.md` section 6 (verified in-script before use,
  no network fetch). The loaded frame is then **sliced down to `[2024-01-26T00:00:00Z,
  2025-03-01T00:00:00Z)`** (warm-up + Train 1 only, `2024-01-26` being the same 35-day warm-up
  buffer the protocol itself uses before Train1_start) before being passed to `run_backtest` —
  Validation/Holdout bars are never included in what the engine sees.
- **Grid**: `max_sl_pct` in {0.03, 0.05, 0.08, 0.12} × 10 strategies × 5 symbols × 2 intervals =
  400 runs. Fixed: `leverage=1`, `cooldown_candles=0`, `atr_multiplier=1.5`, `activate_pct=0.03`,
  `trail_pct=0.02` (backtest_engine's own function-signature defaults, not F005 baseline's
  overridden values — matching what `F006-pipeline-positive-control.md` used), `initial_equity=500`,
  `stake=100`, `commission_rate_bps=10`, `half_spread_bps=5`, `slippage_bps=2` (F005's cost
  defaults). `now` fixed to `2025-03-01T00:00:00Z` (the Train 1 boundary), not wall-clock time.
- **Metrics recorded per run**: net PnL, win rate, number of trades, max drawdown_pct (all from
  the Train-1-only run), and `survived = final_equity >= $100`. `regularity.compute_regularity`
  is deliberately **not** invoked — that metric is reserved for Validation/Holdout per the frozen
  protocol, and this is Train-only hypothesis exploration.

## Run_id

Script: `scripts/f006_stop_width_experiment.py`. `run_timestamp_utc = 2026-09-22T16:39:41.898745+00:00`,
`git_commit_parent = 3efdc1ff5b1d5da3f749f63d961809ed6e526949` (HEAD at the time this script ran,
preceding this note's commit), `elapsed_seconds ≈ 88.7`, `n_runs = 400`. Full parameters/checksums:
`output/f006_stop_width/summary/manifest.json`. Full per-run results:
`output/f006_stop_width/summary/results.csv` (400 rows, 32 KB, committed directly).

## Result

**Aggregate mean, across all 400 runs, per `max_sl_pct`:**

| `max_sl_pct` | Mean net PnL | Mean win rate | Mean n_trades | Mean max_drawdown_pct | Survived (final_equity ≥ $100) | Runs with positive net PnL |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.03 | -$357.81 | 28.94% | 367.8 | 71.80% | 27/100 | 0/100 |
| 0.05 | -$356.51 | 32.38% | 334.0 | 71.62% | 31/100 | 0/100 |
| 0.08 | -$357.92 | 34.07% | 321.8 | 71.95% | 30/100 | 0/100 |
| 0.12 | -$357.12 | 34.60% | 316.1 | 71.84% | 33/100 | 0/100 |

**Win rate improves monotonically and consistently, exactly as the mechanism predicted** —
every one of the 10 sampled strategies individually shows win rate rising (or flat) from
`max_sl_pct=0.03` to `0.12`, and the aggregate mean rises from 28.94% to 34.60%. Fewer trades
fire as stops widen (367.8 → 316.1 mean trades), consistent with fewer premature stop-outs.

**Net PnL does NOT show a clear, meaningful, or monotonic aggregate improvement.** The mean net
PnL across the sample is essentially flat and noisy across the sweep (-$357.81, -$356.51,
-$357.92, -$357.12 — a swing of under $1.70 out of ~$357, non-monotonic: 0.08 is worse than
0.03), not the clear directional improvement the hypothesis predicted. **Zero of the 400 runs,
at any tested `max_sl_pct`, produced a positive net PnL** — the stronger prediction ("could shift
… expectancy … positive, for at least some strategies") is directly contradicted by the data.
Max drawdown and survival counts are similarly flat/noisy (71.6–72.0% DD; survival 27–33/100,
no clean trend distinguishable from binomial noise at n=100).

**Per-strategy breakdown reveals real heterogeneity the aggregate mean hides** —
`output/f006_stop_width/summary/results.csv`, mean net PnL by strategy across the 5×2 basket:

| Strategy | 0.03 | 0.05 | 0.08 | 0.12 | Pattern |
| --- | ---: | ---: | ---: | ---: | --- |
| RSI14_7030 | -$362.8 | -$342.1 | -$337.0 | -$304.8 | improves clearly, still deeply negative |
| TS_13_34_200_14 | -$365.9 | -$355.6 | -$344.2 | -$345.7 | improves, then flattens |
| EMA_8_21 | -$399.0 | -$387.2 | -$385.8 | -$384.3 | improves modestly |
| EMA_13_34_RSI14_55 | -$379.5 | -$372.7 | -$369.8 | -$370.0 | improves, then flattens |
| MACD_RSI14_50 | -$393.2 | -$388.4 | -$388.1 | -$388.1 | improves slightly |
| ADX14_DI_20 | -$400.6 | -$401.6 | -$401.6 | -$401.1 | flat (floor-locked) |
| MACD_12_26_hist | -$401.6 | -$401.4 | -$401.4 | -$401.7 | flat (floor-locked) |
| STOCH14_cross | -$400.6 | -$401.7 | -$400.9 | -$400.9 | flat (floor-locked) |
| BB_20_2_RSI14 | -$306.2 | -$318.5 | -$330.0 | -$341.5 | **worsens monotonically** |
| BB_20_25_breakout | -$168.6 | -$195.9 | -$220.4 | -$233.1 | **worsens monotonically, sharply** |

5/10 strategies show a real, monotonic-ish net PnL improvement as stops widen (mechanism: fewer
noise stop-outs), but none get close to breakeven. 3/10 are floor-locked near -$400 regardless of
stop width — same $500→$100 bankruptcy-floor mechanism `F005-baseline.md` already named, just
reached slightly slower. 2/10 (both Bollinger-Bands-family, both relatively low-frequency,
relatively survivable strategies at 0.03) get **meaningfully worse** as stops widen — for these,
fewer-but-larger losing trades outweigh the reduction in trade count, net PnL degrades. The
aggregate mean is a wash because these opposing effects roughly cancel.

**Falsification check**: mean net PnL does not clearly/monotonically improve at the aggregate
level (flat within noise, non-monotonic) even though mean win rate does. Per the falsification
condition stated above (both metrics must move together in the improving direction), **the
hypothesis is falsified at the aggregate level.**

## Decision

**Abandon stop-width alone as the fix for the existing catalog's negative edge.** Widening
`max_sl_pct` does exactly what the mechanism predicted to win rate (fewer premature stop-outs,
consistently across all 10 strategies) but this does **not** translate into a meaningful net PnL
improvement in aggregate, and produces **zero** profitable (symbol, interval, strategy,
max_sl_pct) combinations out of 400 on Train 1 — the core signal-quality problem F005 identified
(negative average trade expectancy, independent of leverage/cooldown) is not fixed by giving
trades more room to breathe. The per-strategy split is informative for the next step, though: a
minority of strategies (`BB_20_25_breakout`, `BB_20_2_RSI14`) get reliably *worse* with wider
stops, which is itself a useful negative signal about those specific strategies' trade-holding
behaviour, while the floor-locked third (`ADX14_DI_20`, `MACD_12_26_hist`, `STOCH14_cross`) look
structurally different (already-degenerate regardless of stop width) from the improving half —
suggesting these are not one homogeneous problem. Next F006 step: since stop width alone is
ruled out, test a hypothesis that changes trade *selection* rather than trade *exit sizing* —
e.g. a Train-1-only entry-filter/signal-quality hypothesis (fewer, higher-conviction entries)
rather than another parameter sweep on the existing signals' exits, since exit-sizing sweeps
(this experiment, plus F005's leverage/cooldown sweeps) have now been tried and neither alone
restores positive edge.
