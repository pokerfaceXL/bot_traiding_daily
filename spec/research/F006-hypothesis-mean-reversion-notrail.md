# F006 — Mean-reversion signal family at NO_TRAIL: a mechanically different candidate

> Sections "Observation" through "Method" (including the falsification conditions, the
> catalog, the sample and the correlation-analysis design) were written and committed to this
> file BEFORE `scripts/f006_mean_reversion_notrail_experiment.py` was written and before any
> backtest was run, per the same discipline as every prior F006 hypothesis note. "Run_id",
> "Result", "Decision" and "Tests" were filled in after the run.
>
> TRAIN-1 ONLY, same window as every F006 slice: `[2024-03-01T00:00:00Z, 2025-03-01T00:00:00Z)`
> plus the protocol's 35-day warm-up buffer from `2024-01-26T00:00:00Z`. Validation 1-4 and the
> Holdout window are not loaded, not sliced and not looked at.

## Observation

`spec/research/F006-portfolio-diversification-exploration.md` diagnosed why 0/80 already-tested
`NO_TRAIL` `(name, symbol, interval)` series (across
`spec/research/F006-hypothesis-notrail-monthly.md`'s 3 names and
`spec/research/F006-hypothesis-notrail-monthly-catalog5.md`'s 5 names, 8 names total) clear the
monthly criterion, and why combining them into a diversified portfolio does not fix it either:
**every name tested so far is mechanistically momentum/breakout**
(`DONCHIAN_55`/`DONCHIAN_PULLBACK_55` breakout, `BB_20_25_breakout`/`BB_20_2_EMA200`/
`BB_20_25_EMA200` breakout-with-trend-filter, `EMA3_21_50_200`/`EMA3_13_50_200`/`EMA_50_200`
trend-cross). On a broad adverse/choppy Train-1 month, most of them lose together — the
portfolio note's own per-month diagnostic showed a majority of 5 diversified constituents
negative in exactly the two months that decided the pass/fail outcome. The owner's explicit
direction is to test a **mechanically different** signal family — not momentum/breakout, not a
variant of the 8 names already measured — specifically a genuine counter-trend / mean-reversion
mechanism (enters AGAINST an extreme, not on a breakout through one).

## Catalog: every genuinely counter-trend signal generator in `strategy.STRATEGY_CATALOG`

`strategy.py` has 85 catalog names built from a fixed set of signal-generator functions
(`sig_*`). Read in full (`strategy.py` lines 178-368 define every `sig_*` function; lines
369-475 assign catalog names to them). Classifying each function by mechanism — "enters AGAINST
an extreme" (mean-reversion) vs. "enters ON/THROUGH an extreme, or on a directional
cross/filter" (momentum/breakout/trend) — the genuinely counter-trend functions are exactly two:

| Function | Mechanism | Catalog names | Status before this note |
| --- | --- | --- | --- |
| `sig_bb_revert(df, bb_p, bb_k)` | long when `close < lower_band`, short when `close > upper_band` — the literal mirror image of `sig_bb_breakout` | `BB_20_2_revert`, `BB_20_25_revert` | **never tested at `NO_TRAIL`** |
| `sig_rsi_extreme(df, rsi_p, ob, os)` | long when `rsi < os` (oversold), short when `rsi > ob` (overbought) | `RSI14_7030`, `RSI14_6535`, `RSI21_7030`, `RSI7_6535` | `RSI14_7030` already tested at `NO_TRAIL` (see below); the other three untested |

Every other oscillator-adjacent function was checked and explicitly rejected as NOT
counter-trend in mechanism:

- `sig_stoch_cross` (`STOCH14_cross`, `STOCH5_cross`): `%K` vs `%D` crossover, a directional
  momentum cross with no extreme-value gate at all — mechanically identical in shape to
  `sig_ema_cross`, just on a different oscillator. Already tested at `NO_TRAIL` in
  `spec/research/F006-catalog-notrail-sweep.md` and among the **worst two names in the entire
  85-name catalog** (`STOCH14_cross` -$3,924.69 sum, `STOCH5_cross` -$3,897.59 sum over 10
  series) — consistent with momentum-family names losing badly on a mean-reverting oscillator's
  raw crossover, not evidence about the reversion mechanism this note targets.
- `sig_stoch_ema` (`STOCH14_EMA8_21`, `STOCH14_EMA13_34`): only enters on an oscillator extreme
  when it **agrees with the prevailing EMA trend** (`bull & (k < os)`, i.e. buy a dip only
  inside an uptrend) — a trend-following pullback-entry timer, not counter-trend; it requires
  trend alignment, which a genuine reversion signal must not.
- `sig_bb_mid` (`BB_20_2_mid`): price vs. the Bollinger mid-band (a rolling mean) is a
  directional cross, mechanically the same shape as an EMA cross, not an extreme-value
  reversion.
- `sig_rsi_trend` (`RSI14_trend50`, `RSI7_trend50`): RSI vs. the 50 midline is a directional
  filter (RSI > 50 = long), not an extreme-value trigger.

**No separate z-score/distance-from-moving-average reversion signal exists in `strategy.py`
beyond Bollinger Bands** — a Bollinger Band is already a `k`-standard-deviation-from-rolling-mean
band, i.e. `sig_bb_revert` already IS the z-score-distance-reversion mechanism the task
description names as a candidate family; there is no separate signal generator to add for that
case. All 85 catalog names were read (not sampled) via `strategy.py`'s catalog dict
(`STRATEGY_CATALOG`, lines 369-475 plus the Lorentzian and Donchian `.update()` calls) to
confirm no counter-trend mechanism was missed; the two functions/six names in the table above
are the complete set.

## `RSI14_7030`: already retested at `NO_TRAIL`, not a gap to fill

The task names `RSI14_7030` as "the WORST performer of the 8" in
`spec/research/F006-hypothesis-trailing-boundary.md` and asks whether that was measured at a
since-corrected worse exit-geometry corner deserving a `NO_TRAIL` retest. **It was not measured
at a stale corner — `RSI14_7030` already has a `NO_TRAIL` measurement**, because the
trailing-boundary note's 9-cell grid (8 finite `(activate_pct, trail_pct)` cells plus
`NO_TRAIL`) ran all 8 names, including `RSI14_7030`, at every cell. Re-checked directly against
`output/f006_trailing_boundary/summary/results.csv` before writing this note:

