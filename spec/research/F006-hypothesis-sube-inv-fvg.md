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

## Prior NO_TRAIL decision (superseded evaluation policy)

The original pass rejected this five-day geometry on density and legacy H2. The continuation instruction supersedes that sole-DNR decision: assess the frozen exits and sparse H2 before deciding. Entry rules and the original evidence remain unchanged.

## Continuation freeze: exits and sparse H2

Source: `/tmp/F006-continue-sube-exits-h2sparse.md` and `/tmp/F006-eval-policy-sparse-h2-and-exits-2026-09-29.md`. This extension is frozen before the continuation run; it is not a new entry hypothesis.

| Exit cell | activate_pct | trail_pct | take_profit_multiple |
| --- | ---: | ---: | --- |
| NO_TRAIL | 10.0 | 0.04 | None |
| TP_x2 | 10.0 | 0.04 | 2.0 |
| TRAIL_a0.06_t0.04 | 0.06 | 0.04 | None |
| TRAIL_a0.03_t0.02 | 0.03 | 0.02 | None |

Run all five frozen names × ten Train-1 series × four exits, plus DONCHIAN_55 on NO_TRAIL only. Use existing engine hooks and frozen runner constants/loaders without changing the shared harness or signal module. Reproduce the original NO_TRAIL rows exactly. No validation/holdout, entry retune, or new exit cells.

Rank cells by pooled trade-weighted win rate, both per signal and across all five names. H1 remains mean `train1_net_pnl > 0` over ten series per name/cell. Retain legacy H2 unchanged. For `h2_sparse_absent_zero_trade`, group closed-trade net PnL by exit calendar month in Europe/Warsaw (same timezone as legacy regularity); score only the twelve Train-1 months containing exits. Zero-exit months are ABSENT, not losing or scored. Require all scored months nonnegative, series DD <= 50%, Train-1 equity PnL >= 0, and at least one Train-1 exit. Exit-month realized PnL and Train-1 equity PnL are separate fields, not interchangeable.

Density below ten trades/series is reported as a sparsity flag, not a sole-DNR reason. Exits add no signal opportunities; report observed trade counts rather than assume shorter holding times cannot affect execution of later frozen opportunities. Report unconditional per-series H2 flags and counts conditional on H1 separately. Evidence goes in `output/f006_sube_inv_fvg/exit_grid/`.

## Continuation results and verdict

Execution commit: `f5e6d80` (recorded in every exit-grid manifest). The exit-only sibling `scripts/f006_sube_inv_fvg_exit_grid.py` completed 210 runs: 200 candidate cells and ten NO_TRAIL controls. All 60 original NO_TRAIL series match, including Train-1 PnL, trade counts, win rate, drawdown, equity, and legacy H2. The ten DONCHIAN_55 controls match the shared reference exactly. A separate check also reproduced all 720 original NO_TRAIL monthly equity PnLs within 1e-10. `sube_inv_fvg.py`, the shared harness, engine, and production catalog are unchanged.

Pooled trade-weighted win rate ranks TP_x2 **28.89%**, TRAIL_a0.03_t0.02 **26.67%**, TRAIL_a0.06_t0.04 **23.33%**, NO_TRAIL **6.67%**. Mean Train-1 PnL across all 50 candidate series is respectively **-$1.2920, -$3.1208, -$3.0357, +$3.4607**. This pooled description does not replace the per-name H1 test below. Each cell has 90 trades across 50 series (1.8 mean); every name retains its original trade count and signal opportunities. Exits did not fix sparsity.

Each row below is a ten-series pool. Positive mean PnL means H1 PASS, nonpositive means FAIL. H2 counts are unconditional legacy/sparse passing series; only H1-positive rows qualify for conditional H2. WR ordering is within each name; equal WR values are ties, not evidence of superiority.

