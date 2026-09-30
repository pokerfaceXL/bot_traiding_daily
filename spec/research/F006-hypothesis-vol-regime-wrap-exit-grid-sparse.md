# F006 — Hypothesis: H-VOL-REGIME-WRAP-EXIT-GRID-SPARSE-01 (exit grid + sparse H2 on frozen VOL-REGIME-WRAP entries)

> Pre-registration. Everything from **Observation** through **Method** / **Falsification** was copied
> from the coordinator card `/tmp/F006-card-H-VOL-REGIME-WRAP-EXIT-GRID-SPARSE-01.md` and committed on
> base `d016659` BEFORE the exit-grid harness existed and before any Train-1 run. **Result** and
> **Decision** are filled only after the run. Standing policy: `/tmp/F006-eval-policy-sparse-h2-and-exits-2026-09-29.md`.
> Parent: `spec/research/F006-hypothesis-vol-regime-wrap.md` (restored from tip `7341182`, provenance only).

```yaml
id: H-VOL-REGIME-WRAP-EXIT-GRID-SPARSE-01
ticket: S7-EXIT-GRID
name: VOL-REGIME-WRAP standing exit grid + dual sparse H2 (entries frozen)
status: open_prereg
parent: H-VOL-REGIME-WRAP-01 tip 7341182 / limen/2026-09-29-f006-vol-regime-wrap-f663b8a1 (module+hyp+tests on branch tip 7deae4f; Train-1 NO_TRAIL evidence on tip 7341182 / origin/main output/)
universe: BTC/ETH/SOL/XRP/DOGE USDT perps × {60,240}
data_needs: [ohlcv]
exit: exit_grid standing (NO_TRAIL + TP_x2 + TRAIL_a0.06_t0.04 + TRAIL_a0.03_t0.02)
h2: dual legacy + h2_sparse_absent_zero_trade (exit-month; zero trades = ABSENT)
session_filters: off
source: COORDINATOR_RESEARCH_PROTOCOL §7/§8 stuck-loop recovery; digest output/f006_cross_family_digest.md; standing policy /tmp/F006-eval-policy-sparse-h2-and-exits-2026-09-29.md; prior siblings H-BTC-FILTER-EXIT-GRID-SPARSE-01 (closed ordinary DNR / §8 regression) and H-LIQ-RANGE-EQH-EXIT-GRID-SPARSE-01 (in review tip a20a589)
parent_dnr_do_not_reopen_entry:
  - H-VOL-REGIME-WRAP-01 entry construction stays frozen (ATR%/W/edges/hysteresis/Donchian(20) wrap) — this card is EXIT ONLY
  - btc_filter exit-grid closed (ordinary DNR H2=0; §8 TP/trail regression tip f02458b) — do not reopen
  - liq_range_eqh exit-grid currently in review (tip a20a589 / …948151cf) — do not spawn a second liq job
  - catalog5 FREEZE / ORB / ABS-ATR / PARTIAL / EXIT-CLASS stay closed
  - Donchian FREEZE / HTFP ordinary DNR / CASCADE-FADE stay closed
  - Sube exit-grid already done — skip
```

**Sentence (protocol form):** Na podstawie wyniku X (H1 pass / H2 fail on NO_TRAIL for VOLW_HIGH_BRK_20 ~+59.65; btc_filter + liq_range_eqh exit-grids queued/closed as Level-B §8 path) podejrzewam Y (nierówne miesiące przez exit geometry), dlatego testuję Z (standing ≤4-cell exit grid + h2_sparse_absent_zero_trade).

**Train-1 only.** No holdout / Validation. No entry retune. No merge to main. No new catalog names.

---

## Observation

Frozen-schema digest ranks `VOLW_HIGH_BRK_20` among Level-B H1-pass / H2-falsified families that have **not** yet run the standing sparse/swing exit grid (`NO_TRAIL`, `TP_x2`, `TRAIL_a0.06_t0.04`, `TRAIL_a0.03_t0.02` + `h2_sparse_absent_zero_trade`). After `btc_filter` exit-grid closed as ordinary DNR (H2=0; §8 regression under TP/trail — tip f02458b reviewed PASS, not FF-merged; origin/main stays d016659) and `liq_range_eqh` exit-grid tip `a20a589` entered Claude review (`…948151cf`), `vol_regime_wrap` is the next Level-B name without a standing exit grid (~+59.65 mean Train-1).

Digest / parent NO_TRAIL facts (Train-1, 10 series; manifest tip `7deae4f` / evidence tip `7341182`):
- `VOLW_HIGH_BRK_20`: mean Train-1 **+59.6513**, 88.6 trades/series, WR≈23.8%, DD≈14.7%, promotion_pass **0/10**
- `VOLW_HL_20`: +1.3981 (H1 pass / H2 fail; denser combo wrap)
- `VOLW_LOW_MR_20`: −2.8766 (H1 fail — keep in grid for NO_TRAIL reproduction only; not an H1-clearer)

