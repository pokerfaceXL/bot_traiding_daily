# F006 — H-EMA3-13-50-200-ENTRY-CANDLE-CONFIRM-01 (pre-registered)

> Pre-registered **before** implementing or running the gate. After
> `H-EMA3-13-50-200-XSYM-AGREE-SIZING-01` **FALSIFIED (b)** (`34e2c4a`),
> journal + profile close that xsym-agree formula on `EMA3_13_50_200` and
> name the next open axis as a not-yet-run §8 **entry-structure** hypothesis
> on this name's own trades. Entry-vol/abs-ATR is closed (FALSIFIED (a)+(c),
> tip `46e4509` / Decision `3318658`; (d) was not reachable). The xsym sizing
> *formula* is closed; no validation window. Exit / direction / breadth
> levers already closed. This card is **not** a Val-1 of the closed stake
> and does **not** retune it. `EMA_50_200` is **FREEZE** after its own
> liquidity result (`48aef9f`). Its candle result at `778f373` (best T=0.50,
> mean +45.0267104, FALSIFIED (a)+(c)) is **not** this test. `BB_20_2_EMA200`
> candle at `88b0ee3` (T=0.60) and `BB_20_25_EMA200` candle at `e70161d`
> (T=0.70) are **not** this test. Do not copy another name's winning T, and
> do not copy +72.6693115, +95.3217987, +82.900262, +126.744211, or
> +45.0267104 onto this card as an expected result.

experiment_id: H-EMA3-13-50-200-ENTRY-CANDLE-CONFIRM-01
date: 2026-10-03
base_strategy: EMA3_13_50_200 (NO_TRAIL, max_sl_pct=0.03, one-shot entry, signal_reverse exit)

