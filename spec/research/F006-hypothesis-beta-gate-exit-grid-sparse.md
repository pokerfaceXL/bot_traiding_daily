# H-BETA-GATE-EXIT-GRID-SPARSE-01 — Exit-grid + sparse H2 continuation of H-BETA-GATE-01

```yaml
id: H-BETA-GATE-EXIT-GRID-SPARSE-01
ticket: S7-EXIT-GRID
name: BETA-GATE standing exit grid + dual sparse H2 (entries frozen)
status: closed_dnr (prereg a09f3a3 on base d016659; harness+producing commit f506217)
parent: H-BETA-GATE-01 tip 54fd498 / limen/2026-09-29-f006-beta-gate-33f3dc36 (module+hyp+tests on tip b726db1; Train-1 NO_TRAIL evidence on tip 54fd498 / origin/main output/; manifest git_commit b726db1)
universe: BTC/ETH/SOL/XRP/DOGE USDT perps × {60,240}
data_needs: [ohlcv, cross_symbol]
exit: exit_grid standing (NO_TRAIL + TP_x2 + TRAIL_a0.06_t0.04 + TRAIL_a0.03_t0.02)
h2: dual legacy + h2_sparse_absent_zero_trade (exit-month; zero trades = ABSENT)
session_filters: off
source: COORDINATOR_RESEARCH_PROTOCOL §7/§8 stuck-loop recovery; digest output/f006_cross_family_digest.md; standing policy /tmp/F006-eval-policy-sparse-h2-and-exits-2026-09-29.md; prior siblings H-BTC-FILTER-EXIT-GRID-SPARSE-01 (closed ordinary DNR tip f02458b), H-LIQ-RANGE-EQH-EXIT-GRID-SPARSE-01 (ordinary DNR tip a20a589, reviewed PASS …948151cf, not FF-merged), H-VOL-REGIME-WRAP-EXIT-GRID-SPARSE-01 (ordinary DNR tip fc3f094, reviewed PASS …4e6e16f6, not FF-merged), H-MULTI-TF-PA-EXIT-GRID-SPARSE-01 (ordinary DNR tip 09aacef, reviewed PASS …dfb5b5b6, not FF-merged)
parent_dnr_do_not_reopen_entry:
  - H-BETA-GATE-01 entry construction stays frozen (W=48 rolling OLS β, β_min=0.5, β_low=0.2, Donchian-20 trigger, BTC SMA bias) — this card is EXIT ONLY
  - btc_filter exit-grid closed (ordinary DNR H2=0; §8 TP/trail regression tip f02458b) — do not reopen
  - liq_range_eqh exit-grid closed ordinary DNR (tip a20a589 / …948151cf PASS, not FF-merged) — do not spawn a second liq job
  - vol_regime_wrap exit-grid closed ordinary DNR (tip fc3f094 / …4e6e16f6 PASS, not FF-merged) — do not spawn a second VOLW job
  - multi_tf_pa exit-grid closed ordinary DNR (tip 09aacef / …dfb5b5b6 PASS, not FF-merged) — do not spawn a second MTFP job
  - catalog5 FREEZE / ORB / ABS-ATR / PARTIAL / EXIT-CLASS stay closed
  - Donchian FREEZE / HTFP ordinary DNR / CASCADE-FADE stay closed
  - Sube exit-grid already done — skip
```

**Sentence (protocol form):** Na podstawie wyniku X (H1 pass / H2 fail on NO_TRAIL for BETA_GATE_DONCH20 ~+31.40; btc_filter+liq_eqh+volw exit-grids closed ordinary DNR; MTFP in review) podejrzewam Y (nierówne miesiące przez exit geometry), dlatego testuję Z (standing ≤4-cell exit grid + h2_sparse_absent_zero_trade).

**Train-1 only.** No holdout / Validation. No entry retune. No merge to main. No new catalog names.

---

## Observation

Frozen-schema digest ranks `BETA_GATE_DONCH20` among Level-B H1-pass / H2-falsified families that have **not** yet run the standing sparse/swing exit grid (`NO_TRAIL`, `TP_x2`, `TRAIL_a0.06_t0.04`, `TRAIL_a0.03_t0.02` + `h2_sparse_absent_zero_trade`). After `btc_filter` exit-grid closed as ordinary DNR (H2=0; §8 regression under TP/trail — tip f02458b reviewed PASS, not FF-merged; origin/main stays d016659), `liq_range_eqh` tip `a20a589` closed ordinary DNR (reviewed PASS `…948151cf`, not FF-merged), `vol_regime_wrap` tip `fc3f094` closed ordinary DNR (reviewed PASS `…4e6e16f6`, not FF-merged), and `multi_tf_pa` tip `09aacef` closed ordinary DNR (reviewed PASS `…dfb5b5b6`, not FF-merged), `beta_gate` is the next Level-B name without a standing exit grid (~+31.40 mean Train-1).

