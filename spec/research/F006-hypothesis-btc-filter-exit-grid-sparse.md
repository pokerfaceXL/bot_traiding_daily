# F006 — BTC-FILTER standing exit grid + dual sparse H2 (H-BTC-FILTER-EXIT-GRID-SPARSE-01)

> Pre-registered 2026-09-30 (Europe/Warsaw) on base `d016659` before any exit-grid
> harness code or Train-1 run. Sections Observation through Falsification are copied
> from the coordinator card `/tmp/F006-card-H-BTC-FILTER-EXIT-GRID-SPARSE-01.md`
> (ticket S7-EXIT-GRID). Parent: H-BTC-FILTER-01 (`spec/research/F006-hypothesis-btc-filter.md`,
> tip `e518682`). Train-1 only: `[2024-03-01T00:00:00Z, 2025-03-01T00:00:00Z)`.
> Validation and holdout bars are neither loaded nor inspected. Exit-only (§8 Exit
> refinement): entries are the unchanged parent `btc_filter.py`.

**Sentence (protocol form):** Na podstawie wyniku X (H-BTC-FILTER-01 H1 pass / H2 fail
na NO_TRAIL; N20 mean Train-1 ≈ +73.65) podejrzewam Y (nierówne miesiące przez exit
geometry / fat winners cut by NO_TRAIL), dlatego testuję Z (≤4-cell exit grid +
h2_sparse_absent_zero_trade).

## Observation

Frozen-schema digest ranks `BTC_FILTER_ER20_DONCHIAN_20` highest among Level-B H1-pass / H2-falsified families that have **not** yet run the standing sparse/swing exit grid (`NO_TRAIL`, `TP_x2`, `TRAIL_a0.06_t0.04`, `TRAIL_a0.03_t0.02` + `h2_sparse_absent_zero_trade`). Digest mean Train-1: N20 +73.6501 (59.8 trades/series, WR≈20.1%), N10 +60.57, N5 +44.59. Family H2 status: **falsified** (legacy promotion_pass = 0; all series have 12 valid months but only ~2/10 are all-months-nonnegative).

Per COORDINATOR_RESEARCH_PROTOCOL §7: aggregate-positive with uneven months → diagnose before abandoning. §8 Exit refinement: change only post-entry geometry. Standing eval policy requires the exit grid + dual H2 before sole-DNR on legacy monthly H2.

This is **not** a new entry family. Entries stay exactly tip `e518682` / `btc_filter.py` from limen branch `limen/2026-09-29-f006-btc-filter-6a2d2643` (or byte-identical autopsy copy `output/f006_signal_autopsy/sources/btc_filter.py`).

---

## Hypothesis

**H1 (per exit cell, same as parent).** At least one of the three frozen BTC-FILTER names has mean Train-1 `train1_net_pnl > 0` over the fixed ten-series pool under that exit cell. Primary gate geometry for cross-cell comparability remains **NO_TRAIL** (must reproduce parent NO_TRAIL rows within harness tolerance).

**H2 (conditional on H1, dual).** For each H1-clearing name×cell, report:
1. **legacy H2** — unchanged 12-valid-month promotion checklist
2. **`h2_sparse_absent_zero_trade`** — score only exit-calendar months (Europe/Warsaw) with `n_trades > 0`; zero-trade months = ABSENT/neutral; require all scored months `net_pnl >= 0`, series DD ≤ 50%, Train-1 equity PnL ≥ 0, ≥1 Train-1 exit

**Falsify exit cells (§8):** a TP/trail cell that improves win_rate by killing fat winners such that mean Train-1 PnL falls below the NO_TRAIL cell for the same name is a **regression** (do not promote on WR alone). Rank cells by pooled trade-weighted win_rate; still report train1_net_pnl / H1 for every cell.

---

## Frozen names (exactly three — parent set; no expansion)

| Name | Alt prior-channel N | BTC ER window / threshold |
| --- | ---: | --- |
| `BTC_FILTER_ER20_DONCHIAN_5` | 5 | 20 / ±0.30 |
| `BTC_FILTER_ER20_DONCHIAN_10` | 10 | 20 / ±0.30 |
| `BTC_FILTER_ER20_DONCHIAN_20` | 20 | 20 / ±0.30 |

