# F006 — Hypothesis: does the exit-geometry lever have a ceiling, and is that ceiling "no trailing stop at all"? Train 1 only

> Sections "Observation" through "Method" (including the falsification condition and the
> sample) were written and committed to this file BEFORE
> `scripts/f006_trailing_boundary_experiment.py` was written and before any backtest was run,
> per the same discipline as every prior F006 hypothesis note. "Run_id", "Result", "Decision"
> and "Tests" were filled in after the run.
>
> TRAIN-1 ONLY, same window as every F006 slice: `[2024-03-01T00:00:00Z, 2025-03-01T00:00:00Z)`
> plus the protocol's 35-day warm-up buffer from `2024-01-26T00:00:00Z`. Validation 1-4 and the
> Holdout window are not loaded, not sliced and not looked at by any script in this slice.

## Observation

`spec/research/F006-hypothesis-trailing-sweep.md` swept `activate_pct ∈ {0.01, 0.03, 0.06}` ×
`trail_pct ∈ {0.01, 0.02, 0.04}` and found that `avg_winner` — and with it pooled
`breakeven_win_rate_pct` — collapses onto a single variable, `max(activate_pct, trail_pct)`,
across all nine cells. The best cell was the grid's corner, `a=0.06, t=0.04`
(`max = 0.06`), at pooled breakeven 42.90% versus the 58.44% baseline. The `max(a, t)` table in
that note (reproduced below) was still falling at its right edge and had not turned:

| `max(a, t)` | 0.01 | 0.02 | 0.03 | 0.04 | 0.06 |
| --- | ---: | ---: | ---: | ---: | ---: |
| pooled breakeven win% | 77.65 | 55.59 | 58.72 | 44.18 | 44.03 |

The drop from 0.04 to 0.06 (44.18 → 44.03, -0.15 pp) is far smaller than the drop from 0.02 to
0.03 (55.59 → 58.72 — note this one *rises*, because at `max=0.03` both cells that produce it have
the other parameter tiny) or 0.03 to 0.04 (58.72 → 44.18, -14.54 pp). That note's decision section
named two unresolved questions directly: whether the curve keeps falling, flattens, or turns past
0.06, and whether a **no-trailing-stop control** (the `t → ∞` limit of the same collapse) beats
every finite cell — which would mean the trailing machinery is a net cost at any setting the grid
tested, not a lever with an interior optimum.

## Hypothesis

**H1 (diminishing returns, not a turn).** Extending `max(a, t)` from 0.06 up to 0.20 continues to
lower pooled `breakeven_win_rate_pct`, but the marginal improvement per 0.01 of `max(a, t)`
shrinks monotonically — the curve is concave, approaching an asymptote, not turning upward. This is
the direct continuation of the Result section's own reading of the prior grid ("flattening but has
not turned").

**H2 (no-trail is the ceiling, not a fourth option).** A `NO_TRAIL` control — `activate_pct` set so
high the trail can never arm (only `initial_sl` and `signal_reverse` can end a trade) — has a
**lower or equal** pooled `breakeven_win_rate_pct` than the best finite cell in this grid. That is,
the trailing-stop machinery, at its best-tested setting, still gives back more than it locks in
relative to letting the initial stop and the signal alone govern exits. If H2 holds, the trailing
sweep's entire contribution to the project is diagnostic (it shows the exit machinery is a cost
centre), not prescriptive (there is no `(a, t)` to adopt).

The two are logically independent: H1 could hold while H2 fails (an interior optimum exists
somewhere past 0.20), or H1 could fail while H2 holds (the curve already turned by 0.10, but
`NO_TRAIL` is still better than any of it). Both are measured and reported regardless of outcome.

## Falsification condition (stated before running)

Aggregated over the same 8-name × 5-symbol × 2-interval sample as
`spec/research/F006-hypothesis-trailing-sweep.md` (80 series per cell, one-shot mask on,
`cooldown_candles=0`, `max_sl_pct=0.03` fixed), pooled over every trade in the cell.

