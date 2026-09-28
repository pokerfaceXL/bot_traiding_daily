# F006 — UTC opening-range breakout as entry (new signal family)

> Sections "Observation" through "Method" (including falsification) were written and committed
> BEFORE any new signal module / experiment script was written and before any backtest was run,
> per the same pre-registration discipline as every prior F006 hypothesis note. "Run_id",
> "Result", "Decision" and "Tests" are placeholders filled in after the run.
>
> TRAIN-1 ONLY, same window as every F006 slice: `[2024-03-01T00:00:00Z, 2025-03-01T00:00:00Z)`
> plus the protocol's 35-day warm-up buffer from `2024-01-26T00:00:00Z`. Validation 1-4 and the
> Holdout window are not loaded, not sliced and not looked at.

## Observation

After the catalog's momentum and mean-reversion axes were exhausted under `NO_TRAIL`, two
out-of-catalog generators have been tried:

- `RVOL_RE_*` (relative-volume + ATR range-expansion): H1 pass 3/5, H2 fail — family closed
  (`spec/research/F006-hypothesis-vol-range-expansion.md`).
- `XS_RS_*` (cross-sectional relative-strength rank): launched in parallel
  (`spec/research/F006-hypothesis-cross-sectional-rs.md`); **do not duplicate** that family.

What remains untried as a *generator* (and is absent from the 85-name `STRATEGY_CATALOG` —
verified: no `ORB_*` / `SESSION_*` / time-of-day names):

- **Opening-range breakout (ORB) keyed to a UTC session boundary.** Every catalog name is
  path-dependent on rolling windows of the same series (EMA/BB/Donchian/RSI/MACD/Stoch/ADX) or
  Lorentzian neighbors. None defines the entry from "first N bars after a fixed clock anchor,
  then trade the break of that range for the rest of the session." That is a calendar/session
  mechanism, orthogonal to RVOL participation and to cross-sectional rank.

Rejected for this slice (already covered or blocked):

- Re-tuning `RVOL_RE_*` / depending on `vol_range_expansion.py`: family closed.
- Duplicating `XS_RS_*`: already RUNNING.
- True multi-TF HTF structure: 60→240 available, but 240→720 has **no** `*_720_*` manifests in
  `data_cache` for this basket — still deferred (same reason as the XS_RS note).
- Funding / OI: no local series.
- BB squeeze / EMA trend gate / MIN_AGREE: already falsified as filters.

## Hypothesis

**H1 (new generator, aggregate).** An additive opening-range breakout signal family — for each
UTC calendar day, measure high/low over the first `OR_BARS` bars of that day, then after the
range is complete take long on close above the OR high and short on close below the OR low —
produces at least one catalog name whose **mean net PnL across the 10 `(symbol, interval)`
series is > 0** at `NO_TRAIL` (`activate_pct=10.0`, `max_sl_pct=0.03`, one-shot entry mask,
`cd=0`, `leverage=1`), same pooling bar as `spec/research/F006-catalog-notrail-sweep.md`.

Concrete generator (implement as a new additive module — do **not** stuff this into
`add_indicators`; register new `STRATEGY_CATALOG` names via `catalog_entries()` / harness
registration, Donchian/Lorentzian pattern):

- Bar timestamps are treated as UTC (Bybit cache convention). Session day `D` = UTC date of
  each bar's open.
- Within each `(symbol, interval)` series, group bars by `D`. Let `i = 0,1,2,...` be the
  0-based order of bars whose open falls on `D`.
- While `i < OR_BARS`: signal = 0 (range still forming; do not trade). Track
  `or_high = max(high[0..OR_BARS))`, `or_low = min(low[0..OR_BARS))` once `OR_BARS` bars exist
  for that day; if a day has fewer than `OR_BARS` bars, that day never arms (signal stays 0).
