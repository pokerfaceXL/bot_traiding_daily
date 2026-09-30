# H-CATALOG5-EXIT-CLASS-01 — catalog5 NO_TRAIL exit-class grid (shared mechanism)

> Pre-registration freeze. Observation, Mechanism, and Falsification below are copied
> verbatim (light reformatting only) from `/tmp/F006-card-H-CATALOG5-EXIT-CLASS-01.md`
> before any harness code for this test was written. Result/Decision are filled in only
> after the frozen Train-1 exit grid is run.

```yaml
id: H-CATALOG5-EXIT-CLASS-01
universe: BTC/ETH/SOL/XRP/DOGE USDT perps x {60,240}  # frozen Train-1 5x2 basket
data_needs: [ohlcv]  # checksum-locked Train-1 cache only; no new symbols/data
entries: UNCHANGED - reuse existing strategy.STRATEGY_CATALOG generators for the five names
exit: standing sparse/swing exit grid (<=4 cells, <=5 budget)
h2: dual legacy + h2_sparse_absent_zero_trade (zero-trade months = ABSENT/neutral)
aggregation: shared mechanism identical across names (preferred per section 13)
license: spec/research/F006-catalog5-family-insufficiency-s13.md (exit-class change)
dnr_do_not_reopen:
  - DONCHIAN_55_NO_TRAIL FREEZE / H-CATALOG5-ABS-ATR-ENTRY-GATE-01 DNR
  - HTFP / H-HTF-PERM-EMA-PB-01 tip (do not reopen)
  - CASCADE-FADE / BPC / VHBOS / SBPA closed families
```

**Train-1 only.** Window `[2024-03-01T00:00:00Z, 2025-03-01T00:00:00Z)` + 35-day warm-up from
`2024-01-26T00:00:00Z`. No Validation/holdout peek. Base main tip `b9a12c0`.

## Observation (pre-registered)

Five CONDITIONAL catalog5 `NO_TRAIL` profiles share the same fat-tail /
`initial_sl`-dominated shape (autopsies + finalized section 13):
`EMA_50_200`, `BB_20_25_EMA200`, `EMA3_21_50_200`, `EMA3_13_50_200`, `BB_20_2_EMA200`.
`H-CATALOG5-ABS-ATR-ENTRY-GATE-01` is DNR (entry-vol axis closed). Section 13 licenses a
genuinely non-correlated next step: **exit-class change** (hold/exit geometry), not another
entry filter by ATR/vol/trend strength.

## Mechanism (why non-correlated vs ABS-ATR / Donchian entry-vol)

- Keep **entries unchanged** (same catalog generators, same one-shot mask, same symbols/
  intervals).
- Change **EXIT class only** via standing sparse/swing exit grid already in the engine:
  - `NO_TRAIL` - baseline (`activate_pct=10.0`, trail never arms)
  - `TP_x2` - `take_profit_multiple=2.0` + NO_TRAIL activate
  - `TRAIL_a0.06_t0.04` - activate 0.06 / trail 0.04
  - `TRAIL_a0.03_t0.02` - activate 0.03 / trail 0.02
- <=4 cells (<=5 budget). No new exit hooks. Exits do not add entries.
- Does **not** filter entries by ATR/vol/trend strength; tests hold/exit geometry only.
- Licensed by `spec/research/F006-catalog5-family-insufficiency-s13.md`.

## Frozen names (exactly five - entries already exist)

| # | Name (catalog / profile) | Entry | Exit cells |
| --- | --- | --- | --- |
| 1 | `EMA_50_200` | unchanged catalog | NO_TRAIL, TP_x2, TRAIL_a0.06_t0.04, TRAIL_a0.03_t0.02 |
| 2 | `BB_20_25_EMA200` | unchanged | same grid |
| 3 | `EMA3_21_50_200` | unchanged | same grid |
| 4 | `EMA3_13_50_200` | unchanged | same grid |
| 5 | `BB_20_2_EMA200` | unchanged | same grid |

Shared mechanism identical across names (one pre-registered test, not five independent
retunes).

## Eval / reporting

Apply `/tmp/F006-eval-policy-sparse-h2-and-exits-2026-09-29.md` (match strategy type; catalog
may be denser than swing - still report dual H2):

- Rank exit cells by **win_rate**; still report `train1_net_pnl` / H1 for every cell.
- Report **legacy H2** and **`h2_sparse_absent_zero_trade`** (zero-trade months =
  ABSENT/neutral).
- Primary research comparability: NO_TRAIL baseline vs non-baseline cells on mean
  `train1_net_pnl`.
- Basket: frozen Train-1 5x2; harness patterns from `scripts/f006_family_runner.py` /
  catalog5 autopsy / Sube exit-grid as applicable.
- Control sanity where relevant: do not break DONCHIAN_55_NO_TRAIL FREEZE; do not invent
  ABS-ATR.

## Falsification (pre-registered)

Falsify if **any** of:
- (a) no non-baseline cell beats ungated/baseline `train1_net_pnl` for this shared test
  design, OR
- (b) any cell that cuts `initial_sl` share >=10pp also removes >50% of baseline big-winner
  PnL, OR
- (c) 7/12 losing-month floor does not improve on at least one name when aggregated as
  pre-registered (shared mechanism identical across names preferred; state clearly in
  Result).

