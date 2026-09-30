# H-HTF-GAP-MIDFILL-EXIT-GRID-SPARSE-01 — Exit-grid + sparse H2 continuation of H-HTF-GAP-MIDFILL-01

```yaml
id: H-HTF-GAP-MIDFILL-EXIT-GRID-SPARSE-01
ticket: S7-EXIT-GRID
name: HTF-GAP-MIDFILL standing exit grid + dual sparse H2 (entries frozen)
status: prereg_frozen (base origin/main d016659)
parent: H-HTF-GAP-MIDFILL-01 tip be71095 / limen/2026-09-29-f006-htf-gap-midfill-23c4876c (module+hyp+tests on tip aaf00f5; Train-1 NO_TRAIL evidence packaging tip be71095 / origin/main output/; manifest git_commit aaf00f5)
universe: BTC/ETH/SOL/XRP/DOGE USDT perps × {60,240}
data_needs: [ohlcv]
exit: exit_grid standing (NO_TRAIL + TP_x2 + TRAIL_a0.06_t0.04 + TRAIL_a0.03_t0.02)
h2: dual legacy + h2_sparse_absent_zero_trade (exit-month; zero trades = ABSENT)
session_filters: off
source: COORDINATOR_RESEARCH_PROTOCOL §7/§8 stuck-loop recovery; digest output/f006_cross_family_digest.md; standing policy /tmp/F006-eval-policy-sparse-h2-and-exits-2026-09-29.md; prior siblings H-BTC-FILTER-EXIT-GRID-SPARSE-01 (closed ordinary DNR tip f02458b), H-LIQ-RANGE-EQH-EXIT-GRID-SPARSE-01 (ordinary DNR tip a20a589, reviewed PASS …948151cf, not FF-merged), H-VOL-REGIME-WRAP-EXIT-GRID-SPARSE-01 (ordinary DNR tip fc3f094, reviewed PASS …4e6e16f6, not FF-merged), H-MULTI-TF-PA-EXIT-GRID-SPARSE-01 (ordinary DNR tip 09aacef, reviewed PASS …dfb5b5b6, not FF-merged), H-BETA-GATE-EXIT-GRID-SPARSE-01 (coding DONE …32f98868; review not yet spawned by this helper)
parent_dnr_do_not_reopen_entry:
  - H-HTF-GAP-MIDFILL-01 entry construction stays frozen (causal HTF FVG midfill R_MAX={1,2,3}, bias lookback 3, first-touch consume) — this card is EXIT ONLY
  - btc_filter exit-grid closed (ordinary DNR H2=0; §8 TP/trail regression tip f02458b) — do not reopen
  - liq_range_eqh exit-grid closed ordinary DNR (tip a20a589 / …948151cf PASS, not FF-merged) — do not spawn a second liq job
  - vol_regime_wrap exit-grid closed ordinary DNR (tip fc3f094 / …4e6e16f6 PASS, not FF-merged) — do not spawn a second VOLW job
  - multi_tf_pa exit-grid closed ordinary DNR (tip 09aacef / …dfb5b5b6 PASS, not FF-merged) — do not spawn a second MTFP job
  - beta_gate exit-grid coding DONE (…32f98868) — do not spawn a second beta coding job; review is a separate coordinator step
  - catalog5 FREEZE / ORB / ABS-ATR / PARTIAL / EXIT-CLASS stay closed
  - Donchian FREEZE / HTFP ordinary DNR / CASCADE-FADE stay closed
  - Sube exit-grid already done — skip
```

**Sentence (protocol form):** Na podstawie wyniku X (H1 pass / H2 fail on NO_TRAIL for HTF_FVG_MID_R1 ~+26.71; prior Level-B exit-grids btc_filter/liq/volw/mtfp closed ordinary DNR; beta_gate in flight) podejrzewam Y (nierówne miesiące przez exit geometry), dlatego testuję Z (standing ≤4-cell exit grid + h2_sparse_absent_zero_trade).

**Train-1 only.** No holdout / Validation. No entry retune. No merge to main. No new catalog names.

---

## Observation

