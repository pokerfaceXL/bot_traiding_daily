# H-CATALOG5-PARTIAL-EXIT-01 — catalog5 NO_TRAIL partial scale-out (shared mechanism)

> Pre-registration freeze. Observation, Mechanism, frozen cells, Eval, and Falsification below
> are copied verbatim (light reformatting only) from `/tmp/F006-card-H-CATALOG5-PARTIAL-EXIT-01.md`
> before any engine hook or harness code for this test was written. Result/Decision are filled
> in only after the frozen Train-1 partial-exit grid is run.

```yaml
id: H-CATALOG5-PARTIAL-EXIT-01
name: Partial scale-out exits on five CONDITIONAL catalog5 NO_TRAIL profiles
universe: BTC/ETH/SOL/XRP/DOGE USDT perps x {60,240}  # frozen Train-1 5x2 basket
data_needs: [ohlcv]  # checksum-locked Train-1 cache only; no new symbols/data
entries: UNCHANGED - reuse existing strategy.STRATEGY_CATALOG generators for the five names
exit: partial scale-out grid (<=5 cells) - different problem class than full-position EXIT-CLASS-01
h2: dual legacy + h2_sparse_absent_zero_trade (zero-trade months = ABSENT/neutral)
aggregation: shared mechanism identical across names (preferred per section 13)
license: spec/research/F006-catalog5-family-insufficiency-s13.md (named exit mechanism change incl. partial exits)
prior_closed:
  - H-CATALOG5-EXIT-CLASS-01 FALSIFIED (full-position TP/TRAIL vs NO_TRAIL) - tip 923de9c; do not retest that grid
dnr_do_not_reopen:
  - DONCHIAN_55_NO_TRAIL FREEZE / H-CATALOG5-ABS-ATR-ENTRY-GATE-01 DNR
  - H-CATALOG5-EXIT-CLASS-01 full-position TP/TRAIL axis (closed)
  - HTFP / H-HTF-PERM-EMA-PB-01 tip (do not reopen)
  - CASCADE-FADE / BPC / VHBOS / SBPA closed families
```

**Train-1 only.** Window `[2024-03-01T00:00:00Z, 2025-03-01T00:00:00Z)` + 35-day warm-up from
`2024-01-26T00:00:00Z`. No Validation/holdout peek. Base tip `923de9c` (`origin/main`;
EXIT-CLASS-01 already FALSIFIED on tip).

## Observation (pre-registered)

Five CONDITIONAL catalog5 `NO_TRAIL` profiles share the same fat-tail / `initial_sl`-dominated
shape: `EMA_50_200`, `BB_20_25_EMA200`, `EMA3_21_50_200`, `EMA3_13_50_200`, `BB_20_2_EMA200`.

`H-CATALOG5-ABS-ATR-ENTRY-GATE-01` is DNR (entry-vol axis closed).
`H-CATALOG5-EXIT-CLASS-01` is **FALSIFIED**: full-position `TP_x2` / `TRAIL_a0.06_t0.04` /
`TRAIL_a0.03_t0.02` replacements of `NO_TRAIL` lost to baseline on all five names (falsifiers
a/b/c). That test only covered *full-position* exit geometry.

Section 13 (`spec/research/F006-catalog5-family-insufficiency-s13.md`) names exit-mechanism
change including **partial exits** as a different problem class than entry filtering — and
distinct from full-position TP/TRAIL replacement: scale-out can bank part of a runner without
requiring the whole position to exit on the first +NR touch / trail arm.

## Mechanism (shared across five names — identical design)

- Keep **entries unchanged** (same catalog generators, same one-shot mask, same
  symbols/intervals).
- On open: **partial scale-out** — close a fixed fraction of the position at a multiple of
  initial R (R = initial SL distance at entry), manage the **remainder** with either NO_TRAIL
  (stop only) or a single trail cell.
- Shared mechanism identical across the five names (one pre-registered test, not five
  independent retunes).
- Does **not** filter entries by ATR/vol/trend strength; does **not** retest the closed
  full-position EXIT-CLASS-01 cell set as the primary claim (baseline NO_TRAIL full is the
  control only).

### Frozen cells (exactly <=5)

