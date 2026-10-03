# F006 — H-EMA-50-200-ABS-ATR-ENTRY-GATE-01 (pre-registered)

> Pre-registered **before** implementing or running the gate. `BB_20_2_EMA200`
> is **FREEZE** after its own liquidity result (`776e167`, FALSIFIED (c)).
> That result, and every earlier result on `BB_20_2_EMA200` or
> `BB_20_25_EMA200`, is **not** a test of `EMA_50_200`. Do not copy either
> name's control mean (+95.3217987 or +82.900262), its frozen ATR median,
> its floor, or its pass/fail onto this card. Entry-vol / abs-ATR on this
> name is still only a withdrawn DNR-by-transfer. Under the 2026-10-02
> catalog5 correction it stays open until it is earned on this name's own
> trades. Autopsy numbers below are **observations**, not the test. Do not
> start `EMA3_13_50_200` in this run. Do not invent a new signal family.

experiment_id: H-EMA-50-200-ABS-ATR-ENTRY-GATE-01
date: 2026-10-03
base_strategy: EMA_50_200 (NO_TRAIL, max_sl_pct=0.03, one-shot entry, signal_reverse exit)

```text
Observation:
EMA_50_200 is aggregate-Train-1-positive and CONDITIONAL. Catalog5 monthly
table (`output/f006_notrail_monthly_catalog5/summary/results.csv`, strategy
EMA_50_200, 10 rows): sum of train1_net_pnl +726.693115, mean
+72.6693115/series, 7/10 series positive, pooled n_trades 364. Dual autopsy
(`output/f006_catalog5_dual_autopsy/trades/EMA_50_200_train1_trades.csv`):
Train-1 entries n=330, pooled net +587.3851786486206, initial_sl 213/330
(0.6454545454545455) at 0% WR, signal_reverse 112/330. Mean entry ATR%(14)
is higher on initial_sl (1.7465393805016967) than on signal_reverse
(1.0591935076957586). Trades with net≥29.9: 5, pooled net
+843.7639016181568. Summing that same autopsy blotter by entry-month is
negative in 7 of 12 months (2024-03, 2024-04, 2024-05, 2024-08, 2024-09,
2024-12, 2025-01). That count is an observation. The harness entry-month
floor, computed on the control cell the same way as the other catalog
gates, is the binding baseline. Exit, long-only, and breadth already ran
on this name's own series and did not clear the monthly floor. Abs-ATR was
FALSIFIED on other names (`f7ac677`, `3788f11`, Donchian). Those
falsifications do not answer this name.

Problem:
Most losing trades die at the fixed initial_sl (213/330). The aggregate
edge still depends on a few signal_reverse runners (2 of 330 trades sum to
the full pooled entry net in the autopsy). This name has no entry-time
rule, earned on its own trades, that cuts stop-outs without cutting those
runners. Monthly regularity is the unresolved target. Series-level
positivity (7/10) has not produced a series that clears §7 (0/10
promotion_pass).

Mechanism:
Noisy EMA 50/200 crosses that fail into the initial stop tend to fire when
absolute ATR% is elevated, whereas crosses that later travel tend to begin
at lower absolute ATR%. The autopsy measured that direction on this name
(1.7465 vs 1.0592). Whether a causal abs-ATR keep-gate improves expectancy
and the monthly floor here, without destroying the fat tails, is the open
question. Another name's failure is not the answer. This is not a volume
gate, not a candle-location gate, and not a stake change.

Hypothesis:
Adding a single causal entry gate that rejects an EMA_50_200 signal when
ATR%(14) on the signal bar exceeds a pre-registered threshold will raise
mean Train-1 net PnL versus the ungated NO_TRAIL baseline AND cut the
initial_sl share among remaining trades, while keeping enough of this
name's big-winner PnL that the pooled losing-month floor can improve —
earned on this name's own trades, not by analogy.

Change to test:
ONE entry refinement only: `atr_pct <= T` required to take the EMA_50_200
signal (else flat). No exit, sizing, symbol, interval, direction, or
breadth changes. NO_TRAIL unchanged. Reuse the ATR definition and gate
intersection in `scripts/f006_bb_20_2_abs_atr_gate.py`
(`donchian.atr_pct_entry_gate`, SMA true-range / close on the closed
signal bar), pointed at this catalog name. Do not reuse that script's
EXPECTED_MEAN, CONTROL_NAME, or frozen median.

Baseline:
Ungated EMA_50_200 NO_TRAIL on the frozen 5-symbol × 2-interval Train-1
basket. Control must reproduce all 10 `train1_net_pnl` rows in
`output/f006_notrail_monthly_catalog5/summary/results.csv` for strategy
`EMA_50_200` (mean **+72.6693115**/series, sum **+726.693115**) before
any gated cell is trusted. Do not match +95.3217987. That figure belongs
to `BB_20_2_EMA200`. Do not match +82.900262. That figure belongs to
`BB_20_25_EMA200`.

The autopsy cohort above is the expected Train-1 entry cohort. If the
harness control disagrees with n=330, entry net +587.3851786486206, or
initial_sl 213/330, stop and report. Do not retune the gate to force a
match.

Metrics (pre-declared):
1. mean train1_net_pnl across 10 series (primary) / pooled net and net/trade
2. initial_sl share among closed Train-1-entry trades
3. n_trades (reject thin: mean n_trades/series < 10)
4. pooled losing-month floor (of 12, by entry-month, same definition as the
   BB_20_2 harness; confirm the control floor before comparing). Autopsy
   observation is 7/12. The control cell is binding.
5. big-winner PnL retained vs this name's ungated baseline. Big winner =
   net≥29.9, frozen on the ungated blotter before gated cells. Autopsy
   observation is 5 trades, +843.7639016181568. Do not import the
   BB_20_2 set (12 trades, 1251.654084) or the BB_20_25 set.
6. #symbols net-positive / per-symbol losing-month floor (informational)
7. number_of_trials = 5

Expected improvement:
Mean train1_net_pnl > this name's control (+72.6693115) AND initial_sl
share down ≥10pp at the best-PnL T AND ≥50% of this name's big-winner PnL
retained AND pooled losing-month floor strictly below this name's ungated
entry-month floor AND mean trades/series ≥ 10.

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
T grid fixed before run, same shape as the BB_20_2 abs-ATR gate, computed
on THIS name:
{median_train1_atr_pct of this name's ungated Train-1 entries, 1.0%, 1.25%,
1.5%, 2.0%} — max 5 trials.
Freeze that median to disk before evaluating gated cells. The autopsy
median (1.22268881066447) is an observation only; the binding median is
the control blotter. Do not reuse 1.176636% (`BB_20_2_EMA200`) or 1.165%
(`BB_20_25_EMA200`). Report all cells. Pick at most one T for any follow-up.
```

decision_if_pass: REFINE (update EMA_50_200 profile metrics; consider a separate validation later; do not open holdout in this run; do not FREEZE on the pass alone)
decision_if_fail: entry-vol / abs-ATR closed on this name's own trades. Worker must not set FREEZE and must not change profile status. The coordinator decides the profile only after the result. Sizing and other §8 entry structure on this name stay open. Do not treat this result as evidence about other catalog5 names. Do not retune the gate inside this run. Do not start `EMA3_13_50_200`. Do not open a new signal family.

## Result

## Decision
