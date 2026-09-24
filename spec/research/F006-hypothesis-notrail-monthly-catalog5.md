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

## Run_id

`scripts/f006_notrail_monthly_catalog5_experiment.py`, `git_commit_parent = 1e4bd04` (the
pre-registration commit above), single pass, `.venv_test` (Python 3.9.25, pandas 2.3.3),
50 series, 16.3s. Per-series results and monthly tables:
`output/f006_notrail_monthly_catalog5/raw/*.json` (50 files). Summary table:
`output/f006_notrail_monthly_catalog5/summary/results.csv`. Manifest, checksums,
harness-control record: `output/f006_notrail_monthly_catalog5/summary/manifest.json`.

The harness-control invariant needed a correction discovered while running it (not a change to
the pre-registered evaluation methodology, and distinct from the Warsaw-boundary correction
inherited from `spec/research/F006-hypothesis-notrail-monthly.md`, which this note's script
applied from the start and which required no further fix here). `regularity.classify_days`
unconditionally flags the very first calendar day of any equity curve as `"missing"` — there is
no prior day to diff its equity against, so `pnl=None` for that day — and this day's real
equity delta is silently dropped from every `_net_pnl_for_*` sum unless separately captured.
This was invisible for `spec/research/F006-hypothesis-notrail-monthly.md`'s three names because
`DONCHIAN_55`/`DONCHIAN_PULLBACK_55`/`BB_20_25_breakout` all use `pandas.Series.rolling`
(default `min_periods=window`), which cannot produce a valid signal until its full lookback
window is available and therefore never trades on the very first loaded day. The five names in
this sample are EMA-crossover/EMA-filter strategies built on `pandas.Series.ewm` (default
`min_periods=0`), which produces a value from the first bar onward — `EMA3_21_50_200` on
`SOLUSDT/240` does trade on the first loaded day (2024-01-26), moving equity from `500.0` to
`497.049` (a `-$2.951` first-day loss) that the original reconciliation formula silently
dropped, producing exactly `31/50` spurious mismatches of `$2.95`-scale magnitude in the first
run. Verified by hand on that cell: `equity_curve` shows a real trade opening and losing money
within the first loaded day, `regularity.classify_days`'s first `DayResult` has `status="missing"`,
`pnl=None`, and `equity=497.049` — the delta from `initial_equity=500.0` is real money that
belongs in the reconciliation. `scripts/f006_notrail_monthly_catalog5_experiment.py` was
extended with a `first_day_net_pnl` term (`days[0].equity - INITIAL_EQUITY` when `days[0]` is
the unconditional first-day `"missing"` case) added to the reconciliation total; this day falls
inside the warm-up months (2024-01/02) in every case observed, so it is correctly never counted
in either the Train-1 evaluation or the promotion checklist — the fix only affects the harness
reconciliation, not any evaluated quantity. After adding this term, harness control is
**0/50 mismatches** (both `n_trades` and reconstructed net PnL, tolerance $0.001 for CSV
round-trip rounding), diffed against `output/f006_catalog_notrail_sweep/summary/results.csv`'s
stored `no_trail=True`, `mask_mode="one_shot"` rows for these 5 names.

This first-day artifact is a pre-existing property of `regularity.classify_days` (unchanged in
this slice — the fix lives entirely in this note's reconciliation script, not in `regularity.py`
itself) and is worth flagging for any future F006 slice sampling `ewm`-based names: the original
monthly note's boundary-day fix and this note's first-day fix are two independent artifacts of
the same design (a day with no counterpart to diff against is always `"missing"`, at both ends
of the loaded window), and a future slice combining both a `.rolling`-based name and an
`.ewm`-based name in the same run should expect to need both corrections simultaneously.

## Result

**H1 is falsified. Zero of the 50 series clear the monthly promotion checklist.**

No series fails on drawdown or data completeness: `full_run_max_drawdown_pct` ranges
7.5%-25.1% across all 50 series (max well under the 50% hard cutoff), every series has all 12
Train-1 calendar months `is_valid=True`, and every series has `n_trades > 0` (min 13 trades,
`DOGEUSDT/240/EMA_50_200`) — the explicit zero-trade guard this note's falsification condition
added is never actually triggered in this sample (0/50 series have `n_trades == 0`), so it is
exercised-but-vacuous here, not load-bearing for this particular result.

The checklist is decided entirely by criterion 2 (net PnL ≥ 0 in every evaluated month), exactly
as in `spec/research/F006-hypothesis-notrail-monthly.md`'s result for the original 3 names:
**every single one of the 50 series has at least 3 negative months out of 12**, so
`all_valid_months_nonnegative=False` for all 50 and `promotion_pass=False` for all 50.

| n_neg_months (out of 12) | n_series |
| ---: | ---: |
| 3 | 3 |
| 4 | 4 |
| 5 | 13 |
| 6 | 9 |
| 7 | 13 |
| 8 | 3 |
| 9 | 5 |