Trade universe: ETH/SOL/XRP/DOGE only. BTC permission-only forced-flat diagnostics. Basket = original parent 5×2 Train-1 (same as `run_family`).

---

## Frozen exit cells (exactly four)

| Exit cell | activate_pct | trail_pct | take_profit_multiple |
| --- | ---: | ---: | --- |
| NO_TRAIL | 10.0 | 0.04 | None |
| TP_x2 | 10.0 | 0.04 | 2.0 |
| TRAIL_a0.06_t0.04 | 0.06 | 0.04 | None |
| TRAIL_a0.03_t0.02 | 0.03 | 0.02 | None |

Use existing engine hooks only. Entries computed once; exits do not add signal opportunities. Reproduce original NO_TRAIL rows exactly. DONCHIAN_55 control on NO_TRAIL only (~+58.387 mean Train-1).

---

## Method

1. **Docs first:** write `spec/research/F006-hypothesis-btc-filter-exit-grid-sparse.md` (Observation→Falsification/Method from this card; leave Result/Decision empty until after run). Also restore parent hyp note `spec/research/F006-hypothesis-btc-filter.md` from tip `e518682` / limen branch if absent on base (read-only provenance; do not edit parent freeze).
2. Restore `btc_filter.py` + original experiment unit tests from tip `e518682` / branch `limen/2026-09-29-f006-btc-filter-6a2d2643` (or autopsy source) **unchanged**.
3. Add sibling exit-grid script patterned on `scripts/f006_sube_inv_fvg_exit_grid.py` → `scripts/f006_btc_filter_exit_grid.py` writing `output/f006_btc_filter/exit_grid/`.
4. Run Train-1 only; dual H2; rank tables; manifest records producing commit.
5. Targeted pytest for sparse-month ABSENT vs scored and NO_TRAIL reproduction. Stop when docs+harness+evidence committed on job branch. No merge. No follow-up spawn.

---

## Falsification

- H1 falsified for a cell if no frozen name has mean Train-1 > 0 under that cell.
- H2 falsified if every H1-clearer fails both legacy and sparse H2.
- Exit regression: TP/trail cell with higher WR but lower mean Train-1 than NO_TRAIL for the same name = falsified as improvement (protocol §8).
- Any entry retune, new N/ER threshold, BTC trade, catalog5/ORB/ABS-ATR/Donchian FREEZE reopen, holdout peek, or merge invalidates the run.

## Run_id

`f006_btc_filter/exit_grid`, producing commit `853ec73` (recorded in
`output/f006_btc_filter/exit_grid/manifest.json`), script
`scripts/f006_btc_filter_exit_grid.py`, bounded Train-1 cache checksums as in the
parent manifest; executed 2026-09-30. 130 runs = 3 names × 4 cells × 10 series +
DONCHIAN_55 × NO_TRAIL × 10.

## Result

Integrity: NO_TRAIL reproduced all 30 parent candidate rows plus 10 DONCHIAN_55
rows exactly (40/40 compared, 0 mismatches on n_calls, trades, wins, WR, net and
Train-1 PnL, DD, final equity, valid months, month sign, legacy H2). DONCHIAN_55
harness control 10/10 matched `output/f006_trailing_boundary` (mean Train-1
`+58.387`). No one-shot violation; BTC rows had zero calls and zero trades in every cell.

Rank by trade-weighted win_rate (ten-row mean Train-1 PnL, H1; Δ vs NO_TRAIL same name):