Frozen-schema digest ranks `HTF_FVG_MID_R1` among Level-B H1-pass / H2-falsified families that have **not** yet run the standing sparse/swing exit grid (`NO_TRAIL`, `TP_x2`, `TRAIL_a0.06_t0.04`, `TRAIL_a0.03_t0.02` + `h2_sparse_absent_zero_trade`). After `btc_filter` exit-grid closed as ordinary DNR (H2=0; §8 regression under TP/trail — tip f02458b reviewed PASS, not FF-merged; origin/main stays d016659), `liq_range_eqh` tip `a20a589` closed ordinary DNR (reviewed PASS `…948151cf`, not FF-merged), `vol_regime_wrap` tip `fc3f094` closed ordinary DNR (reviewed PASS `…4e6e16f6`, not FF-merged), `multi_tf_pa` tip `09aacef` closed ordinary DNR (reviewed PASS `…dfb5b5b6`, not FF-merged), and `beta_gate` exit-grid coding job `…32f98868` just reached DONE (board idle 0/2 at this spawn; review not part of this helper), `htf_gap_midfill` is the next Level-B name without a standing exit grid (~+26.71 mean Train-1).

Digest / parent NO_TRAIL facts (Train-1, 10 series; evidence tip `be71095` / module tip `aaf00f5`):
- `HTF_FVG_MID_R1`: mean Train-1 **+26.7072**, 35.8 trades/series, WR≈20.7%, DD≈12.2%, promotion_pass **0/10**
- `HTF_FVG_MID_R3`: +23.8136 (H1 pass / H2 fail)
- `HTF_FVG_MID_R2`: +23.7520 (H1 pass / H2 fail)

Family H2 status: **falsified** (legacy promotion_pass = 0 across all three H1-clearers; 0/30 monthly-clean; every series has ≥1 losing valid month). Parent Decision: H1 holds 3/3; H2 falsified; stop at pre-registered grid; no R_MAX / bias / midfill retune.

Per COORDINATOR_RESEARCH_PROTOCOL §7: aggregate-positive with uneven months → diagnose before abandoning. §8 Exit refinement: change only post-entry geometry. Standing eval policy requires the exit grid + dual H2 before sole-DNR on legacy monthly H2. Prior siblings already showed §8 TP/trail can regress mean Train-1 despite WR — apply the same falsifier here.

This is **not** a new entry family. Entries stay exactly tip `aaf00f5` / `htf_gap_midfill.py` from limen branch `limen/2026-09-29-f006-htf-gap-midfill-23c4876c` (packaging/evidence tip `be71095`). Evidence/decision tip `be71095` is read-only provenance.

---

## Hypothesis

**H1 (per exit cell, same as parent).** At least one of the three H1-passing frozen HTF-GAP names (`HTF_FVG_MID_R1`, `HTF_FVG_MID_R2`, `HTF_FVG_MID_R3`) has mean Train-1 `train1_net_pnl > 0` over the fixed ten-series pool under that exit cell. Primary gate geometry for cross-cell comparability remains **NO_TRAIL** (must reproduce parent NO_TRAIL rows within harness tolerance).

**H2 (conditional on H1, dual).** For each H1-clearing name×cell, report:
1. **legacy H2** — unchanged 12-valid-month promotion checklist
2. **`h2_sparse_absent_zero_trade`** — score only exit-calendar months (Europe/Warsaw) with `n_trades > 0`; zero-trade months = ABSENT/neutral; require all scored months `net_pnl >= 0`, series DD ≤ 50%, Train-1 equity PnL ≥ 0, ≥1 Train-1 exit

**Falsify exit cells (§8):** a TP/trail cell that improves win_rate by killing fat winners such that mean Train-1 PnL falls below the NO_TRAIL cell for the same name is a **regression** (do not promote on WR alone). Rank cells by pooled trade-weighted win_rate; still report train1_net_pnl / H1 for every cell.

---

## Frozen names (exactly three — parent set; no expansion)

| Name | `R_MAX` input bars | HTF blocks | Bias lookback | role |
| --- | ---: | --- | ---: | --- |
| `HTF_FVG_MID_R1` | 1 | 4h on 60m; 12h on 240m | 3 | primary / best mean |
| `HTF_FVG_MID_R2` | 2 | 4h on 60m; 12h on 240m | 3 | H1-pass ablation |
| `HTF_FVG_MID_R3` | 3 | 4h on 60m; 12h on 240m | 3 | H1-pass ablation |

