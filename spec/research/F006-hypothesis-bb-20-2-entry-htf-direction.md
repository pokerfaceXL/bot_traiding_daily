# F006 — H-BB-20-2-ENTRY-HTF-DIRECTION-01 (pre-registered)

> Pre-registered **before** implementing or running the gate. After
> `H-BB-20-2-ENTRY-BREAKOUT-DEPTH-01` **FALSIFIED (a)+(c)** (`27fa7f6`),
> journal + profile close breakout depth on `BB_20_2_EMA200` and name the
> next open axis as a not-yet-run §8 **HTF direction** hypothesis on this
> name's own trades. Entry-vol/abs-ATR is closed (FALSIFIED (a)+(c), tip
> `f7ac677`); the xsym sizing *formula* is closed (Val-4 `139ed3d`
> FALSIFIED (c)); candle close-strength is closed (`88b0ee3`); breakout
> depth is closed (`27fa7f6`). Exit / long-only direction / breadth already
> closed. This card is **not** a retune of D, **not** a Val-5 of the closed
> stake, **not** long-only, and **not** a liquidity filter. `BB_20_25_EMA200`
> is FREEZE on its own loop; its HTF result at `3495b16` (and that name's
> gated mean +70.515667, control +82.900262, n=512, initial_sl 0.580078) is
> **not** this test. Do not copy that name's control mean, cohort, or
> pass/fail onto this card as an expected result. Do not use `bb_20_2.5_*`
> — this name's signal is k=2.0. The structural shape of the gate (prior
> fully closed 4-bar HTF candle) is the licensed §8 pattern; every threshold
> and baseline below is this name's own.

experiment_id: H-BB-20-2-ENTRY-HTF-DIRECTION-01
date: 2026-10-03
base_strategy: BB_20_2_EMA200 (NO_TRAIL, max_sl_pct=0.03, one-shot entry, signal_reverse exit)