| cell | `RSI14_7030` sum net PnL (10 series) | mean net PnL |
| --- | ---: | ---: |
| 0.06/0.04 | -$1,744.46 | -$174.45 |
| 0.06/0.08 | -$1,471.61 | -$147.16 |
| 0.10/0.04 | -$1,531.52 | -$153.15 |
| 0.10/0.08 | -$1,450.37 | -$145.04 |
| 0.15/0.04 | -$1,364.18 | -$136.42 |
| 0.15/0.08 | -$1,331.26 | -$133.13 |
| 0.20/0.04 | -$1,308.58 | -$130.86 |
| 0.20/0.08 | -$1,307.13 | -$130.71 |
| **`NO_TRAIL`** | **-$1,298.09** | **-$129.81** |

`NO_TRAIL` is `RSI14_7030`'s **best** cell of the nine (least negative), consistent with
`spec/research/F006-hypothesis-trailing-boundary.md`'s H2 (no-trail beats every finite trailing
setting, for every name). It is still clearly aggregate-negative — the worst of the original
8-name sample at `NO_TRAIL` per that note's own reported table (mean net PnL -$129.81, 0/10
series individually reported profitable in that note's pooled figures). **This closes the
question: `RSI14_7030` does not deserve a further `NO_TRAIL` retest — it already has one, at
the corrected corner, and the result is unambiguous.** No further compute is spent re-running
it as a hypothesis candidate; it is reused only as this note's harness control (below), because
it is a name this note's script needs to reproduce exactly to prove the harness is correct
before trusting the five genuinely new names.