Shared freeze unchanged: causal non-overlapping UTC HTF blocks; FVG create on completed HTF c1/c2/c3; mid = 0.5*(gap_top+gap_bot); first midpoint touch consumes gap ID even under opposite/flat bias; continuation close / far-side reject within R_MAX; one-shot; most-recent gap wins on collision; runtime-only catalog via `htf_gap_midfill.catalog_entries()` (no strategy.py edit). Basket = original parent 5×2 Train-1 (same as `run_family` / parent experiment).

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

1. **Docs first:** write `spec/research/F006-hypothesis-htf-gap-midfill-exit-grid-sparse.md` (Observation→Falsification/Method from this card; leave Result/Decision empty until after run). Also restore parent hyp note `spec/research/F006-hypothesis-htf-gap-midfill.md` from tip `be71095` / `aaf00f5` / limen branch if absent on base (read-only provenance; do not edit parent freeze).
2. Restore `htf_gap_midfill.py` + `tests/test_htf_gap_midfill.py` + parent experiment script provenance from tip `aaf00f5` / branch `limen/2026-09-29-f006-htf-gap-midfill-23c4876c` (or packaging tip `be71095`) **unchanged**.
3. Add sibling exit-grid script patterned on `scripts/f006_sube_inv_fvg_exit_grid.py` (and/or `scripts/f006_btc_filter_exit_grid.py` / `scripts/f006_liq_range_eqh_exit_grid.py` / `scripts/f006_vol_regime_wrap_exit_grid.py` / `scripts/f006_multi_tf_pa_exit_grid.py` / `scripts/f006_beta_gate_exit_grid.py` on sibling branches) → `scripts/f006_htf_gap_midfill_exit_grid.py` writing `output/f006_htf_gap_midfill/exit_grid/`.
4. Run Train-1 only; dual H2; rank tables; manifest records producing commit.
5. Targeted pytest for sparse-month ABSENT vs scored and NO_TRAIL reproduction. Stop when docs+harness+evidence committed on job branch. No merge. No follow-up spawn.

---

## Falsification

- H1 falsified for a cell if no frozen H1-pass name has mean Train-1 > 0 under that cell.
- H2 falsified if every H1-clearer fails both legacy and sparse H2.
- Exit regression: TP/trail cell with higher WR but lower mean Train-1 than NO_TRAIL for the same name = falsified as improvement (protocol §8) — same lesson as closed btc_filter / liq_range_eqh / vol_regime_wrap / multi_tf_pa exit-grids.
- Any entry retune, new R_MAX / bias lookback / mid factor / block size, fourth catalog name, catalog5/ORB/ABS-ATR/Donchian FREEZE reopen, holdout peek, or merge invalidates the run.

## Run_id

`python3 scripts/f006_htf_gap_midfill_exit_grid.py` at producing commit `7f2ee4a` (manifest `git_commit` 7f2ee4a4d759…; parent module tip `aaf00f5`, parent evidence tip `be71095`). 130 runs = 3 names × 10 series × 4 cells + DONCHIAN_55 × 10 on NO_TRAIL. Evidence: `output/f006_htf_gap_midfill/exit_grid/` (`results.csv`, `monthly.csv`, `trades.csv`, `rank_by_name.csv`, `rank_pooled.csv`, `manifest.json`, per-cell subdirs).

## Result

Harness checks: NO_TRAIL reproduces the parent raw rows exactly (40/40 rows incl. control, 0 mismatches on n_calls/n_trades/n_wins/win_rate/net_pnl/train1_net_pnl/DD/final_equity/n_valid_months/legacy H2); DONCHIAN_55 control 10/10 vs trailing-boundary reference, mean Train-1 **+58.387**; one-shot violations 0. Entry masks computed once per series×name and shared by all cells (signal hashes in manifest).

Per name × exit cell (win_rate = trade-weighted over all run trades; mean Train-1 over 10 series):

