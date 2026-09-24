# F006 — Train-1 monthly PnL breakdown for the five catalog-sweep NO_TRAIL leads

> Sections "Observation" through "Method" (including the falsification condition and the
> sample) were written and committed to this file BEFORE
> `scripts/f006_notrail_monthly_catalog5_experiment.py` was written and before any backtest
> was run, per the same discipline as every prior F006 hypothesis note. "Run_id", "Result",
> "Decision" and "Tests" were filled in after the run.
>
> TRAIN-1 ONLY: `[2024-03-01T00:00:00Z, 2025-03-01T00:00:00Z)`, exactly
> `spec/research/F005-validation-protocol.md` section 3's `train_1` calendar-month window
> (2024-03 … 2025-02, 12 full calendar months), loaded from
> `[2024-01-26T00:00:00Z, 2025-03-01T00:00:00Z)` for the same 35-day warm-up buffer every
> F006 slice uses. Validation 1-4 and Holdout are not loaded, not sliced and not looked at.

## Observation

`spec/research/F006-catalog-notrail-sweep.md`'s Decision section named five new
`NO_TRAIL`-aggregate-positive names — `EMA3_21_50_200`, `EMA3_13_50_200`, `BB_20_2_EMA200`,
`EMA_50_200`, `BB_20_25_EMA200` — that beat the original three leads (`DONCHIAN_55`,
`BB_20_25_breakout`, `DONCHIAN_PULLBACK_55`) on every reported measure (mean net PnL,
profitable-series count, breakeven-win-rate gap). That note explicitly did **not** run the
monthly PnL check that decides promotion eligibility, and its own Result section stated the
caveat directly: "aggregate-positive is not the monthly criterion... a positive full-Train-1
sum can hide a single losing month, which alone blocks promotion under
`spec/research/F005-validation-protocol.md` section 7 regardless of how large the aggregate
is." `spec/research/F006-hypothesis-notrail-monthly.md` already ran this exact check for the
original 3 names and found 0/30 series clear it. This note runs the identical check, same
method, for the 5 new names.

## Hypothesis

**H1.** At least one of the 50 `(name, symbol, interval)` series (5 names × 5 symbols ×
2 intervals) evaluated at `NO_TRAIL` on Train 1 clears every criterion below and becomes a
candidate for Validation.

There is no H2 — this is a measurement/promotion-gate slice, not a parameter sweep, identical
in structure to `spec/research/F006-hypothesis-notrail-monthly.md`.

## Falsification condition (stated before running)