```text
Observation:
EMA3_13_50_200 stays CONDITIONAL after H-EMA3-13-50-200-XSYM-AGREE-SIZING-01
FALSIFIED (b) (tip 34e2c4a). Control mean +91.1483016/series reproduced
(max abs diff 0.0, sum +911.483016). Sized mean +127.142706 (delta
+35.994404/series). Pooled losing entry-months stayed 7/12, so falsifier
(b) fired and the formula is closed. No validation window. Series higher
count on that run is 6/10 (the Result text said 7/10; results.csv says 6).
That count is not a falsifier. Entry-vol / abs-ATR own-trades gate
FALSIFIED (a)+(c) tip 46e4509; (d) not reachable. Exit-class / partial-exit
/ long-only / breadth already closed on this name's own-trade evidence.
Abs-ATR and xsym control (Train-1 n=423): initial_sl 292/423 (69.03%) at
0% WR; signal_reverse 122/423 carries profit. The signal is
sig_ema3_cross(13, 50, 200); it does not require the signal bar to close
decisively in the trade direction relative to its own high-low range.
Abs-ATR rejected high absolute volatility; the closed stake rejected a
cross-symbol agreement multiplier because the month floor did not improve.
Neither asked whether the signal candle's close location (candle
confirmation) separates stop-outs from runners on THIS name.

Problem:
Most trades still die at the fixed initial_sl; pooled Train-1 losing-month
floor is 7/12; 0/10 series clear §7. Closed levers (vol gate, one sizing
formula, exit, direction, breadth) did not fix regularity. We need one
remaining §8 entry-structure change on THIS name, orthogonal to absolute
ATR% and to the closed stake, written before the run.

Mechanism:
A cross that closes near the mid of its own bar (weak / dojish confirmation)
is more likely a transient print that reverses into the initial stop. A
cross that closes near the favourable extreme of the bar (strong directional
close) commits more of the bar's range to the trade side and is more likely
to travel to the opposite structural extreme (signal_reverse). Candle
close-strength is computed only from the closed signal bar's OHLC — causal,
no look-ahead, and not an absolute-volatility threshold and not a stake
multiplier. It is not EMA_50_200's close-strength and not a BB name's.

Hypothesis:
Adding a single causal entry gate that rejects an EMA3_13_50_200 one-shot
signal when the signal bar's directional close-strength is below a
pre-registered threshold T will raise mean Train-1 net PnL versus the ungated
NO_TRAIL baseline AND cut the initial_sl share among remaining trades, while
retaining enough big-winner PnL that the pooled losing-month floor can
improve — earned on this name's own trades.

Change to test:
ONE entry refinement only (§8 candle confirmation). On the closed signal bar:

  range = high - low
  close_strength_long  = (close - low)  / range   # undefined / fail if range == 0
  close_strength_short = (high - close) / range
  keep iff:
    direction == +1 and close_strength_long  >= T
    direction == -1 and close_strength_short >= T
    (range == 0 => reject)

Intersect with the existing one-shot entry mask (same pattern as
scripts/f006_ema3_13_50_200_abs_atr_gate.py). No exit, sizing, symbol,
interval, direction, breadth, or ATR-threshold changes. NO_TRAIL unchanged.
Exits continue to use the ungated persistent signal (same as the abs-ATR
gate harness). Do not reuse the closed stake multiplier.

Baseline:
Ungated EMA3_13_50_200 NO_TRAIL on the frozen 5-symbol x 2-interval Train-1
basket. Control must reproduce this name's catalog / abs-ATR / xsym control
figures before trusting gated cells:
  - mean train1_net_pnl = +91.1483016 (10 series, sum +911.483016)
  - Train-1 entry cohort n = 423, entry net = +771.283617
  - initial_sl share = 292/423 = 0.6903073286052009 (69.03%)
  - big-winner PnL at net>=29.9 = +1131.9561537333418 (9 trades;
    xsym control blotter confirmed 9 / +1131.956154)
  - pooled losing entry-months = 7/12
Reference source: output/f006_ema3_13_50_200_abs_atr_gate/ control row,
confirmed by output/f006_ema3_13_50_200_xsym_agree_sizing/summary/cell_summary.json
control. Do NOT import +72.6693115. Do NOT import +95.3217987. Do NOT import
+82.900262. Do NOT import +126.744211. Do NOT import n=330, n=756, or n=512.

Metrics (pre-declared):
1. mean train1_net_pnl across 10 series (primary) / pooled net and net/trade
2. initial_sl share among closed Train-1-entry trades
3. n_trades (reject thin: mean n_trades/series < 10)
4. pooled losing-month floor (of 12, by entry-month). Confirm the control
   floor in this run. The xsym control measured 7/12; that is an observation
   to confirm, not an imported pass line from another name.
5. big-winner PnL retained vs this name's ungated baseline (freeze big winner
   = net>=29.9 before run). Recompute the set on this run's ungated blotter.
   The abs-ATR freeze observed 9 trades / +1131.9561537333418; confirm, do not
   import another name's set (not 5 / +843.7639016181568).
6. #symbols net-positive / per-symbol losing-month floor (informational)
7. number_of_trials = 5

Expected improvement:
Mean train1_net_pnl > this name's control (+91.1483016) AND initial_sl
share down >=10pp at the best-PnL T AND >=50% of this name's big-winner PnL
retained AND pooled losing-month floor strictly below this name's ungated
entry-month floor AND mean trades/series >= 10. The 10pp and 50% figures
are the same pre-declared entry-gate checks already used on this name's
abs-ATR card. They are not another name's measured SL drop.

Falsification condition (any one => FALSIFIED):
(a) mean train1_net_pnl <= baseline at every T; OR
(b) every non-thin T removes >50% of baseline big-winner PnL; OR
(c) initial_sl share fails to fall >=10pp at the best-PnL T; OR
(d) pooled losing-month floor does not improve (stays >= baseline floor) at
    every T that otherwise passes (a)-(c); OR
(e) improvement is only from collapsing to <10 trades/series mean.
On this entry-gate card, (b) is the big-winner clause, not the month floor.
The month floor is (d), and (d) is reachable only at a T that otherwise
passes (a)-(c). A flat floor by itself is not (b) here. Do not widen T
after seeing results without a new written hypothesis. Do not declare this
falsified because EMA_50_200 candle failed at 778f373, because BB_20_2
candle failed at 88b0ee3, or because BB_20_25 candle failed at e70161d,
and do not declare it passed because any of those names' Train-1 T raised
mean PnL.

Data split:
Train-1 only (2024-03-01 <= entry < 2025-03-01 UTC). No validation/holdout.
If a T looks promising, schedule a separate validation run later — do not
tune on it now. Do not open a validation window of the closed sizing formula.

Budget:
T grid fixed before run:
{0.50, 0.60, 0.70, 0.80, 0.90} — max 5 trials.
Control (ungated) + 5 gated cells. Report all cells. Pick at most one T for
any follow-up. The grid shape is the licensed §8 candle-confirm pattern
(the same five cut-points used as a shape, not as a selected winner). It is
not a copy of another name's winning T (not 0.60 from BB_20_2, not 0.70
from BB_20_25, and not EMA_50_200's best-but-failed T=0.50 chosen as the
answer). Every T is reported. No cell is pre-picked.
```

decision_if_pass: REFINE (update EMA3_13_50_200 profile metrics; consider a separate validation later; do not open holdout in this run; do not FREEZE on the pass alone; status stays CONDITIONAL)
decision_if_fail: keep CONDITIONAL; mark candle-confirm entry-structure axis closed on this
  name's own trades; next open §8 entry-structure variant is breakout depth, with a new written
  mechanism — still develop-not-abandon on this name; do not FREEZE; do not retune T; do not
  reopen abs-ATR; do not reopen the closed xsym formula; do not start funding-carry,
  spread-capture, or catalog mean-reversion

## Result

(empty — worker fills)

## Decision

(empty — coordinator only)
