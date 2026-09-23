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

*(filled in after running)*

## Result

*(filled in after running)*

## Decision

*(filled in after running)*

## Tests

*(filled in after running)*