Family H2 status: **falsified** (legacy promotion_pass = 0 across H1-clearers; every H1-passing series has ≥3 losing valid months).

Per COORDINATOR_RESEARCH_PROTOCOL §7: aggregate-positive with uneven months → diagnose before abandoning. §8 Exit refinement: change only post-entry geometry. Standing eval policy requires the exit grid + dual H2 before sole-DNR on legacy monthly H2. Prior siblings already showed §8 TP/trail can regress mean Train-1 despite WR — apply the same falsifier here.

This is **not** a new entry family. Entries stay exactly tip `7deae4f` / `vol_regime_wrap.py` from limen branch `limen/2026-09-29-f006-vol-regime-wrap-f663b8a1` (or byte-identical autopsy copy `output/f006_signal_autopsy/sources/vol_regime_wrap.py`). Evidence/decision tip `7341182` is read-only provenance.

---

## Hypothesis

**H1 (per exit cell, same as parent).** At least one of the two H1-passing frozen VOLW names (`VOLW_HIGH_BRK_20`, `VOLW_HL_20`) has mean Train-1 `train1_net_pnl > 0` over the fixed ten-series pool under that exit cell. Primary gate geometry for cross-cell comparability remains **NO_TRAIL** (must reproduce parent NO_TRAIL rows within harness tolerance).

**H2 (conditional on H1, dual).** For each H1-clearing name×cell, report:
1. **legacy H2** — unchanged 12-valid-month promotion checklist
2. **`h2_sparse_absent_zero_trade`** — score only exit-calendar months (Europe/Warsaw) with `n_trades > 0`; zero-trade months = ABSENT/neutral; require all scored months `net_pnl >= 0`, series DD ≤ 50%, Train-1 equity PnL ≥ 0, ≥1 Train-1 exit

**Falsify exit cells (§8):** a TP/trail cell that improves win_rate by killing fat winners such that mean Train-1 PnL falls below the NO_TRAIL cell for the same name is a **regression** (do not promote on WR alone). Rank cells by pooled trade-weighted win_rate; still report train1_net_pnl / H1 for every cell.

---

## Frozen names (exactly three — parent set; no expansion)

| Name | HIGH bucket | MID | LOW bucket | role |
| --- | --- | --- | --- | --- |
| `VOLW_HIGH_BRK_20` | Donchian(20) as-is | 0 | 0 | primary / best mean |
| `VOLW_LOW_MR_20` | 0 | 0 | inverted Donchian(20) | H1-fail ablation (keep for NO_TRAIL reproduction) |
| `VOLW_HL_20` | Donchian(20) as-is | 0 | inverted Donchian(20) | combo H1-marginal |

Shared freeze unchanged: ATR14/close percentile W=100, edges LOW=25 / HIGH=75, hysteresis=10, base trigger `donchian.sig_donchian_breakout(df, 20)`. Basket = original parent 5×2 Train-1 (same as `run_family` / parent experiment).

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

1. **Docs first:** write `spec/research/F006-hypothesis-vol-regime-wrap-exit-grid-sparse.md` (Observation→Falsification/Method from this card; leave Result/Decision empty until after run). Also restore parent hyp note `spec/research/F006-hypothesis-vol-regime-wrap.md` from tip `7341182` / `745f888` / limen branch if absent on base (read-only provenance; do not edit parent freeze).
2. Restore `vol_regime_wrap.py` + `tests/test_vol_regime_wrap.py` + parent experiment script provenance from tip `7deae4f` / branch `limen/2026-09-29-f006-vol-regime-wrap-f663b8a1` (or autopsy source) **unchanged**.
3. Add sibling exit-grid script patterned on `scripts/f006_sube_inv_fvg_exit_grid.py` (and/or `scripts/f006_btc_filter_exit_grid.py` / `scripts/f006_liq_range_eqh_exit_grid.py` on sibling branches) → `scripts/f006_vol_regime_wrap_exit_grid.py` writing `output/f006_vol_regime_wrap/exit_grid/`.
4. Run Train-1 only; dual H2; rank tables; manifest records producing commit.
5. Targeted pytest for sparse-month ABSENT vs scored and NO_TRAIL reproduction. Stop when docs+harness+evidence committed on job branch. No merge. No follow-up spawn.

---

## Falsification

- H1 falsified for a cell if no frozen H1-pass name has mean Train-1 > 0 under that cell.
- H2 falsified if every H1-clearer fails both legacy and sparse H2.
- Exit regression: TP/trail cell with higher WR but lower mean Train-1 than NO_TRAIL for the same name = falsified as improvement (protocol §8) — same lesson as closed btc_filter / in-review liq_range_eqh exit-grids.
- Any entry retune, new ATR%/W/edges/hysteresis/Donchian n, catalog5/ORB/ABS-ATR/Donchian FREEZE reopen, holdout peek, or merge invalidates the run.

## Result

_(empty until after Train-1)_

## Decision

_(empty until after Train-1)_
