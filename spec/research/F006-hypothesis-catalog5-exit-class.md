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

_Filled in after the frozen Train-1 exit grid runs. Not run yet as of this freeze commit._

## Decision

_Filled in after Result. Not decided yet as of this freeze commit._
