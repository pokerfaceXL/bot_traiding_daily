# F006 — H-EMA3-13-50-200-ABS-ATR-ENTRY-GATE-01 (pre-registered)

> Pre-registered **before** implementing or running the gate. `EMA_50_200`
> is **FREEZE** after its own liquidity result (`48aef9f`, FALSIFIED
> (a)+(c)+(d)). That result, and every earlier result on `EMA_50_200`,
> `BB_20_2_EMA200`, or `BB_20_25_EMA200`, is **not** a test of
> `EMA3_13_50_200`. Do not copy any of those control means (+72.6693115,
> +95.3217987, or +82.900262), any frozen ATR median, any floor, or any
> pass/fail onto this card. Entry-vol / abs-ATR on this name is still only
> a withdrawn DNR-by-transfer. Under the 2026-10-02 catalog5 correction it
> stays open until it is earned on this name's own trades. Autopsy numbers
> below are **observations**, not the test. Do not invent a new signal
> family. Do not start funding-carry or spread-capture. Do not retest
> catalog mean-reversion.

experiment_id: H-EMA3-13-50-200-ABS-ATR-ENTRY-GATE-01
date: 2026-10-03
base_strategy: EMA3_13_50_200 (NO_TRAIL, max_sl_pct=0.03, one-shot entry, signal_reverse exit)

