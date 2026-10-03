# F006 — H-BB-20-2-ENTRY-CANDLE-CONFIRM-01 (pre-registered)

> Pre-registered **before** implementing or running the gate. After
> `H-BB-20-2-XSYM-AGREE-SIZING-VAL4-01` **FALSIFIED (c)** (`139ed3d`), journal +
> profile close that xsym-agree formula on `BB_20_2_EMA200` and name the next
> open axis as a not-yet-run §8 **entry-structure** hypothesis on this name's
> own trades. Entry-vol/abs-ATR is closed (FALSIFIED (a)+(c), tip `f7ac677`);
> the xsym sizing *formula* is closed; exit / direction / breadth levers
> already closed. This card is **not** a Val-5 of the closed stake and does
> **not** retune it. `BB_20_25_EMA200` is FREEZE on its own loop; its candle
> result at `e70161d` (and that name's T=0.70 numbers) is **not** this test.
> Do not copy that name's control mean (+82.90), n=512, initial_sl 58.01%, or
> pass/fail onto this card as an expected result.

experiment_id: H-BB-20-2-ENTRY-CANDLE-CONFIRM-01
date: 2026-10-03
base_strategy: BB_20_2_EMA200 (NO_TRAIL, max_sl_pct=0.03, one-shot entry, signal_reverse exit)

```text
Observation:
BB_20_2_EMA200 stays CONDITIONAL after H-BB-20-2-XSYM-AGREE-SIZING-VAL4-01
FALSIFIED (c) (tip 139ed3d; pooled mult gap -0.102941). Entry-vol/abs-ATR
own-trades gate FALSIFIED (a)+(c) tip f7ac677. Exit-class / partial-exit /
long-only / breadth already closed on this name's own-trade evidence.
Autopsy (Train-1 n=756): initial_sl 358/756 (47.35%) at 0% WR; signal_reverse
carries profit; avg winner +12.50 / avg loser -2.67. The signal itself is
close-beyond-band + EMA200 agree; it does not require the signal bar to close
decisively in the breakout direction relative to its own high-low range.
Abs-ATR rejected high absolute volatility; the closed stake rejected a
cross-symbol agreement multiplier on Val-4. Neither asked whether the
breakout candle's close location (candle confirmation) separates stop-outs
from runners on THIS name.

Problem:
Most trades still die at the fixed initial_sl; pooled Train-1 losing-month
floor is 7/12; 0/10 series clear §7. Closed levers (vol gate, one sizing
formula, exit, direction, breadth) did not fix regularity. We need one
remaining §8 entry-structure change on THIS name, orthogonal to absolute
ATR% and to the closed stake, written before the run.

Mechanism:
A BB pierce that closes near the mid of its own bar (weak / dojish
confirmation) is more likely a transient wick-through that reverses into the
initial stop. A pierce that closes near the favourable extreme of the bar
(strong directional close) commits more of the bar's range to the breakout
side and is more likely to travel to the opposite structural extreme
(signal_reverse). Candle close-strength is computed only from the closed
signal bar's OHLC — causal, no look-ahead, and not an absolute-volatility
threshold and not a stake multiplier.

Hypothesis:
Adding a single causal entry gate that rejects a BB_20_2_EMA200 one-shot
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
    (range == 0 ⇒ reject)

Intersect with the existing one-shot entry mask (same pattern as
scripts/f006_bb_20_2_abs_atr_gate.py). No exit, sizing, symbol, interval,
direction, breadth, or ATR-threshold changes. NO_TRAIL unchanged. Exits
continue to use the ungated persistent signal (same as abs-ATR gate harness).

Baseline:
Ungated BB_20_2_EMA200 NO_TRAIL on the frozen 5-symbol × 2-interval Train-1
basket. Control must reproduce this name's catalog / abs-ATR / xsym control
figures before trusting gated cells:
  - mean train1_net_pnl = +95.3217987 (10 series)
  - Train-1 entry cohort n = 756, entry net ≈ +834.347778
  - initial_sl share ≈ 0.473545 (47.35%)
  - big-winner PnL at net≥29.9 ≈ 1251.654084 (12 trades)
  - pooled losing entry-months = 7/12
Reference source: output/f006_bb_20_2_abs_atr_gate/cell_summary.csv control
row (and matching xsym control_replay). Do NOT import +82.900262 or n=512.

Metrics (pre-declared):
1. mean train1_net_pnl across 10 series (primary) / pooled net and net/trade
2. initial_sl share among closed Train-1-entry trades
3. n_trades (reject thin: mean n_trades/series < 10)
4. pooled losing-month floor (of 12, by entry-month)
5. big-winner PnL retained vs ungated baseline (freeze big winner = net≥29.9 before run)
6. #symbols net-positive / per-symbol losing-month floor (informational)
7. number_of_trials (threshold grid size)

Expected improvement:
Mean train1_net_pnl > baseline AND initial_sl share down ≥10pp AND ≥50% of
big-winner PnL retained AND pooled losing-month floor strictly below this
name's ungated floor (7/12 on the pooled control — confirm in control cell
before comparing).

Falsification condition (any one ⇒ FALSIFIED):
(a) mean train1_net_pnl ≤ baseline at every T; OR
(b) every non-thin T removes >50% of baseline big-winner PnL; OR
(c) initial_sl share fails to fall ≥10pp at the best-PnL T; OR
(d) pooled losing-month floor does not improve (stays ≥ baseline floor) at
    every T that otherwise passes (a)–(c); OR
(e) improvement is only from collapsing to <10 trades/series mean.
Do not widen T after seeing results without a new written hypothesis.
Do not declare this falsified because BB_20_25 candle failed, and do not
declare it passed because that name's T=0.70 raised mean PnL.

Data split:
Train-1 only (2024-03-01 ≤ entry < 2025-03-01 UTC). No validation/holdout.
If a T looks promising, schedule a separate validation run later — do not
tune on it now.

Budget:
T grid fixed before run:
{0.50, 0.60, 0.70, 0.80, 0.90} — max 5 trials.
Control (ungated) + 5 gated cells. Report all cells. Pick at most one T for
any follow-up. The grid shape matches the licensed §8 candle-confirm pattern
used elsewhere; it is not a copy of another name's winning T.
```

decision_if_pass: REFINE (update BB_20_2_EMA200 profile metrics; consider validation)
decision_if_fail: keep CONDITIONAL; mark candle-confirm entry-structure axis closed on this
  name's own trades; next open §8 entry-structure variant (breakout depth / HTF direction)
  with a new written mechanism — still develop-not-abandon on this name; do not FREEZE

## Result

(empty — worker fills)

## Decision

(empty — coordinator only)