36/50 series (72%) have positive full-Train-1-period net PnL (criterion 3 alone would pass
36/50) — a materially higher hit rate than the original 3 names' 18/30 (60%), consistent with
`spec/research/F006-catalog-notrail-sweep.md`'s finding that these 5 names beat the originals
on every aggregate measure. But, exactly as in the original monthly note, positive full-period
PnL and a clean monthly record are unrelated in this sample: the single best full-period series,
`EMA3_21_50_200`/XRPUSDT/4h at **+$300.02** (10/10 series from the catalog sweep's pooled
table had this name profitable), still has **5 losing months out of 12**. The series with the
*fewest* negative months, `BB_20_25_EMA200`/SOLUSDT/1h at **+$85.52** full-period with only
**3** losing months, is the closest any series in this sample came to clearing the checklist and
still fails it outright — the criterion is exactly "zero", not "few", per the protocol's own
wording ("regardless of regularity"). Two other series also reach the 3-losing-month floor —
`EMA3_21_50_200`/DOGEUSDT/1h (+$213.44) and `EMA_50_200`/DOGEUSDT/1h (+$198.46) — so the
best-in-sample result is not a single outlier: three independent (name, symbol, interval)
combinations converge on the same "3 losing months" floor, still short of the zero-tolerance
bar by 3 months.

The losing months are **spread across the year, not concentrated in one bad stretch**, same
pattern as the original monthly note: no series has fewer than 3 losing months, the mode is
5/12 and 7/12 (13 series each), and even the three best-in-sample series (3/12 losing months)
still fail because the criterion has zero tolerance. This is consistent with the same mechanism
every prior F006 note in the `NO_TRAIL` family has described (a low win rate carried by a few
large winners, confirmed for these 5 names by `spec/research/F006-catalog-notrail-sweep.md`'s
own reported breakeven-win-rate gaps of -8.6 to -10.9 percentage points, on trade counts as low
as 364-820 pooled over 10 series): a strategy whose edge comes from occasional large wins will,
by construction, log a negative month whenever a calendar month happens not to contain one of
those wins.

## Decision

**No promotion. None of the 50 `(name, symbol, interval)` series at `NO_TRAIL` clears
`spec/research/F005-validation-protocol.md` section 7's monthly criterion on Train 1.** Despite
beating the original 3 leads on every aggregate measure reported in
`spec/research/F006-catalog-notrail-sweep.md` (mean net PnL, profitable-series count,
breakeven-win-rate gap), these 5 names resolve to the same "spread thin" pattern the original
monthly note found: every series has multiple losing months regardless of its full-period sign,
and a wider breakeven-win-rate margin does not by itself translate into monthly cleanliness —
it shrinks the number of losing months somewhat (this sample's best is 3/12 vs. the original
3 names' best of 2/12) but does not come close to eliminating them.

**This closes out the `NO_TRAIL` line for these five catalog-sweep names without a Validation
candidate, and — combined with `spec/research/F006-hypothesis-notrail-monthly.md`'s result for
the original 3 — means 0/80 `NO_TRAIL` `(name, symbol, interval)` series tested across both
notes clear the monthly promotion checklist.** No series across either note has produced this
project's first real Validation candidate. The best result across both notes remains
`DONCHIAN_55`/DOGEUSDT/1h at 2/12 losing months (the original monthly note); this note's best,
`BB_20_25_EMA200`/SOLUSDT/1h at 3/12, does not improve on that. Any future F006 work aimed at
clearing this criterion needs a change to the entry/exit mechanism that raises the win rate or
smooths the monthly PnL distribution more fundamentally than widening the strategy-name search
has — widening the name axis found names with a wider aggregate edge, but did not change the
underlying lumpy-winner shape that the zero-tolerance monthly rule rejects.

## Tests

No change to `backtest_engine.py`/`entry_masks.py`/`regularity.py`/`data_contract.py`/
`strategy.py` in this slice — the new computation lives entirely in
`scripts/f006_notrail_monthly_catalog5_experiment.py`, so the load-bearing check is the harness
control above (0/50 mismatches after the first-day fix), not a new unit test.
`tests/test_regularity.py` (the module this slice reuses unmodified) re-run to confirm no
regression: 8/8 passed.

Full suite, both interpreters, this slice's script/note included:

| | Result |
| --- | --- |
| Python 3.9.25 `.venv_test` | 168 passed, 9 skipped |
| Python 3.11.16 `.venv_lorentzian` | 171 passed, 6 skipped |

Higher pass counts than `spec/research/F006-hypothesis-notrail-monthly.md`'s post-slice
baseline (136/139) reflect the tests added by every F006 slice merged in between (cooldown,
donchian, entry-cross-symbol, catalog sweep, etc.) — not a regression, and not attributable to
this slice, which adds no new test (no computation module changed).

