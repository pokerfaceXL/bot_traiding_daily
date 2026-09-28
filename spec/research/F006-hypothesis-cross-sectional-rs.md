# F006 — Cross-sectional relative-strength rank as entry (new signal family)

> Sections "Observation" through "Method" (including falsification) were written and committed
> BEFORE any new signal module / experiment script was written and before any backtest was run,
> per the same pre-registration discipline as every prior F006 hypothesis note. "Run_id",
> "Result", "Decision" and "Tests" are placeholders filled in after the run.
>
> TRAIN-1 ONLY, same window as every F006 slice: `[2024-03-01T00:00:00Z, 2025-03-01T00:00:00Z)`
> plus the protocol's 35-day warm-up buffer from `2024-01-26T00:00:00Z`. Validation 1-4 and the
> Holdout window are not loaded, not sliced and not looked at.

## Observation

After the catalog's momentum and mean-reversion axes were exhausted under `NO_TRAIL`, the first
out-of-catalog OHLCV generator (`RVOL_RE_*` relative-volume + ATR range-expansion,
`spec/research/F006-hypothesis-vol-range-expansion.md`) cleared H1 for 3/5 names but failed H2
exactly like every momentum name (best series still 3 losing months; family closed — do not
re-tune RVOL thresholds). `vol_range_expansion.py` may still live only on branch
`limen/2026-09-28-f006-vol-range-expansion-7c12a336` and is **not** required for this slice;
spawn from current `main` HEAD and do not depend on that module.

What remains untried as a *generator* (not a filter on an existing catalog name):

- **Cross-sectional relative strength vs basket peers.** Hip. 14
  (`F006-hypothesis-entry-cross-symbol-agreement.md` / refined) tested `MIN_AGREE` — a
  same-bar *direction-agreement filter* on already-defined BB/Donchian signals across the other
  four symbols. That moved win rate the right way for 2/3 names but never cleared monthly.
  It never asked: *can the rank of a symbol's own lookback return vs its peers BE the entry
  signal?* That is a different mechanism (relative outperformance / underperformance as the
  primary trigger), and it is the natural follow-up to
  `F006-portfolio-diversification-exploration.md`'s finding that correlated same-family signals
  stay correlated in bad months — a rank-based rotator is designed to force cross-sectional
  differentiation rather than agree with peers.

Rejected for this slice (already covered or blocked):

- BB squeeze / compress-then-expand: `BB_20_2_SQ` / `BB_20_25_SQ` already in catalog
  (`sig_bb_breakout_squeeze`); width-expansion gate also falsified as a filter.
- Same-TF EMA trend gate: falsified (`F006-hypothesis-entry-trend-confirm.md`).
- True multi-TF structure using a higher cached interval: 60→240 is available, but 240 needs
  720 and no `*_720_*` manifests exist in `data_cache` for this basket — deferred rather than
  half-built.
- Funding / OI: no local series.
- Re-tuning `RVOL_RE_*`: family closed.

## Hypothesis

**H1 (new generator, aggregate).** An additive cross-sectional relative-strength signal family —
rank each basket symbol by its own lookback simple return at each aligned bar, then take long
the top `TOP_K` ranks and short the bottom `TOP_K` ranks — produces at least one catalog name
whose **mean net PnL across the 10 `(symbol, interval)` series is > 0** at `NO_TRAIL`
(`activate_pct=10.0`, `max_sl_pct=0.03`, one-shot entry mask, `cd=0`, `leverage=1`), same
pooling bar as `spec/research/F006-catalog-notrail-sweep.md`.

Concrete generator (implement as a new additive module — do **not** stuff this into
`add_indicators`; register new `STRATEGY_CATALOG` names via `catalog_entries()` / harness
registration the same way peer-aware plumbing was done for the cross-symbol gate experiment):

- Basket = the frozen F006 five: `SOLUSDT`, `ETHUSDT`, `BTCUSDT`, `XRPUSDT`, `DOGEUSDT`.
- At each timestamp `t` present on **all five** symbols for that interval (inner-join index;
  no forward-fill of missing peers), compute
  `ret_i(t) = close_i(t) / close_i(t - LOOKBACK) - 1` (NaN → no rank that bar).
- Rank descending by `ret` (rank 1 = strongest). Ties: use a stable, deterministic tie-break
  (e.g. symbol name ascending) so ranks are a permutation of `{1..5}` whenever all five rets
  are finite.
- Long (+1) when `rank <= TOP_K`. Short (−1) when `rank >= (5 - TOP_K + 1)`. Else 0.
  Persistent-state signal; family one-shot mask applied by the experiment harness as elsewhere.
- Causality: only closes at or before `t`; no future bars. Peer closes at `t` are same-bar
  (already accepted for MIN_AGREE); do not use peer bars after `t`.

Pre-registered small name grid (≤5 names so 5×2×names stays in the usual ~50-run budget; do
**not** grid-search after seeing results):

