# F006 — Train-1 monthly PnL breakdown for the three NO_TRAIL aggregate-positive names

> Sections "Observation" through "Method" (including the falsification condition and the
> sample) were written and committed to this file BEFORE
> `scripts/f006_notrail_monthly_experiment.py` was written and before any backtest was run,
> per the same discipline as every prior F006 hypothesis note. "Run_id", "Result", "Decision"
> and "Tests" were filled in after the run.
>
> TRAIN-1 ONLY: `[2024-03-01T00:00:00Z, 2025-03-01T00:00:00Z)`, exactly
> `spec/research/F005-validation-protocol.md` section 3's `train_1` calendar-month window
> (2024-03 … 2025-02, 12 full calendar months), loaded from
> `[2024-01-26T00:00:00Z, 2025-03-01T00:00:00Z)` for the same 35-day warm-up buffer every
> F006 slice uses. Validation 1-4 and Holdout are not loaded, not sliced and not looked at.

## Observation

`spec/research/F006-hypothesis-trailing-boundary.md`'s Decision section named this exact next
step: three names — `DONCHIAN_55`, `BB_20_25_breakout`, `DONCHIAN_PULLBACK_55` — have positive
**aggregate** Train-1 net PnL at the `NO_TRAIL` control (`activate_pct=10.0`, trail never arms,
`max_sl_pct=0.03`, one-shot mask, `cooldown_candles=0`, `leverage=1`), pooling across their 10
`(symbol, interval)` series each. That note explicitly flagged this as untested at the
resolution the frozen protocol actually requires: `spec/research/F005-validation-protocol.md`
section 7 rejects on "negative net PnL in ANY evaluated month or over the full period ...
regardless of regularity" — a fact `spec/build.md` states directly ("Regularność zysku nie
usprawiedliwia ujemnego wyniku netto"). A positive full-Train-1 sum can still contain a losing
month; no monthly series has been built for any `NO_TRAIL` candidate before this note.

## Hypothesis

**H1.** At least one of the 30 `(name, symbol, interval)` series (3 names × 5 symbols ×
2 intervals) evaluated at `NO_TRAIL` on Train 1 clears every criterion below and becomes a
candidate for Validation.

There is no H2 — this is a measurement/promotion-gate slice, not a parameter sweep. The only
question pre-registered is whether the monthly criterion, applied series-by-series (not
pooled), leaves any candidate standing.

## Falsification condition (stated before running)

**H1 is falsified if none of the 30 series clears all of the following**, evaluated against
`spec/research/F005-validation-protocol.md` section 7, verbatim:

1. **Full-run max drawdown ≤ 50%** (mark-to-market, `result.metrics["max_drawdown_pct"]` over
   the continuous run) — hard rejection criterion, checked first, independent of the monthly
   breakdown.
2. **Net PnL ≥ 0 in every evaluated month.** "Evaluated month" = one of the 12 `train_1`
   calendar months (2024-03 … 2025-02) for which `regularity.monthly_regularity` reports
   `is_valid=True` (no day in that month is `missing`) — i.e. a full, data-complete calendar
   month. A month with `is_valid=False` (missing equity data that day) is not evaluated, per
   the protocol's own rule ("brakujące dane unieważniają ocenę miesiąca"), not silently treated
   as passing or failing. Net PnL for a month is the sum of `DayResult.pnl` over that month's
   non-missing days (identical definition to `scripts/f005_run_baseline.py`'s
   `_net_pnl_for_months`, applied here per single month instead of pooled across a window).
3. **Net PnL ≥ 0 over the full Train-1 period** — sum of `DayResult.pnl` over all 12 `train_1`
   calendar-month days (the warm-up buffer itself, 2024-01-26 … 2024-02-29, is explicitly
   excluded from this sum: it exists only for indicator lookback, exactly as in every other
   F006 script, and is never evaluated).

Any series failing any one of the three fails the checklist; a series that fails is not a
promotion candidate regardless of how it does on the other two. **Deviation_pct > 20% in a
given month is reported per protocol ("report, don't hide by averaging") but does NOT by
itself disqualify a series** — only the net-PnL and drawdown criteria above are hard rejection
criteria under section 7; the regularity target is a separate, softer measure reported
alongside.

## Sample

