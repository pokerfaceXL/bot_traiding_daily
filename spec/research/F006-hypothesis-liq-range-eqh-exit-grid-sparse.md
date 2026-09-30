# F006 hypothesis — H-LIQ-RANGE-EQH-EXIT-GRID-SPARSE-01

Pre-registered 2026-09-30 (Europe/Warsaw) before any exit-grid code ran. Source card:
`/tmp/F006-card-H-LIQ-RANGE-EQH-EXIT-GRID-SPARSE-01.md`; standing policy
`/tmp/F006-eval-policy-sparse-h2-and-exits-2026-09-29.md`. Parent: `H-LIQ-RANGE-EQH-01`
(`spec/research/F006-hypothesis-liq-range-eqh.md`, tip `785d5cf`). Base: origin/main `d016659`.

Protocol category: COORDINATOR_RESEARCH_PROTOCOL §8 **Exit refinement** (entries frozen), via §7 diagnose-before-abandon.

**Sentence:** Na podstawie wyniku X (H1 pass / H2 fail on NO_TRAIL for RANGE_EQH_RECLAIM_WIDE ~+64.32; btc_filter exit-grid already closed as §8 regression under TP/trail) podejrzewam Y (nierówne miesiące przez exit geometry), dlatego testuję Z (standing ≤4-cell exit grid + h2_sparse_absent_zero_trade).

**Train-1 only.** No holdout / Validation. No entry retune. No merge to main. No new catalog names.

## Observation

Frozen-schema digest ranks `RANGE_EQH_RECLAIM_WIDE` second among Level-B H1-pass / H2-falsified families that have **not** yet run the standing sparse/swing exit grid (`NO_TRAIL`, `TP_x2`, `TRAIL_a0.06_t0.04`, `TRAIL_a0.03_t0.02` + `h2_sparse_absent_zero_trade`). After `btc_filter` exit-grid closed as ordinary DNR (H2=0; §8 regression under TP/trail — tip f02458b reviewed PASS, not FF-merged; origin/main stays d016659), `liq_range_eqh` is the next Level-B name without a standing exit grid.

Digest / parent NO_TRAIL facts (Train-1, 10 series):
- `RANGE_EQH_RECLAIM_WIDE`: mean Train-1 **+64.3201**, 58.8 trades/series, WR≈28.8%, DD≈13.2%, promotion_pass **0/10**
- `RANGE_EQH_RECLAIM_L2`: +54.1309 (H1 pass / H2 fail)
- `RANGE_EQH_RECLAIM_TIGHT`: +39.5076 (H1 pass / H2 fail)
- `RANGE_EQH_RECLAIM_WICK`: +31.2783 (H1 pass / H2 fail)
- `RANGE_EQH_RECLAIM_L3`: −4.1399 (H1 fail — keep in grid for NO_TRAIL reproduction only; not an H1-clearer)

Family H2 status: **falsified** (legacy promotion_pass = 0 across H1-clearers; all series have 12 valid months but not all-months-nonnegative).

Per COORDINATOR_RESEARCH_PROTOCOL §7: aggregate-positive with uneven months → diagnose before abandoning. §8 Exit refinement: change only post-entry geometry. Standing eval policy requires the exit grid + dual H2 before sole-DNR on legacy monthly H2. Prior sibling `H-BTC-FILTER-EXIT-GRID-SPARSE-01` already showed §8 TP/trail can regress mean Train-1 despite WR — apply the same falsifier here.

This is **not** a new entry family. Entries stay exactly tip `785d5cf` / `liq_range_eqh.py` from limen branch `limen/2026-09-29-f006-liq-range-eqh-87ed8676` (or byte-identical autopsy copy `output/f006_signal_autopsy/sources/liq_range_eqh.py`).

---

## Hypothesis

**H1 (per exit cell, same as parent).** At least one of the four H1-passing frozen EQH names (`WIDE`, `L2`, `TIGHT`, `WICK`) has mean Train-1 `train1_net_pnl > 0` over the fixed ten-series pool under that exit cell. Primary gate geometry for cross-cell comparability remains **NO_TRAIL** (must reproduce parent NO_TRAIL rows within harness tolerance).

**H2 (conditional on H1, dual).** For each H1-clearing name×cell, report:
1. **legacy H2** — unchanged 12-valid-month promotion checklist
2. **`h2_sparse_absent_zero_trade`** — score only exit-calendar months (Europe/Warsaw) with `n_trades > 0`; zero-trade months = ABSENT/neutral; require all scored months `net_pnl >= 0`, series DD ≤ 50%, Train-1 equity PnL ≥ 0, ≥1 Train-1 exit

**Falsify exit cells (§8):** a TP/trail cell that improves win_rate by killing fat winners such that mean Train-1 PnL falls below the NO_TRAIL cell for the same name is a **regression** (do not promote on WR alone). Rank cells by pooled trade-weighted win_rate; still report train1_net_pnl / H1 for every cell.

---

## Frozen names (exactly five — parent set; no expansion)

