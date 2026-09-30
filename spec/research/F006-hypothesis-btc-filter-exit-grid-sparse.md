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

_(empty until after Train-1)_

## Result

_(empty until after Train-1)_

## Decision

_(empty until after Train-1)_