**H1 is falsified if** the pooled breakeven win rate at the widest finite cell
(`a=0.20, t=0.08`) is **not** at least 0.5 pp better than at `a=0.06, t=0.04` (i.e. the curve has
already fully flattened or turned by 0.06, so this slice's range added nothing), **or** if the
per-0.01-of-`max(a,t)` marginal improvement from 0.06→0.10 is smaller than from 0.10→0.20 (i.e.
the curve is not concave — it is convex or non-monotonic, contradicting "diminishing returns").

**H2 is falsified if** the best finite cell's pooled breakeven win rate is **more than 1.0 pp
better** than `NO_TRAIL`'s (i.e. some finite trailing setting genuinely beats having no trail at
all, by a margin bigger than the grid's own cell-to-cell noise — see the 0.06/0.04 vs 0.06/0.02
comparison in the prior note, which differed by only 0.17 pp and was called "indistinguishable").

Both are evaluated and reported independently; one can be falsified while the other survives.

**Quality gates, applied to any cell before it counts toward either verdict** (same discipline as
the prior note's clause (b), collapsed to one check since trade-count invariance was already
established structurally in that note and is re-verified here, not re-litigated):
pooled `n_trades` in a cell must be within 10% of the `a=0.06, t=0.04` baseline's, and net PnL
**per trade** must not be worse than at that baseline. A cell that "improves" breakeven only by
trading through the $100 margin floor early (the mechanism the prior note found in 15 of 80
series) does not count as a genuine improvement.

## Sample (identical to the prior slice, not re-derived)

Same 8 names, 5 symbols, 2 intervals as `spec/research/F006-hypothesis-trailing-sweep.md`'s
"Sample" section: `EMA_8_21`, `MACD_12_26_hist`, `RSI14_7030`, `BB_20_25_breakout`,
`ADX14_DI_20`, `LORENTZIAN_default`, `DONCHIAN_55`, `DONCHIAN_PULLBACK_55` ×
`SOLUSDT`/`ETHUSDT`/`BTCUSDT`/`XRPUSDT`/`DOGEUSDT` × `240`/`60` = 80 series. Reused unchanged so
this grid's cells are directly comparable to the prior note's without re-derivation.

## Method

Same engine, same fixed block, same data slice and checksum discipline as
`scripts/f006_trailing_sweep_experiment.py`. **No engine change.** `NO_TRAIL` is produced by
setting `activate_pct` to a value the price cannot reach in Train 1 (`activate_pct=10.0`, i.e.
+1000%) — `backtest_engine._update_trailing`'s arming condition
`best_price >= entry_price * (1 + activate_pct)` then never fires, so `trail_active` stays `False`
for the life of every trade and the only exits are `initial_sl`, `signal_reverse` and
`end_of_data`. `trail_pct` is irrelevant in that cell and is recorded as `None`. This needs no
change to `backtest_engine.py`: it uses the existing parameter at a value outside its normal
range, and a new regression test pins that no `trailing_sl` exit occurs anywhere in that cell.

- **Script**: `scripts/f006_trailing_boundary_experiment.py`. Same two-pass split as the prior
  script (`--catalog` on `.venv_test` Python 3.9, `--lorentzian` on `.venv_lorentzian` Python
  3.11, `--merge`), reusing `entry_masks`, `trade_stats`, `data_contract` unmodified.
- **Grid**: `activate_pct ∈ {0.06, 0.10, 0.15, 0.20}` × `trail_pct ∈ {0.04, 0.08}` = 8 cells,
  plus `NO_TRAIL` (`activate_pct=10.0`) = 9 cells × 80 series = 720 runs, matching the prior
  slice's scale. `a=0.06, t=0.04` is included as the harness-control / baseline cell: its rows
  are diffed against the stored `output/f006_trailing_sweep/summary/results.csv` rows for that
  exact cell, the same pattern the prior note used against the notes before it.
