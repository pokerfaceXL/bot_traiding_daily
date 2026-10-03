# F006 — H-BB-20-2-ABS-ATR-ENTRY-GATE-01 (pre-registered)

> Pre-registered **before** implementing or running the gate. `BB_20_25_EMA200`
> is **FREEZE** after its own HTF-direction result (`3495b16`, FALSIFIED
> (a)+(c)+(d)). That result, and every earlier result on `BB_20_25_EMA200`,
> is **not** a test of `BB_20_2_EMA200`. Do not copy that name's control mean,
> its frozen ATR median, its floor, or its pass/fail onto this card.
> Entry-vol / abs-ATR on this name is still only DNR-by-transfer. Under the
> 2026-10-02 catalog5 correction it stays open until it is earned on this
> name's own trades. Autopsy numbers below are **observations**, not the test.

experiment_id: H-BB-20-2-ABS-ATR-ENTRY-GATE-01
date: 2026-10-03
base_strategy: BB_20_2_EMA200 (NO_TRAIL, max_sl_pct=0.03, one-shot entry, signal_reverse exit)

```text
Observation:
BB_20_2_EMA200 is aggregate-Train-1-positive and CONDITIONAL. Catalog5 monthly
table (`output/f006_notrail_monthly_catalog5/summary/results.csv`): 10 series,
sum of train1_net_pnl +953.217987, mean +95.3217987/series, 8/10 series
positive. Trio autopsy (`output/f006_catalog5_trio_autopsy/trades/BB_20_2_EMA200_train1_trades.csv`):
Train-1 entries n=756, pooled net +834.347778, initial_sl 358/756 (47.35%) at
0% WR, signal_reverse 388/756. Mean entry ATR%(14) is higher on initial_sl
(1.762) than on signal_reverse (1.079). Trades with net≥29.9: 12, pooled net
+1251.654084. Calendar-month pool of the catalog5 raw monthly nets is negative
in 8 of 12 months. That calendar count is an observation. The harness
entry-month floor, computed on the control cell the same way as the other
catalog gates, is the binding baseline. Exit, long-only, and breadth already
ran on this name's own series and did not clear the monthly floor. Abs-ATR was
FALSIFIED on other names. Those falsifications do not answer this name.

Problem:
Most losing trades die at the fixed initial_sl. The aggregate edge still
depends on signal_reverse runners. This name has no entry-time rule, earned
on its own trades, that cuts stop-outs without cutting those runners. Monthly
regularity is the unresolved target. Series-level positivity (8/10) has not
produced a series that clears §7.

Mechanism:
Noisy BB breakouts that fail into the initial stop tend to fire when absolute
ATR% is elevated, whereas breakouts that later travel to the opposite
structural extreme more often begin at lower absolute ATR%. The autopsy
measured that direction on this name (1.762 vs 1.079). Whether a causal
abs-ATR keep-gate improves expectancy and the monthly floor here, without
destroying the fat tails, is the open question. Another name's failure is
not the answer.

Hypothesis:
Adding a single causal entry gate that rejects a BB_20_2_EMA200 signal when
ATR%(14) on the signal bar exceeds a pre-registered threshold will raise mean
Train-1 net PnL versus the ungated NO_TRAIL baseline AND cut the initial_sl
share among remaining trades, while keeping enough of this name's big-winner
PnL that the pooled losing-month floor can improve — earned on this name's
own trades, not by analogy.

Change to test:
ONE entry refinement only: `atr_pct <= T` required to take the BB_20_2_EMA200
signal (else flat). No exit, sizing, symbol, interval, direction, or breadth
changes. NO_TRAIL unchanged. Reuse the ATR definition and gate intersection
in `scripts/f006_bb_20_25_abs_atr_gate.py` (`donchian.atr_pct_entry_gate`,
SMA true-range / close on the closed signal bar), pointed at this catalog
name. Do not reuse that script's EXPECTED_MEAN, CONTROL_NAME, or frozen median.

Baseline:
Ungated BB_20_2_EMA200 NO_TRAIL on the frozen 5-symbol × 2-interval Train-1
basket. Control must reproduce all 10 `train1_net_pnl` rows in
`output/f006_notrail_monthly_catalog5/summary/results.csv` for strategy
`BB_20_2_EMA200` (mean **+95.3217987**/series, sum **+953.217987**) before
any gated cell is trusted. Do not match +82.900262. That figure belongs to
`BB_20_25_EMA200`. `output/f006_signal_autopsy/catalog5_ema_bb/summary/results.csv`
does not contain this name; do not use it as the reference.

Metrics (pre-declared):
1. mean train1_net_pnl across 10 series (primary) / pooled net and net/trade
2. initial_sl share among closed Train-1-entry trades
3. n_trades (reject thin: mean n_trades/series < 10)
4. pooled losing-month floor (of 12, by entry-month, same definition as the
   BB_20_25 harness; confirm the control floor before comparing)
5. big-winner PnL retained vs this name's ungated baseline. Big winner =
   net≥29.9, frozen on the ungated blotter before gated cells. Do not import
   the other name's $968.02 set.
6. #symbols net-positive / per-symbol losing-month floor (informational)
7. number_of_trials = 5

Expected improvement:
Mean train1_net_pnl > this name's control AND initial_sl share down ≥10pp at
the best-PnL T AND ≥50% of this name's big-winner PnL retained AND pooled
losing-month floor strictly below this name's ungated entry-month floor AND
mean trades/series ≥ 10.

Falsification condition (any one ⇒ FALSIFIED):
(a) mean train1_net_pnl ≤ baseline at every T; OR
(b) every non-thin T removes >50% of baseline big-winner PnL; OR
(c) initial_sl share fails to fall ≥10pp at the best-PnL T; OR
(d) pooled losing-month floor does not improve (stays ≥ baseline floor) at
    every T that otherwise passes (a)–(c); OR
(e) improvement is only from collapsing to <10 trades/series mean.
Do not widen T after seeing results without a new written hypothesis.
Do not declare this falsified because another catalog name was falsified.

Data split:
Train-1 only (2024-03-01 ≤ entry < 2025-03-01 UTC). No validation/holdout.
If a T looks promising, schedule a separate validation run later — do not
tune on it now.

Budget:
T grid fixed before run, same shape as the Donchian abs-ATR gate, computed
on THIS name:
{median_train1_atr_pct of this name's ungated Train-1 entries, 1.0%, 1.25%,
1.5%, 2.0%} — max 5 trials.
Freeze that median to disk before evaluating gated cells. The other name's
median (1.165%) is not this median. Report all cells. Pick at most one T
for any follow-up.
```