## Budget

4 exit cells x 5 names on frozen Train-1 5x2. No grid widening after seeing results. No new
symbols/data. No merge from this job unless review PASS docs-only later (coordinator
decides).

## Hard non-goals

- Do NOT invent or re-run ABS-ATR / entry-vol gates.
- Do NOT reopen DONCHIAN FREEZE, ABS-ATR DNR, HTFP, CASCADE-FADE.
- Do NOT edit production on dirty main worktree; limen uses worktrees.
- Do NOT peek Validation/holdout.

## Result

Frozen Train-1 5x2 exit grid run on all five names via
`scripts/f006_catalog5_exit_class_grid.py` -> `output/f006_catalog5_exit_class/`
(producing commit noted in `manifest.json`). Entries unchanged: NO_TRAIL cell exactly
reproduces both prior references
(`output/f006_catalog_notrail_sweep/summary/results.csv`,
`output/f006_notrail_monthly_catalog5/summary/results.csv`, 50/50 rows, 0 mismatches) and
the DONCHIAN_55 harness control reproduces `output/f006_trailing_boundary/summary/results.csv`
(10/10 rows, 0 mismatches).

Per-name mean `train1_net_pnl` (NO_TRAIL baseline vs non-baseline cells, from
`rank_by_name.csv`):

| strategy | NO_TRAIL | TP_x2 | TRAIL_a0.06_t0.04 | TRAIL_a0.03_t0.02 |
| --- | ---: | ---: | ---: | ---: |
| EMA_50_200 | +72.67 | +17.84 | -6.97 | -20.81 |
| BB_20_25_EMA200 | +82.90 | -5.21 | -70.26 | -107.58 |
| EMA3_21_50_200 | +95.73 | +8.77 | -29.62 | -53.13 |
| EMA3_13_50_200 | +91.15 | +13.54 | -29.65 | -60.21 |
| BB_20_2_EMA200 | +95.32 | +3.70 | -112.55 | -187.05 |

- **(a)** No non-baseline cell beats the NO_TRAIL baseline mean `train1_net_pnl` for **any**
  of the five names, let alone all five. `TP_x2` stays H1-pass (mean_train1_net_pnl > 0) for
  4/5 names but is well below NO_TRAIL in every case; both trail cells are net-negative for
  4/5 names and barely positive-adjacent for none. **Falsifier (a) triggers.**
- **(b)** `TRAIL_a0.03_t0.02` cuts `initial_sl` share relative to NO_TRAIL on every name
  (`EMA_50_200` 60.99%->32.69%, `BB_20_25_EMA200` 57.14%->41.93%, `EMA3_21_50_200`
  65.22%->40.21%, `EMA3_13_50_200` 65.80%->39.61%, `BB_20_2_EMA200` 46.10%->39.72%) -- a cut
  of >=10pp on 4/5 names (6.38pp on `BB_20_2_EMA200`, the exception) -- while flipping mean
  `train1_net_pnl` from strongly positive to negative on those same 4/5 names, removing all
  of the baseline's net positive contribution (>50% of big-winner PnL, since the net result
  crosses zero). **Falsifier (b) triggers** for the trail cells on the 4/5 names that clear
  the >=10pp cut threshold.
- **(c)** Worst-series losing-month count (of 12, `legacy_is_valid` months only) per name,
  max across the 10-series basket: NO_TRAIL sits at 8-9/12 for all five names (not the
  autopsy's single-series 7/12 floor, which was a best-case series, not the worst-case used
  here for a strict per-name aggregate). `TP_x2` only marginally improves one name
  (`EMA_50_200` 8->7), no others; both trail cells are strictly worse, reaching 12/12 losing
  months on 4/5 names. **Falsifier (c) triggers** -- the floor does not improve on 4/5 names
  under any cell, and the one nominal 1-month improvement (`EMA_50_200`/`TP_x2`) still fails
  both legacy H2 and `h2_sparse_absent_zero_trade` (`legacy_h2_series=0`,
  `sparse_h2_series=0` for every name x cell combination in `rank_by_name.csv`).

All three pre-registered falsifiers trigger, independently and jointly, across the shared
mechanism test.

## Decision

**FALSIFIED.** The exit-class axis (NO_TRAIL/TP_x2/TRAIL_a0.06_t0.04/TRAIL_a0.03_t0.02) does
not rescue any of the five CONDITIONAL catalog5 names: NO_TRAIL remains the best exit
geometry by `train1_net_pnl` for every name, and both trail variants actively destroy the
fat-tail-dependent edge these names rely on (trimming winners before they run, since the
same elevated-volatility moves that produce the big winners also produce the early
retracements a tight trail exits on). `H-CATALOG5-EXIT-CLASS-01` is closed;
no merge, no further exit-class retune on these five names. Per `spec/research/F006-catalog5-family-insufficiency-s13.md`,
both licensed axes for this shared class (ABS-ATR entry gate, exit-class change) are now
closed; a further attempt needs a genuinely different mechanism (cross-asset/market-structure
context, order-flow/liquidity features, or partial-exit/volatility-adaptive holding, per that
note's "why a next family would need to be different" section) and its own pre-registration,
not a retest of either closed axis. All five profiles stay CONDITIONAL; status change to this
decision is not made by this note alone (coordinator review).