Digest / parent NO_TRAIL facts (Train-1, 10 series; evidence tip `54fd498` / pre-reg tip `b726db1`):
- `BETA_GATE_DONCH20`: mean Train-1 **+31.4003**, 136.2 trades/series, WR≈26.5%, DD≈17.4%, promotion_pass **0/10**
- `BETA_GATE_MR_DONCH20`: −3.6515 (H1 fail — keep in grid for NO_TRAIL reproduction only; not an H1-clearer; degenerate thin sample at β_low=0.2)

Family H2 status: **falsified** (legacy promotion_pass = 0 across H1-clearers; every H1-passing series has ≥1 losing valid month). Parent Decision: H1 holds for trend gate; H2 falsified; no W/β retune.

Per COORDINATOR_RESEARCH_PROTOCOL §7: aggregate-positive with uneven months → diagnose before abandoning. §8 Exit refinement: change only post-entry geometry. Standing eval policy requires the exit grid + dual H2 before sole-DNR on legacy monthly H2. Prior siblings already showed §8 TP/trail can regress mean Train-1 despite WR — apply the same falsifier here.

This is **not** a new entry family. Entries stay exactly tip `b726db1` / `beta_gate.py` from limen branch `limen/2026-09-29-f006-beta-gate-33f3dc36` (or byte-identical autopsy copy `output/f006_signal_autopsy/sources/beta_gate.py`). Evidence/decision tip `54fd498` is read-only provenance.

---

## Hypothesis

**H1 (per exit cell, same as parent).** The H1-passing frozen BETA name (`BETA_GATE_DONCH20`) has mean Train-1 `train1_net_pnl > 0` over the fixed ten-series pool under that exit cell. Primary gate geometry for cross-cell comparability remains **NO_TRAIL** (must reproduce parent NO_TRAIL rows within harness tolerance). `BETA_GATE_MR_DONCH20` is kept for NO_TRAIL reproduction only (parent H1-fail).

**H2 (conditional on H1, dual).** For each H1-clearing name×cell, report:
1. **legacy H2** — unchanged 12-valid-month promotion checklist
2. **`h2_sparse_absent_zero_trade`** — score only exit-calendar months (Europe/Warsaw) with `n_trades > 0`; zero-trade months = ABSENT/neutral; require all scored months `net_pnl >= 0`, series DD ≤ 50%, Train-1 equity PnL ≥ 0, ≥1 Train-1 exit

**Falsify exit cells (§8):** a TP/trail cell that improves win_rate by killing fat winners such that mean Train-1 PnL falls below the NO_TRAIL cell for the same name is a **regression** (do not promote on WR alone). Rank cells by pooled trade-weighted win_rate; still report train1_net_pnl / H1 for every cell.

---

## Frozen names (exactly two — parent set; no expansion)

| Name | gate | role |
| --- | --- | --- |
| `BETA_GATE_DONCH20` | Donchian-20 continuation allowed only if β>β_min=0.5 AND BTC SMA(W) bias agrees | primary / best mean |
| `BETA_GATE_MR_DONCH20` | fade of Donchian-20 when β<β_low=0.2 (no BTC-bias) | H1-fail ablation (keep for NO_TRAIL reproduction) |

Shared freeze unchanged: W=48 bars (same bar-count on 60m and 240m); rolling OLS β(alt, BTC) on returns; β_min=0.5; β_low=0.2; underlying trigger `donchian.sig_donchian_breakout(df, 20)`; BTC bias = sign(close − SMA(close, W)); runtime-only catalog via `beta_gate.catalog_entries()` (no strategy.py edit). Basket = original parent 5×2 Train-1 (same as `run_family` / parent experiment).

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

1. **Docs first:** write `spec/research/F006-hypothesis-beta-gate-exit-grid-sparse.md` (Observation→Falsification/Method from this card; leave Result/Decision empty until after run). Also restore parent hyp note `spec/research/F006-hypothesis-beta-gate.md` from tip `54fd498` / `b726db1` / limen branch if absent on base (read-only provenance; do not edit parent freeze).
2. Restore `beta_gate.py` + `tests/test_beta_gate.py` + parent experiment script provenance from tip `b726db1` / branch `limen/2026-09-29-f006-beta-gate-33f3dc36` (or autopsy source) **unchanged**.
3. Add sibling exit-grid script patterned on `scripts/f006_sube_inv_fvg_exit_grid.py` (and/or `scripts/f006_btc_filter_exit_grid.py` / `scripts/f006_liq_range_eqh_exit_grid.py` / `scripts/f006_vol_regime_wrap_exit_grid.py` / `scripts/f006_multi_tf_pa_exit_grid.py` on sibling branches) → `scripts/f006_beta_gate_exit_grid.py` writing `output/f006_beta_gate/exit_grid/`.
4. Run Train-1 only; dual H2; rank tables; manifest records producing commit.
5. Targeted pytest for sparse-month ABSENT vs scored and NO_TRAIL reproduction. Stop when docs+harness+evidence committed on job branch. No merge. No follow-up spawn.

