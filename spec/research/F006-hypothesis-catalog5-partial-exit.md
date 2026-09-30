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

_(empty until the frozen Train-1 partial-exit grid is run)_

## Decision

_(empty until the frozen Train-1 partial-exit grid is run)_
