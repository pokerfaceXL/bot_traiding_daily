# H-MULTI-TF-PA-EXIT-GRID-SPARSE-01 — Exit-grid + sparse H2 continuation of H-MULTI-TF-PA-01

```yaml
id: H-MULTI-TF-PA-EXIT-GRID-SPARSE-01
ticket: S7-EXIT-GRID
name: MULTI-TF-PA standing exit grid + dual sparse H2 (entries frozen)
status: closed_dnr (prereg 3ce656b on base d016659; evidence d332457)
parent: H-MULTI-TF-PA-01 tip 3fc50ec / limen/2026-09-29-f006-multi-tf-pa-effff4e7 (module+hyp+tests+Train-1 NO_TRAIL evidence on branch tip 3fc50ec; manifest git_commit_parent 582f69c)
universe: BTC/ETH/SOL/XRP/DOGE USDT perps × {60,240}
data_needs: [ohlcv]
exit: exit_grid standing (NO_TRAIL + TP_x2 + TRAIL_a0.06_t0.04 + TRAIL_a0.03_t0.02)
h2: dual legacy + h2_sparse_absent_zero_trade (exit-month; zero trades = ABSENT)
session_filters: off
source: COORDINATOR_RESEARCH_PROTOCOL §7/§8 stuck-loop recovery; digest output/f006_cross_family_digest.md; standing policy /tmp/F006-eval-policy-sparse-h2-and-exits-2026-09-29.md; prior siblings H-BTC-FILTER-EXIT-GRID-SPARSE-01 (closed ordinary DNR / §8 regression tip f02458b), H-LIQ-RANGE-EQH-EXIT-GRID-SPARSE-01 (ordinary DNR tip a20a589, reviewed PASS …948151cf, not FF-merged), H-VOL-REGIME-WRAP-EXIT-GRID-SPARSE-01 (in flight …702f3f3f)
parent_dnr_do_not_reopen_entry:
  - H-MULTI-TF-PA-01 entry construction stays frozen (HTF bias/block gates + BRK20/10/5/BLOCK/PIN) — this card is EXIT ONLY
  - btc_filter exit-grid closed (ordinary DNR H2=0; §8 TP/trail regression tip f02458b) — do not reopen
  - liq_range_eqh exit-grid closed ordinary DNR (tip a20a589 / …948151cf PASS, not FF-merged) — do not spawn a second liq job
  - vol_regime_wrap exit-grid currently RUNNING (…702f3f3f) — do not spawn a second VOLW job
  - catalog5 FREEZE / ORB / ABS-ATR / PARTIAL / EXIT-CLASS stay closed
  - Donchian FREEZE / HTFP ordinary DNR / CASCADE-FADE stay closed
  - Sube exit-grid already done — skip
```

**Sentence (protocol form):** Na podstawie wyniku X (H1 pass / H2 fail on NO_TRAIL for MTFP_HTF_BRK20 ~+35.08; btc_filter+liq_range_eqh exit-grids closed ordinary DNR; vol_regime_wrap in flight) podejrzewam Y (nierówne miesiące przez exit geometry), dlatego testuję Z (standing ≤4-cell exit grid + h2_sparse_absent_zero_trade).

**Train-1 only.** No holdout / Validation. No entry retune. No merge to main. No new catalog names.

---

## Observation

Frozen-schema digest ranks `MTFP_HTF_BRK20` among Level-B H1-pass / H2-falsified families that have **not** yet run the standing sparse/swing exit grid (`NO_TRAIL`, `TP_x2`, `TRAIL_a0.06_t0.04`, `TRAIL_a0.03_t0.02` + `h2_sparse_absent_zero_trade`). After `btc_filter` exit-grid closed as ordinary DNR (H2=0; §8 regression under TP/trail — tip f02458b reviewed PASS, not FF-merged; origin/main stays d016659), `liq_range_eqh` exit-grid tip `a20a589` closed ordinary DNR (reviewed PASS `…948151cf`, not FF-merged), and `vol_regime_wrap` exit-grid occupies 1 RUNNING slot (`…702f3f3f`), `multi_tf_pa` is the next Level-B name without a standing exit grid (~+35.08 mean Train-1).

Digest / parent NO_TRAIL facts (Train-1, 10 series; evidence tip `3fc50ec` / pre-reg tip `582f69c`):
- `MTFP_HTF_BRK20`: mean Train-1 **+35.0825**, 97.8 trades/series, WR≈25.0%, DD≈16.3%, promotion_pass **0/10**
- `MTFP_HTF_BRK10`: +29.8073 (H1 pass / H2 fail)
- `MTFP_HTF_PIN`: +22.5572 (H1 pass / H2 fail; sparsest)
- `MTFP_HTF_BLOCK`: +18.9065 (H1 pass / H2 fail)
- `MTFP_HTF_BRK5`: +11.0717 (H1 pass / H2 fail)

