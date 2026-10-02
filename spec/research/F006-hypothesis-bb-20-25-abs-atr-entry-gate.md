# F006 — H-BB-20-25-ABS-ATR-ENTRY-GATE-01 (pre-registered)

> Pre-registered **before** implementing or running the gate. Entry-vol/abs-ATR was only ever
> DNR-by-transfer for `BB_20_25_EMA200`; under the 2026-10-02 catalog5 FREEZE→CONDITIONAL
> correction this axis is open until earned on this name's own trades. Dual autopsy numbers
> below are **observations**, not the test.

experiment_id: H-BB-20-25-ABS-ATR-ENTRY-GATE-01
date: 2026-10-02
base_strategy: BB_20_25_EMA200 (NO_TRAIL, max_sl_pct=0.03, one-shot entry, signal_reverse exit)

```text
Observation:
BB_20_25_EMA200 is aggregate-Train-1-positive (dual autopsy pooled net +709.85 on n=512;
catalog5 monthly best-in-batch floor 3/12 on SOLUSDT/60) but still fails §7 monthly promotion
(0/10 series clear). Exit axis closed (EXIT-CLASS / PARTIAL-EXIT FALSIFIED). Direction and
breadth levers already run on this name's own trades via H-CATALOG5-CLASS-CLOSURE-01 and did
not lower the pooled floor below 7/12. Dual autopsy: mean entry ATR%(14) is higher on
initial_sl exits (1.70) than on signal_reverse exits (1.06); initial_sl share 58% at 0% WR;
signal_reverse carries the profit (WR 57.6%, sum +1532). Abs-ATR entry gate was FALSIFIED on
DONCHIAN_55_NO_TRAIL and entry-vol was independently FALSIFIED on EMA3_21_50_200, but never
run as a formal protocol hyp on BB_20_25_EMA200's own trades (only DNR-by-transfer).

Problem:
Most trades die at the fixed initial_sl; aggregate edge depends on rare signal_reverse runners.
We lack an entry-time rule, earned on THIS name, that reduces stop-outs without cutting those
runners. Monthly regularity remains the unresolved target.

Mechanism:
Noisy BB breakouts that fail into the initial stop tend to fire when absolute ATR% is elevated,
whereas breakouts that later travel to the opposite structural extreme more often begin at
lower absolute ATR%. This is the same directional shape the dual autopsy measured here; the
open question is whether a causal abs-ATR keep-gate improves expectancy AND monthly floor on
this name without destroying the fat tails — which transfer from Donchian/EMA3_21 does not
answer.

Hypothesis:
Adding a single causal entry gate that rejects a BB_20_25_EMA200 signal when ATR%(14) on the
signal bar exceeds a pre-registered threshold will raise mean Train-1 net PnL / expectancy
versus the ungated NO_TRAIL baseline AND cut the initial_sl share among remaining trades,
while keeping enough big-winner PnL that the pooled losing-month floor can improve — earned
on this name's own trades, not by analogy.

Change to test:
ONE entry refinement only: `atr_pct <= T` required to take the BB_20_25_EMA200 signal (else
flat). No exit, sizing, symbol, interval, direction, or breadth changes. NO_TRAIL unchanged.
Reuse the same ATR definition and gate intersection pattern as
`scripts/f006_donchian_abs_atr_gate.py` / `donchian.atr_pct_entry_gate` (SMA true-range / close
on the closed signal bar), applied to this catalog name via the family harness.

Baseline:
Ungated BB_20_25_EMA200 NO_TRAIL on the frozen 5-symbol × 2-interval Train-1 basket. Control
must reproduce dual-autopsy / catalog5 figures for this name (pooled Train-1 entry net ≈
+709.85 on the autopsy blotter cohort, or the harness mean train1_net_pnl already recorded
for this name — report which and match exactly before gating).

Metrics (pre-declared):
1. mean train1_net_pnl across 10 series (primary) / pooled net and net/trade
2. initial_sl share among closed Train-1-entry trades
3. n_trades (reject thin: mean n_trades/series < 10)
4. pooled losing-month floor (of 12, by entry-month)
5. big-winner PnL retained vs this name's ungated baseline (define big winner on ungated
   blotter; prefer net≥29.9 for class consistency with class-closure, or the Donchian-gate
   note's net≥10 if reusing that script's helper — pick ONE before run and freeze it)
6. #symbols net-positive / per-symbol losing-month floor (informational)
7. number_of_trials (threshold grid size)

Expected improvement:
Mean train1_net_pnl > baseline AND initial_sl share down ≥10pp AND ≥50% of big-winner PnL
retained AND pooled losing-month floor strictly below this name's ungated floor (7/12 on the
pooled autopsy monthly; confirm baseline floor in the control cell before comparing).

Falsification condition (any one ⇒ FALSIFIED):
(a) mean train1_net_pnl ≤ baseline at every T; OR
(b) every non-thin T removes >50% of baseline big-winner PnL; OR
(c) initial_sl share fails to fall ≥10pp at the best-PnL T; OR
(d) pooled losing-month floor does not improve (stays ≥ baseline floor) at every T that
    otherwise passes (a)–(c); OR
(e) improvement is only from collapsing to <10 trades/series mean.
Do not widen T after seeing results without a new written hypothesis.

Data split:
Train-1 only (2024-03-01 ≤ entry < 2025-03-01 UTC). No validation/holdout. If a T looks
promising, schedule a separate validation run later — do not tune on it now.

Budget:
T grid fixed before run, same shape as Donchian abs-ATR gate:
{median_train1_atr_pct_of_this_name's ungated entries, 1.0%, 1.25%, 1.5%, 2.0%} — max 5 trials.
Freeze the median to disk before evaluating gated cells. Report all cells. Pick at most one T
for any follow-up.
```