| Name | LOOKBACK | TOP_K |
| --- | ---: | ---: |
| `XS_RS_20_TOP1` | 20 | 1 |
| `XS_RS_48_TOP1` | 48 | 1 |
| `XS_RS_96_TOP1` | 96 | 1 |
| `XS_RS_20_TOP2` | 20 | 2 |
| `XS_RS_48_TOP2` | 48 | 2 |

**Why mechanistically new:** entry is defined by *who is outperforming / underperforming the
basket*, not by a single-series channel/band/EMA/RSI/volume rule, and not by whether other
symbols' *existing* BB/Donchian signals agree in direction (`MIN_AGREE`). That is outside
`add_indicators`'s single-df catalog and outside `RVOL_RE_*`.

**H2 (monthly, conditional on H1).** For any name that clears H1, at least one of its 10 series
clears the F005 section-7 monthly promotion checklist with `n_trades > 0` (every valid month
non-negative, all 12 Train-1 months valid, full-window net PnL ≥ 0, DD ≤ 50%).

## Falsification condition (stated before running)

**H1 falsified** if none of the pre-registered names has positive mean net PnL over its
10-series pool at `NO_TRAIL`.

**H2 falsified** if every H1-clearing name has zero series clearing all monthly criteria (with
`n_trades > 0`). If H1 fails, H2 is "not applicable — H1 failed", not silently passed/failed.

Do **not** invent extra lookbacks/`TOP_K` after seeing results. Do **not** mix in BB/Donchian/EMA
gates "to help" mid-slice. Do **not** depend on `vol_range_expansion.py`. A negative Result is
valid and must be reported honestly; Decision should then close this cross-sectional-rank family
at this geometry/basket (or name one narrow, pre-justified follow-up only if the Result itself
surfaces a clean, non-overfit lever).

## Sample

5 names × 5 symbols × 2 intervals (`240`/`60`) = 50 series, Train-1 only. Plus one
harness-control re-run of a known catalog name already measured at `NO_TRAIL` (e.g.
`DONCHIAN_55` on one symbol/interval) to prove the experiment script matches stored numbers
before trusting new names.

## Method

1. Implement additive module (suggested path: `cross_sectional_rs.py`) exposing
   `compute_basket_signals(closes_by_symbol, lookback, top_k) -> dict[symbol, pd.Series]` and
   a way to register `XS_RS_*` names into `STRATEGY_CATALOG` for `run_backtest` (peer context /
   precomputed series closed over by callables is fine — document it; single-df-only stubs that
   cannot see peers must not silently return zeros). No live trading, no API keys.
2. Experiment script under `scripts/f006_cross_sectional_rs_experiment.py` mirroring the
   catalog-sweep / mean-reversion / vol-range harnesses (checksums from F005 protocol §6,
   one-shot mask, `NO_TRAIL` geometry, output under `output/f006_cross_sectional_rs/`). Load all
   five symbols per interval, align, compute ranks once, then run each `(symbol, name)` series.
3. Unit tests: hand-built 5-symbol close fixture (known top/bottom ranks → ±1; missing peer bar
   drops that timestamp; LOOKBACK warm-up → 0; TOP_K=2 covers two longs and two shorts).
   Regression: untouched default catalog names unchanged.
4. Fill Result / Decision / Run_id / Tests after the run; commit evidence.

## Run_id

Base commit `cfcb919` (this note's pre-registration commit). Additive module `cross_sectional_rs.py`
wired into `strategy.py`'s `STRATEGY_CATALOG` (90 entries, up from 85; 5 new `XS_RS_*` names,
no existing entry touched). `scripts/f006_cross_sectional_rs_experiment.py`, single pass,
`output/f006_cross_sectional_rs/` (`summary/results.csv`, `summary/manifest.json`,
`raw/*.json`). 51 series in 10.3s (50 candidate series = 5 names x 5 symbols x 2 intervals, +
1 harness-control series: `DONCHIAN_55` on `BTCUSDT/240`). Checksums matched
`spec/research/F005-validation-protocol.md` section 6 for all 10 `(symbol, interval)` pairs.
Harness control: 0/1 mismatch against `output/f006_catalog_notrail_sweep/summary/results.csv`'s
stored `DONCHIAN_55`/`BTCUSDT`/`240` NO_TRAIL row -- the script's engine call reproduces stored
numbers exactly. `no_trail_mechanism_check`: 0/50 candidate runs produced a `trailing_sl` exit.
`one_shot_violations`: 0.

## Result

**H1: 2/5 names clear** (mean net PnL over the 10-series pool at NO_TRAIL):

