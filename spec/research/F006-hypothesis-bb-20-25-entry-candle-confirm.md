# F006 — H-BB-20-25-ENTRY-CANDLE-CONFIRM-01 (pre-registered)

> Pre-registered **before** implementing or running the gate. After Val-1 of the xsym-agree
> sizing formula FALSIFIED (c) (`89e936a`), journal + profile name the next open axis on
> `BB_20_25_EMA200` as a not-yet-run §8 **entry-structure** hypothesis on this name's own
> trades. Entry-vol/abs-ATR is closed (FALSIFIED a, tip `3788f11`); the xsym sizing *formula*
> is closed; exit / direction / breadth levers already closed. This card is **not** a Val-2 of
> the closed stake and does **not** retune it.

experiment_id: H-BB-20-25-ENTRY-CANDLE-CONFIRM-01
date: 2026-10-03
base_strategy: BB_20_25_EMA200 (NO_TRAIL, max_sl_pct=0.03, one-shot entry, signal_reverse exit)

```text
Observation:
BB_20_25_EMA200 stays CONDITIONAL after H-BB-20-25-XSYM-AGREE-SIZING-VAL1-01 FALSIFIED (c)
(tip 89e936a; mult gap -0.026). Entry-vol/abs-ATR own-trades gate FALSIFIED (a) tip 3788f11.
Exit-class / partial-exit / long-only / breadth already closed on this name's own-trade
evidence. Dual autopsy (Train-1 n=512): initial_sl 58% at 0% WR (sum -986); signal_reverse
carries profit (WR 57.6%, sum +1532); avg winner +14.30 / avg loser -2.92. The signal itself
is close-beyond-band + EMA200 agree (`sig_bb_breakout_ema`); it does **not** require the
signal bar to close decisively in the breakout direction relative to its own high-low range.
Abs-ATR rejected high absolute volatility; it never asked whether the breakout candle's
close location (candle confirmation) separates stop-outs from runners.

Problem:
Most trades still die at the fixed initial_sl; monthly floor remains 7/12 pooled; 0/10 series
clear §7. Closed levers (vol gate, one sizing formula, exit, direction, breadth) did not fix
regularity. We need one remaining §8 entry-structure change on THIS name, orthogonal to
absolute ATR%, written before the run.

Mechanism:
A BB pierce that closes near the mid of its own bar (weak / dojish confirmation) is more
likely a transient wick-through that reverses into the initial stop. A pierce that closes
near the favourable extreme of the bar (strong directional close) commits more of the bar's
range to the breakout side and is more likely to travel to the opposite structural extreme
(`signal_reverse`). Candle close-strength is computed only from the closed signal bar's
OHLC — causal, no look-ahead, and not an absolute-volatility threshold.

Hypothesis:
Adding a single causal entry gate that rejects a BB_20_25_EMA200 one-shot signal when the
signal bar's directional close-strength is below a pre-registered threshold T will raise
mean Train-1 net PnL versus the ungated NO_TRAIL baseline AND cut the initial_sl share among
remaining trades, while retaining enough big-winner PnL that the pooled losing-month floor
can improve — earned on this name's own trades.

Change to test:
ONE entry refinement only (§8 candle confirmation). On the closed signal bar:

  range = high - low
  close_strength_long  = (close - low)  / range   # undefined / fail if range == 0
  close_strength_short = (high - close) / range
  keep iff:
    direction == +1 and close_strength_long  >= T
    direction == -1 and close_strength_short >= T
    (range == 0 ⇒ reject)

Intersect with the existing one-shot entry mask (same pattern as
`scripts/f006_bb_20_25_abs_atr_gate.py`). No exit, sizing, symbol, interval, direction,
breadth, or ATR-threshold changes. NO_TRAIL unchanged. Exits continue to use the ungated
persistent signal (same as abs-ATR gate harness).

Baseline:
Ungated BB_20_25_EMA200 NO_TRAIL on the frozen 5-symbol × 2-interval Train-1 basket. Control
must reproduce catalog5 / abs-ATR / xsym control figures for this name (mean train1_net_pnl
≈ +82.90 across 10 series; pooled Train-1 entry cohort n=512 net ≈ +709.85 — report which
and match exactly before gating).

Metrics (pre-declared):
1. mean train1_net_pnl across 10 series (primary) / pooled net and net/trade
2. initial_sl share among closed Train-1-entry trades
3. n_trades (reject thin: mean n_trades/series < 10)
4. pooled losing-month floor (of 12, by entry-month)
5. big-winner PnL retained vs ungated baseline (freeze big winner = net≥29.9 before run)
6. #symbols net-positive / per-symbol losing-month floor (informational)
7. number_of_trials (threshold grid size)

Expected improvement:
Mean train1_net_pnl > baseline AND initial_sl share down ≥10pp AND ≥50% of big-winner PnL
retained AND pooled losing-month floor strictly below this name's ungated floor (7/12 on the
pooled control — confirm in control cell before comparing).

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
T grid fixed before run:
{0.50, 0.60, 0.70, 0.80, 0.90} — max 5 trials.
Control (ungated) + 5 gated cells. Report all cells. Pick at most one T for any follow-up.
```

decision_if_pass: REFINE (update BB_20_25_EMA200 profile metrics; consider validation)
decision_if_fail: keep CONDITIONAL; mark candle-confirm entry-structure axis closed on this
  name's own trades; next open §8 entry-structure variant (breakout depth / HTF direction)
  with a new written mechanism — still develop-not-abandon on this name; do not FREEZE

## Result

(empty — filled by T0 worker)

## Decision

(empty — coordinator only)