---

## Falsification

- H1 falsified for a cell if no frozen H1-pass name has mean Train-1 > 0 under that cell.
- H2 falsified if every H1-clearer fails both legacy and sparse H2.
- Exit regression: TP/trail cell with higher WR but lower mean Train-1 than NO_TRAIL for the same name = falsified as improvement (protocol §8) — same lesson as closed btc_filter / liq_range_eqh / vol_regime_wrap / multi_tf_pa exit-grids.
- Any entry retune, new W / β_min / β_low / Donchian n / BTC-bias definition, catalog5/ORB/ABS-ATR/Donchian FREEZE reopen, holdout peek, or merge invalidates the run.

## Implementation notes (frozen before code)

- Sparse-month bucket: trade `exit_time` converted to Europe/Warsaw; only Train-1 calendar months (`f006_family_runner.TRAIN1_MONTHS`) scored; months with zero exits = ABSENT.
- Legacy H2 = parent `promotion_pass` rule (12 valid months, all valid months equity-PnL ≥ 0, DD ≤ 50%, Train-1 PnL ≥ 0, ≥1 trade).
- Pooled rank = trade-weighted win_rate across the two BETA names (DONCHIAN_55 excluded); per-name rank = same metric within name. H1/H2 decision reads the per-name table for `BETA_GATE_DONCH20` (the only parent H1-clearer); `BETA_GATE_MR_DONCH20` is reported but is not an H1-clearer at NO_TRAIL.
- §8 regression flag per name×cell: `win_rate > NO_TRAIL win_rate` AND `mean train1_net_pnl < NO_TRAIL mean` for the same name.
- Harness: `scripts/f006_beta_gate_exit_grid.py` → `output/f006_beta_gate/exit_grid/`; must reproduce parent `output/f006_beta_gate/raw/*` NO_TRAIL rows exactly and DONCHIAN_55 control rows. Entry one-shot mask computed once per series × name and shared by all four cells.

## Result

Train-1 only, run 2026-09-30. Harness `scripts/f006_beta_gate_exit_grid.py` at producing commit `f506217` (manifest `git_commit`); evidence `output/f006_beta_gate/exit_grid/` (results / monthly / trades / rank_by_name / rank_pooled / per-cell dirs / manifest). 90 runs = 2 names × 10 series × 4 cells + DONCHIAN_55 × 10 on NO_TRAIL.

Checks: parent NO_TRAIL reproduction **30/30 rows, 0 mismatches** (n_calls, n_trades, n_wins, win_rate, net_pnl, train1_net_pnl, DD, final_equity, n_valid_months, month sign, legacy H2 vs parent `promotion_pass`; 20 BETA rows + 10 DONCHIAN_55 rows against `output/f006_beta_gate/raw/*`); DONCHIAN_55 harness control 10/10, 0 mismatches, mean Train-1 **+58.387**; one-shot violations 0; `n_calls` identical across cells (2840 per cell for BETA_GATE_DONCH20 = parent). `beta_gate.py` byte-identical to `b726db1` and to `output/f006_signal_autopsy/sources/beta_gate.py`.

Per name × cell (trade-weighted WR; mean Train-1 over 10 series; legacy/sparse H2 = series passing):

