# H-MULTI-TF-PA-EXIT-GRID-SPARSE-01 — Exit-grid + sparse H2 continuation of H-MULTI-TF-PA-01

```yaml
id: H-MULTI-TF-PA-EXIT-GRID-SPARSE-01
ticket: S7-EXIT-GRID
name: MULTI-TF-PA standing exit grid + dual sparse H2 (entries frozen)
status: prereg_frozen (base origin/main d016659)
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

_(empty until after Train-1)_

## Decision

_(empty until after Train-1)_