## Hypothesis

**H1 (aggregate).** At least one of the two untested `sig_bb_revert` names (`BB_20_2_revert`,
`BB_20_25_revert`) or the three untested `sig_rsi_extreme` names (`RSI14_6535`, `RSI21_7030`,
`RSI7_6535`) — 5 names × 5 symbols × 2 intervals = 50 series — has **positive mean net PnL
across its 10 `(symbol, interval)` series** at `NO_TRAIL`, matching the bar
`spec/research/F006-catalog-notrail-sweep.md` used to flag names for a follow-up monthly check
(mean net PnL > 0 over the 10-series pool).

**H2 (monthly, conditional on H1).** For any name that clears H1, at least one of its 10
`(symbol, interval)` series clears `spec/research/F005-validation-protocol.md` section 7's
zero-tolerance monthly promotion checklist on Train 1, using the identical four-criterion
falsification condition `spec/research/F006-hypothesis-notrail-monthly-catalog5.md` established
(drawdown ≤ 50%, net PnL ≥ 0 in every one of the 12 valid Train-1 months, all 12 months valid,
full-Train-1 net PnL ≥ 0, `n_trades > 0`). H2 is evaluated only for names that clear H1 — per
the task's own instruction, the monthly check is not run "at all costs" if the aggregate gate
already fails, but (per the same instruction) H1 alone is explicitly **not** treated as
sufficient for a positive result if it holds; H2 must also be checked before this note calls
anything a lead.

**H3 (mechanism diversity, conditional on H1 and reported regardless of H2).** For any name
that clears H1 and has at least one aggregate-positive series with a computable monthly
profile, that series' Train-1 losing months are **less correlated** with the 80 already-measured
momentum-family series' losing-month pattern (from
`output/f006_notrail_monthly/raw/*.json` and `output/f006_notrail_monthly_catalog5/raw/*.json`)
than the momentum-family series are correlated with each other. This is the specific new
measurement this note adds beyond a plain aggregate/monthly check, per the task's explicit
requirement — the actual point of testing a different mechanism is whether its bad months
happen in different calendar months than the momentum family's bad months, not just whether it
is separately profitable.

There is no H4. A negative result on any of H1/H2/H3 is reported honestly and is not searched
around.

## Falsification condition (stated before running)

**H1 is falsified if none of the 5 names has positive mean net PnL over its 10-series pool** at
`NO_TRAIL` (identical exit geometry, sample and pooling convention as
`spec/research/F006-catalog-notrail-sweep.md`).

**H2 is falsified if, for every name that clears H1, none of its 10 series clears all four
promotion criteria** (drawdown ≤ 50%, all 12 valid months net PnL ≥ 0, all 12 months valid,
full-Train-1 net PnL ≥ 0, `n_trades > 0`) — identical wording to
`spec/research/F006-hypothesis-notrail-monthly-catalog5.md`'s falsification condition. If H1 is
itself falsified, H2 is not evaluated (there is nothing to check monthly) and is reported as
"not applicable — H1 failed", not silently treated as falsified or passed.

**H3 is falsified if, for every H1-clearing name with a computable monthly profile,** the
per-calendar-month "fraction of the 80 momentum-family series that are individually negative
that month" is **statistically indistinguishable or higher** during this candidate's own losing
months than during its winning months (i.e. this candidate loses in the same months the
momentum family loses, providing no diversification benefit) — measured concretely as: for each
of this candidate's 12 Train-1 months, record the momentum-family's negative-fraction (count of
the 80 series with `net_pnl < 0` that month, divided by 80, restricted to months `is_valid=True`
for that series in the source JSON — all 80 have `is_valid=True` for all 12 months per both
source notes' Result sections, so no restriction is actually needed but the check is coded
defensively anyway); H3 holds only if the mean momentum-family negative-fraction across this
candidate's own losing months is **lower** than across its own winning months (the opposite of
the correlated-loss pattern the portfolio-diversification note found for the momentum family
combining with itself). If H1 fails entirely, H3 is likewise "not applicable — H1 failed".

