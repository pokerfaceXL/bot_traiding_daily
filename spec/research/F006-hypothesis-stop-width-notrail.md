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