| # | Cell id | Scale-out | Remainder |
| --- | --- | --- | --- |
| 1 | `NO_TRAIL` | none (full position) | NO_TRAIL — **control / baseline** |
| 2 | `PARTIAL_50_at_1R_NO_TRAIL` | close 50% at +1R | remainder NO_TRAIL (stop only) |
| 3 | `PARTIAL_50_at_1R_TRAIL_a0.06_t0.04` | close 50% at +1R | remainder TRAIL activate 0.06 / trail 0.04 |
| 4 | `PARTIAL_50_at_1.5R_NO_TRAIL` | close 50% at +1.5R | remainder NO_TRAIL |
| 5 | `PARTIAL_50_at_2R_NO_TRAIL` | close 50% at +2R | remainder NO_TRAIL |

R = distance from entry to initial stop (`max_sl_pct` / effective initial SL distance as used
by the engine for that trade). Partial fill must be recorded in trades/exit-mix so scale-out
PnL is attributable (e.g. partial take vs remainder exit_reason).

Implementation note: engine has no partial-exit hook (only full-position
`take_profit_multiple` / `activate_pct` / `trail_pct`). An **additive** research hook for
partial fraction + R-multiple is in-scope for this hyp; must not break NO_TRAIL full baseline
reproduction against prior catalog5 references. Extend `backtest_engine.run_backtest` /
harness rather than drive-by `strategy.py` entry changes.

## Frozen names (exactly five — entries already exist)

| # | Name | Entry | Exit cells |
| --- | --- | --- | --- |
| 1 | `EMA_50_200` | unchanged catalog | all five cells above |
| 2 | `BB_20_25_EMA200` | unchanged | same grid |
| 3 | `EMA3_21_50_200` | unchanged | same grid |
| 4 | `EMA3_13_50_200` | unchanged | same grid |
| 5 | `BB_20_2_EMA200` | unchanged | same grid |

## Eval / reporting

Apply `/tmp/F006-eval-policy-sparse-h2-and-exits-2026-09-29.md` (dual H2 always):

- Rank exit cells by **win_rate**; still report `train1_net_pnl` / H1 for every cell.
- Report **legacy H2** and **`h2_sparse_absent_zero_trade`** (zero-trade months =
  ABSENT/neutral).
- Primary research comparability: baseline `NO_TRAIL` full vs partial cells on mean
  `train1_net_pnl` across the shared design.
- Report `initial_sl_share` and big-winner PnL retention for falsifier (b) (trade-level
  Train-1 winners; definition documented in Result, consistent with EXIT-CLASS-01 / autopsy
  practice).
- Basket: frozen Train-1 5x2; harness patterns from `scripts/f006_family_runner.py` /
  `scripts/f006_catalog5_exit_class_grid.py`.
- Control sanity: DONCHIAN_55_NO_TRAIL FREEZE not broken; ABS-ATR not invented; EXIT-CLASS-01
  full TP/TRAIL grid not re-run as a claim.

## Falsification (pre-registered)

Falsify if **any** of:
- (a) no partial cell beats baseline mean `train1_net_pnl` across the shared design, OR
- (b) any cell that cuts `initial_sl` share >=10pp also removes >50% of baseline big-winner
  PnL, OR
- (c) 7/12 losing-month floor does not improve.

## Budget

<=5 cells x 5 names on frozen Train-1 5x2. No grid widening after seeing results. No new
symbols/data. No merge from this job unless review PASS later (coordinator decides).

## Hard non-goals

- Do NOT invent or re-run ABS-ATR / entry-vol gates.
- Do NOT reopen DONCHIAN FREEZE, ABS-ATR DNR, HTFP, CASCADE-FADE.
- Do NOT retest H-CATALOG5-EXIT-CLASS-01 full-position TP/TRAIL as the experiment
  (closed/FALSIFIED).
- Do NOT edit production on dirty main worktree; limen uses worktrees.
- Do NOT peek Validation/holdout.

## Result

Frozen Train-1 5x2 partial scale-out grid run on all five names via
`scripts/f006_catalog5_partial_exit_grid.py` -> `output/f006_catalog5_partial_exit/`
(producing commit `ae5212d` in `manifest.json`; engine hook `097e0ba`:
`backtest_engine.run_backtest(partial_fraction=, partial_r_multiple=)` +
`equity.Portfolio.split_position`, default-None path proven identical by
`tests/test_backtest_engine.py::test_partial_exit_none_matches_call_without_the_parameters`).
Entries unchanged: the `NO_TRAIL` cell exactly reproduces both prior catalog5 references
(`output/f006_catalog_notrail_sweep/summary/results.csv`,
`output/f006_notrail_monthly_catalog5/summary/results.csv`: 50/50 rows, 0 mismatches) and the
DONCHIAN_55 harness control reproduces `output/f006_trailing_boundary/summary/results.csv`
(10/10 rows, 0 mismatches). One-shot violations: 0. EXIT-CLASS-01's full TP/TRAIL cells were
not re-run; no ABS-ATR gate.