```text
Observation:
EMA3_13_50_200 is aggregate-Train-1-positive and CONDITIONAL. Catalog5 monthly
table (`output/f006_notrail_monthly_catalog5/summary/results.csv`, strategy
EMA3_13_50_200, 10 rows): sum of train1_net_pnl +911.483016, mean
+91.1483016/series, 6/10 series positive, pooled n_trades 459. Trio autopsy
(`output/f006_catalog5_trio_autopsy/trades/EMA3_13_50_200_train1_trades.csv`):
Train-1 entries n=423, pooled net +771.2836172145888236, initial_sl 292/423
(0.6903073286052009) at 0% WR, signal_reverse 122/423, end_of_data 9.
Mean entry ATR%(14) is higher on initial_sl (1.7665907796247597) than on
signal_reverse (1.0992842964809795). Trades with net≥29.9: 9, pooled net
+1131.95615373334168. Summing that same autopsy blotter by entry-month is
negative in 7 of 12 months (2024-03, 2024-04, 2024-05, 2024-08, 2024-09,
2024-12, 2025-01). That count is an observation. The harness entry-month
floor, computed on the control cell the same way as the other catalog
gates, is the binding baseline. Exit, long-only, and breadth already ran
on this name's own series and did not clear the monthly floor. Abs-ATR was
FALSIFIED on other names (`80e7fa6`, `f7ac677`, `3788f11`, Donchian). Those
falsifications do not answer this name. The profile's own core-metrics
Train-1-window sum is +$911.48, which is this +911.483016 rounded, not
another name's sum.

Problem:
Most losing trades die at the fixed initial_sl (292/423). The aggregate
edge still depends on a few signal_reverse runners (3 of 423 trades sum to
the full pooled entry net in the autopsy). This name has no entry-time
rule, earned on its own trades, that cuts stop-outs without cutting those
runners. Monthly regularity is the unresolved target. Series-level
positivity (6/10) has not produced a series that clears §7 (0/10
promotion_pass).

Mechanism:
Noisy triple-EMA crosses (`sig_ema3_cross(13, 50, 200)`) that fail into the
initial stop tend to fire when absolute ATR% is elevated, whereas crosses
that later travel tend to begin at lower absolute ATR%. The autopsy measured
that direction on this name (1.7666 vs 1.0993). Whether a causal abs-ATR
keep-gate improves expectancy and the monthly floor here, without destroying
the fat tails, is the open question. Another name's failure is not the
answer. This is not a volume gate, not a candle-location gate, and not a
stake change. The signal is not `sig_ema_cross(50, 200)` and not a Bollinger
band.

Hypothesis:
Adding a single causal entry gate that rejects an EMA3_13_50_200 signal when
ATR%(14) on the signal bar exceeds a pre-registered threshold will raise
mean Train-1 net PnL versus the ungated NO_TRAIL baseline AND cut the
initial_sl share among remaining trades, while keeping enough of this
name's big-winner PnL that the pooled losing-month floor can improve —
earned on this name's own trades, not by analogy.

Change to test:
ONE entry refinement only: `atr_pct <= T` required to take the EMA3_13_50_200
signal (else flat). No exit, sizing, symbol, interval, direction, or
breadth changes. NO_TRAIL unchanged. Reuse the ATR definition and gate
intersection in `scripts/f006_ema_50_200_abs_atr_gate.py`
(`donchian.atr_pct_entry_gate`, SMA true-range / close on the closed
signal bar), pointed at this catalog name (`sig_ema3_cross(13, 50, 200)`).
Do not reuse that script's EXPECTED_MEAN, CONTROL_NAME, or frozen median.
Do not use `EXPECTED_MEAN = 72.6693115`. Do not use `EXPECTED_MEAN = 95.3217987`.

Baseline:
Ungated EMA3_13_50_200 NO_TRAIL on the frozen 5-symbol × 2-interval Train-1
basket. Control must reproduce all 10 `train1_net_pnl` rows in
`output/f006_notrail_monthly_catalog5/summary/results.csv` for strategy
`EMA3_13_50_200` (mean **+91.1483016**/series, sum **+911.483016**) before
any gated cell is trusted. Do not match +72.6693115. That figure belongs
to `EMA_50_200`. Do not match +95.3217987. That figure belongs to
`BB_20_2_EMA200`. Do not match +82.900262. That figure belongs to
`BB_20_25_EMA200`.

The autopsy cohort above is the expected Train-1 entry cohort. If the
harness control disagrees with n=423, entry net +771.2836172145888236, or
initial_sl 292/423, stop and report. Do not retune the gate to force a
match.

Metrics (pre-declared):
1. mean train1_net_pnl across 10 series (primary) / pooled net and net/trade
2. initial_sl share among closed Train-1-entry trades
3. n_trades (reject thin: mean n_trades/series < 10)
4. pooled losing-month floor (of 12, by entry-month, same definition as the
   EMA_50_200 harness; confirm the control floor before comparing). Autopsy
   observation is 7/12. The control cell is binding.
5. big-winner PnL retained vs this name's ungated baseline. Big winner =
   net≥29.9, frozen on the ungated blotter before gated cells. Autopsy
   observation is 9 trades, +1131.95615373334168. Do not import the
   EMA_50_200 set (5 trades, +843.7639016181568) or any BB set.
6. #symbols net-positive / per-symbol losing-month floor (informational)
7. number_of_trials = 5

Expected improvement:
Mean train1_net_pnl > this name's control (+91.1483016) AND initial_sl
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
T grid fixed before run, same shape as the EMA_50_200 abs-ATR gate, computed
on THIS name:
{median_train1_atr_pct of this name's ungated Train-1 entries, 1.0%, 1.25%,
1.5%, 2.0%} — max 5 trials.
Freeze that median to disk before evaluating gated cells. The autopsy
median (1.3050960028982004) is an observation only; the binding median is
the control blotter. Do not reuse 1.22268881066447 (`EMA_50_200`),
1.176636% (`BB_20_2_EMA200`), or 1.165% (`BB_20_25_EMA200`). Report all
cells. Pick at most one T for any follow-up.
```

decision_if_pass: REFINE (update EMA3_13_50_200 profile metrics; consider a separate validation later; do not open holdout in this run; do not FREEZE on the pass alone)
decision_if_fail: entry-vol / abs-ATR closed on this name's own trades. Worker must not set FREEZE and must not change profile status. The coordinator decides the profile only after the result. Sizing and other §8 entry structure on this name stay open. Do not treat this result as evidence about other catalog5 names. Do not treat the EMA_50_200 FREEZE as this name's FREEZE. Do not retune the gate inside this run. Do not open a new signal family. Do not start funding-carry, spread-capture, or catalog mean-reversion.

## Result

(empty — worker fills)

## Decision

(empty — coordinator only)
