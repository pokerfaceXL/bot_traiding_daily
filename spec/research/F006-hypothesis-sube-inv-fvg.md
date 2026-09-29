# F006 — Sube-inspired inversion: first opposing FVG or HTF inversion close

> This pre-registration was written before the signal module, tests, experiment script, or backtest. It implements card `H-SUBE-INV-FVG-01` without changing its frozen five-name set.
>
> **Train-1 only:** `[2024-03-01T00:00:00Z, 2025-03-01T00:00:00Z)`, with the shared 35-day warm-up. No validation or holdout data is loaded or inspected.

## Observation

SubeTradingPolska's public tape distinguishes an official higher-timeframe close which changes structure from an aggressive first fair-value gap printed against the old structure. A later same-direction H4 gap and cross-asset SMT are optional confirmations. His narrated momentum cloud, money-flow, and level-60 concepts are unavailable in the OHLCV cache and are intentionally excluded.

This is not the closed `HTF-GAP-MIDFILL` geometry: no entry compares price with a gap midpoint or enters on a gap touch. It is not `H-MULTI-TF-PA-01`: MSS breaks a confirmed P=2 swing only when the preceding HTF trend is not already the trade direction. It contains no equal-high/equal-low, sweep, reclaim, funding, OI, RSI, or Donchian permission rule.

## Hypothesis

**H1.** At least one of the exactly five pre-registered names has mean Train-1 net PnL above zero over the frozen ten-series pool under the shared `NO_TRAIL` harness.

**H2, conditional on H1.** At least one H1-clearing name has a series which clears the shared monthly promotion checklist.

Frozen names, with no parameter grid:

| Name | Signal |
| --- | --- |
| `SINV_FIRST_FVG` | First bull/bear 5-day FVG created against an existing opposite HTF trend |
| `SINV_MSS_CLOSE` | Bull/bear MSS close beyond the latest confirmed P=2 swing while the prior trend is not that sign |
| `SINV_MSS_IN_FVG` | The same MSS only when its HTF block intersects a previously-created, still-open HTF FVG |
| `SINV_FIRST_H4` | First same-direction H4 FVG born within 24 hours after a first HTF FVG event |
| `SINV_FIRST_SMT` | First opposing HTF FVG gated by same-block BTC/reference swing-extreme XOR SMT |

## Causal construction

Bars use fixed Unix-epoch-aligned blocks. HTF blocks are 7200 minutes (five days); H4 blocks are 240 minutes. A block exists only when complete; missing bars prevent a block and a three-block FVG cannot cross a hole. A signal at close of bar `i` is filled only at open of `i+1` by the engine.

A P=2 HTF swing is confirmed only after both right-wing blocks complete. Trend at completed block `k` is +1 when its last two confirmed swing highs and lows both rise, -1 when both fall, otherwise 0. Highs and lows are independent lists; no alternation repair.

A bull FVG is `low[k] > high[k-2]`; a bear FVG is `high[k] < low[k-2]`, requiring consecutive existing block ids. Its far-edge full fill, checked only after creation and before the tested bar, is bull `bar.low <= gap_bot`, bear `bar.high >= gap_top`. No midfill price exists.

Bull MSS requires close[k] above the latest swing high confirmed by `k-1`, previous trend not +1, and an unused swing id; bear mirrors it. A first bull (bear) FVG requires prior trend exactly -1 (+1) and no prior same-direction FVG since that trend first became -1 (+1). Each FVG or swing event is one-shot.

For `SINV_FIRST_H4`, an HTF first-FVG event starts a six-H4-block window; the first later same-direction H4 FVG birth fires, not the HTF event itself. For `SINV_FIRST_SMT`, BTC references ETH; every other symbol references BTC. On the same HTF block both sides must have the relevant confirmed swing and exactly one must run it. This is an XOR boolean gate, not lagged BTC returns or a Donchian filter.

## Falsification

- H1 is falsified if no frozen name has mean Train-1 net PnL > 0.
- H2 is falsified if every H1-clearing name has zero monthly-promotion series. If H1 fails, H2 is not applicable.
- A candidate with mean trades per series below 10 fails for sparsity, even if H1 is positive.
- Any lookahead, unclosed block, pre-confirmation pivot, same-bar fill, midpoint/touch entry, continuation prior-N break, EQH/EQL/sweep/reclaim, or non-XOR SMT invalidates the run.

## Method

Add an isolated signal module with runtime-only catalog registration, unit-test the block, pivot, FVG, MSS, H4, SMT, and causality boundaries, then call the unmodified `run_family` once. The shared runner fixes the 5×2 Train-1 basket, `DONCHIAN_55` control, checksums, and `NO_TRAIL` exit. Evidence is written under `output/f006_sube_inv_fvg/` and includes the execution commit in its manifest.

## Run_id

`output/f006_sube_inv_fvg/summary/manifest.json`, executed at implementation tip `9c06e32dd9a3724dabff7e092dc91d408f57e07c`.

## Result

The `DONCHIAN_55` control reproduced all ten stored rows (zero mismatches); all 60 runs had zero trailing exits and zero one-shot violations. `SINV_FIRST_H4` alone clears the PnL part of H1 at +$41.4145 mean Train-1 net PnL, but it has just six trades over ten series (0.6 mean trades/series), so it is falsified by the pre-registered density rule. Its two positive XRP series still have two negative months and no series passes H2. The other four names have negative mean PnL: FIRST_FVG -$7.1403, MSS_CLOSE -$10.1421, MSS_IN_FVG -$5.4986, and FIRST_SMT -$1.3298; all are sparse too.

## Decision

This five-day geometry is rejected on Train-1. The positive H4 aggregate is not a candidate: it is six trades concentrated in two XRP series, below the frozen minimum, and does not clear monthly regularity. Do not shorten blocks or add confirmations after this result.

## Tests

`python3 -m pytest -q tests/test_sube_inv_fvg.py` passed: 4 tests. It checks complete epoch blocks, missing-block rejection, prefix invariance under appended future bars, frozen names/no midpoint geometry, and H4 alignment. `python3 scripts/f006_sube_inv_fvg_experiment.py` completed in 446.2 seconds; its checked manifest and raw/summary evidence are under `output/f006_sube_inv_fvg/`.