Definitions (frozen in the harness docstring before the run): **entry-level** accounting (the
`partial_take` leg + remainder leg of one `parent_id` = one trade for win_rate / n_trades);
`initial_sl_share` = entries ending at `initial_sl` with no partial banked (full-R losers);
**big-winner retention** = per name, the top-decile (ceil 10%) NO_TRAIL entries by net_pnl
pooled over the 10 series, keyed (symbol, interval, entry_time) -- cell net_pnl of those same
entries / baseline net_pnl; losing-month floor = legacy-valid Train-1 months with equity
net_pnl < 0, per name worst (max) / best (min) series. Sparse months bucket each leg by its
own exit month.

Shared-design mean `train1_net_pnl` (all 5 names x 10 series): NO_TRAIL **+87.55**;
P50@2R +51.08; P50@1.5R +49.19; P50@1R +44.88; P50@1R+TRAIL -32.88.

Per name x cell (`falsifiers_by_name.csv`; sorted by win_rate within name; cells: P50@xR =
`PARTIAL_50_at_xR_NO_TRAIL`, P50@1R+TRAIL = `PARTIAL_50_at_1R_TRAIL_a0.06_t0.04`):

| strategy | cell | win_rate % | mean train1_net_pnl | entries | initial_sl % | SL cut pp | big-winner retention % | losing months worst/best | legacy/sparse H2 series |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| BB_20_25_EMA200 | P50@1.5R | 45.89 | +47.48 | 560 | 43.9 | +13.2 | 56.1 | 8/3 | 0/0 |
| BB_20_25_EMA200 | P50@2R | 38.39 | +47.68 | 560 | 48.8 | +8.4 | 58.2 | 8/4 | 0/0 |
| BB_20_25_EMA200 | P50@1R+TRAIL | 35.28 | -48.50 | 927 | 42.9 | +14.2 | 12.4 | 11/7 | 0/0 |
| BB_20_25_EMA200 | P50@1R | 35.00 | +41.85 | 560 | 38.6 | +18.6 | 53.9 | 8/2 | 0/0 |
| BB_20_25_EMA200 | NO_TRAIL | 25.54 | +82.90 | 560 | 57.1 | +0.0 | 100.0 | 8/3 | 0/0 |
| BB_20_2_EMA200 | P50@1.5R | 40.00 | +47.93 | 820 | 38.3 | +7.8 | 56.8 | 8/4 | 0/0 |
| BB_20_2_EMA200 | P50@1R | 36.34 | +41.22 | 820 | 34.8 | +11.3 | 54.4 | 8/4 | 0/0 |
| BB_20_2_EMA200 | P50@2R | 35.24 | +53.17 | 820 | 40.5 | +5.6 | 59.3 | 9/4 | 0/0 |
| BB_20_2_EMA200 | P50@1R+TRAIL | 34.74 | -79.03 | 1448 | 39.6 | +6.5 | 13.1 | 12/8 | 0/0 |
| BB_20_2_EMA200 | NO_TRAIL | 24.88 | +95.32 | 820 | 46.1 | +0.0 | 100.0 | 9/5 | 0/0 |
| EMA3_13_50_200 | P50@1.5R | 47.71 | +53.34 | 459 | 43.4 | +22.4 | 54.5 | 9/2 | 0/0 |
| EMA3_13_50_200 | P50@2R | 40.96 | +55.21 | 459 | 48.6 | +17.2 | 56.2 | 8/2 | 0/0 |
| EMA3_13_50_200 | P50@1R+TRAIL | 39.11 | -17.32 | 698 | 39.4 | +26.4 | 8.4 | 11/4 | 0/0 |
| EMA3_13_50_200 | P50@1R | 26.36 | +50.55 | 459 | 35.1 | +30.7 | 52.9 | 9/4 | 0/0 |
| EMA3_13_50_200 | NO_TRAIL | 20.26 | +91.15 | 459 | 65.8 | +0.0 | 100.0 | 9/4 | 0/0 |
| EMA3_21_50_200 | P50@1.5R | 47.14 | +53.93 | 437 | 44.6 | +20.6 | 54.4 | 9/2 | 0/0 |
| EMA3_21_50_200 | P50@2R | 39.59 | +54.07 | 437 | 50.1 | +15.1 | 56.0 | 9/2 | 0/0 |
| EMA3_21_50_200 | P50@1R+TRAIL | 39.14 | -18.43 | 626 | 40.3 | +25.0 | 8.1 | 9/4 | 0/0 |
| EMA3_21_50_200 | P50@1R | 27.23 | +50.21 | 437 | 37.1 | +28.1 | 52.8 | 9/4 | 0/0 |
| EMA3_21_50_200 | NO_TRAIL | 21.05 | +95.73 | 437 | 65.2 | +0.0 | 100.0 | 9/3 | 0/0 |
| EMA_50_200 | P50@1.5R | 48.08 | +43.27 | 364 | 40.9 | +20.1 | 54.5 | 8/3 | 0/0 |
| EMA_50_200 | P50@1R+TRAIL | 42.03 | -1.12 | 364 | 32.7 | +28.3 | 8.6 | 7/2 | 0/0 |
| EMA_50_200 | P50@2R | 41.76 | +45.26 | 364 | 45.9 | +15.1 | 56.2 | 8/3 | 0/0 |
| EMA_50_200 | P50@1R | 29.12 | +40.58 | 364 | 33.2 | +27.7 | 52.9 | 8/3 | 0/0 |
| EMA_50_200 | NO_TRAIL | 22.25 | +72.67 | 364 | 61.0 | +0.0 | 100.0 | 8/3 | 0/0 |