| Signal / exit cell | Win rate | Mean Train-1 PnL | Legacy / sparse H2 |
| --- | ---: | ---: | ---: |
| SINV_FIRST_FVG / TP_x2 | 27.27% | -1.9004 | 0 / 0 |
| SINV_FIRST_FVG / TRAIL_a0.06_t0.04 | 27.27% | -3.6077 | 0 / 0 |
| SINV_FIRST_FVG / TRAIL_a0.03_t0.02 | 22.73% | -4.3070 | 0 / 0 |
| SINV_FIRST_FVG / NO_TRAIL | 0.00% | -7.1403 | 0 / 0 |
| SINV_FIRST_H4 / TP_x2 | 66.67% | +1.6071 | 2 / 2 |
| SINV_FIRST_H4 / TRAIL_a0.03_t0.02 | 66.67% | -0.2568 | 2 / 2 |
| SINV_FIRST_H4 / TRAIL_a0.06_t0.04 | 66.67% | +1.5586 | 2 / 2 |
| SINV_FIRST_H4 / NO_TRAIL | 33.33% | +41.4145 | 0 / 0 |
| SINV_FIRST_SMT / NO_TRAIL | 0.00% | -1.3298 | 0 / 0 |
| SINV_FIRST_SMT / TP_x2 | 0.00% | -1.3298 | 0 / 0 |
| SINV_FIRST_SMT / TRAIL_a0.03_t0.02 | 0.00% | -1.3298 | 0 / 0 |
| SINV_FIRST_SMT / TRAIL_a0.06_t0.04 | 0.00% | -1.3298 | 0 / 0 |
| SINV_MSS_CLOSE / TP_x2 | 27.78% | -2.9403 | 0 / 0 |
| SINV_MSS_CLOSE / TRAIL_a0.03_t0.02 | 27.78% | -5.6309 | 0 / 0 |
| SINV_MSS_CLOSE / TRAIL_a0.06_t0.04 | 19.44% | -7.3956 | 0 / 0 |
| SINV_MSS_CLOSE / NO_TRAIL | 5.56% | -10.1421 | 0 / 0 |
| SINV_MSS_IN_FVG / TP_x2 | 27.27% | -1.8968 | 2 / 2 |
| SINV_MSS_IN_FVG / TRAIL_a0.03_t0.02 | 22.73% | -4.0795 | 2 / 2 |
| SINV_MSS_IN_FVG / TRAIL_a0.06_t0.04 | 18.18% | -4.4038 | 0 / 0 |
| SINV_MSS_IN_FVG / NO_TRAIL | 9.09% | -5.4986 | 0 / 0 |

**Verdict:** retain SINV_FIRST_H4 with TP_x2 and TRAIL_a0.06_t0.04 for independent review under the revised policy, rather than sole-DNR on density. Both clear H1 and both H2 definitions; their passing series are XRPUSDT/60 and XRPUSDT/240, each with two trades and two scored exit months. They are not independent confirmations across assets: both timeframes trade XRP, and the entire name/cell has only six trades (0.6 per series). TP_x2 has a tied highest name-level WR and slightly higher aggregate PnL than the wider trail, not a proven statistical advantage. Neither is validated or authorized for live trading.

The other four names fail H1 in every cell. SINV_FIRST_H4 with the tighter trail also fails H1 despite its WR; NO_TRAIL H4 clears H1 but fails both H2 definitions. Sparse H2 and legacy H2 happen to select the same series here; absent-month semantics are separately tested rather than inferred from that coincidence. Density means remain FIRST_FVG 2.2, MSS_CLOSE 3.6, MSS_IN_FVG 2.2, FIRST_H4 0.6, FIRST_SMT 0.4. No sole density rejection, entry change, merge, or validation/holdout access occurred.

Evidence includes per-cell CSV/manifests, per-name and pooled rank tables, 2,520 dual-rule monthly rows, and 836 trade records (including the control) under `output/f006_sube_inv_fvg/exit_grid/`. Per-series and per-name maximum DD and full exit-mix histograms are retained in the CSVs. Focused tests: `python3 -m pytest -q tests/test_sube_exit_grid.py tests/test_sube_inv_fvg.py` → 12 passed; the sparse fixture proves an absent month is neutral, a losing exit-month fails, and an all-absent series cannot pass. Warm-up/boundary exclusion, Warsaw month assignment, DD/PnL gates, weighted ranking, and the NO_TRAIL mismatch guard are also checked.

## Original NO_TRAIL tests

`python3 -m pytest -q tests/test_sube_inv_fvg.py` passed: 4 tests. It checks complete epoch blocks, missing-block rejection, prefix invariance under appended future bars, frozen names/no midpoint geometry, and H4 alignment. `python3 scripts/f006_sube_inv_fvg_experiment.py` completed in 446.2 seconds; its checked manifest and raw/summary evidence are under `output/f006_sube_inv_fvg/`.
