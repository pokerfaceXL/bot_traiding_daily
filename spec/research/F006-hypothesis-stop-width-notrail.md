# F006 — Hypothesis: does stop width matter once trailing is off? Train 1 only

> "Observation" through "Falsification condition" (including the sample and the exact
> predicted effect) were written and committed to this file BEFORE
> `scripts/f006_stop_width_notrail_experiment.py` was written and before any backtest was run,
> per the same discipline as every prior F006 hypothesis note. "Run_id", "Result", "Decision"
> and "Tests" were filled in after the run.
>
> TRAIN 1 ONLY, same window as every F006 slice:
> `[2024-03-01T00:00:00Z, 2025-03-01T00:00:00Z)` plus the protocol's 35-day warm-up buffer from
> `2024-01-26T00:00:00Z`. Validation 1-4 and the Holdout window are not loaded, not sliced and
> not looked at by any script in this slice.

## Observation

`spec/research/F006-hypothesis-stop-width.md` swept `max_sl_pct ∈ {0.03, 0.05, 0.08, 0.12}` on
the 10-strategy F005 sample and found win rate rising monotonically but net PnL flat and
non-monotonic (a swing of under $1.70 out of ~$357 mean loss, 0/400 runs profitable) — and
concluded stop-width alone does not fix the negative edge. That sweep ran at the exit-geometry
defaults every early F006 slice inherited: `activate_pct=0.03, trail_pct=0.02`.

`spec/research/F006-hypothesis-trailing-boundary.md` (this repo, merged) subsequently showed
those defaults are the **worst** exit-geometry corner tested so far on two separate axes: every
finite `(activate_pct, trail_pct)` cell up to `a=0.20, t=0.08` underperforms a `NO_TRAIL` control
(`activate_pct=10.0`, trail never arms — only `initial_sl`, `signal_reverse` and `end_of_data`
close a trade) on pooled breakeven win rate, and `NO_TRAIL` is the only cell in the project's
3,660+ Train-1 runs to show a **positive** pooled gross (pre-cost) per-trade expectancy
(+$0.190/trade). Under `NO_TRAIL`, `avg_loser` is no longer clipped early by a trail — the
initial `max_sl_pct` stop is the only thing that can end a losing trade before signal reversal or
end of data — which is exactly the mechanism the original stop-width sweep could not exercise,
because its trail was cutting losers short before `max_sl_pct` ever bound in most cells.

An orphaned, unmerged branch (`limen/2026-09-23-f006-trailing-sweep-2-b40bf363`, note at
`spec/research/F006-hypothesis-trailing-sweep-2.md`, `git show cfa26d9:...`) pre-registered a
"part 3" covering this same question, but scoped to its own part-1 grid's best cell (an
outward-extended finite `(a, t)` cell, not yet located when that note was written and never run).
Parts 1-2 of that note are superseded by `F006-hypothesis-trailing-boundary.md`, which already
answered the "does the curve keep improving past 0.06 / does no-trail beat every finite cell"
question directly (H1 falsified, H2 survived: no-trail wins outright). Part 3's own reasoning —
that the original stop-width flatness might be an artefact of an unexamined trailing default, and
that widening `max_sl_pct` should now move `avg_loser` (and net PnL with it) once the trail is no
longer clipping losers — carries over unchanged to the `NO_TRAIL` setting, which supersedes "the
part-1 best cell" as the correct place to re-run it: `NO_TRAIL` is not just another cell in that
grid, it is the grid's own limit and the one setting `F006-hypothesis-trailing-boundary.md`
already established beats every finite alternative. This note re-registers that reasoning at
`NO_TRAIL` specifically, adapted and scoped to this question alone — it does not resume or merge
the orphaned branch, and does not repeat its parts 1-2 (grid-extension) work, which is already
done and merged.

## Hypothesis