WR rank: `PARTIAL_50_at_1.5R_NO_TRAIL` wins win_rate on every name (40-48% vs NO_TRAIL 20-26%)
while roughly halving `train1_net_pnl`. Density: entries are identical to NO_TRAIL for the
three NO_TRAIL-remainder cells; the trail-remainder cell frees the position earlier and takes
more entries on 4/5 names (exits add no signals, only re-occupy one-shot calls sooner).

- **(a) triggers.** No partial cell beats baseline mean `train1_net_pnl` across the shared
  design (best P50@2R +51.08 vs +87.55), nor on any single name. The three NO_TRAIL-remainder
  cells stay H1-pass on all five names; the trail-remainder cell is H1-fail on all five.
- **(b) triggers.** `PARTIAL_50_at_1R_TRAIL_a0.06_t0.04` cuts `initial_sl` share by >=10pp on
  4/5 names (EMA_50_200 +28.3, BB_20_25_EMA200 +14.2, EMA3_21_50_200 +25.0, EMA3_13_50_200
  +26.4) while keeping only 8-12% of baseline big-winner PnL (>50% removed). The
  NO_TRAIL-remainder cells cut the share by >=10pp on most names but retain 52.8-59.3% of
  big-winner PnL -- just above the 50% line, i.e. they give up ~half of every runner by
  construction (50% banked at +1-2R vs runners that go far beyond), which is the whole
  shortfall under (a).
- **(c) does not trigger** under the EXIT-CLASS-01 aggregation (worst-series losing months
  improve on at least one name): worst-series count drops by 1 month on EMA3_13_50_200/P50@2R
  (9->8), BB_20_2_EMA200/P50@1R and P50@1.5R (9->8), and EMA_50_200/P50@1R+TRAIL (8->7).
  Improvements are single-month, and legacy H2 and `h2_sparse_absent_zero_trade` pass on
  **0 series** for every name x cell (as under NO_TRAIL).

## Decision

**FALSIFIED** (falsifiers (a) and (b) trigger; (c) alone would not). Partial scale-out raises
win_rate (the standing-policy rank key) but does not rescue any of the five CONDITIONAL
catalog5 names: banking half at +1R/+1.5R/+2R trades roughly half of the fat-tail runner PnL
for stop-outs avoided, net-negative relative to full-position NO_TRAIL on every name, and a
trailed remainder destroys the big winners outright (as the full-position trail did in
EXIT-CLASS-01). NO_TRAIL full remains the best exit geometry by `train1_net_pnl` for all five
names. `H-CATALOG5-PARTIAL-EXIT-01` is closed; no grid widening, no retune of fraction/R
after seeing Train-1. The additive engine hook stays available (default-None path identical).
All five profiles stay CONDITIONAL; any status change is for coordinator review, not this
note. No merge from this job.