Family H2 status: **falsified** (legacy promotion_pass = 0 across all five H1-clearers; every series has ≥1 losing valid month). Parent Decision: H1 holds 5/5; H2 falsified; no sixth name / no retune.

Per COORDINATOR_RESEARCH_PROTOCOL §7: aggregate-positive with uneven months → diagnose before abandoning. §8 Exit refinement: change only post-entry geometry. Standing eval policy requires the exit grid + dual H2 before sole-DNR on legacy monthly H2. Prior siblings already showed §8 TP/trail can regress mean Train-1 despite WR — apply the same falsifier here.

This is **not** a new entry family. Entries stay exactly tip `3fc50ec` / `multi_tf_pa.py` from limen branch `limen/2026-09-29-f006-multi-tf-pa-effff4e7` (or byte-identical autopsy copy `output/f006_signal_autopsy/sources/multi_tf_pa.py`). Evidence/decision tip `3fc50ec` is read-only provenance.

---

## Hypothesis

**H1 (per exit cell, same as parent).** At least one of the five H1-passing frozen MTFP names (`MTFP_HTF_BRK20`, `MTFP_HTF_BRK10`, `MTFP_HTF_PIN`, `MTFP_HTF_BLOCK`, `MTFP_HTF_BRK5`) has mean Train-1 `train1_net_pnl > 0` over the fixed ten-series pool under that exit cell. Primary gate geometry for cross-cell comparability remains **NO_TRAIL** (must reproduce parent NO_TRAIL rows within harness tolerance).

**H2 (conditional on H1, dual).** For each H1-clearing name×cell, report:
1. **legacy H2** — unchanged 12-valid-month promotion checklist
2. **`h2_sparse_absent_zero_trade`** — score only exit-calendar months (Europe/Warsaw) with `n_trades > 0`; zero-trade months = ABSENT/neutral; require all scored months `net_pnl >= 0`, series DD ≤ 50%, Train-1 equity PnL ≥ 0, ≥1 Train-1 exit

**Falsify exit cells (§8):** a TP/trail cell that improves win_rate by killing fat winners such that mean Train-1 PnL falls below the NO_TRAIL cell for the same name is a **regression** (do not promote on WR alone). Rank cells by pooled trade-weighted win_rate; still report train1_net_pnl / H1 for every cell.

---

## Frozen names (exactly five — parent set; no expansion)

| Name | LTF trigger | HTF gate | role |
| --- | --- | --- | --- |
| `MTFP_HTF_BRK20` | prior-20 LTF high/low strict cross | bias ±1 | primary / best mean |
| `MTFP_HTF_BRK10` | prior-10 LTF high/low strict cross | bias ±1 | H1-pass ablation |
| `MTFP_HTF_BRK5` | prior-5 LTF high/low strict cross | bias ±1 | densest / lower mean |
| `MTFP_HTF_BLOCK` | prior completed HTF block high/low strict cross | bias ±1 | HTF-level analogue |
| `MTFP_HTF_PIN` | pin/rejection vs prior-20 extreme + close tertile | bias ±1 | sparsest H1-pass |

Shared freeze unchanged: HTF = non-overlapping 4h blocks for LTF=60 / daily (6×240m) for LTF=240; bias from completed P1 vs P2 HHHL/LHLL only; causality = completed blocks only; no session-hour gate. Basket = original parent 5×2 Train-1 (same as `run_family` / parent experiment).

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

1. **Docs first:** write `spec/research/F006-hypothesis-multi-tf-pa-exit-grid-sparse.md` (Observation→Falsification/Method from this card; leave Result/Decision empty until after run). Also restore parent hyp note `spec/research/F006-hypothesis-multi-tf-pa.md` from tip `3fc50ec` / `582f69c` / limen branch if absent on base (read-only provenance; do not edit parent freeze).
2. Restore `multi_tf_pa.py` + `tests/test_multi_tf_pa.py` + parent experiment script provenance from tip `3fc50ec` / branch `limen/2026-09-29-f006-multi-tf-pa-effff4e7` (or autopsy source) **unchanged**.
3. Add sibling exit-grid script patterned on `scripts/f006_sube_inv_fvg_exit_grid.py` (and/or `scripts/f006_btc_filter_exit_grid.py` / `scripts/f006_liq_range_eqh_exit_grid.py` / `scripts/f006_vol_regime_wrap_exit_grid.py` on sibling branches) → `scripts/f006_multi_tf_pa_exit_grid.py` writing `output/f006_multi_tf_pa/exit_grid/`.
4. Run Train-1 only; dual H2; rank tables; manifest records producing commit.
5. Targeted pytest for sparse-month ABSENT vs scored and NO_TRAIL reproduction. Stop when docs+harness+evidence committed on job branch. No merge. No follow-up spawn.