decision_if_pass: REFINE (update BB_20_2_EMA200 profile metrics; consider a separate validation later; do not open holdout in this run)
decision_if_fail: entry-vol / abs-ATR closed on this name's own trades. Worker must not
  set FREEZE and must not change profile status. The coordinator decides the
  profile only after the result. Do not treat this result as evidence about
  other catalog5 names. Do not retune the gate inside this run.

## Result

Run: `python3 scripts/f006_bb_20_2_abs_atr_gate.py` (cwd = main checkout for the
frozen `*_20240126T000000Z_20250301T000000Z.csv` Train-1 caches only; checksums
pass the harness check). Artifacts: `output/f006_bb_20_2_abs_atr_gate/`
(`grid_freeze.json`, `cell_summary.csv`, `results.csv`, `manifest.json`,
`run.log`, per-cell `raw/` + `blotters/` + `summary.json`).

Control replay: `BB_20_2_EMA200` ungated NO_TRAIL reproduces all 10 rows of
`output/f006_notrail_monthly_catalog5/summary/results.csv` exactly on
`train1_net_pnl` (max |diff| 0.0) and `n_trades`; sum **+953.217987**, mean
**+95.3217987**/series. Frozen to `grid_freeze.json` before any gated cell:
median entry ATR%(14) of this name's 756 ungated Train-1 entries =
**1.176636%**; big winner = net≥29.9 on the ungated blotter → **12 trades,
+1251.654084**. Control harness entry-month losing-month floor = **7/12**
(computed, not assumed; losing entry months 2024-03/04/05/06/08/09/12).
number_of_trials = 5.

| cell | T (ATR%) | mean train1 net/series | entry cohort net | net/trade | n entries (mean/series) | initial_sl share | Δ initial_sl (pp) | big winners kept | big-winner PnL kept | losing entry months |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| control | — | **+95.3218** | +834.35 | 1.104 | 756 (75.6) | 47.35% | — | 12/12 | 1251.65 (100%) | **7/12** |
| median | 1.1766 | +52.2257 | +427.69 | 0.979 | 437 (43.7) | 33.87% | 13.49 | 5/12 | 488.54 (39.0%) | 6/12 |
| t_1_0 | 1.00 | +53.2348 | +438.37 | 1.238 | 354 (35.4) | 29.10% | 18.26 | 5/12 | 480.58 (38.4%) | 7/12 |
| t_1_25 | 1.25 | +49.8092 | +403.52 | 0.872 | 463 (46.3) | 34.77% | 12.58 | 5/12 | 488.54 (39.0%) | 6/12 |
| t_1_5 | 1.50 | +39.3347 | +317.72 | 0.576 | 552 (55.2) | 37.68% | 9.67 | 5/12 | 488.54 (39.0%) | 6/12 |
| t_2_0 | 2.00 | +64.0461 | +564.85 | 0.861 | 656 (65.6) | 43.90% | 3.45 | 7/12 | 905.20 (72.3%) | 9/12 |

