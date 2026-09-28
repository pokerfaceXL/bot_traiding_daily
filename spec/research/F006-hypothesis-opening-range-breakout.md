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

`scripts/f006_opening_range_breakout_experiment.py`, system Python 3.10.12 (pandas 2.3.3),
single pass, 50 candidate backtests (5 `ORB_UTC_*` names x 5 symbols x 2 intervals) + 1 harness-
control backtest (`DONCHIAN_55`, `BTCUSDT/240`), 10.9s. Summary table:
`output/f006_opening_range_breakout/summary/results.csv`. Per-series raw JSON:
`output/f006_opening_range_breakout/raw/*.json` (50 files). Manifest, checksums,
harness-control record, H1/H2 tables and verdicts: `output/f006_opening_range_breakout/summary/manifest.json`.
Commit at run time: `4ec792bf3b43eeba8d97c0fb9433b296bedc9d4b`.

The frozen-window `data_cache` CSVs (git-ignored, checksum-verified per symbol/interval against
`spec/research/F005-validation-protocol.md` section 6) were missing from this worktree (only the
`.manifest.json` sidecars are tracked in git; the CSVs are a local build artifact of the main
chekout) and were symlinked read-only from
`/home/limen/bot_traiding_daily/bot_traiding_daily/data_cache/` before this script's first run --
a per-worktree environment gap, not a change to the frozen dataset itself. The script's own
checksum check (`EXPECTED_CHECKSUMS` against `data_contract.load_dataset`'s returned manifest)
passed for all 10 `(symbol, interval)` pairs plus the control pair, confirming the symlinked
files are byte-identical to the frozen cache, not a re-fetch.

## Result

**H1 is falsified. All 5 `ORB_UTC_*` names have negative mean net PnL over their 10-series pool
at `NO_TRAIL`:**

| Name | OR_BARS | sum net PnL (10 series) | mean net PnL | profitable series | mean n_trades |
| --- | ---: | ---: | ---: | ---: | ---: |
| `ORB_UTC_1` | 1 | -$1,367.74 | -$136.77 | 0/10 | 419.9 |
| `ORB_UTC_2` | 2 | -$1,043.30 | -$104.33 | 2/10 | 336.4 |
| `ORB_UTC_3` | 3 | -$643.18 | -$64.32 | 1/10 | 281.1 |
| `ORB_UTC_4` | 4 | -$354.42 | -$35.44 | 3/10 | 228.8 |
| `ORB_UTC_6` | 6 | -$554.38 | -$55.44 | 0/10 | 159.7 |

All checks clean and recorded in the manifest: harness control (`DONCHIAN_55`/`BTCUSDT/240`, one
row) matched `output/f006_catalog_notrail_sweep/summary/results.csv`'s stored `NO_TRAIL`
one-shot/cd=0 row exactly (0 mismatches on `net_pnl`, `win_rate`, `n_trades`,
`max_drawdown_pct`, `final_equity`) -- this script's harness reproduces the established
`NO_TRAIL` cell correctly before any `ORB_UTC_*` row is trusted. `NO_TRAIL` mechanism check:
0/50 candidate runs produced a `trailing_sl` exit. One-shot rule: 0/50 violations (`n_trades <=
n_calls` held on every masked run, including the 5 all-zero-signal rows below).

**Mechanical, pre-registered-and-honestly-reported edge case, not a bug fix:** every
`ORB_UTC_6`/`240` row (all 5 symbols) traded **zero times** (`n_calls=0`, `n_trades=0`,
`net_pnl=0.00`). A UTC calendar day on the `240` (4h) interval has exactly 6 bars
(`24h / 4h = 6`), so within that day `i` only ever reaches `0..5` -- the condition `i >= OR_BARS`
(`i >= 6`) is never true for any bar of any day, so the range never "completes" and no bar is
ever active. This is the literal, pre-registered generator definition applied to this basket's
exact interval structure ("a day with fewer than OR_BARS bars ... never arms" generalizes
mechanically to "a day with exactly OR_BARS bars never arms either", since arming requires a bar
*after* the OR_BARS-th one) -- not an implementation defect, and not adjusted after seeing it,
per the note's own instruction not to re-tune. `ORB_UTC_6`'s reported -$55.44 mean/-$554.38 sum
come entirely from its 5 `60`-interval series (where a UTC day has 24 one-hour bars, so the
condition arms normally); its 5 `240`-interval series are flat zeros, which is why the
aggregate is milder than `ORB_UTC_1`/`ORB_UTC_2`/`ORB_UTC_3` despite the same falsification
outcome.

**No consistent per-symbol lead.** `XRPUSDT/240` is net-positive for `ORB_UTC_2`
(+$17.11), `ORB_UTC_3` (+$77.69) and `ORB_UTC_4` (+$99.64, its own name's single best series),
and `DOGEUSDT/240` is positive for `ORB_UTC_4` (+$137.16, the sample's largest positive series).
Both are `240`-interval, low-trade-count series (`n_trades` 95-187) on the same two lower-priced,
higher-volatility names -- consistent with a handful of large, well-timed moves rather than a
repeatable edge, and neither symbol is positive across all 5 names (`XRPUSDT/240`'s own
`ORB_UTC_1` is -$15.96). No name clears H1's aggregate (10-series mean net PnL) bar regardless.

**H2 is not applicable -- H1 failed for every one of the 5 candidates**, exactly per the
pre-registered falsification condition ("If H1 fails, H2 is 'not applicable -- H1 failed', not
silently passed/failed"). No monthly promotion-checklist table is reported because there is no
H1-clearing name to evaluate it against.

## Decision

**Close the `ORB_UTC_*` family at this geometry/basket. Do not pursue further `OR_BARS` values,
alternate anchors, or gate combinations for this generator.** The UTC opening-range breakout
mechanism -- genuinely new relative to the catalog (a session-clock anchor, not a rolling
indicator window) -- is aggregate-negative across all 5 pre-registered `OR_BARS` values, with a
monotonic-ish improvement from `OR_BARS=1` (-$136.77 mean, worst) toward `OR_BARS=4` (-$35.44
mean, least bad) before `OR_BARS=6` gets pulled back down by its `240`-interval degenerate-zero
rows -- consistent with tighter (1-2 bar) opening ranges producing more false breakouts that a
commission/spread/slippage-bearing one-shot entry pays for repeatedly (mean `n_trades` falls
monotonically from 419.9 at `OR_BARS=1` to 159.7 at `OR_BARS=6`), not with a signal that becomes
profitable as the range widens. Widening further (the note's own falsification condition already
forbids inventing extra `OR_BARS` values or alternate session anchors after seeing results) would
most plausibly continue reducing trade count and losses toward zero without ever crossing into
aggregate profitability, which is not a lead worth a follow-up run.

The `240`-interval degenerate-zero case for `ORB_UTC_6` is a basket/interval-structure artifact
(a UTC day has exactly 6 four-hour bars), not a lever to re-tune inside this slice; a
narrower-than-day session anchor (e.g. London/NY open) that would not collide with `240`'s exact
bar count is exactly the kind of alternate-anchor variant the pre-registration explicitly
forbids trying "after seeing results", so it is named here as a possible, separately
pre-registered future note rather than pursued now.

## Tests

`tests/test_opening_range_breakout.py` (new, 24 tests, all passing): hand-built 3-day/`OR_BARS=2`
fixture pinning (a) the exact bars a breakout fires on, (b) bars still inside the forming range
stay 0, (c) a day with fewer bars than `OR_BARS` never arms, (d) exact equality with `or_high`
stays flat (strict inequality only), (e) a new UTC day never carries the previous day's range or
state; causality (`compute_orb_signal` at bar i unchanged when 20 future bars are appended, all
5 `OR_BARS` values x 3 truncation points on the real OHLCV fixture); catalog wiring
(`STRATEGY_CATALOG` gained exactly the 5 `ORB_UTC_*` entries, length 90) and an additive-only
regression check (83 pre-existing non-Lorentzian catalog entries hash bit-identical to
`tests/fixtures/catalog_fingerprints_pre_orb.json`, captured before this module was wired in);
end-to-end engine wiring through `entry_masks`/`backtest_engine` with the one-shot mask.

`tests/test_donchian.py`'s pre-existing catalog-length assertion was updated from 85 to 90 (the
same count-bump pattern every prior additive F006 family applied to the family before it).

Full suite, system Python 3.10.12:

| | Result |
| --- | --- |
| `python3 -m pytest tests/` | 195 passed, 6 skipped |

No pre-existing test failed or was weakened; the only change outside the two new files
(`opening_range_breakout.py`, `scripts/f006_opening_range_breakout_experiment.py`) and the new
test file is the catalog-length bump in `tests/test_donchian.py` and the 8-line registration
block in `strategy.py`. `advanced_ta` is not installed in this interpreter, so
`tests/test_lorentzian.py`'s `advanced_ta`-dependent case is skipped (pre-existing environment
limitation, unrelated to this slice); it does not affect any `ORB_UTC_*`/Donchian test above,
none of which import `lorentzian.py`.