## Sample

50 new series: `BB_20_2_revert`, `BB_20_25_revert`, `RSI14_6535`, `RSI21_7030`, `RSI7_6535` ×
`SOLUSDT`/`ETHUSDT`/`BTCUSDT`/`XRPUSDT`/`DOGEUSDT` × `240`/`60`. Identical set of
`(symbol, interval)` pairs as every prior F006 slice. All five are plain
`strategy.STRATEGY_CATALOG` entries built from `sig_bb_revert`/`sig_rsi_extreme`, no Lorentzian
or Donchian dependency — a single pass on `.venv_test` (Python 3.9) covers all 50 series, no
`--merge` step needed.

Plus 10 control series: `RSI14_7030` × the same 5 symbols × 2 intervals, re-run in this script
purely as a harness control (diffed against `output/f006_trailing_boundary/summary/results.csv`'s
stored `NO_TRAIL` rows for that name) — not a hypothesis candidate, since that question is
already closed above. 60 total runs.

## Method

**Exit geometry: identical to the `NO_TRAIL` cell of every prior F006 slice, unchanged.**
`activate_pct=10.0` (unreachable in Train 1, trail never arms), `trail_pct` moot (recorded as
`None`), `max_sl_pct=0.03`, one-shot `entry_regime_mask` via `entry_masks.strategy_signal_series`
+ `entry_masks.one_shot_entry_mask` (unmodified), `cooldown_candles=0`, `leverage=1`,
`atr_multiplier=1.5`, `initial_equity=500`, `stake=100`, `commission_rate_bps=10`,
`half_spread_bps=5`, `slippage_bps=2`, `now` pinned to `2025-03-01T00:00:00Z`. No change to
`backtest_engine.py`, `strategy.py`, `entry_masks.py`, `regularity.py`, `data_contract.py`.

**Aggregation**: for the H1 aggregate check, `trade_stats.win_loss_decomposition` /
`trade_stats.pool_decompositions`, reused unmodified — identical to
`spec/research/F006-catalog-notrail-sweep.md`'s pooled-per-name convention. For the H2 monthly
check, `regularity.py`, unchanged, reused exactly as
`spec/research/F006-hypothesis-notrail-monthly-catalog5.md`'s script calls it (same
`TRAIN1_MONTHS` table, same `_net_pnl_for_month(s)` helpers, same `promotion_pass` formula with
the explicit `n_trades > 0` guard). The monthly computation is run for **every** series in the
sample regardless of its individual aggregate sign (cheap — 60 backtests total, no separate
pass needed to gate it), but this note's Result/Decision sections only interpret and report the
monthly/H3 figures for names that clear H1 in aggregate, per the falsification conditions above
— computing it for all series ahead of time is an implementation convenience, not a change to
what counts as evidence.

For H3, the script loads the 80 already-computed raw JSON files from
`output/f006_notrail_monthly/raw/*.json` (30 files) and
`output/f006_notrail_monthly_catalog5/raw/*.json` (50 files), and for each of the 12 Train-1
calendar months computes `neg_fraction_momentum[month] = (count of the 80 series with
monthly[i].net_pnl < 0) / 80`. This reuses the exact per-month negative-count mechanism
`spec/research/F006-portfolio-diversification-exploration.md`'s script established, applied to
all 80 series instead of a 5-series subset, and to a completely different candidate series
computed by this note (no new backtest re-run of the 80 momentum series — pure read of their
already-stored `monthly` arrays, no import of `backtest_engine.py`/`strategy.py` for that part).