**H1 is falsified if none of the 50 series clears all of the following**, evaluated against
`spec/research/F005-validation-protocol.md` section 7, verbatim (identical wording to
`spec/research/F006-hypothesis-notrail-monthly.md`'s falsification condition, plus the
explicit `n_trades > 0` guard this sub-family's prior notes have repeatedly needed):

1. **Full-run max drawdown ≤ 50%** (mark-to-market, `result.metrics["max_drawdown_pct"]` over
   the continuous run) — hard rejection criterion, checked first, independent of the monthly
   breakdown.
2. **Net PnL ≥ 0 in every evaluated month.** "Evaluated month" = one of the 12 `train_1`
   calendar months (2024-03 … 2025-02) for which `regularity.monthly_regularity` reports
   `is_valid=True` (no day in that month is `missing`) — i.e. a full, data-complete calendar
   month. A month with `is_valid=False` is not evaluated, per the protocol's own rule, not
   silently treated as passing or failing. Net PnL for a month is the sum of `DayResult.pnl`
   over that month's non-missing days (identical definition to
   `scripts/f005_run_baseline.py`'s `_net_pnl_for_months`, applied per single month).
3. **Net PnL ≥ 0 over the full Train-1 period** — sum of `DayResult.pnl` over all 12 `train_1`
   calendar-month days (the warm-up buffer itself, 2024-01-26 … 2024-02-29, is excluded from
   this sum: it exists only for indicator lookback and is never evaluated, exactly as in every
   other F006 script).
4. **`n_trades > 0`.** A series that clears criteria 1-3 by never entering a trade (net PnL
   trivially 0, drawdown trivially 0) does not count as a promotion candidate — this is the
   recurring guard this sub-family requires, stated explicitly here because the prior
   `f006_notrail_monthly_experiment.py`'s `promotion_pass` formula did not include it
   explicitly (relying on net_pnl==0 not being caught as a false positive there only because
   none of the 30 series in that note happened to have zero trades; this note's sample must
   not rely on the same coincidence going unchecked).

Any series failing any one of the four fails the checklist; a series that fails is not a
promotion candidate regardless of how it does on the others. **`deviation_pct > 20%` in a given
month is reported per protocol ("report, don't hide by averaging") but does NOT by itself
disqualify a series** — only criteria 1-4 above are hard rejection criteria under section 7;
the regularity target is a separate, softer measure reported alongside.

## Sample

50 series: `EMA3_21_50_200`, `EMA3_13_50_200`, `BB_20_2_EMA200`, `EMA_50_200`,
`BB_20_25_EMA200` × `SOLUSDT`/`ETHUSDT`/`BTCUSDT`/`XRPUSDT`/`DOGEUSDT` × `240`/`60`. Identical
set of `(symbol, interval)` pairs as every prior F006 slice; the five names are exactly the
ones `spec/research/F006-catalog-notrail-sweep.md`'s Decision section named. All five are
plain `strategy.STRATEGY_CATALOG` entries (verified present before writing this note) — no
Lorentzian dependency in this sample, a single pass on `.venv_test` (Python 3.9) covers all
50 series, no `--merge` step needed.

## Method

**Engine parameters: identical to the `NO_TRAIL` cell used throughout this sub-family,
unchanged.** `activate_pct=10.0` (unreachable, trail never arms), `trail_pct=0.04` (moot,
recorded as `None`), `max_sl_pct=0.03`, `atr_multiplier=1.5`, `cooldown_candles=0`,
`leverage=1.0`, `commission_rate_bps=10.0`, `half_spread_bps=5.0`, `slippage_bps=2.0`,
`initial_equity=500.0`, `stake=100.0`, one-shot `entry_regime_mask` via
`entry_masks.strategy_signal_series` + `entry_masks.one_shot_entry_mask` (unmodified), `now`
pinned to `2025-03-01T00:00:00Z`. No change to `backtest_engine.py`, `strategy.py`,
`entry_masks.py`.

**Aggregation: `regularity.py`, unchanged, reused exactly as
`spec/research/F006-hypothesis-notrail-monthly.md`'s script called it.** For each of the 50
series: `days, months = regularity.compute_regularity(result.equity_curve)`. `months` filtered
to the 12 `(year, month)` pairs in `train_1` (identical `TRAIN1_MONTHS` table, duplicated not
imported, same pattern as every F006 script). Per-month net PnL computed with the same
summation `scripts/f005_run_baseline.py`'s `_net_pnl_for_months` uses, applied to one month's
days at a time. No new aggregation logic is written; no change to `regularity.py`.

- **Script**: `scripts/f006_notrail_monthly_catalog5_experiment.py`, adapted directly from
  `scripts/f006_notrail_monthly_experiment.py` (same structure, same helper functions,
  `NAMES` list swapped to the 5 catalog-sweep names, `promotion_pass` extended with the
  explicit `n_trades > 0` guard per falsification condition 4 above). Single pass, `.venv_test`
  only (`python scripts/f006_notrail_monthly_catalog5_experiment.py`) — no
  `--catalog`/`--lorentzian` split, no `--merge`, since the sample needs no Lorentzian
  dependency.
- **Data**: identical checksum-verified load (`data_contract.load_dataset`,
  `EXPECTED_CHECKSUMS` table duplicated from `spec/research/F005-validation-protocol.md`
  section 6) and Train-1 slice (`[2024-01-26T00:00:00Z, 2025-03-01T00:00:00Z)`) as every F006
  script. No network fetch.
- **Harness control**: for each of the 50 series, this note's Train-1-window net PnL sum plus
  the same day-level sum restricted to the two warm-up months (2024-01, 2024-02) plus the
  Europe/Warsaw boundary-day correction (`spec/research/F006-hypothesis-notrail-monthly.md`'s
  Run_id section: the last UTC bar(s) before `2025-03-01T00:00:00Z` can land on Warsaw-local
  2025-03-01, a day outside both the Train-1 months and the warm-up months) must equal the
  pooled per-`(name, symbol, interval)` `net_pnl` already stored in
  `output/f006_catalog_notrail_sweep/summary/results.csv`'s `no_trail=True`, `mask_mode="one_shot"`
  rows for these 5 names — that prior script's `net_pnl` is the full loaded-slice total
  (warm-up buffer + Train 1, never sliced by calendar month, same as the
  `f006_trailing_boundary_experiment.py` rows the original monthly note reconciled against),
  so the invariant checked is `train1_net_pnl + warmup_net_pnl + boundary_net_pnl == prior
  net_pnl`, applying the boundary correction from the start rather than discovering it mid-run
  (the correction is a known, already-diagnosed fact of this exact data slice, not something
  this note needs to rediscover). Any mismatch in the reconstructed-total invariant, or in
  `n_trades`, stops the run rather than being silently reported as a finding.
- **Recorded per series**: `symbol`, `interval`, `strategy`, full-run `max_drawdown_pct`,
  `final_equity`, `n_trades`, Train-1 total net PnL, 12 monthly rows (`year`, `month`,
  `is_valid`, `is_partial`, `net_pnl` if `is_valid` else `None`, `positive_day_pct`,
  `deviation_pct`, `target_met`), and a per-series `promotion_pass: bool` computed exactly per
  the falsification condition above (drawdown ≤ 50%, all valid months net PnL ≥ 0, all 12
  months valid, full-Train-1 net PnL ≥ 0, `n_trades > 0`).

**Discriminating checks:**

1. **Harness control** — Train-1-window net PnL sum plus warm-up-months net PnL sum plus
   boundary-day net PnL sum (this note's day-level aggregation) must equal
   `output/f006_catalog_notrail_sweep/summary/results.csv`'s stored `no_trail=True`,
   `mask_mode="one_shot"` row's `net_pnl` for the same `(name, symbol, interval)`, for all 50
   series (0 mismatches expected; any mismatch stops the run).
2. **Regularity module regression, unmodified**: `tests/test_regularity.py`'s existing tests
   are re-run, not extended — no new logic is added to `regularity.py` in this slice, so the
   harness control above is the load-bearing check for this slice's actual computation, which
   lives entirely in the new script.
3. **`n_trades > 0` guard is exercised, not vacuous**: the manifest records how many of the 50
   series (if any) have `n_trades == 0`, so the guard's effect (if any) is visible rather than
   assumed absent by construction.