| Name | Cell | WR % | mean Train-1 | H1 | trades/series | max DD % | legacy H2 | sparse H2 | §8 regression |
| --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | --- |
| BETA_GATE_DONCH20 | TRAIL_a0.03_t0.02 | 36.18 | −173.76 | fail | 182.4 | 74.37 | 0 | 0 | yes |
| BETA_GATE_DONCH20 | TP_x2 | 32.64 | −30.82 | fail | 164.5 | 38.09 | 0 | 0 | yes |
| BETA_GATE_DONCH20 | TRAIL_a0.06_t0.04 | 30.93 | −114.03 | fail | 160.7 | 53.93 | 0 | 0 | yes |
| BETA_GATE_DONCH20 | NO_TRAIL | 26.65 | **+31.40** | pass | 136.2 | 31.97 | 0 | 0 | — |
| BETA_GATE_MR_DONCH20 | TP_x2 | 9.09 | −2.75 | fail | 1.1 | 3.47 | 0 | 0 | no (PnL up, still < 0) |
| BETA_GATE_MR_DONCH20 | TRAIL_a0.03_t0.02 | 9.09 | −2.61 | fail | 1.1 | 3.77 | 0 | 0 | no (PnL up, still < 0) |
| BETA_GATE_MR_DONCH20 | TRAIL_a0.06_t0.04 | 9.09 | −2.87 | fail | 1.1 | 4.01 | 0 | 0 | no (PnL up, still < 0) |
| BETA_GATE_MR_DONCH20 | NO_TRAIL | 0.00 | −3.65 | fail | 1.1 | 5.55 | 0 | 0 | — |

Pooled (descriptive, two BETA names, 20 series): TRAIL_a0.03_t0.02 WR 36.02 / mean −88.19; TP_x2 32.49 / −16.78; TRAIL_a0.06_t0.04 30.78 / −58.45; NO_TRAIL 26.44 / +13.87.

- **WR rank winner** (policy primary key): TRAIL_a0.03_t0.02 for BETA_GATE_DONCH20 (+9.5 pp WR) — but every non-NO_TRAIL cell drives mean Train-1 below zero.
- **H1 per cell:** NO_TRAIL holds (BETA_GATE_DONCH20 +31.40, parent reproduced). TP_x2, TRAIL_a0.06_t0.04, TRAIL_a0.03_t0.02 each **falsified** (no name > 0). Interval split for BETA_GATE_DONCH20 (mean Train-1, 60m / 240m): NO_TRAIL −13.49 / +76.29; TP_x2 −81.57 / +19.94; TRAIL_a0.06_t0.04 −165.75 / −62.31; TRAIL_a0.03_t0.02 −250.50 / −97.03.
- **H2 dual:** legacy 0/80 name×series×cell; `h2_sparse_absent_zero_trade` 0/80. Under NO_TRAIL BETA_GATE_DONCH20 scores all 12 exit-months on every series (0 ABSENT) and has 5–10 losing scored months per series; TP_x2 3–10, TRAIL_a0.06_t0.04 7–12, TRAIL_a0.03_t0.02 10–12. The sparse rule changes nothing: the family is dense and losing months are traded months. All 460 ABSENT months belong to BETA_GATE_MR_DONCH20 (11 trades total over 10 series), which fails on Train-1 PnL < 0 regardless.
- **§8:** all 3 TP/trail cells for BETA_GATE_DONCH20 are WR-for-PnL regressions (WR +4.3…+9.5 pp, mean Train-1 −62.2…−205.2 vs NO_TRAIL). Exit mix confirms fat-winner truncation (BETA_GATE_DONCH20 winners from `trades.csv`): NO_TRAIL 363 winners, mean +8.54 (354 on `signal_reverse` at +8.40); TP_x2 537 winners, mean +5.01 (462 `take_profit` at +5.68); TRAIL_a0.06_t0.04 497, mean +3.59 (400 `trailing_sl` at +3.98); TRAIL_a0.03_t0.02 660, mean +1.44 (651 `trailing_sl` at +1.45).
- **Density note:** NO_TRAIL trades/series 136.2 (DONCH20) / 1.1 (MR; mechanism-degenerate, not an H1-clearer). TP/trail raise realized trades/series (136.2 → 182.4) without new signal opportunities: `n_calls` unchanged, positions free up earlier for later one-shot calls already in the mask (n_trades ≤ n_calls everywhere).

## Decision

**Ordinary DNR for the BETA-GATE exit-grid continuation** (same outcome shape as closed btc_filter / liq_range_eqh / vol_regime_wrap / multi_tf_pa exit-grids).

- H1: holds only under NO_TRAIL (parent reproduced exactly; BETA_GATE_DONCH20 +31.40). Falsified under TP_x2, TRAIL_a0.06_t0.04, TRAIL_a0.03_t0.02.
- H2: falsified under both legacy and `h2_sparse_absent_zero_trade` for the sole H1-clearer in every cell.
- §8: every TP/trail cell is a WR-for-PnL regression; no exit cell is promoted. Uneven months are **not** explained by exit geometry — hypothesis Y (nierówne miesiące przez exit geometry) is rejected for this frozen entry set.
- No entry retune (W / β_min / β_low / Donchian n / BTC bias unchanged), no new name, no holdout, no merge. Entries stay frozen at `b726db1`. Parent H-BETA-GATE-01 Decision (H1 trend gate / H2 falsified) stands unchanged.