decision_if_pass: REFINE (update BB_20_25_EMA200 profile metrics; consider validation)
decision_if_fail: keep CONDITIONAL; mark entry-vol/abs-ATR axis closed on this name's own trades;
  next open axis = position sizing (or another §8 entry structure with a new written mechanism)

## Result

Ran 2026-10-02. Base: a77fc9c. Script: `scripts/f006_bb_20_25_abs_atr_gate.py`.
Artifacts: `output/f006_bb_20_25_abs_atr_gate/`.

Control reproduced catalog5 harness baseline exactly: mean Train-1 net PnL = +82.90 across
10 series (pooled entry cohort n=512, net=+709.85). Frozen median entry ATR% = 1.165%
(computed on ungated cohort before any gated eval).

```text
Threshold  Mean     Pooled   Entry-n  SL%   ΔSL(pp)  BigWin  Retain%  Floor  Pass
─────────────────────────────────────────────────────────────────────────────────
control    +82.90   +829.00   512     58.0%   —       10/968   100%     7/12   —
median     +43.14   +431.42   296     48.3%   +9.7    1/336     35%     7/12   ✗
1.0%       +37.36   +373.57   239     43.9%  +14.1    1/336     35%     6/12   ✗
1.25%      +47.19   +471.93   314     48.4%   +9.6    3/409     42%     6/12   ✗
1.5%       +49.13   +491.31   363     49.9%   +8.1    3/409     42%     7/12   ✗
2.0%       +73.76   +737.59   435     54.9%   +3.1    7/824     85%     7/12   ✗
```

*BigWin = count/pooled_pnl of net≥29.9 trades; Retain% = gated_big_pnl / baseline_big_pnl;*
*Floor = losing entry-months out of 12.*

**Verdict: FALSIFIED** (all 5 T fail)

Every threshold reduced mean Train-1 net PnL below the ungated baseline (+82.90), violating
pre-declared falsifier (a). Even T=1.0%, which achieved the largest initial_sl share drop
(14.1pp) and the lowest losing-month floor (6/12), still underperformed the baseline by
45.54 mean PnL. The gate correctly reduced stop-outs, but the filtered-out trades included
essential fat-tail winners: baseline had 10 big winners (net≥29.9) contributing +968 pooled
PnL; T=1.0% retained only 1 (+336, 35% of baseline big-winner PnL). The median and tight
thresholds destroyed >60% of big-winner economics; even the loose T=2.0% retained 85% of
big-winner PnL but still fell 9.14 mean PnL short of the baseline, and its sl share
improvement was only 3.1pp (below the 10pp target).

The directional shape observed in the dual autopsy (mean entry ATR% higher on initial_sl
exits than on signal_reverse exits) was real, but the causal mechanism failed: removing
high-ATR entries filtered essential signal_reverse runners, not just noise. The losing-month
floor remained 7/12 at most thresholds (same as ungated), and the one threshold that reached
6/12 (T=1.0% and 1.25%) did so by collapsing trade count and destroying mean expectancy, not
by improving monthly regularity.

Conclusion: abs-ATR entry gate **FALSIFIED** on BB_20_25_EMA200's own trades. The entry-vol
axis remains closed for this name (was DNR-by-transfer from Donchian/EMA3_21, now formally
evaluated and rejected). Monthly promotion (§7) and the 7/12 pooled floor remain unresolved;
next open lever = position sizing or a §8 entry structure with a new written mechanism.

## Decision

(empty — coordinator only after Result)