| Name | Cell | WR % | mean Train-1 | H1 | Δ vs NO_TRAIL | trades/series | max DD % | §8 regression |
| --- | --- | ---: | ---: | --- | ---: | ---: | ---: | --- |
| N5 | TP_x2 | 35.34 | −14.85 | fail | −59.44 | 124.8 | 21.2 | yes |
| N5 | TRAIL_a0.03_t0.02 | 34.74 | −161.12 | fail | −205.71 | 149.4 | 62.7 | yes |
| N5 | TRAIL_a0.06_t0.04 | 30.83 | −106.06 | fail | −150.65 | 115.8 | 37.8 | yes |
| N5 | NO_TRAIL | 26.92 | +44.59 | pass | 0 | 79.5 | 20.8 | — |
| N10 | TP_x2 | 36.11 | −8.10 | fail | −68.67 | 108.0 | 19.2 | yes |
| N10 | TRAIL_a0.03_t0.02 | 34.97 | −137.51 | fail | −198.07 | 128.4 | 55.2 | yes |
| N10 | TRAIL_a0.06_t0.04 | 31.54 | −90.68 | fail | −151.25 | 100.5 | 33.6 | yes |
| N10 | NO_TRAIL | 26.83 | +60.57 | pass | 0 | 69.7 | 20.6 | — |
| N20 | TP_x2 | 36.33 | −3.21 | fail | −76.86 | 95.8 | 21.1 | yes |
| N20 | TRAIL_a0.03_t0.02 | 35.86 | −118.17 | fail | −191.82 | 114.9 | 49.6 | yes |
| N20 | TRAIL_a0.06_t0.04 | 30.79 | −79.17 | fail | −152.82 | 89.0 | 34.9 | yes |
| N20 | NO_TRAIL | 26.76 | +73.65 | pass | 0 | 59.8 | 20.7 | — |

- **H1 per cell:** passes only under NO_TRAIL (all three names). TP_x2,
  TRAIL_a0.06_t0.04 and TRAIL_a0.03_t0.02 are H1-falsified for every name.
- **§8 exit regression:** every TP/trail cell raises WR (+4 to +9.5 pp) while
  cutting mean Train-1 PnL below NO_TRAIL for the same name — all nine are
  regressions. Mechanism is the suspected one, inverted: N20 NO_TRAIL has 27 trades
  > $20 (largest `+267.64`, XRP/240); no TP/trail cell has any trade > $20 (largest
  `+5.69` TP_x2, `+16.16` a0.06). The edge *is* the fat winners that NO_TRAIL's
  signal-reverse exit lets run. Earlier exits free the one-shot slot sooner, so
  realized trades rise (n_calls unchanged, trades ≤ calls verified) — exits do not
  add entry opportunities.
- **H2 (dual) for H1-clearers (NO_TRAIL × 3 names):** legacy H2 0/10 series per
  name (reproduces parent). `h2_sparse_absent_zero_trade` also 0/10: alt series
  score 11–12 exit months under NO_TRAIL (density 60–80 trades/series; no sparsity
  to forgive) and the best series still have 3 losing exit-months (N10 DOGE/60,
  N10 ETH/60, N20 DOGE/60). BTC rows fail sparse H2 by rule (zero trades).
  Density note: not sparse — mean 59.8–79.5 trades/series under NO_TRAIL;
  density is not a DNR reason here.

Evidence: `output/f006_btc_filter/exit_grid/` (`results.csv`, `rank_by_name.csv`,
`rank_pooled.csv`, `monthly.csv` with scored/ABSENT exit months and legacy equity
months, `trades.csv`, per-cell `*/results.csv`, `manifest.json`).

## Decision

H1 holds only under NO_TRAIL; H2 is falsified under both legacy and sparse rules
for every H1-clearing name × cell. All three TP/trail cells are §8 regressions
(WR up by killing fat winners). The uneven-month problem is not an exit-geometry
artifact recoverable within the frozen grid, and it is not a sparse-H2 artifact
(series are dense, months are scored and negative). Close
H-BTC-FILTER-EXIT-GRID-SPARSE-01: do not promote any BTC-FILTER name × exit cell,
do not add further exit cells or retune entries on this family from this result,
and do not touch Validation/holdout. H-BTC-FILTER-01 stays at its parent verdict
(H1 pass / H2 fail, NO_TRAIL).

## Tests

`python3 scripts/f006_btc_filter_exit_grid.py` at `853ec73`: prior NO_TRAIL
40/40 rows matched, control 10/10 matched. `python3 -m pytest
tests/test_btc_filter_exit_grid.py tests/test_btc_filter.py -q`: 8 passed.