30 series: `DONCHIAN_55`, `BB_20_25_breakout`, `DONCHIAN_PULLBACK_55` ×
`SOLUSDT`/`ETHUSDT`/`BTCUSDT`/`XRPUSDT`/`DOGEUSDT` × `240`/`60`. Identical set of
`(symbol, interval)` pairs as every prior F006 slice; the three names are exactly the ones
`spec/research/F006-hypothesis-trailing-boundary.md`'s Decision section named. `DONCHIAN_55`
and `DONCHIAN_PULLBACK_55` need `donchian.py` (pure pandas, `.venv_test` only, same as the
prior slice's catalog pass); `BB_20_25_breakout` is a plain `strategy.STRATEGY_CATALOG` entry.
No Lorentzian dependency in this sample — a single pass on `.venv_test` (Python 3.9) covers
all 30 series, no `--merge` step needed.

## Method

**Engine parameters: identical to the `NO_TRAIL` cell of
`scripts/f006_trailing_boundary_experiment.py`, unchanged.** `activate_pct=10.0` (unreachable,
trail never arms), `trail_pct=0.04` (moot, recorded as `None`), `max_sl_pct=0.03`,
`atr_multiplier=1.5`, `cooldown_candles=0`, `leverage=1.0`, `commission_rate_bps=10.0`,
`half_spread_bps=5.0`, `slippage_bps=2.0`, `initial_equity=500.0`, `stake=100.0`, one-shot
`entry_regime_mask` via `entry_masks.strategy_signal_series` +
`entry_masks.one_shot_entry_mask` (unmodified), `now` pinned to `2025-03-01T00:00:00Z`. No
change to `backtest_engine.py`, `strategy.py`, `entry_masks.py`, `donchian.py`.

**Aggregation: `regularity.py`, unchanged, reused exactly as `spec/research/F005-baseline.md`
built it and `scripts/f005_run_baseline.py` calls it.** For each of the 30 series:
`days, months = regularity.compute_regularity(result.equity_curve)`. `months` filtered to the
12 `(year, month)` pairs in `train_1` (`scripts/f005_run_baseline.py`'s `_month_range(2024, 3,
2025, 2)`, duplicated here not imported, same pattern as every F006 script duplicating the
checksum table). Per-month net PnL computed with the same summation
`scripts/f005_run_baseline.py`'s `_net_pnl_for_months` uses, applied to one month's days at a
time. No new aggregation logic is written; no change to `regularity.py`.

- **Script**: `scripts/f006_notrail_monthly_experiment.py`. Single pass, `.venv_test` only
  (`python scripts/f006_notrail_monthly_experiment.py`) — no `--catalog`/`--lorentzian` split,
  no `--merge`, since the sample needs no Lorentzian dependency.
- **Data**: identical checksum-verified load (`data_contract.load_dataset`, `EXPECTED_CHECKSUMS`
  table duplicated from `spec/research/F005-validation-protocol.md` section 6) and Train-1 slice
  (`[2024-01-26T00:00:00Z, 2025-03-01T00:00:00Z)`) as every F006 script. No network fetch.
- **Harness control**: for each of the 30 series, this note's Train-1-window net PnL sum plus
  the same day-level sum restricted to the two warm-up months (2024-01, 2024-02) must equal the
  pooled per-`(name, symbol, interval)` `net_pnl` already stored in
  `output/f006_trailing_boundary/summary/results.csv`'s `no_trail=True` rows — that prior
  script's `net_pnl` is the full loaded-slice total (warm-up buffer + Train 1, never sliced by
  calendar month), so the correct invariant is `train1_net_pnl + warmup_net_pnl == prior net_pnl`,
  not `train1_net_pnl == prior net_pnl` alone (a warm-up-only signal can and does fire before
  2024-03-01 for these fast-forming Donchian/BB signals, so warm-up does NOT contribute $0).
  Any mismatch in the reconstructed-total invariant, or in `n_trades`, stops the run rather than
  being silently reported as a finding.
- **Recorded per series**: `symbol`, `interval`, `strategy`, full-run `max_drawdown_pct`,
  `final_equity`, `n_trades`, Train-1 total net PnL, 12 monthly rows (`year`, `month`,
  `is_valid`, `is_partial`, `net_pnl` if `is_valid` else `None`, `positive_day_pct`,
  `deviation_pct`, `target_met`), and a per-series `promotion_pass: bool` computed exactly per
  the falsification condition above.

**Discriminating checks:**

1. **Harness control** — Train-1-window net PnL sum plus warm-up-months net PnL sum (this
   note's day-level aggregation) must equal `output/f006_trailing_boundary/summary/results.csv`'s
   stored `no_trail=True` row's `net_pnl` for the same `(name, symbol, interval)`, for all 30
   series (0 mismatches expected; any mismatch is a bug in this note's aggregation or a genuine
   engine non-determinism, either way it stops the run).
2. **Regularity module regression, unmodified**: `tests/test_regularity.py`'s existing 8 tests
   are re-run, not extended — no new logic is added to `regularity.py` in this slice, so no new
   test of that module is warranted; the harness control above is the load-bearing check for
   this slice's actual computation, which lives entirely in the new script.

## Run_id

(filled in after running)

## Result

(filled in after running)

## Decision

(filled in after running)

## Tests

(filled in after running)
