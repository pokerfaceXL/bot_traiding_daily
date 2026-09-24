# F006 — Catalog-wide NO_TRAIL sweep: is there a name beyond the original 3?

> **This is an exploratory catalog sweep, not a pre-registered falsifiable hypothesis in
> the strict sense every other F006 note in this directory uses.** There is no H1/H2, no
> falsification condition and nothing here is "confirmed" or "falsified" — it is a search
> over the strategy-name axis, at a single fixed exit geometry, to find candidates worth a
> future monthly-criterion check. The scope is stated up front for exactly that reason.
>
> TRAIN-1 ONLY, same window as every F006 slice: `[2024-03-01T00:00:00Z, 2025-03-01T00:00:00Z)`
> plus the protocol's 35-day warm-up buffer from `2024-01-26T00:00:00Z`. Validation 1-4 and the
> Holdout window are not loaded, not sliced and not looked at.

## Scope and purpose

`spec/research/F006-hypothesis-exit-take-profit.md` closed out the entry/exit/sizing axis for
the three original `NO_TRAIL` leads (`DONCHIAN_55`, `BB_20_25_breakout`,
`DONCHIAN_PULLBACK_55`) — six independent mechanisms across that note and its predecessors all
falsified. That note's own Decision section, and the project owner's explicit direction, is to
widen the search to a different axis: `strategy.STRATEGY_CATALOG` has **85 names** total, and
`spec/research/F006-hypothesis-trailing-boundary.md`'s 8-name sample — the only slice ever run
at `NO_TRAIL` — was **chosen for family coverage, not exhaustiveness** (see that note's own
"Sample" section). This script runs the other ~77 names through the **identical** `NO_TRAIL`
exit geometry, on the **identical** 5-symbol × 2-interval × Train-1-only basket
(`SOLUSDT`/`ETHUSDT`/`BTCUSDT`/`XRPUSDT`/`DOGEUSDT` × `240`/`60`), per
`spec/build.md`'s basket rule: only the strategy-name axis is widened, nothing is added or
selected post-hoc by PnL.