| Name | L | EPS | SWEEP_EPS | R_MAX | C | extra |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `RANGE_EQH_RECLAIM_L2` | 2 | 0.20 | 0.05 | 3 | 6 | primary |
| `RANGE_EQH_RECLAIM_L3` | 3 | 0.20 | 0.05 | 3 | 6 | lag ablation (H1 fail on NO_TRAIL) |
| `RANGE_EQH_RECLAIM_WIDE` | 2 | 0.30 | 0.05 | 5 | 6 | densest / best mean |
| `RANGE_EQH_RECLAIM_TIGHT` | 2 | 0.15 | 0.10 | 2 | 8 | stricter |
| `RANGE_EQH_RECLAIM_WICK` | 2 | 0.20 | 0.05 | 3 | 6 | wick-only sweep |

Shared freeze unchanged: `W_MIN=1.5`, `W_MAX=8.0`, `N_MIN=8`, `N_MAX=64`, dead-vol veto ATR14/close < 0.002. Basket = original parent 5×2 Train-1 (same as `run_family` / parent experiment).

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

1. **Docs first:** write `spec/research/F006-hypothesis-liq-range-eqh-exit-grid-sparse.md` (Observation→Falsification/Method from this card; leave Result/Decision empty until after run). Also restore parent hyp note `spec/research/F006-hypothesis-liq-range-eqh.md` from tip `785d5cf` / limen branch if absent on base (read-only provenance; do not edit parent freeze).
2. Restore `liq_range_eqh.py` + `tests/test_liq_range_eqh.py` + parent experiment script provenance from tip `785d5cf` / branch `limen/2026-09-29-f006-liq-range-eqh-87ed8676` (or autopsy source) **unchanged**.
3. Add sibling exit-grid script patterned on `scripts/f006_sube_inv_fvg_exit_grid.py` (and/or `scripts/f006_btc_filter_exit_grid.py` on sibling branch) → `scripts/f006_liq_range_eqh_exit_grid.py` writing `output/f006_liq_range_eqh/exit_grid/`.
4. Run Train-1 only; dual H2; rank tables; manifest records producing commit.
5. Targeted pytest for sparse-month ABSENT vs scored and NO_TRAIL reproduction. Stop when docs+harness+evidence committed on job branch. No merge. No follow-up spawn.

---

## Falsification

- H1 falsified for a cell if no frozen H1-pass name has mean Train-1 > 0 under that cell.
- H2 falsified if every H1-clearer fails both legacy and sparse H2.
- Exit regression: TP/trail cell with higher WR but lower mean Train-1 than NO_TRAIL for the same name = falsified as improvement (protocol §8) — same lesson as closed btc_filter exit-grid.
- Any entry retune, new L/EPS/SWEEP/R_MAX/C, catalog5/ORB/ABS-ATR/Donchian FREEZE reopen, holdout peek, or merge invalidates the run.

## Result

Train-1 only. Producing commit `4bfb69f` (harness; manifest `git_commit`). Evidence:
`output/f006_liq_range_eqh/exit_grid/` (`results.csv`, `monthly.csv`, `trades.csv`,
`rank_by_name.csv`, `rank_pooled.csv`, `manifest.json`, per-cell subdirs). 5 names × 4 cells × 10
series + DONCHIAN_55 on NO_TRAIL = 210 runs, ~60 s.

Checks: NO_TRAIL reproduces the parent raw rows exactly (60/60 rows incl. control; n_calls,
n_trades, n_wins, win_rate, net/train1 PnL, DD, final equity, n_valid_months, legacy H2 —
0 mismatches). DONCHIAN_55 harness control 10/10 vs trailing_boundary, mean Train-1 **+58.387**.
One-shot violations 0. `n_calls` identical across cells for every series (exits add no signal
opportunities; `n_trades` rises under TP/trail only because earlier exits free the one-position
engine to fill more of the same frozen calls).

Per name × cell (trade-weighted WR is the rank key; mean Train-1 = H1):