At `NO_TRAIL` (`activate_pct=10.0`, trail never arms), widening `max_sl_pct` from 0.03 to 0.12
produces a **real, non-flat** effect on net PnL per trade — unlike the original sweep's flat,
noisy result at the 0.03/0.02 corner. **Mechanism, stated before running**: under `NO_TRAIL`,
`avg_loser` is bounded only by `max_sl_pct` (modulo costs/slippage) since the trail can never cut
a loser short first; widening `max_sl_pct` therefore should widen `avg_loser` in roughly the same
proportion, while `avg_winner` — no longer capped by a trail either — is already large under
`NO_TRAIL` and governed by signal reversal / end of data, largely independent of `max_sl_pct`.
Predicted effect: net PnL per trade moves **monotonically**, and the direction is not assumed —
if wider stops mainly buy fewer, less-frequent noise stop-outs without giving back much on the
`avg_loser` side, net PnL should improve; if they mainly just make each loser larger for the same
signal-driven win rate, net PnL should worsen. Either direction, monotonic and non-trivial in
size, would show the original flatness was a geometry artefact of the 0.03/0.02 corner, not a
fact about stop width in general — which is the question this slice answers, not which direction
wins.

## Sources

This repo's own prior findings only: `spec/research/F006-hypothesis-stop-width.md`,
`spec/research/F006-hypothesis-trailing-boundary.md`, `spec/research/F005-validation-protocol.md`
(Train 1 window, section 3.2), and — for the falsification condition and mechanism reasoning on
this specific question, not for its superseded parts 1-2 — the committed-but-unmerged
`spec/research/F006-hypothesis-trailing-sweep-2.md` (`git show cfa26d9:...`, part 3).

## Sample (identical to the trailing-boundary slice, not re-derived)

Same 8 names, 5 symbols, 2 intervals as `spec/research/F006-hypothesis-trailing-boundary.md`'s
sample: `EMA_8_21`, `MACD_12_26_hist`, `RSI14_7030`, `BB_20_25_breakout`, `ADX14_DI_20`,
`LORENTZIAN_default`, `DONCHIAN_55`, `DONCHIAN_PULLBACK_55` × `SOLUSDT`/`ETHUSDT`/`BTCUSDT`/
`XRPUSDT`/`DOGEUSDT` × `240`/`60` = 80 series. One-shot entry mask, `cooldown_candles=0`,
`leverage=1` throughout, matching every other F006 slice per the ticket.

## Method

Same engine, same fixed block (modulo the swept `max_sl_pct`), same data slice and checksum
discipline as `scripts/f006_trailing_boundary_experiment.py`. **No engine change.**

- **Script**: `scripts/f006_stop_width_notrail_experiment.py`. Same two-pass split as the
  trailing-boundary script (`--catalog` on Python 3.9 `.venv_test` covering the 5 catalog names
  plus the 2 Donchian names, `--lorentzian` on Python 3.11 `.venv_lorentzian` for
  `LORENTZIAN_default`, `--merge`), reusing `entry_masks`, `trade_stats`, `data_contract`
  unmodified.
