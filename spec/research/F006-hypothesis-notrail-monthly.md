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

`scripts/f006_notrail_monthly_experiment.py`, `git_commit_parent = 7098388` (the
pre-registration commit above), single pass, `.venv_test` (Python 3.9.25, pandas 2.3.3),
30 series, 8.5s. Per-series results and monthly tables: `output/f006_notrail_monthly/raw/*.json`
(30 files). Summary table: `output/f006_notrail_monthly/summary/results.csv`. Manifest,
checksums, harness-control record: `output/f006_notrail_monthly/summary/manifest.json`.

The harness-control invariant needed one correction discovered while running it (not a change
to the pre-registered evaluation methodology): the very last UTC bar(s) of the Train-1 slice
(just before `2025-03-01T00:00:00Z`) land on Warsaw-local calendar day 2025-03-01, a day inside
neither `TRAIN1_MONTHS_SET` nor the warm-up months, because Europe/Warsaw is ahead of UTC. This
boundary day is correctly excluded from the Train-1 evaluation (it is not one of Train 1's 12
calendar months) but was initially missing from the harness's reconciliation sum, producing
spurious "mismatches" against `output/f006_trailing_boundary/summary/results.csv`'s stored
totals of up to $0.70/series on 11/30 series in the first run. Verified by hand on
`SOLUSDT/60/DONCHIAN_55` before fixing the script generally: `train1 (-49.643) + warmup (13.831)
+ boundary (0.702) = 52.671 == 52.671` (`net_pnl` stored for that cell). After adding the
boundary term to the reconciliation, harness control is **0/30 mismatches** (both `n_trades`
and reconstructed net PnL, tolerance $0.001 for CSV round-trip rounding).

## Result

**H1 is falsified. Zero of the 30 series clear the monthly promotion checklist.**

No series fails on drawdown or data completeness: `full_run_max_drawdown_pct` ranges 5.4%-27.7%
across all 30 series (max well under the 50% hard cutoff), and every series has all 12 Train-1
calendar months `is_valid=True` (no missing-data day anywhere in any series' Train-1 window --
the data cache has no gaps in this range). The checklist is decided entirely by criterion 2
(net PnL >= 0 in every evaluated month): **every single one of the 30 series has at least 2
negative months out of 12**, so `all_valid_months_nonnegative=False` for all 30 and
`promotion_pass=False` for all 30.

| n_neg_months (out of 12) | n_series |
| ---: | ---: |
| 2 | 1 |
| 3 | 1 |
| 4 | 2 |
| 5 | 3 |
| 6 | 5 |
| 7 | 10 |
| 8 | 6 |
| 9 | 2 |

18/30 series have positive full-Train-1-period net PnL (criterion 3 alone would pass 18/30),
confirming the prior note's pooled-positive names do contain individually-positive series, not
just a favourable pool average. But positive full-period PnL and a clean monthly record are
unrelated in this sample: the single best full-period series,
`DONCHIAN_PULLBACK_55`/DOGEUSDT/4h at **+$235.66** (8/10 series from the prior note's pooled
table), still has **8 losing months out of 12**, including a -$77.89 December 2024. The series
with the *fewest* negative months, `DONCHIAN_55`/DOGEUSDT/1h at **+$197.91** full-period with
only **2** losing months (-$18.94 in July 2024 being the worse of the two), is the closest any
series came to clearing the checklist and still fails it outright -- the criterion is exactly
"zero", not "few", per the protocol's own wording ("regardless of regularity").

The losing months are **spread across the year, not concentrated in one bad stretch**: no
series has fewer than 2 losing months, the mode is 7/12 (10 of 30 series), and even the two
series with only 2-3 negative months still fail because the criterion has zero tolerance. This
is a spread-thin pattern, not a concentrated-crash pattern -- consistent with the mechanism
every prior F006 note in this family has described (a low win rate carried by a few large
winners): a strategy whose edge comes from occasional large wins will, by construction, log a
negative month whenever a calendar month happens not to contain one of those wins, and at these
win rates (14-30% per the trailing-boundary note's pooled figures) a run of several losing
months within any 12-month window is close to guaranteed, not an anomaly.

## Decision

**No promotion. None of the 30 `(name, symbol, interval)` series at `NO_TRAIL` clears
`spec/research/F005-validation-protocol.md` section 7's monthly criterion on Train 1.** The
reason is the one the trailing-boundary note's Decision section anticipated ("concentrated in a
few good months vs. spread thin") and it resolves cleanly to **spread thin**: every series has
multiple losing months regardless of its full-period sign, and the win-rate/reward-ratio
profile this whole exit-geometry line of research has repeatedly found (few large winners,
many small losers) is structurally incompatible with a 12-month window containing zero losing
months, independent of which of the three names or which `(symbol, interval)` is chosen.

**This closes out the `NO_TRAIL` line for these three names without a Validation candidate.**
Finding a monthly-clean series by searching further inside `{DONCHIAN_55, BB_20_25_breakout,
DONCHIAN_PULLBACK_55} x NO_TRAIL` is very unlikely to produce a different answer: the best
candidate by monthly-cleanliness (`DONCHIAN_55`/DOGEUSDT/1h, 2/12 losing months) was one bad
month away from the criterion having any chance at all, and the best candidate by full-period
PnL (`DONCHIAN_PULLBACK_55`/DOGEUSDT/4h) had 8/12. Any future F006 work aimed at clearing this
criterion needs a change to the entry/exit mechanism that raises the *win rate* or otherwise
smooths the monthly PnL distribution, not a further search within the exit-geometry axis this
and the two prior notes have already exhausted (trailing sweep, trailing boundary, and now
monthly resolution all point the same direction: the signal has a real but lumpy edge that the
frozen protocol's zero-tolerance monthly rule does not currently admit).

## Tests

No change to `backtest_engine.py`/`entry_masks.py`/`regularity.py`/`data_contract.py`/
`strategy.py` in this slice -- the new computation lives entirely in
`scripts/f006_notrail_monthly_experiment.py`, so the load-bearing check is the harness control
above (0/30 mismatches after the boundary-day fix), not a new unit test. `tests/test_regularity.py`
(the module this slice reuses unmodified) re-run to confirm no regression: 8/8 passed, unchanged
from `spec/research/F005-baseline.md`.

Full suite, both interpreters, this slice's script/note included:

| | Result |
| --- | --- |
| Python 3.9.25 `.venv_test` | 136 passed, 9 skipped |
| Python 3.11.16 `.venv_lorentzian` | 139 passed, 6 skipped |

Identical counts to `spec/research/F006-hypothesis-trailing-boundary.md`'s post-slice baseline
on both interpreters -- no test added or broken, consistent with zero changes to any tested
module.