| Name | Exit cell | WR % | mean Train-1 | H1 | trades/series | max DD % | legacy H2 | sparse H2 | §8 regression |
| --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | --- |
| HTF_FVG_MID_R1 | TRAIL_a0.03_t0.02 | 43.36 | −36.28 | fail | 45.9 | 18.01 | 0/10 | 0/10 | yes |
| HTF_FVG_MID_R1 | TP_x2 | 36.96 | −4.29 | fail | 44.1 | 9.52 | 0/10 | 0/10 | yes |
| HTF_FVG_MID_R1 | TRAIL_a0.06_t0.04 | 36.11 | −30.90 | fail | 43.2 | 13.92 | 0/10 | 0/10 | yes |
| HTF_FVG_MID_R1 | NO_TRAIL | 23.74 | **+26.71** | pass | 35.8 | 21.96 | 0/10 | 0/10 | — |
| HTF_FVG_MID_R2 | TRAIL_a0.03_t0.02 | 43.85 | −41.59 | fail | 50.4 | 20.10 | 0/10 | 0/10 | yes |
| HTF_FVG_MID_R2 | TP_x2 | 37.45 | −6.20 | fail | 48.6 | 11.28 | 0/10 | 0/10 | yes |
| HTF_FVG_MID_R2 | TRAIL_a0.06_t0.04 | 36.61 | −35.26 | fail | 47.8 | 14.29 | 0/10 | 0/10 | yes |
| HTF_FVG_MID_R2 | NO_TRAIL | 24.69 | +23.75 | pass | 39.7 | 22.25 | 0/10 | 0/10 | — |
| HTF_FVG_MID_R3 | TRAIL_a0.03_t0.02 | 43.61 | −42.41 | fail | 50.9 | 20.10 | 0/10 | 0/10 | yes |
| HTF_FVG_MID_R3 | TP_x2 | 37.20 | −6.89 | fail | 49.2 | 12.21 | 0/10 | 0/10 | yes |
| HTF_FVG_MID_R3 | TRAIL_a0.06_t0.04 | 36.36 | −35.96 | fail | 48.4 | 14.68 | 0/10 | 0/10 | yes |
| HTF_FVG_MID_R3 | NO_TRAIL | 24.44 | +23.81 | pass | 40.1 | 22.25 | 0/10 | 0/10 | — |

Pooled WR rank (descriptive): TRAIL_a0.03_t0.02 43.61% (−40.09) > TP_x2 37.21% (−5.79) > TRAIL_a0.06_t0.04 36.37% (−34.04) > NO_TRAIL 24.31% (+24.76).

- **H1 per cell:** holds only under NO_TRAIL (3/3 names). Falsified under TP_x2, TRAIL_a0.06_t0.04, TRAIL_a0.03_t0.02 (0/3 names with mean Train-1 > 0).
- **§8:** every TP/trail cell raises WR (+11.9 to +19.6 pp) while cutting mean Train-1 by −30 to −66 vs NO_TRAIL for the same name → all 9 non-baseline cells are regressions. Fat-winner example: DOGEUSDT 240 HTF_FVG_MID_R1 Train-1 +131.61 under NO_TRAIL (one 161-USDT winner) becomes −27.52 (TP_x2), −32.41 (a0.06/t0.04), −29.41 (a0.03/t0.02).
- **H2 dual:** legacy 0/30 and `h2_sparse_absent_zero_trade` 0/30 in every cell. Sparse relief is irrelevant here: the family is not sparse (≈10.4–11.2 scored exit-months of 12 per series; 130 ABSENT series-months over all 130 runs), and every series in every cell has ≥4 losing scored exit-months (min 6 under NO_TRAIL). Not a single series has ≤1 losing month.
- **Density note:** 35.8–50.9 trades/series; no density flag. TP/trail cells fill more of the same pre-computed one-shot calls (e.g. R1 358→441 trades) only because earlier exits free the position slot; n_calls and signal hashes are identical across cells, n_trades ≤ n_calls everywhere.

## Decision

**Ordinary DNR for the exit-grid continuation.** H1 holds only on the NO_TRAIL baseline already recorded by the parent; no TP/trail cell survives H1, all are §8 regressions (WR up by clipping the fat winners that carry the mean). H2 is falsified under both legacy and sparse rules in all four cells — the uneven months are not an exit-geometry artefact (Y rejected). Entries stay frozen at `aaf00f5`; no R_MAX / bias / midfill / exit retune follows. Train-1 only; no Validation/holdout; no merge; no follow-up spawn from this note.