---

## Falsification

- H1 falsified for a cell if no frozen H1-pass name has mean Train-1 > 0 under that cell.
- H2 falsified if every H1-clearer fails both legacy and sparse H2.
- Exit regression: TP/trail cell with higher WR but lower mean Train-1 than NO_TRAIL for the same name = falsified as improvement (protocol §8) — same lesson as closed btc_filter / closed liq_range_eqh exit-grids.
- Any entry retune, new N / HTF definition / sixth name, catalog5/ORB/ABS-ATR/Donchian FREEZE reopen, holdout peek, or merge invalidates the run.

## Implementation notes (frozen before code)

- Sparse-month bucket: trade `exit_time` converted to Europe/Warsaw; only Train-1 calendar months (`f006_family_runner.TRAIN1_MONTHS`) scored; months with zero exits = ABSENT.
- Legacy H2 = parent `promotion_pass` rule (12 valid months, all valid months equity-PnL ≥ 0, DD ≤ 50%, Train-1 PnL ≥ 0, ≥1 trade).
- Pooled rank = trade-weighted win_rate across the five MTFP names (DONCHIAN_55 excluded); per-name rank = same metric within name.
- §8 regression flag per name×cell: `win_rate > NO_TRAIL win_rate` AND `mean train1_net_pnl < NO_TRAIL mean` for the same name.
- Harness: `scripts/f006_multi_tf_pa_exit_grid.py` → `output/f006_multi_tf_pa/exit_grid/`; must reproduce parent `output/f006_multi_tf_pa/raw/*` NO_TRAIL rows exactly and DONCHIAN_55 control rows.

## Result

Train-1 only, run 2026-09-30. Harness `scripts/f006_multi_tf_pa_exit_grid.py` at producing commit `d332457` (manifest `git_commit`); evidence `output/f006_multi_tf_pa/exit_grid/` (results / monthly / trades / rank_by_name / rank_pooled / per-cell dirs / manifest). 210 runs = 5 names × 10 series × 4 cells + DONCHIAN_55 × 10 on NO_TRAIL.

Checks: parent NO_TRAIL reproduction **60/60 rows, 0 mismatches** (n_calls, n_trades, n_wins, win_rate, net_pnl, train1_net_pnl, DD, final_equity, n_valid_months, month sign, legacy H2 vs parent `promotion_pass`); DONCHIAN_55 harness control 10/10, 0 mismatches, mean Train-1 **+58.387**; one-shot violations 0. Module `multi_tf_pa.py` byte-identical to `3fc50ec` and to the autopsy source copy.

Per name × cell (trade-weighted WR; mean Train-1 over 10 series; legacy/sparse H2 series passing):

| Name | Cell | WR % | mean Train-1 | H1 | trades/series | max DD % | legacy H2 | sparse H2 | §8 regression |
| --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | --- |
| MTFP_HTF_BRK20 | TRAIL_a0.03_t0.02 | 35.02 | −171.17 | fail | 158.5 | 65.87 | 0 | 0 | yes |
| MTFP_HTF_BRK20 | TP_x2 | 34.38 | −23.67 | fail | 137.3 | 28.32 | 0 | 0 | yes |
| MTFP_HTF_BRK20 | TRAIL_a0.06_t0.04 | 30.38 | −114.39 | fail | 127.4 | 46.32 | 0 | 0 | yes |
| MTFP_HTF_BRK20 | NO_TRAIL | 25.26 | **+35.08** | pass | 97.8 | 24.85 | 0 | 0 | — |
| MTFP_HTF_BRK10 | TP_x2 | 34.59 | −14.76 | fail | 169.4 | 24.70 | 0 | 0 | yes |
| MTFP_HTF_BRK10 | TRAIL_a0.03_t0.02 | 34.13 | −204.17 | fail | 196.3 | 80.53 | 0 | 0 | yes |
| MTFP_HTF_BRK10 | TRAIL_a0.06_t0.04 | 30.81 | −115.78 | fail | 157.4 | 49.91 | 0 | 0 | yes |
| MTFP_HTF_BRK10 | NO_TRAIL | 27.32 | +29.81 | pass | 127.0 | 22.43 | 0 | 0 | — |
| MTFP_HTF_BRK5 | TP_x2 | 34.13 | −20.39 | fail | 184.0 | 29.24 | 0 | 0 | yes |
| MTFP_HTF_BRK5 | TRAIL_a0.03_t0.02 | 33.46 | −219.89 | fail | 210.7 | 80.26 | 0 | 0 | yes |
| MTFP_HTF_BRK5 | TRAIL_a0.06_t0.04 | 30.06 | −131.90 | fail | 172.0 | 53.86 | 0 | 0 | yes |
| MTFP_HTF_BRK5 | NO_TRAIL | 26.68 | +11.07 | pass | 138.7 | 23.39 | 0 | 0 | — |
| MTFP_HTF_BLOCK | TRAIL_a0.03_t0.02 | 35.44 | −189.82 | fail | 188.2 | 80.69 | 0 | 0 | yes |
| MTFP_HTF_BLOCK | TP_x2 | 34.42 | −31.05 | fail | 165.6 | 22.32 | 0 | 0 | yes |
| MTFP_HTF_BLOCK | TRAIL_a0.06_t0.04 | 31.46 | −118.55 | fail | 155.1 | 54.31 | 0 | 0 | yes |
| MTFP_HTF_BLOCK | NO_TRAIL | 27.59 | +18.91 | pass | 128.3 | 32.82 | 0 | 0 | — |
| MTFP_HTF_PIN | TRAIL_a0.03_t0.02 | 45.91 | −21.30 | fail | 25.7 | 11.06 | 0 | 0 | yes |
| MTFP_HTF_PIN | TRAIL_a0.06_t0.04 | 36.61 | −12.50 | fail | 25.4 | 10.30 | 0 | 0 | yes |
| MTFP_HTF_PIN | TP_x2 | 36.47 | −6.31 | fail | 25.5 | 9.92 | 0 | 0 | yes |
| MTFP_HTF_PIN | NO_TRAIL | 21.94 | +22.56 | pass | 23.7 | 20.76 | 0 | 0 | — |