**Purpose**: find new `NO_TRAIL`-aggregate-positive names beyond the original 3, to seed a
future monthly-criterion check — exactly the check
`spec/research/F006-hypothesis-notrail-monthly.md` ran for the original 3, and which alone
decides promotion eligibility under
`spec/research/F005-validation-protocol.md` section 7. **This script does not run that check.**
Aggregate-Train-1-positive is reported honestly as a necessary but explicitly *not sufficient*
condition — a positive full-Train-1 sum can still contain a losing month, which alone blocks
promotion regardless of the aggregate (`spec/build.md`: "Regularność zysku nie usprawiedliwia
ujemnego wyniku netto").

## Method

**Exit geometry: identical to the `NO_TRAIL` cell of every prior F006 slice, unchanged.**
`activate_pct=10.0` (unreachable in Train 1, so `backtest_engine._update_trailing`'s arming
condition `best_price >= entry_price * (1 + activate_pct)` never fires and `trail_active` stays
`False` for the life of every trade), `trail_pct` moot (recorded as `None`), `max_sl_pct=0.03`,
one-shot `entry_regime_mask`, `cooldown_candles=0`, `leverage=1`, `atr_multiplier=1.5`,
`initial_equity=500`, `stake=100`, `commission_rate_bps=10`, `half_spread_bps=5`,
`slippage_bps=2`, `now` pinned to `2025-03-01T00:00:00Z`. No engine change.

**Names**: all `strategy.STRATEGY_CATALOG` entries (85) minus the 8 already tested at
`NO_TRAIL` (`EMA_8_21`, `MACD_12_26_hist`, `RSI14_7030`, `BB_20_25_breakout`, `ADX14_DI_20`,
`LORENTZIAN_default`, `DONCHIAN_55`, `DONCHIAN_PULLBACK_55`) = **77 new names**. Per
`spec/research/F006-hypothesis-one-shot-entry.md`'s Run_id recipe, Lorentzian variants beyond
`LORENTZIAN_default` (already tested) and `LORENTZIAN_raw` are excluded — the catalog only has
those two, so only `LORENTZIAN_raw` (1 name, cheap) is new and is included.

**Harness control**: `DONCHIAN_55` — one of the 8 already-tested names — is re-run at
`NO_TRAIL` in this script and diffed row by row against the stored `NO_TRAIL` rows of
`output/f006_trailing_boundary/summary/results.csv`, to prove this script reproduces the
established harness before trusting any of the 77 new numbers.

- **Script**: `scripts/f006_catalog_notrail_sweep.py`. Two-pass split, same pattern as every
  other F006 script: `--catalog` on `.venv_test` (Python 3.9) — 76 new non-Lorentzian names +
  the `DONCHIAN_55` control = 77 names × 10 series = 770 runs; `--lorentzian` on
  `.venv_lorentzian` (Python 3.11 + advanced-ta) — `LORENTZIAN_raw` × 10 series = 10 runs;
  `--merge` combines and checks. 780 runs total, one pass each, no timeout-driven splitting
  needed (took under 4 minutes combined).
- **Aggregation**: `trade_stats.win_loss_decomposition` / `trade_stats.pool_decompositions`,
  reused unmodified — the same pooled-not-averaged decomposition
  `spec/research/F006-hypothesis-donchian.md` established (`avg_winner`, `avg_loser`,
  `breakeven_win_rate_pct`, pooled over every trade in a name's 10-series cell, not averaged
  across series).
- **Data**: identical checksum-verified load (`data_contract.load_dataset`, duplicated
  `EXPECTED_CHECKSUMS` table) and Train-1 slice as every F006 script. No network fetch.

**Discriminating checks:**

1. **Harness control** — `DONCHIAN_55`'s 10 rows diffed row by row against
   `output/f006_trailing_boundary/summary/results.csv`'s stored `NO_TRAIL` rows for that name,
   on `net_pnl`, `win_rate`, `n_trades`, `max_drawdown_pct`, `final_equity`.
2. **`NO_TRAIL` mechanism check**: `exit_trailing_sl` count must be 0 in every one of the 780
   runs.
3. **One-shot rule**: `n_trades` must never exceed `n_calls` (the number of first-bar-of-call
   entries the mask permits) in any run.
4. **No overlap**: the 77 names run here have zero intersection with the 8 already-tested names
   (besides the deliberate `DONCHIAN_55` control).

## Run_id

`scripts/f006_catalog_notrail_sweep.py`, `n_runs = 780`. Catalog pass: Python 3.9.25,
`.venv_test`, 770 runs, 176.3s. Lorentzian pass: Python 3.11.16 + advanced-ta 0.1.8,
`.venv_lorentzian`, 10 runs, 30.4s. pandas in both. Full parameters, checksums, per-name
aggregate table and ranking: `output/f006_catalog_notrail_sweep/summary/manifest.json`.
Per-run results, 780 rows: `output/f006_catalog_notrail_sweep/summary/results.csv`.

## Result

**All checks clean.** Harness control: `DONCHIAN_55`'s 10 rows match
`output/f006_trailing_boundary/summary/results.csv`'s stored `NO_TRAIL` rows exactly
(0/10 mismatches on `net_pnl`, `win_rate`, `n_trades`, `max_drawdown_pct`, `final_equity`).
`NO_TRAIL` mechanism check: 0/780 runs produced a `trailing_sl` exit. One-shot rule: 0/780
violations. No overlap: the 77 names run are disjoint from the 8 already-tested names besides
the deliberate control.

**54 of the 77 new names (70%) are aggregate-Train-1-positive at `NO_TRAIL`** — a much larger
hit rate than the original 8-name sample's 3/8 (37.5%). Ranked by both net PnL and by the
breakeven-win-rate gap (`breakeven_win_rate_pct - win_rate_pct`; more negative means the actual
win rate clears the breakeven bar by a larger margin), the top 5 candidates by both measures
overlap almost entirely:

| Name | mean net PnL (10 series) | sum net PnL | profitable series | gap (pp) | net/trade | n_trades |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `EMA3_21_50_200` | **+$125.30** | +$1,253.02 | 10/10 | -10.25 | +$2.867 | 437 |
| `EMA3_13_50_200` | **+$120.43** | +$1,204.27 | 10/10 | -9.41 | +$2.624 | 459 |
| `BB_20_2_EMA200` | **+$115.57** | +$1,155.71 | 9/10 | -8.64 | +$1.409 | 820 |
| `EMA_50_200` | **+$102.55** | +$1,025.45 | 10/10 | -10.88 | +$2.817 | 364 |
| `BB_20_25_EMA200` | **+$101.90** | +$1,019.01 | 10/10 | -9.84 | +$1.820 | 560 |

For context: the three original `NO_TRAIL` leads had mean net PnL of **+$67.69**
(`DONCHIAN_55`), **+$57.55** (`BB_20_25_breakout`) and **+$49.54**
(`DONCHIAN_PULLBACK_55`). All five names above beat every one of the three originals on mean
net PnL, three of the five hit 10/10 profitable series (the originals' best was 8/10), and all
five have a substantially wider breakeven-win-rate gap than any figure reported for the
originals in the trailing-boundary note — meaning actual win rate clears the geometry's
breakeven bar by a wider margin, not just a larger dollar total on more trades.

**A pattern in what worked**: 4 of the top 5 (and a large share of the other 49 positive names)
are long-lookback EMA triple/dual-crossover names (`EMA3_21_50_200`, `EMA3_13_50_200`,
`EMA_50_200`) or Bollinger-Band-plus-long-EMA composites (`BB_20_2_EMA200`,
`BB_20_25_EMA200`) — names built around a 200-period EMA, the longest, smoothest trend filter
in the catalog. This is consistent with (not proof of) the same low-trade-count,
large-average-winner mechanism the original `DONCHIAN_*` leads showed: `EMA3_21_50_200` has
only 437 trades pooled across 10 series (vs. thousands for shorter-lookback names), the
smallest trade count among the top 5.

**Worst-performing names**, reported for honesty, not analysis: `STOCH14_cross`
(-$3,924.69 sum), `STOCH5_cross` (-$3,897.59), `RSI7_trend50` (-$2,571.34),
`MACD_8_21_hist`/`MACD_8_21_sig` (-$2,318.39 each) — short-lookback oscillator names, the same
family the original 8-name sample already found negative (`RSI14_7030`, `MACD_12_26_hist`,
`ADX14_DI_20`).

**Full ranked table (all 77 names, both orderings) and every per-name pooled statistic**:
`output/f006_catalog_notrail_sweep/summary/manifest.json`'s `per_name_aggregate` and `ranking`
keys.

**Honest caveat, stated once and meant seriously: aggregate-positive is not the monthly
criterion.** None of these 54 names — including the 5 flagged below — has had a monthly PnL
breakdown run. `spec/research/F006-hypothesis-notrail-monthly.md` built that exact check for
the original 3 names and found (that note's own Result, referenced not reproduced here) that
the monthly bar is materially harder to clear than the aggregate one. A positive full-Train-1
sum can hide a single losing month, which alone blocks promotion under
`spec/research/F005-validation-protocol.md` section 7 regardless of how large the aggregate is.
Nothing in this note should be read as a promotion candidate.

## Decision

**Flag the top 5 by net PnL for a follow-up monthly check, do not run that check here:**
`EMA3_21_50_200`, `EMA3_13_50_200`, `BB_20_2_EMA200`, `EMA_50_200`, `BB_20_25_EMA200`. These
also rank in the top 5 by breakeven-win-rate gap, so the two rankings agree on the shortlist
rather than trading off against each other. The next step is the same one
`spec/research/F006-hypothesis-notrail-monthly.md` took for the original 3: build the
Train-1 monthly PnL series for these 5 names (or as many as budget allows), reusing
`regularity.py`/`spec/research/F005-baseline.md`'s machinery unmodified, and check them
against the protocol's monthly/full-period rejection criteria before any Validation spend.

**This is not a repeat of "nothing new turns up"**: 54/77 new names cleared the aggregate bar,
and the best 5 beat all three original leads on every reported measure. The catalog-name axis
was worth widening.

## Tests

No new computation module was added in this slice (reuses `trade_stats.py`,
`entry_masks.py`, `data_contract.py`, `backtest_engine.py` unmodified — the same discipline as
`spec/research/F006-hypothesis-trailing-boundary.md`'s Tests section, which also added no
computation module for its `NO_TRAIL` cell). The load-bearing checks are the harness-control
diff (0/10 mismatches against the trailing-boundary note's stored rows) and the in-script
`NO_TRAIL`/one-shot/overlap checks (all clean, 0 violations), both of which ran as part of
`--merge` above and are recorded in `output/f006_catalog_notrail_sweep/summary/manifest.json`.