```text
Observation:
BB_20_2_EMA200 stays CONDITIONAL after H-BB-20-2-ENTRY-BREAKOUT-DEPTH-01
FALSIFIED (a)+(c) (tip 27fa7f6). Best D=0.02 mean +87.8448967 versus control
+95.3217987 (−7.476902/series). Initial_sl share rose +1.010625pp (0.473545
to 0.483651) against a required 10pp drop. Frozen big-winner PnL retained
was 82.2% (9/12, 1029.065151 of 1251.654084). The pooled floor printed 6/12
at D=0.02 and D=0.05 and was not otherwise qualifying. Entry-vol, the xsym
sizing formula, candle close-strength, and breakout depth are already closed
on this name's own trades. Exit / long-only direction / breadth are already
closed. The signal is close-beyond-band + same-timeframe EMA200 agree
(`sig_bb_breakout_ema`, period 20, k=2.0). That EMA200 is not a higher
timeframe. Depth asked how far the close sat beyond this name's k=2.0 band.
It did not ask whether the prior completed higher-timeframe bar pointed the
same way.

Problem:
Most trades still die at the fixed initial_sl (358/756, 47.35%, 0% WR on the
ungated Train-1 cohort). A breakout taken against the direction of the last
completed higher-timeframe bar is treated the same as one taken with it.
Depth and candle location did not separate stop-outs from runners on this
name. One remaining §8 entry change on THIS name, orthogonal to absolute
ATR%, to close-location inside the bar, to band-penetration depth, to the
closed stake, and to the already-closed long-only lever.

Mechanism:
The fixed initial stop is the death of a pierce that is already fighting the
coarser swing. A signal whose direction matches the previous fully closed
higher-timeframe candle is trading with that swing; a signal against it is
fading it. The higher-timeframe candle is built only from native bars of the
same loaded series that closed strictly before the signal bar's open, so the
signal bar is not inside it. Direction is the sign of that candle's close
minus its open. It is not an EMA, not ATR, not (close-low)/(high-low), not
band depth, and not "drop all shorts".

Hypothesis:
Adding a single causal entry gate that rejects a BB_20_2_EMA200 one-shot
signal when the prior fully closed 4-bar higher-timeframe candle does not
agree in direction will raise mean Train-1 net PnL versus the ungated
NO_TRAIL baseline AND cut the initial_sl share among remaining trades, while
retaining enough big-winner PnL that the pooled losing-month floor can
improve — earned on this name's own trades.

Change to test:
ONE entry refinement only (§8 higher-timeframe direction). From the closed
bars of the same symbol and the same interval already loaded for Train-1
(do not load another cache file, do not download, do not read *_20260901*
or *_20200325*):

  htf_minutes = 4 * interval_minutes
  # 60 → 240-minute buckets; 240 → 960-minute buckets
  # bucket open = Unix-epoch floor of the native bar open to htf_minutes

  For a signal bar with open time t, use the latest HTF bucket whose close
  time is <= t. That bucket does not contain the signal bar.
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
bucket that contains the signal bar, even when the signal bar is its last
bar.

Intersect with the existing one-shot entry mask (same pattern as
scripts/f006_bb_20_2_entry_breakout_depth.py). No exit, sizing, symbol,
interval, long-only, breadth, ATR-threshold, candle-strength, or
breakout-depth changes. NO_TRAIL unchanged. Exits continue to use the
ungated persistent signal (same as the breakout-depth and candle harnesses).
Do not use ATR. Do not use an EMA for this gate. Do not read bb_20_2.5_*.

Baseline:
Ungated BB_20_2_EMA200 NO_TRAIL on the frozen 5-symbol × 2-interval Train-1
basket. Control must reproduce this name's catalog / abs-ATR / xsym / candle
/ breakout-depth control figures before trusting the gated cell:
  - mean train1_net_pnl = +95.3217987 (10 series)
  - Train-1 entry cohort n = 756, entry net ≈ +834.347778
  - initial_sl share ≈ 0.473545 (358/756)
  - big-winner PnL at net≥29.9 ≈ 1251.654084 (12 trades)
  - pooled losing entry-months = 7/12
Reference source: output/f006_bb_20_2_entry_breakout_depth/cell_summary.csv
control row (and the matching candle-confirm control row). Do NOT import
+82.900262, n=512, initial_sl 0.580078, big-winner 968.020732, or any
BB_20_25 HTF cell (including +70.515667).

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
big-winner PnL retained AND pooled losing-month floor strictly below this
name's ungated floor (7/12 on the pooled control — confirm in the control
cell before comparing) AND mean trades/series ≥ 10.

Falsification condition (any one ⇒ FALSIFIED):
(a) mean train1_net_pnl ≤ baseline; OR
(b) the gate removes >50% of baseline big-winner PnL; OR
(c) initial_sl share fails to fall ≥10pp; OR
(d) pooled losing-month floor does not improve (stays ≥ baseline floor); OR
(e) mean trades/series < 10.
Do not add a second threshold, a second HTF length, or a strength filter
after seeing the result without a new written hypothesis.
Do not declare this falsified because BB_20_25 HTF direction failed, and do
not declare it passed because some other name's HTF cell moved PnL.

Data split:
Train-1 only (2024-03-01 ≤ entry < 2025-03-01 UTC). No validation/holdout.
If the gate looks promising, schedule a separate validation run later — do
not tune on it now.

Budget:
One gated cell plus the ungated control. number_of_trials = 1.
No parameter sweep. The 4-bar HTF length is the licensed structural pattern;
it is not a copy of another name's passing cell (that other name had none).
```

decision_if_pass: REFINE (update BB_20_2_EMA200 profile metrics; consider a separate validation later; do not open holdout in this run)
decision_if_fail: keep CONDITIONAL; mark HTF direction closed on this name's own trades;
  next open §8 entry variant is liquidity, with a new written mechanism — still
  develop-not-abandon on this name; do not FREEZE; do not jump to EMA_50_200 /
  EMA3_13_50_200; do not treat this result as evidence about other catalog5 names;
  do not retune the HTF length inside this run; do not start a new name while
  liquidity is still open here