| Name | mean net PnL | sum net PnL | profitable series | H1 |
| --- | ---: | ---: | ---: | --- |
| `XS_RS_20_TOP1` | -11.61 | -116.08 | 4/10 | fail |
| `XS_RS_48_TOP1` | **+12.45** | +124.53 | 4/10 | **pass** |
| `XS_RS_96_TOP1` | **+39.19** | +391.90 | 7/10 | **pass** |
| `XS_RS_20_TOP2` | -74.14 | -741.43 | 2/10 | fail |
| `XS_RS_48_TOP2` | -9.39 | -93.87 | 3/10 | fail |

H1 is not falsified: both longer-lookback `TOP1` names (`XS_RS_48_TOP1`, `XS_RS_96_TOP1`) have
positive mean net PnL, and `XS_RS_96_TOP1` also has the most profitable series (7/10) of any
name in this slice. The `TOP2` variants are aggregately worse than every `TOP1` variant
(2x the exposure -- 2 longs + 2 shorts per bar instead of 1+1 -- did not average out into a
better result; it concentrated the losing `XS_RS_20` cell's loss further).

**H2: 0/20 series clear the monthly promotion checklist** (checked for the 2 H1-passing names
only, per the note's conditional). Every one of the 20 `(symbol, interval)` series for
`XS_RS_48_TOP1` / `XS_RS_96_TOP1` has at least 2 losing valid Train-1 months (worst 11, best 2 --
`DOGEUSDT`/`60`/`XS_RS_96_TOP1`, `train1_net_pnl=+197.83`, 2 losing months, still fails the
"every valid month non-negative" clause). Full table in
`output/f006_cross_sectional_rs/summary/manifest.json`'s `h2_monthly_table`. H2 is falsified.

## Decision

**Cross-sectional relative-strength rank is closed as a family at this basket/geometry.** H1
held (a genuinely new generator -- entry defined by peer rank, not a single-series
channel/band/EMA/RSI rule -- produced 2 aggregate-positive names, the first out-of-catalog
generator this basket's F006 slices have found to clear H1 outright with 7/10 profitable series
for the best name), but H2 did not: every H1-clearing series still has the same "lumpy winner,
lumpy loser" monthly shape every other F006 family has hit (2-11 losing Train-1 months, never 0).
Per the pre-registration, no extra lookbacks/`TOP_K` are added after seeing that `TOP1` beats
`TOP2` and longer lookback beats shorter -- that ordering is a real, monotonic finding in this
Result, but chasing it (e.g. `LOOKBACK=144`) is exactly the re-tuning the note forbids, and
nothing in this Result is a "clean, non-overfit lever" distinct from what every prior F006
family already tried and failed to fix (fewer losing months without giving up the winning ones).
The module (`cross_sectional_rs.py`) and its 5 catalog entries stay in the codebase, additive and
inert (unused by `STRATEGY`/live trading), as a working, tested generator for a future slice that
asks a genuinely different question (e.g. combining rank with an existing filter, or a different
basket) rather than re-tuning this one.

## Tests

`tests/test_cross_sectional_rs.py`, 10/10 passing:

- Rank math on hand-built fixtures: known top/bottom ranks resolve to +1/-1 with the middle rank
  flat; a bar missing on one symbol drops that timestamp for every symbol's own precomputed
  series (not forward-filled, not partially ranked); the first `LOOKBACK` bars are flat for
  everyone (no partial-return ranking); `TOP_K=2` covers exactly 2 longs + 2 shorts + 1 flat;
  malformed baskets (wrong symbol set) raise.
- Additive-only regression: `STRATEGY_CATALOG` gained exactly the 5 `XS_RS_*` entries (90 total,
  up from 85) and the other 83 pre-existing entries (79 F005 + 4 Donchian; `LORENTZIAN_*`
  excluded -- `advanced-ta` not importable on this interpreter, same exclusion
  `tests/test_donchian.py` already makes) hash bit-identical to their pre-this-slice fingerprints
  (`tests/fixtures/catalog_fingerprints_pre_cross_sectional_rs.json`). Updated
  `tests/test_donchian.py`'s hardcoded catalog-length assertion (85 -> 90) to match.
- Peer-aware plumbing contract: a `XS_RS_*` catalog entry called with no active
  `(symbol, interval)` context raises `RuntimeError` (not a silent zero signal); called with a
  context nothing was registered for also raises; called with a registered context returns
  exactly that precomputed series.
- End-to-end: `entry_masks.strategy_signal_series` -> `one_shot_entry_mask` ->
  `backtest_engine.run_backtest` on a real OHLCV fixture reproduces the same index alignment
  contract `tests/test_donchian.py` checks for the Donchian family.

Full suite: `python3 -m pytest tests/ -q --deselect tests/test_lorentzian.py` (excluded for the
same `advanced-ta` reason as above; run separately: 3 passed, 4 skipped, unaffected) ->
**174 passed, 6 skipped** (skips are pre-existing, environment-only: missing raw output on disk,
one uncached symbol/interval, three trailing-geometry fixtures that don't produce a `trailing_sl`
exit at those params -- none touch this slice). No pre-existing test's assertions changed except
the catalog-length constant noted above.