- **Script**: `scripts/f006_mean_reversion_notrail_experiment.py`, adapted directly from
  `scripts/f006_notrail_monthly_catalog5_experiment.py` (same per-series computation and
  `promotion_pass` formula), extended with (a) the pooled aggregate decomposition from
  `scripts/f006_catalog_notrail_sweep.py`'s pattern for the H1 check, and (b) a new
  `_momentum_neg_fraction_by_month()` step that reads the 80 prior raw JSON files for the H3
  check. Single pass, `.venv_test` only.
- **Data**: identical checksum-verified load (`data_contract.load_dataset`, `EXPECTED_CHECKSUMS`
  table duplicated from `spec/research/F005-validation-protocol.md` section 6) and Train-1 slice
  as every F006 script. No network fetch.
- **Harness control**: the 10 `RSI14_7030` control rows' `net_pnl`, `win_rate`, `n_trades`,
  `max_drawdown_pct`, `final_equity` diffed row by row against
  `output/f006_trailing_boundary/summary/results.csv`'s stored `no_trail=True` rows for
  `RSI14_7030` — 0 mismatches required before trusting any of the 50 new-name numbers, identical
  discipline to `spec/research/F006-catalog-notrail-sweep.md`'s `DONCHIAN_55` control.
- **Recorded per series**: identical schema to
  `scripts/f006_notrail_monthly_catalog5_experiment.py`'s per-series dict (symbol, interval,
  strategy, `n_trades`, Train-1/warmup/boundary/first-day net PnL components, full-run drawdown
  and final equity, 12 monthly rows, `promotion_pass`), plus `net_pnl`/`win_rate` at the
  aggregate (pooled) level per name for the H1 check.

**Discriminating checks:**

1. **Harness control** — `RSI14_7030`'s 10 rows match
   `output/f006_trailing_boundary/summary/results.csv`'s stored `NO_TRAIL` rows exactly (0/10
   mismatches on `net_pnl`, `win_rate`, `n_trades`, `max_drawdown_pct`, `final_equity`) — proves
   this note's harness reproduces the established `NO_TRAIL` cell before trusting the 5 new
   names, which have no prior `NO_TRAIL` measurement to diff against directly.
2. **`NO_TRAIL` mechanism check**: `exit_trailing_sl` count must be 0 in every one of the 60
   runs (identical check to every prior `NO_TRAIL` script).
3. **One-shot rule**: `n_trades` must never exceed the number of first-bar-of-call entries the
   mask permits, in any run.
4. **Mirror-image sanity check**: `BB_20_2_revert`'s and `BB_20_25_revert`'s raw entry signals
   (before the one-shot mask) must be the exact bitwise negation of `BB_20_2_breakout`'s and
   `BB_20_25_breakout`'s signals wherever either is nonzero (both derive from the same band
   crossing, with long/short swapped) — checked directly on one `(symbol, interval)` pair
   before trusting that `sig_bb_revert` was read correctly from `strategy.py`.
5. **80-file momentum read**: exactly 30 + 50 = 80 raw JSON files loaded for the H3 check, each
   with exactly 12 monthly entries and `is_valid=True` for all 12 (matching both source notes'
   Result sections, which state this explicitly) — any file missing or any month
   `is_valid=False` stops the run rather than silently producing a wrong denominator.

## Run_id

`scripts/f006_mean_reversion_notrail_experiment.py`, `.venv_test` (Python 3.9.25, pandas
2.3.3), single pass, 60 backtests. Per-series results: `output/f006_mean_reversion_notrail/raw/*.json`
(60 files). Summary table: `output/f006_mean_reversion_notrail/summary/results.csv`. Manifest,
checksums, harness-control record, H1/H2/H3 verdicts:
`output/f006_mean_reversion_notrail/summary/manifest.json`.

## Result

(filled in after running)

## Decision

(filled in after running)

## Tests

(filled in after running)