- **Fixed**: identical to the prior slice — one-shot `entry_regime_mask` on, `cooldown_candles=0`,
  `leverage=1`, `max_sl_pct=0.03`, `atr_multiplier=1.5`, `initial_equity=500`, `stake=100`,
  `commission_rate_bps=10`, `half_spread_bps=5`, `slippage_bps=2`, `now` pinned to
  `2025-03-01T00:00:00Z`.
- **Data**: identical checksum-verified load and Train-1 slice as every F006 script, duplicated
  `EXPECTED_CHECKSUMS` table, no network fetch.
- **Recorded per run**: identical schema to the prior slice's `results.csv`, plus a
  `no_trail` boolean column.

**Discriminating checks:**

1. **Harness control** — the `a=0.06, t=0.04` cell's 80 rows diffed row by row against
   `output/f006_trailing_sweep/summary/results.csv`'s stored rows for that cell, on `net_pnl`,
   `win_rate`, `n_trades`, `max_drawdown_pct`, `final_equity`.
2. **`NO_TRAIL` mechanism check** (`tests/test_trailing_geometry.py`, extended): with
   `activate_pct=10.0`, `trailing_sl` exit reason never appears in any trade, on both a
   synthetic long-only fixture and a real Train-1 run.
3. **Trade-count / margin-floor re-check**: same `verify_trade_count_invariance` function reused
   from the prior script, applied to this grid, so any cell's "improvement" can be traced back to
   the margin-floor mechanism if present.

## Run_id

`scripts/f006_trailing_boundary_experiment.py`, `git_commit_parent = 18d56de` (the
pre-registration commit above), `n_runs = 720`. Catalog+Donchian pass: Python 3.9.25,
`.venv_test`, 630 runs, 107.3s. Lorentzian pass: Python 3.11.16 + advanced-ta 0.1.8,
`.venv_lorentzian` (rebuilt in this worktree from the cached tarball at `/tmp/cpy311.tar.gz`,
sha256 verified against the recorded value before use, per
`spec/research/F006-hypothesis-one-shot-entry.md`'s recipe), 90 runs, 42.3s. pandas 2.3.3 in
both. Full parameters, checksums, cross-checks and aggregate tables:
`output/f006_trailing_boundary/summary/manifest.json`. Per-run results, 720 rows:
`output/f006_trailing_boundary/summary/results.csv`.

## Result

**H1 (diminishing returns) is falsified. H2 (no-trail is the ceiling) is NOT falsified — and
by a clean, sizeable margin.**

The 9-cell grid, pooled over all 18,302-18,916 trades per cell (80 series each: 8 names ×
5 symbols × 2 intervals, one-shot mask, `cd=0`, `max_sl_pct=0.03`):

| cell | max(a,t) | avg winner | avg loser | R:R | breakeven win% | actual win% | net/trade | gross/trade | trades | profitable runs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.06/0.04 (prior best) | 0.06 | $2.710 | -$2.036 | 1.331 | 42.90 | 29.95 | -$0.614 | -$0.294 | 18,302 | 4/80 |
| 0.06/0.08 | 0.08 | $3.551 | -$2.011 | 1.766 | 36.16 | 28.51 | -$0.426 | -$0.155 | 18,866 | 13/80 |
| 0.10/0.04 | 0.10 | $3.353 | -$2.061 | 1.627 | 38.07 | 28.49 | -$0.519 | -$0.223 | 18,682 | 5/80 |
| 0.10/0.08 | 0.10 | $3.727 | -$2.055 | 1.814 | 35.54 | 28.54 | -$0.404 | -$0.114 | 18,904 | 15/80 |
| 0.15/0.04 | 0.15 | $3.780 | -$2.064 | 1.832 | 35.31 | 28.22 | -$0.414 | -$0.112 | 18,916 | 15/80 |
| 0.15/0.08 | 0.15 | $3.988 | -$2.061 | 1.935 | 34.08 | 28.25 | -$0.352 | -$0.055 | 18,890 | 18/80 |
| 0.20/0.04 | 0.20 | $4.039 | -$2.064 | 1.957 | 33.82 | 28.24 | -$0.341 | -$0.043 | 18,874 | 17/80 |
| **0.20/0.08 (widest)** | 0.20 | $4.128 | -$2.062 | 2.001 | **33.32** | 28.26 | -$0.313 | **+$0.007** | 18,856 | 21/80 |
| **NO_TRAIL** | n/a | **$4.773** | -$2.060 | **2.318** | **30.14** | 28.23 | **-$0.131** | **+$0.190** | 18,771 | **35/80** |

**Harness control and mechanism checks both clean.** The `a=0.06, t=0.04` cell's 80 rows match
`spec/research/F006-hypothesis-trailing-sweep.md`'s stored rows exactly (0/80 mismatches on
`net_pnl`, `win_rate`, `n_trades`, `max_drawdown_pct`, `final_equity`). `NO_TRAIL` produced zero
`trailing_sl` exits across all 80 runs, confirmed by the same check both in-script and in
`tests/test_no_trail_control.py`. The trade-count spread (43/80 series identical, max relative
spread 47.7%) reproduces the prior note's margin-floor mechanism, not a new confound; every cell
in this grid passes the pre-registered quality gate (trade drop ≤10% of baseline, net/trade no
worse than baseline) with room to spare.

