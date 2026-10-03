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

Train-1 run completed on the frozen 5-symbol × 2-interval basket. The ungated control
reproduced all 10 reference rows exactly: mean Train-1 net PnL **+$82.900262/series**
(+$829.002620 summed by series), while the pre-registered entry cohort reproduced
**n=512, +$709.849209**, initial-SL share **58.01%**, big-winner PnL **$968.020732**, and
**7/12** pooled losing entry-months. `number_of_trials = 5`.

| T | mean net/series | cohort net/trade | trades/series | initial-SL share (drop) | big-winner PnL retained | pooled losing months | net-positive symbols |
|---:|---:|---:|---:|---:|---:|---:|---:|
| control | +$82.90 | +$1.386 | 51.2 | 58.01% (0.00pp) | 100.0% | 7/12 | 4/5 |
| 0.50 | +$85.46 | +$1.468 | 50.1 | 57.68% (0.32pp) | 100.0% | 7/12 | 5/5 |
| 0.60 | +$85.31 | +$1.501 | 48.9 | 57.46% (0.54pp) | 100.0% | 7/12 | 5/5 |
| 0.70 | **+$89.28** | **+$1.700** | 45.5 | **56.04% (1.96pp)** | 100.0% | 7/12 | 5/5 |
| 0.80 | +$85.17 | +$1.894 | 38.8 | 58.76% (-0.76pp) | 92.4% | 7/12 | 4/5 |
| 0.90 | +$43.36 | +$1.467 | 25.9 | 57.53% (0.48pp) | 19.2% | **5/12** | 3/5 |

**FALSIFIED by (c).** The best-PnL threshold, T=0.70, improved mean PnL by $6.38/series
and retained every pre-frozen big winner, but reduced initial-SL share by only **1.96pp**,
far short of the required 10pp. Falsifier (a) did not trigger (T=0.50–0.80 beat control);
(b) did not trigger (all thresholds were non-thin and T=0.50–0.80 retained >50%); (d) was
not independently applicable because no cell passed (c)—empirically T=0.50–0.80 stayed
at 7/12, while T=0.90 reached 5/12 only by failing PnL and big-winner retention; (e) did
not trigger (all cells remained above 10 trades/series). No threshold passed all declared
checks. Artifacts: `output/f006_bb_20_25_entry_candle_confirm/`.

## Decision

**FALSIFIED (c).** Checked 2026-10-03 ~09:49 Europe/Warsaw against
`output/f006_bb_20_25_entry_candle_confirm/cell_summary.csv` on the FF-merged run
`e70161d` (review PASS, job `2026-10-03-f006-bb2025-entry-structure-revi-3883672f`).
The Result table matches the artifact after ordinary rounding.

Control reproduced the pre-registered baseline exactly: mean Train-1 net
**+$82.900262/series**, entry cohort **n=512, +$709.849209**, initial-SL share
**0.580078 (58.01%)**, big-winner PnL **$968.020732**, pooled losing entry-months
**7/12**. `number_of_trials = 5`.

Best-PnL cell is **T=0.70**: mean **+$89.279908/series**, which is **+$6.379646
(+$6.38/series)** versus control. Initial-SL share **0.560440**, drop
**1.963856 pp** — short of the pre-registered **10 pp**. Big-winner PnL retained
**100%**. Pooled floor stays **7/12**. Mean trades/series **45.5** (not thin).

(a) does not fire (T=0.50-0.80 beat control). (b) does not fire (non-thin cells
T=0.50-0.80 retain more than 50% of big-winner PnL). (d) does not apply: no T
passes (c). T=0.90 reaches 5/12 only by failing mean PnL and keeping 19.2% of
big-winner PnL. (e) does not fire (every cell stays above 10 trades/series).
No cell passed all declared checks.

Candle close-strength is closed on this name's own trades. `BB_20_25_EMA200`
stays **CONDITIONAL**. Do not FREEZE. This is one entry-structure variant, not a
class closure of entry refinement. Entry-vol (`3788f11`) and the xsym sizing
formula (`89e936a`) stay closed on their own evidence. Breakout depth and HTF
direction are still untested on this name's own trades. Next = one breakout-depth
hypothesis, written after this decision — not a transfer, not Validation-2, not
another catalog name.