Falsifiers (on this name's own trades):

- (a) **FALSIFIED.** Mean train1 net ≤ control (+95.32) at every T; best is
  t_2_0 at +64.05.
- (b) Not triggered. t_2_0 (non-thin) keeps 72.3% of big-winner PnL; the four
  tighter cells keep 38–39%.
- (c) **FALSIFIED.** Best-PnL T = t_2_0; initial_sl share falls only 3.45pp
  (<10pp). The cells that cut ≥10pp (median, 1.0, 1.25) lose ~45% of mean PnL
  and >60% of big-winner PnL.
- (d) Not reachable: no T passes (a)–(c), so no cell qualifies for the floor
  test. Informational: median / 1.25 / 1.5 reach 6/12 (< 7/12) while failing
  (a); t_1_0 stays 7/12; t_2_0 worsens to 9/12.
- (e) Not applicable: every cell is non-thin (≥35.4 entries/series) and none
  improves mean PnL.

Pre-declared checks passed by no cell (`passing_cells: []` in `manifest.json`).
Directionally, the 1.762 vs 1.079 autopsy split holds (tighter T cuts stop-outs),
but the gate removes signal_reverse runners and big winners faster than it
removes stop-out losses. Profile `status:` untouched; Decision left to the
coordinator.

## Decision

**FALSIFIED (a)+(c).** Checked 2026-10-03 ~11:22 Europe/Warsaw against
`output/f006_bb_20_2_abs_atr_gate/cell_summary.csv`, `grid_freeze.json`, and
`manifest.json` on the FF-merged run `f7ac677` (review PASS, job
`2026-10-03-f006-bb202-abs-atr-review-59bf2edf`). The Result table matches the
artifact after ordinary rounding. Manifest `passing_cells` is `[]` and
`decision` is null. Harness control `max_abs_train1_diff` is 0.0.

Control reproduced this name's catalog5 baseline: mean Train-1 net
**+95.3217987/series** (sum +953.217987), entry cohort **n=756, +834.347778**,
initial-SL share **0.473545 (47.35%)**, big-winner set **12 trades,
+1251.654084** (net≥29.9), pooled losing entry-months **7/12**. Frozen median
entry ATR% **1.176636**. `number_of_trials = 5`.

Best-PnL cell **t_2_0** (T=2.0%): mean **+64.046122/series**, which is below
the control. Initial-SL share **0.439024**, drop **3.45 pp** (required ≥10 pp).
Big-winner PnL retained **72.3%** on the published retention metric. Floor
**9/12**. The cells that cut initial-SL by ≥10 pp (median, t_1_0, t_1_25) all
sit near +50/series and keep ~39% of big-winner PnL.

(a) fires: every T has mean Train-1 net ≤ +95.3217987. (b) does not fire on
the published metric: t_2_0 keeps 72.3% of big-winner PnL, so it is not true
that every non-thin T removes >50%. (c) fires: at the best-PnL T the
initial-SL drop is 3.45 pp. (d) is not reachable: no T passes (a)–(c). (e)
does not fire: every cell is non-thin (≥35.4 entries/series). No cell passed
the pre-declared checks.

Review noted that big-winner retention counts any gated trade with net≥29.9,
not necessarily the original 12 keys. That caveat cannot rescue (a) or (c).
It is not used to add (b).

Entry-vol / abs-ATR is closed on `BB_20_2_EMA200` own trades. Do not retune T.
Do not treat this as evidence about `EMA_50_200`, `EMA3_13_50_200`, or
`BB_20_25_EMA200`.

**Strategy status:** **CONDITIONAL**. Do not FREEZE. Exit, long-only, breadth,
and now entry-vol are closed on this name. Position sizing has never been
tested here. Other §8 entry structure (candle confirm, breakout structure, HTF
direction, liquidity) has not been pre-registered here. §7 develop-not-abandon:
do not leave this name while a licensed axis is still open, and do not jump to
`EMA_50_200` or `EMA3_13_50_200`. `BB_20_25_EMA200` FREEZE (`f1fffc8`) does
not transfer.

**reason:** falsifiers (a) and (c). A keep-low-ATR gate on this name's own
trades does not raise mean Train-1 net PnL, and the best-PnL threshold does
not cut the initial-SL share by 10 pp. Tighter thresholds that do cut stops
also cut the runners that carry the aggregate edge.

**next_action:** one position-sizing hypothesis on this name only,
`H-BB-20-2-XSYM-AGREE-SIZING-01`. The ungated book is aggregate-positive, so
§8 allows sizing. The stake map is a structural encoding of peer-symbol
agreement, not an abs-ATR retune and not a copy of the `BB_20_25_EMA200`
Train-1 pass or Val-1 fail. Entry structure stays open.