**H1 — falsified.** The bar was: widest cell improves breakeven by ≥0.5 pp over the 0.06/0.04
baseline (met: 9.58 pp), **and** the marginal gain per step is concave (0.06→0.10 gain ≥
0.10→0.20 gain). It is not: pooled breakeven by activate level (each pooling its two trail
values) is 39.48 (a=0.06) → 36.80 (a=0.10) → 33.57 (a=0.20), and the 0.10→0.20 step
(-3.23 pp) is **larger** than the 0.06→0.10 step (-2.68 pp). The curve is not flattening in
this range — if anything it is still accelerating. The prior note's own read ("flattening but
has not turned") undersold how much room was left: this slice's widest cell is 9.6 pp better
than the previous grid's best, nearly two-thirds of the *entire* first sweep's total gain
(15.54 pp from 58.44% down to 42.90%) captured again just by continuing in the same direction.

**H2 — not falsified, and the ceiling is definitive within this range.** Every one of the 8
finite cells has a *worse* (higher) breakeven win rate than `NO_TRAIL`. The best finite cell,
0.20/0.08, still trails `NO_TRAIL` by 3.18 pp (33.32% vs 30.14%) — nowhere close to the 1.0 pp
margin that would have falsified H2. Every quantity moves the same direction: `avg_winner`
keeps rising past every finite cell to `NO_TRAIL`'s $4.77, `mean_max_drawdown_pct` falls from
30.6% (baseline) to 22.8-23.3% at both the widest finite cell and `NO_TRAIL`, and
`positive_net_pnl` runs rise from 4/80 to 21/80 (widest finite) to **35/80** at `NO_TRAIL` — 44%
of the sample. **The trailing-stop machinery, at every setting this project has ever tested, is
a net cost relative to letting the initial stop and the signal alone govern exits.**

**A finding beyond either pre-registered hypothesis, reported because it changes what the next
step should be.** `NO_TRAIL`'s pooled **gross** (pre-cost) per-trade expectancy is **positive**
— $0.190, the first positive gross figure in any F006 measurement across 3,660 total runs to
date (2,940 prior + 720 here). Net is still negative ($0.131 of the $0.320 constant cost per
trade is not covered), but the entry+initial-stop+signal-reversal combination, unconstrained by
any trailing exit, has a real edge before costs. Three of the eight names have **positive mean
net PnL** over Train 1 at `NO_TRAIL`, pooling across their 10 (symbol, interval) series each:

| Name | mean net PnL | profitable series |
| --- | ---: | ---: |
| `DONCHIAN_55` | **+$67.69** | 8/10 |
| `BB_20_25_breakout` | **+$57.55** | 7/10 |
| `DONCHIAN_PULLBACK_55` | **+$49.54** | 5/10 |
| `LORENTZIAN_default` | -$4.18 | 4/10 |
| `EMA_8_21` | -$9.91 | 6/10 |
| `RSI14_7030` | -$129.81 | 0/10 |
| `ADX14_DI_20` | -$129.61 | 3/10 |
| `MACD_12_26_hist` | -$146.61 | 2/10 |