- For bars with `i >= OR_BARS`:
  - Long (+1) when `close > or_high`.
  - Short (−1) when `close < or_low`.
  - Else 0.
  - If both could fire on the same bar (pathological `or_high < or_low` impossible; equal-range
    flat bar: `close` cannot be both strictly above and below) — use strict inequalities only.
- At the first bar of a new UTC day, previous day's state is discarded (no carry across days).
- Persistent-state signal; family one-shot mask applied by the experiment harness as elsewhere.
- Causality: OR high/low use only bars with `i < OR_BARS` on the same day; breakout decision
  uses only the current bar's close vs that completed range. No future bars.

Pre-registered small name grid (≤5 names so 5×2×names stays in the usual ~50-run budget; do
**not** grid-search after seeing results). `OR_BARS` is a bar count (clock duration therefore
differs by interval — 1 bar = 1h on 60, 4h on 240 — that is intentional and documented, not a
bug to "fix" mid-slice):

| Name | OR_BARS | Anchor |
| --- | ---: | --- |
| `ORB_UTC_1` | 1 | UTC day start |
| `ORB_UTC_2` | 2 | UTC day start |
| `ORB_UTC_3` | 3 | UTC day start |
| `ORB_UTC_4` | 4 | UTC day start |
| `ORB_UTC_6` | 6 | UTC day start |

**Why mechanistically new:** entry is defined by a *session-clock opening range* and a later
break of that range — not by rolling indicator state, not by relative volume, not by basket
rank. No `ORB_*` / session name exists in `STRATEGY_CATALOG` today.

**H2 (monthly, conditional on H1).** For any name that clears H1, at least one of its 10 series
clears the F005 section-7 monthly promotion checklist with `n_trades > 0` (every valid month
non-negative, all 12 Train-1 months valid, full-window net PnL ≥ 0, DD ≤ 50%).

## Falsification condition (stated before running)

**H1 falsified** if none of the pre-registered names has positive mean net PnL over its
10-series pool at `NO_TRAIL`.

**H2 falsified** if every H1-clearing name has zero series clearing all monthly criteria (with
`n_trades > 0`). If H1 fails, H2 is "not applicable — H1 failed", not silently passed/failed.

Do **not** invent extra `OR_BARS` / alternate anchors (London/NY) after seeing results. Do
**not** mix in BB/Donchian/EMA/RVOL/XS gates "to help" mid-slice. Do **not** depend on
`vol_range_expansion.py` or the XS_RS module. A negative Result is valid and must be reported
honestly; Decision should then close this ORB-UTC family at this geometry/basket (or name one
narrow, pre-justified follow-up only if the Result itself surfaces a clean, non-overfit lever).

## Sample

5 names × 5 symbols × 2 intervals (`240`/`60`) = 50 series, Train-1 only. Plus one
harness-control re-run of a known catalog name already measured at `NO_TRAIL` (e.g.
`DONCHIAN_55` on one symbol/interval) to prove the experiment script matches stored numbers
before trusting new names.

## Method

1. Implement additive module (suggested path: `opening_range_breakout.py`) exposing
   `compute_orb_signal(df, or_bars) -> pd.Series` (+1/0/−1) and `catalog_entries()` registering
   the five `ORB_UTC_*` names into `STRATEGY_CATALOG` for `run_backtest`. No live trading, no
   API keys.
2. Experiment script under `scripts/f006_opening_range_breakout_experiment.py` mirroring the
   catalog-sweep / mean-reversion / vol-range / XS-RS harnesses (checksums from F005 protocol
   §6, one-shot mask, `NO_TRAIL` geometry, output under `output/f006_opening_range_breakout/`).
3. Unit tests: hand-built single-day fixture (known OR high/low → breakout ±1 after arming;
   bars inside OR window → 0; day with `< OR_BARS` bars → never arms; new UTC day resets).
   Regression: untouched default catalog names unchanged.
4. Fill Result / Decision / Run_id / Tests after the run; commit evidence.

## Run_id

_(placeholder)_

## Result

_(placeholder)_

## Decision

_(placeholder)_

## Tests

_(placeholder)_