| Name | Cell | WR % | mean Train-1 | H1 | trades/series | legacy H2 | sparse H2 | §8 regression |
| --- | --- | ---: | ---: | :-: | ---: | ---: | ---: | :-: |
| WIDE | TRAIL_a0.03_t0.02 | 45.36 | −53.07 | fail | 70.1 | 0/10 | 0/10 | **yes** |
| WIDE | TP_x2 | 39.31 | −9.69 | fail | 66.9 | 0/10 | 0/10 | **yes** |
| WIDE | TRAIL_a0.06_t0.04 | 38.37 | −34.66 | fail | 66.2 | 0/10 | 0/10 | **yes** |
| WIDE | NO_TRAIL | 30.95 | **+64.32** | pass | 58.8 | 0/10 | 0/10 | — |
| L2 | TRAIL_a0.03_t0.02 | 45.41 | −53.62 | fail | 66.5 | 0/10 | 0/10 | **yes** |
| L2 | TP_x2 | 40.00 | −7.31 | fail | 63.0 | 0/10 | 0/10 | **yes** |
| L2 | TRAIL_a0.06_t0.04 | 38.88 | −30.94 | fail | 62.5 | 0/10 | 0/10 | **yes** |
| L2 | NO_TRAIL | 30.88 | +54.13 | pass | 55.7 | 0/10 | 0/10 | — |
| TIGHT | TRAIL_a0.03_t0.02 | 45.11 | −50.10 | fail | 61.4 | 0/10 | 0/10 | **yes** |
| TIGHT | TP_x2 | 39.18 | −8.62 | fail | 58.2 | 0/10 | 0/10 | **yes** |
| TIGHT | TRAIL_a0.06_t0.04 | 37.95 | −31.67 | fail | 57.7 | 0/10 | 0/10 | **yes** |
| TIGHT | NO_TRAIL | 29.10 | +39.51 | pass | 51.2 | 0/10 | 0/10 | — |
| WICK | TRAIL_a0.03_t0.02 | 43.88 | −48.99 | fail | 53.1 | 0/10 | 0/10 | **yes** |
| WICK | TP_x2 | 38.02 | −11.69 | fail | 50.5 | 0/10 | 0/10 | **yes** |
| WICK | TRAIL_a0.06_t0.04 | 37.52 | −29.94 | fail | 50.1 | 0/10 | 0/10 | **yes** |
| WICK | NO_TRAIL | 26.19 | +31.28 | pass | 44.3 | 0/10 | 0/10 | — |
| L3 | TRAIL_a0.03_t0.02 | 44.98 | −94.55 | fail | 112.5 | 0/10 | 0/10 | **yes** |
| L3 | TP_x2 | 42.87 | −20.35 | fail | 108.0 | 0/10 | 0/10 | **yes** |
| L3 | TRAIL_a0.06_t0.04 | 42.33 | −49.61 | fail | 107.5 | 0/10 | 0/10 | **yes** |
| L3 | NO_TRAIL | 37.12 | −4.14 | fail | 99.4 | 0/10 | 0/10 | — |

Pooled WR rank (descriptive): TRAIL_a0.03_t0.02 45.0% (−60.06) > TP_x2 40.3% (−11.53) >
TRAIL_a0.06_t0.04 39.5% (−35.36) > NO_TRAIL 31.9% (+37.02).

- **H1:** passes only under NO_TRAIL (WIDE, L2, TIGHT, WICK — parent result reproduced). Falsified
  for TP_x2, TRAIL_a0.06_t0.04 and TRAIL_a0.03_t0.02: no name has mean Train-1 > 0 in those cells.
- **H2 (dual):** every H1-clearer (NO_TRAIL × 4 names, 40 series) fails **both** legacy H2 (0/40)
  and `h2_sparse_absent_zero_trade` (0/40). Sparse H2 does not rescue it: these series are dense
  (44–59 trades/series; mean 11.2 of 12 Train-1 months scored under NO_TRAIL; 39 ABSENT
  series-months across 50 series) and every candidate series has ≥3 losing scored exit-months
  (NO_TRAIL mean ≈7 losing scored months/series). The failure is losing months, not missing months.
- **§8 regression:** all 15 non-NO_TRAIL name×cell rows (incl. L3) raise WR (+5.2 to +17.7 pp)
  while lowering mean Train-1 (−16 to −117) vs the same name's NO_TRAIL — every TP/trail cell is a
  regression, the same lesson as closed btc_filter exit-grid.
- **Mechanism note (diagnostic, not a gate):** the NO_TRAIL edge sits in a few fat winners
  exited by `signal_reverse`/end of data. WIDE NO_TRAIL: the top three trades (XRP 240 +381.4,
  DOGE 240 +196.3, XRP 60 +121.8, all Dec 2024–Jan 2025 exits) sum to ≈ +699, more than
  WIDE's whole ten-series trade PnL (≈ +659). Under TP_x2 / both trails WIDE's largest single
  trade is ≤ +20.6 and it has at most one trade above +15 (NO_TRAIL: 25). TP/trail cut the tail
  that the family's aggregate depends on.
- Density note: no name×cell below 10 trades/series; the sparse-H2 policy is not the binding
  constraint for this family.

## Decision

**Ordinary DNR for the exit-refinement branch of LIQ-RANGE-EQH.** None of the four frozen exit
cells makes the family promotable: TP_x2 and both trails fail H1 and are §8 regressions for every
name; NO_TRAIL stays H1 pass / H2 fail under both legacy and sparse H2 (0/40). Exit geometry does
not explain the uneven months (Y rejected): the frozen exits trade one losing-month pattern for
a negative aggregate by cutting the few fat winners the edge depends on. Entries were not touched,
no new names/cells, Train-1 only, no holdout/Validation, no merge. Not reopening btc_filter
exit-grid, catalog5, ORB, ABS-ATR, PARTIAL, EXIT-CLASS, Donchian FREEZE, HTFP or CASCADE-FADE.
Any further LIQ-RANGE-EQH work would need a new pre-registered card (e.g. the fat-winner tail
concentration above); this note does not authorize one.