The largest single series is `DONCHIAN_PULLBACK_55`/DOGEUSDT/4h at **+$279.63** net (14 trades,
14.29% win rate, 21.58% max DD) — a large average winner carrying a low win rate, consistent
with the mechanism this whole family of notes has been describing. This is a full-Train-1
aggregate figure, not a monthly one: the protocol's hard rejection criterion ("negative net PnL
in any evaluated month or over the full period → no promotion, regardless of regularity") has
not been checked at monthly granularity for any of these candidates, since this script only
records the aggregate per-run metrics `f006_trailing_sweep_experiment.py`'s schema already
carried. Reported as a lead, not a result: three names clearing full-period positive net PnL for
the first time is the strongest signal F006 has produced, and it is untested at the resolution
the protocol actually requires.

## Decision

**Do not promote anything from this slice.** No monthly PnL series exists yet for any candidate
here, and the protocol's rejection criterion is monthly, not aggregate — a positive full-Train-1
sum can still contain a losing month, which alone blocks promotion regardless of the aggregate.
Spending Validation budget on an unverified monthly profile would repeat the mistake the
trailing-sweep note's Decision section warned against.

**Both hypotheses resolve cleanly and change the shape of the next step.** H2 surviving means
the project should stop sweeping `(activate_pct, trail_pct)` combinations that keep a trail
active — within the entire range tested across two slices (18 finite cells now), no trail ever
beat no trail. H1 being falsified in the "still accelerating" direction, not the "already
turned" direction, is moot for the same reason: there is no more reason to push `max(a, t)`
further out, because `NO_TRAIL` already dominates the whole direction that grid explores.

**Next step: build the Train-1 monthly PnL series for `NO_TRAIL`, focused on `DONCHIAN_55`,
`BB_20_25_breakout` and `DONCHIAN_PULLBACK_55`** — the three names with positive aggregate net
PnL — reusing the equity/daily/monthly machinery `spec/research/F005-baseline.md` established,
rather than opening a new hypothesis. This is the first time F006 has had a specific,
aggregate-positive candidate worth checking at that resolution; every prior slice's numbers were
negative before a monthly breakdown was ever justified. If any (name, symbol, interval) triple
clears the monthly criterion on Train 1, it becomes the first F006 candidate for Validation.
If none do, the reason will itself be informative (concentrated in a few good months vs. spread
thin) and should be recorded rather than silently dropped.

**Also worth carrying forward, lower priority than the monthly check:** re-testing
`spec/research/F006-hypothesis-stop-width.md`'s `max_sl_pct` sweep at `NO_TRAIL` rather than at
the old 0.03/0.02 corner, since that note's "nothing at any width" conclusion was measured
inside what these two slices together have now shown is the worst corner of the exit-parameter
space on two separate axes (trailing geometry and, potentially, stop width).

## Tests

`tests/test_no_trail_control.py` (2 new tests, one on the committed fixture, one on real
Train-1 BTCUSDT/1h data) pins that `activate_pct=10.0` — an existing parameter used outside its
normal range, not new logic — produces zero `trailing_sl` exits. No new computation module was
added in this slice (unlike the trailing-sweep note's `trade_stats.py`), so no mutation testing
applies; the load-bearing check is the harness-control diff against the prior note's stored
rows (0/80 mismatches) plus the in-script `no_trail` mechanism check (0/80 trailing exits),
both of which ran as part of `--merge` above.

Full suite, before and after this slice, on both interpreters:

| | Baseline (this slice's test file excluded) | With this slice |
| --- | --- | --- |
| Python 3.9 `.venv_test` | 134 passed, 9 skipped | **136 passed, 9 skipped** |
| Python 3.11 `.venv_lorentzian` | 137 passed, 6 skipped | **139 passed, 6 skipped** |

Exactly the 2 new tests on both, no behaviour change in any existing test.
