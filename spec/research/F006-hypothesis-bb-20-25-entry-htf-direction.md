# F006 — H-BB-20-25-ENTRY-HTF-DIRECTION-01 (pre-registered)

> Pre-registered **before** implementing or running the gate. After breakout depth
> FALSIFIED (a)+(c) (`0685ce5`), the profile keeps `BB_20_25_EMA200` CONDITIONAL.
> Breakout depth closed one §8 entry variant on this name's own trades. It did not
> close HTF direction. HTF direction is the remaining open axis named on
> `spec/research/strategy_profiles/BB_20_25_EMA200.md`. Entry-vol/abs-ATR is closed
> (FALSIFIED a, tip `3788f11`). The xsym sizing formula is closed (Val-1 FALSIFIED c,
> `89e936a`). Candle close-strength is closed (FALSIFIED c, `e70161d`). Long-only
> direction is already closed (class-closure own-trade cell) and is **not** this test.
> This card is not a retune of D, not a Val-2 of the closed stake, and not another
> catalog name.

experiment_id: H-BB-20-25-ENTRY-HTF-DIRECTION-01
date: 2026-10-03
base_strategy: BB_20_25_EMA200 (NO_TRAIL, max_sl_pct=0.03, one-shot entry, signal_reverse exit)

```text
Observation:
BB_20_25_EMA200 stays CONDITIONAL after H-BB-20-25-ENTRY-BREAKOUT-DEPTH-01
FALSIFIED (a)+(c) (tip 0685ce5). Control mean +$82.900262/series. Best D=0.02
mean +$71.985313/series (−$10.91). Initial-SL share went from 58.01% to 58.07%
(required drop 10pp). D=0.50 took zero trades. Candle close-strength, entry-vol,
and the xsym sizing formula are already closed on this name's own trades. Exit,
long-only direction, and breadth are already closed. The signal is close-beyond-band
plus same-timeframe EMA200 agree (`sig_bb_breakout_ema`). That EMA200 is not a
higher-timeframe direction. Depth asked how far the close sat beyond the band.
It did not ask whether the prior completed higher-timeframe bar pointed the same way.

Problem:
Most trades still die at the fixed initial_sl. A breakout taken against the
direction of the last completed higher-timeframe bar is treated the same as one
taken with it. Depth and candle location did not separate stop-outs from runners.
One remaining §8 entry change on THIS name, orthogonal to absolute ATR%, to
close-location inside the bar, to band-penetration depth, and to the already-closed
long-only lever.

Mechanism:
The fixed initial stop is the death of a pierce that is already fighting the
coarser swing. A signal whose direction matches the previous fully closed
higher-timeframe candle is trading with that swing; a signal against it is fading
it. The higher-timeframe candle is built only from native bars of the same loaded
series that closed strictly before the signal bar's open, so the signal bar is
not inside it. Direction is the sign of that candle's close minus its open. It
is not an EMA, not ATR, not (close-low)/(high-low), and not "drop all shorts".

Hypothesis:
Adding a single causal entry gate that rejects a BB_20_25_EMA200 one-shot signal
when the prior fully closed 4-bar higher-timeframe candle does not agree in
direction will raise mean Train-1 net PnL versus the ungated NO_TRAIL baseline
AND cut the initial_sl share among remaining trades, while retaining enough
big-winner PnL that the pooled losing-month floor can improve — earned on this
name's own trades.

Change to test:
ONE entry refinement only (§8 higher-timeframe direction). From the closed bars
of the same symbol and the same interval already loaded for Train-1 (do not load
another cache file, do not download, do not read *_20260901* or *_20200325*):

  htf_minutes = 4 * interval_minutes
  # 60 → 240-minute buckets; 240 → 960-minute buckets
  # bucket open = Unix-epoch floor of the native bar open to htf_minutes

  For a signal bar with open time t, use the latest HTF bucket whose close time
  is <= t. That bucket does not contain the signal bar.
  The bucket is valid only if it contains all 4 native bars
  (opens = bucket_open + k * interval_minutes for k = 0,1,2,3).
  Otherwise reject.
  htf_open  = open of the first native bar
  htf_close = close of the last native bar
  htf_dir   = +1 if htf_close > htf_open
            = -1 if htf_close < htf_open
            = reject if equal
  keep iff signal direction == htf_dir

Index timestamps are bar OPEN times (UTC), as in data_cache. A bar closes at
open + interval. Do not use a still-forming HTF bucket. Do not use the HTF
bucket that contains the signal bar, even when the signal bar is its last bar.

Intersect with the existing one-shot entry mask (same pattern as
`scripts/f006_bb_20_25_entry_breakout_depth.py`). No exit, sizing, symbol,
interval, long-only, breadth, ATR-threshold, candle-strength, or breakout-depth
changes. NO_TRAIL unchanged. Exits continue to use the ungated persistent signal.
Do not use ATR. Do not use an EMA for this gate.

Baseline:
Ungated BB_20_25_EMA200 NO_TRAIL on the frozen 5-symbol × 2-interval Train-1 basket.
Control must reproduce the breakout-depth / candle-confirm / abs-ATR control
figures for this name before gating: mean train1_net_pnl +82.900262 across 10
series; pooled Train-1 entry cohort n=512 net +709.849209; initial_sl share
0.580078125; big-winner PnL 968.020732; pooled losing entry-months 7/12.
Report the matched figures exactly.

Metrics (pre-declared):
1. mean train1_net_pnl across 10 series (primary) / pooled net and net/trade
2. initial_sl share among closed Train-1-entry trades
3. n_trades (reject thin: mean n_trades/series < 10)
4. pooled losing-month floor (of 12, by entry-month)
5. big-winner PnL retained vs ungated baseline (freeze big winner = net≥29.9 before run)
6. #symbols net-positive / per-symbol losing-month floor (informational)
7. number_of_trials = 1 (this gate is binary; do not add a strength grid)

Expected improvement:
Mean train1_net_pnl > baseline AND initial_sl share down ≥10pp AND ≥50% of
big-winner PnL retained AND pooled losing-month floor strictly below this name's
ungated floor (7/12 on the pooled control — confirm in the control cell before
comparing) AND mean trades/series ≥ 10.

Falsification condition (any one ⇒ FALSIFIED):
(a) mean train1_net_pnl ≤ baseline; OR
(b) the gate removes >50% of baseline big-winner PnL; OR
(c) initial_sl share fails to fall ≥10pp; OR
(d) pooled losing-month floor does not improve (stays ≥ baseline floor); OR
(e) mean trades/series < 10.
Do not add a second threshold, a second HTF length, or a strength filter after
seeing the result without a new written hypothesis.

Data split:
Train-1 only (2024-03-01 ≤ entry < 2025-03-01 UTC). No validation/holdout. If the
gate looks promising, schedule a separate validation run later — do not tune on
it now.

Budget:
One gated cell plus the ungated control. number_of_trials = 1.
No parameter sweep.
```

decision_if_pass: REFINE (update BB_20_25_EMA200 profile metrics; consider a separate validation later; do not open holdout in this run)
decision_if_fail: HTF direction closed on this name's own trades. Worker must not
  set FREEZE and must not change profile status. The coordinator decides the
  profile only after the result. Do not treat this result as evidence about other
  catalog5 names. Do not retune the gate inside this run.

## Result

(empty — worker fills after the run)

## Decision

(empty — coordinator only)