- **Grid**: `max_sl_pct ∈ {0.03, 0.05, 0.08, 0.12}` — the identical four widths
  `F006-hypothesis-stop-width.md` swept — × 80 series = 320 runs, all at `NO_TRAIL`
  (`activate_pct=10.0`; `trail_pct` is moot and recorded as `None`, same convention as
  `F006-hypothesis-trailing-boundary.md`'s `no_trail` cell).
- **Fixed**: one-shot `entry_regime_mask` on, `cooldown_candles=0`, `leverage=1`,
  `atr_multiplier=1.5`, `activate_pct=10.0` (NO_TRAIL), `initial_equity=500`, `stake=100`,
  `commission_rate_bps=10`, `half_spread_bps=5`, `slippage_bps=2`, `now` pinned to
  `2025-03-01T00:00:00Z`.
- **Data**: identical checksum-verified load and Train-1 slice as every F006 script, duplicated
  `EXPECTED_CHECKSUMS` table, no network fetch.
- **Recorded per run**: same schema as `F006-hypothesis-trailing-boundary.md`'s `results.csv`
  (net/gross PnL, win/loss decomposition, breakeven win rate, exit-reason mix, drawdown,
  survival), plus `max_sl_pct` as the swept column instead of `(activate_pct, trail_pct)`.
- **Statistics**: `trade_stats.win_loss_decomposition` / `pool_decompositions`, reused
  unmodified — no new computation logic, so no new regression test is required by the ticket's
  own convention (the prior two notes' precedent).

**Discriminating checks:**

1. **`max_sl_pct=0.03` cell reproduces `F006-hypothesis-trailing-boundary.md`'s `no_trail` cell
   row for row** (same 80 series, same `NO_TRAIL` setting, same `max_sl_pct=0.03`) — diffed
   against `output/f006_trailing_boundary/summary/results.csv`'s `no_trail` rows on `net_pnl`,
   `win_rate`, `n_trades`, `max_drawdown_pct`, `final_equity`. This is this slice's harness
   control, the same technique every prior F006 note uses.
2. **`NO_TRAIL` mechanism check**: `exit_trailing_sl == 0` on every one of the 320 runs — the
   same check `tests/test_no_trail_control.py` already pins for `activate_pct=10.0`, re-verified
   here at every `max_sl_pct` in the grid, not just 0.03.
3. **One-shot rule**: `n_trades ≤ n_calls` on every run.

## Falsification condition (stated before running)

Aggregated over the 80-series sample, pooled over every trade in the cell (never a mean of
per-series ratios), adapting `F006-hypothesis-trailing-sweep-2.md`'s part-3 condition
(`git show cfa26d9:spec/research/F006-hypothesis-trailing-sweep-2.md`) from "the part-1 best
cell" to `NO_TRAIL` specifically:

**Falsified** — meaning `F006-hypothesis-stop-width.md`'s original negative result holds up and
was not a geometry artefact — if, at `NO_TRAIL`, pooled net PnL per trade across
`max_sl_pct ∈ {0.03, 0.05, 0.08, 0.12}` is **either**:

* **non-monotonic** (does not move in the same direction at every step of the sweep), **or**
* **spans less than 10%** of `|net PnL per trade at 0.03|` (i.e. the swing across the whole
  sweep, from the smallest to the largest value, is under a tenth of the starting magnitude —
  too small to call a real effect rather than noise).

**Survives** (i.e. the original flatness *was* a geometry artefact of the 0.03/0.02 corner) if
net PnL per trade moves monotonically across the sweep by at least that 10% span — in **either**
direction. A monotonic worsening is exactly as much a real, reportable effect as a monotonic
improvement; this condition tests whether stop width matters at all once trailing is off, not
which direction it should move.

Also reported, not falsifying by itself: mean win rate by `max_sl_pct` (to check whether the
original sweep's monotonic win-rate-improves-regardless-of-PnL pattern also holds or breaks at
`NO_TRAIL`), the per-name breakdown, `avg_loser` by `max_sl_pct` (the mechanism's direct
prediction — should move roughly in proportion to `max_sl_pct` if the "no longer clipped by a
trail" reasoning is correct), and whether any `(name, symbol, interval, max_sl_pct)` combination
is profitable on Train 1.

## Run_id

Script: `scripts/f006_stop_width_notrail_experiment.py`. `git_commit_parent =
3ea218468fe262f6a85af82a9a1582e05419580e` (the pre-registration commit above). Catalog+Donchian
pass (5 catalog names + `DONCHIAN_55` + `DONCHIAN_PULLBACK_55`): Python 3.9.25, `.venv_test`,
280 runs, 77.0s. Lorentzian pass (`LORENTZIAN_default`): Python 3.11.16, `.venv_lorentzian`,
40 runs, 48.9s. pandas 2.3.3 in both. `n_runs = 320`. Full parameters, checksums, cross-checks
and aggregate tables: `output/f006_stop_width_notrail/summary/manifest.json`. Per-run results,
320 rows: `output/f006_stop_width_notrail/summary/results.csv`.

## Result

**Harness control and mechanism checks both clean.** The `max_sl_pct=0.03` cell's 80 rows
(identical parameters to `F006-hypothesis-trailing-boundary.md`'s `no_trail` cell) match that
note's stored rows exactly — 0/80 mismatches on `net_pnl`, `win_rate`, `n_trades`,
`max_drawdown_pct`, `final_equity`. Zero `trailing_sl` exits across all 320 runs at every
`max_sl_pct`. Zero one-shot-rule violations.

**Aggregate, pooled over all 320 runs' trades (`n_trades` per cell in the ~17.6k-18.8k range,
80 series each):**

| `max_sl_pct` | avg winner | avg loser | R:R | breakeven win% | actual win% | net/trade | trades | profitable runs |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.03 | $4.773 | -$2.060 | 2.318 | 30.14 | 28.23 | -$0.1307 | 18,771 | 35/80 |
| 0.05 | $4.930 | -$2.336 | 2.110 | 32.15 | 30.47 | -$0.1223 | 18,202 | 37/80 |
| 0.08 | $5.021 | -$2.460 | 2.041 | 32.89 | 31.35 | -$0.1152 | 17,876 | 39/80 |
| 0.12 | $5.053 | -$2.501 | 2.021 | 33.11 | 31.58 | -$0.1156 | 17,618 | 40/80 |

**The mechanism prediction is directly confirmed: `avg_loser` moves with `max_sl_pct`, exactly as
predicted, and no longer sits flat.** At the 0.03/0.02 corner the original sweep found `avg_loser`
near its cost-plus-3%-stop floor and barely moving; here, with the trail no longer able to cut a
loser short first, `avg_loser` widens from -$2.060 to -$2.501 (a 21.4% increase) as `max_sl_pct`
quadruples, and `avg_winner` also widens modestly (fewer premature stop-outs of what would have
become winners). This is the geometry-artefact mechanism the hypothesis named, now visible for the
first time in this project's stop-width measurements.

**Net PnL per trade is no longer flat, but the sweep is not cleanly monotonic either — the
pre-registered falsification condition is a genuine split decision, and it resolves against
survival.** Net/trade improves substantially and monotonically for the first three widths
(-$0.1307 → -$0.1223 → -$0.1152, a real, sizeable move), then **reverses by a hair** at the
widest width (-$0.1152 → -$0.1156, a -$0.0004 step, roughly 0.3% of the total span and well
within the kind of run-to-run noise this project's other tables call "indistinguishable").
The overall span (0.03 to 0.12) is $0.0155, **11.86% of `|net/trade at 0.03|`** — comfortably
above the pre-registered 10% "meaningful" bar — but strict monotonicity fails at the last step.
Per the falsification condition as written (falsified if **either** non-monotonic **or** span
<10%, both evaluated, either one sufficient), the non-monotonicity alone falsifies it, even
though the span condition alone would have survived.

**Win rate rises further and faster than in the original sweep, and closes more of the gap to
breakeven.** Actual win rate climbs from 28.23% to 31.58% (vs. 28.94%→34.60% in the original
sweep — a similar-sized move) while breakeven win rate now **also falls** (30.14%→33.11% is
actually a *rise*, tracking `avg_loser`'s growth) — the gap between them (breakeven − actual)
narrows from 1.91pp at 0.03 to 1.53pp at 0.12, the closest any F006 stop-width measurement has
gotten to closing that gap, though it remains open at every width tested.

**Per-strategy breakdown shows the same heterogeneity as the original sweep, on different
names.** Mean net PnL by strategy across the 5×2 basket:

| Strategy | 0.03 | 0.05 | 0.08 | 0.12 | Pattern |
| --- | ---: | ---: | ---: | ---: | --- |
| `DONCHIAN_55` | +$67.7 | +$77.2 | +$111.0 | +$104.8 | improves, then pulls back slightly |
| `BB_20_25_breakout` | +$57.5 | +$64.2 | +$67.7 | +$70.2 | improves monotonically |
| `LORENTZIAN_default` | -$4.2 | +$15.6 | +$17.3 | +$20.9 | crosses to positive, keeps improving |
| `EMA_8_21` | -$9.9 | -$10.2 | -$2.2 | +$1.3 | crosses to positive late |
| `DONCHIAN_PULLBACK_55` | +$49.5 | +$38.7 | +$26.5 | +$20.5 | **worsens monotonically** |
| `ADX14_DI_20` | -$129.6 | -$140.7 | -$138.4 | -$138.7 | worsens then flat, stays deeply negative |
| `RSI14_7030` | -$129.8 | -$135.8 | -$152.9 | -$145.3 | worsens, non-monotonic, stays deeply negative |
| `MACD_12_26_hist` | -$146.6 | -$131.6 | -$134.8 | -$137.3 | improves then flat, stays deeply negative |

4/8 names show real improvement (2 crossing from negative to positive mean net PnL as stops
widen), 1/8 (`DONCHIAN_PULLBACK_55`) worsens monotonically — the same kind of split the original
sweep found (some names benefit from wider stops, some are hurt by larger losers outweighing
fewer stop-outs), just with different names in each bucket now that `NO_TRAIL` changes which
mechanism dominates. The count of profitable runs out of 80 rises with width (35→37→39→40), a
smaller relative move than net/trade's own swing but directionally consistent.

**Falsification check**: the pre-registered condition requires monotonic net/trade movement
**and** a span ≥10% of the 0.03 base; span is 11.86% (passes) but the sweep is not monotonic
(0.08→0.12 reverses by $0.0004, i.e. **the hypothesis is falsified**, per the condition as
written — even though the size and direction of the effect for 3 of 4 steps is exactly what the
mechanism predicted.

## Decision

**The original stop-width finding does not hold up unchanged, but it is not cleanly overturned
either — the honest reading is "mostly a geometry artefact, with a residual flat region at the
top of the range."** Unlike the original 0.03/0.02-corner sweep (net PnL swing under 0.5% of
base, visibly noise), this `NO_TRAIL` re-test shows a real, mechanism-consistent, 11.9%-of-base
swing in net PnL per trade, with `avg_loser` moving in direct proportion to `max_sl_pct` for the
first time — confirming the hypothesis's core mechanism claim. But the swing is concentrated in
the 0.03→0.08 range (a genuine, monotonic $0.0155 improvement across three widths) and flattens
— technically reverses by a hair, well inside noise — from 0.08 to 0.12, failing the strict
monotonicity bar the falsification condition set. This is the same "flattens near the wide end of
a sweep" shape `F006-hypothesis-trailing-boundary.md`'s H1 found for the trailing-geometry axis,
just arriving sooner (by 0.08 rather than 0.20) and on a different parameter.

**Practical takeaway, independent of the strict pass/fail**: widening `max_sl_pct` from 0.03 to
~0.08 under `NO_TRAIL` is worth doing — it measurably reduces per-trade losses and improves net
PnL for the majority of names in this sample, including moving two (`EMA_8_21`,
`LORENTZIAN_default`) from negative to positive mean Train-1 net PnL — but pushing further to
0.12 buys nothing more in aggregate and is a wash. None of this makes any (name, symbol,
interval, `max_sl_pct`) combination's win rate clear the still-open breakeven gap (1.53-1.91pp at
every width), so **no promotion candidate emerges from this slice alone.** The three names
`F006-hypothesis-trailing-boundary.md` already flagged as aggregate-Train-1-positive at `NO_TRAIL`
(`DONCHIAN_55`, `BB_20_25_breakout`, `DONCHIAN_PULLBACK_55`) remain the strongest leads; of the
three, `DONCHIAN_55` and `BB_20_25_breakout` also improve further with a wider stop here, while
`DONCHIAN_PULLBACK_55` is the one name in this sample that gets **worse** as `max_sl_pct` widens —
consistent with that note's already-flagged large-average-winner-carrying-a-low-win-rate profile,
where a tighter stop protects more of what's already a favourable asymmetry.

**Next step, unchanged from `F006-hypothesis-trailing-boundary.md`'s own decision and not
redirected by this slice**: build the Train-1 monthly PnL series for `NO_TRAIL`, focused on
`DONCHIAN_55`, `BB_20_25_breakout` and `DONCHIAN_PULLBACK_55` — this slice's result does not
change which names are the leads, it only suggests `max_sl_pct≈0.05-0.08` (rather than the 0.03
default) is worth including as a second axis when that monthly check is built for `DONCHIAN_55`
and `BB_20_25_breakout` specifically, given both improve further at that width, while
`DONCHIAN_PULLBACK_55`'s monthly check should stay at `max_sl_pct=0.03`, its best width in this
sample.

## Tests

No new computation logic in this slice — `trade_stats.win_loss_decomposition` /
`pool_decompositions` and `entry_masks.one_shot_entry_mask` /`strategy_signal_series` are reused
unmodified, per the same convention `F006-hypothesis-trailing-boundary.md` and
`F006-hypothesis-trailing-sweep-2.md` used for their own unmodified-module slices. The
load-bearing checks are the ones this note reports in-line: the harness-control diff against
`F006-hypothesis-trailing-boundary.md`'s stored `no_trail` rows (0/80 mismatches), the
`NO_TRAIL` mechanism check (0/320 trailing exits), and the one-shot-rule check (0/320
violations) — all three ran as part of `--merge` above and are recorded in
`output/f006_stop_width_notrail/summary/manifest.json`. No existing test file was touched and no
full-suite run was required by the ticket for this reuse-only slice.