Pooled (descriptive, five MTFP names, 50 series): TRAIL_a0.03_t0.02 WR 34.83 / mean −161.27; TP_x2 34.45 / −19.24; TRAIL_a0.06_t0.04 30.91 / −98.62; NO_TRAIL 26.58 / +23.49.

- **WR rank winner** (per policy primary key): TRAIL_a0.03_t0.02 for BRK20/BLOCK/PIN, TP_x2 for BRK10/BRK5 — but every non-NO_TRAIL cell lowers mean Train-1 below zero.
- **H1 per cell:** NO_TRAIL holds (5/5 names, reproduces parent). TP_x2, TRAIL_a0.06_t0.04, TRAIL_a0.03_t0.02 each **falsified** (no name > 0).
- **H2 dual:** legacy 0/200 name×series×cell; `h2_sparse_absent_zero_trade` 0/200. Under NO_TRAIL every MTFP series still has ≥ 4 losing *scored* exit-months (BRK20 min 6/series); ABSENT months exist (125 across all MTFP rows, mostly PIN) but removing them does not rescue any series — the failure is losing traded months, not sparsity.
- **§8:** all 15 TP/trail name×cells are regressions (WR +3.4…+24.0 pp, mean Train-1 −28.9…−234.0 vs NO_TRAIL same name). Exit mix confirms fat-winner truncation (pooled MTFP winners from `trades.csv`): NO_TRAIL 1370 winners, mean +8.73 on `signal_reverse`; TP_x2 mean winner +5.68 on `take_profit`; TRAIL_a0.06_t0.04 +3.92 and TRAIL_a0.03_t0.02 +1.39 on `trailing_sl`.
- **Density note:** NO_TRAIL trades/series 23.7 (PIN) … 138.7 (BRK5); no name below 10. TP/trail raise realized trades/series (e.g. BRK20 97.8 → 158.5) without new signal opportunities: `n_calls` unchanged, positions simply free up earlier for later one-shot calls already in the mask (n_trades ≤ n_calls holds everywhere).

## Decision

**Ordinary DNR for the MULTI-TF-PA exit-grid continuation** (same outcome shape as closed btc_filter / liq_range_eqh exit-grids).

- H1: holds only under NO_TRAIL (parent result reproduced exactly; BRK20 +35.08). Falsified under TP_x2, TRAIL_a0.06_t0.04, TRAIL_a0.03_t0.02.
- H2: falsified under both legacy and `h2_sparse_absent_zero_trade` for every H1-clearer in every cell. The sparse rule changes nothing here — the family is not sparse (except PIN) and losing months are traded months.
- §8: every TP/trail cell is a WR-for-PnL regression; no exit cell is promoted. Uneven months are **not** explained by exit geometry — hypothesis Y (nierówne miesiące przez exit geometry) is rejected for this frozen entry set.
- No entry retune, no sixth name, no holdout, no merge. Entries stay frozen at `3fc50ec`. Parent H-MULTI-TF-PA-01 Decision (H1 5/5 / H2 falsified) stands unchanged.
