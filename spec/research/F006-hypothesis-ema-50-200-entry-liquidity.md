# F006 — H-EMA-50-200-ENTRY-LIQUIDITY-01 (pre-registered)

> Pre-registered **before** implementing or running the gate. After
> `H-EMA-50-200-ENTRY-HTF-DIRECTION-01` **FALSIFIED (a)+(b)+(c)+(d)**
> (`3a7c094`, Decision this commit), journal + profile close HTF direction
> on `EMA_50_200` and name the next open axis as a not-yet-run §8
> **liquidity** hypothesis on this name's own trades. Entry-vol/abs-ATR is
> closed (FALSIFIED (a)+(c), tip `80e7fa6` / Decision `67af347`); the xsym
> sizing *formula* is closed (FALSIFIED (b), tip `48d03b0` / Decision
> `f54e362`); candle close-strength is closed (FALSIFIED (a)+(c), tip
> `778f373` / Decision `4e32994`); breakout depth is closed (FALSIFIED
> (a)+(c), tip `485de51` / Decision `925eee1`); HTF direction is closed
> (FALSIFIED (a)+(b)+(c)+(d), tip `3a7c094`). Exit / long-only direction /
> breadth already closed. This card is **not** a retune of the 4-bar HTF
> length, **not** a Val-1 of the closed stake, **not** a candle retune,
> **not** a depth retune, and **not** `vol_ratio > 1.2`. `BB_20_2_EMA200`
> is **FREEZE** after its own liquidity result (`776e167`). That measured
> liquidity cell (mean, n, initial_sl share, big-winner retention, floor
> move, pass/fail) is **not** this test. Do not copy +97.2455987, +1.923800,
> n=742, initial_sl 0.4743935309973046, 12/12 big winners, or a 7/12 to 6/12
> floor onto this card as an expected result. Do not copy +95.3217987 or
> +82.900262. Do not use `bb_20_2.0_*` or `bb_20_2.5_*` — this name's signal
> is `sig_ema_cross(50, 200)`, columns `ema50` / `ema200`, not a Bollinger
> band. The profile names liquidity as an axis and does not specify a
> formula. The licensed shape is the one already used on `BB_20_2_EMA200`:
> a one-shot keep on base volume versus the prior-20 median. The lookback
> 20 is that licensed shape, not this name's EMA length and not a Bollinger
> period transferred as a parameter of this signal.

experiment_id: H-EMA-50-200-ENTRY-LIQUIDITY-01
date: 2026-10-03
base_strategy: EMA_50_200 (NO_TRAIL, max_sl_pct=0.03, one-shot entry, signal_reverse exit)

```text
Observation:
EMA_50_200 stays CONDITIONAL after H-EMA-50-200-ENTRY-HTF-DIRECTION-01
FALSIFIED (a)+(b)+(c)+(d) (tip 3a7c094). Control mean +72.6693115/series
reproduced (max abs diff 0.0, n=330). Gated htf_4 mean +20.7369913 (delta
-51.9323202/series), entry n=239. Initial_sl share rose 2.818562190947127 pp
(213/330 = 0.6454545454545455 to 161/239 = 0.6736401673640168). Big-winner
PnL kept 3 / +371.1233324523375 / 0.4398426286554843. Pooled entry-month
floor stayed 7/12. The card's (d) sentence is "pooled losing-month floor
does not improve (stays >= baseline floor)", so the flat floor fires (d).
Entry-vol / abs-ATR own-trades gate FALSIFIED (a)+(c) tip 80e7fa6. The xsym
sizing formula FALSIFIED (b) tip 48d03b0 (floor stayed 7/12; no Val-1).
Candle close-strength FALSIFIED (a)+(c) tip 778f373. Breakout depth
FALSIFIED (a)+(c) tip 485de51. Exit-class / partial-exit / long-only /
breadth already closed on this name's own-trade evidence. HTF asked whether
the prior completed coarser candle pointed the same way. It did not ask
whether the signal bar itself traded on above-median base volume.

Problem:
Most trades still die at the fixed initial_sl (213/330, 64.55%, 0% WR on the
ungated Train-1 cohort); pooled Train-1 losing-month floor is 7/12; 0/10
series clear §7. Closed levers (vol gate as absolute ATR%, one sizing
formula, candle close-strength, breakout depth, HTF direction, exit,
direction, breadth) did not fix regularity. A cross printed on a quiet bar
and a cross printed when base volume is at least the recent median are
treated as the same signal. One remaining §8 entry change on THIS name,
orthogonal to absolute ATR%, to close-location inside the bar, to
ema200-normalized depth, and to the closed HTF-direction lever, written
before the run. The profile only names the axis. The shape below is the
licensed liquidity rule, not another name's measured result.

Mechanism:
The fixed initial stop is where a cross that prints without participation
dies. A one-shot signal whose bar has base volume at least the median of
the prior 20 closed bars is trading when the book is at least as active as
the recent past; a signal below that median is a quiet cross. The window is
the 20 native bars strictly before the signal bar. The signal bar is not
inside it. The column is native base volume, not quote volume, not
vol_ratio, not vol_ma20, not ATR, not ema50/ema200, not (close-low)/(high-low),
not (close-ema200)/ema200, and not the sign of a higher-timeframe candle.
Long-only is already closed and is not this test. Absolute ATR% is already
closed and is not this test.

Hypothesis:
Adding a single causal entry gate that rejects an EMA_50_200 one-shot
signal when the signal bar's base volume is below the median volume of the
prior 20 closed bars will raise mean Train-1 net PnL versus the ungated
NO_TRAIL baseline AND cut the initial_sl share among remaining trades, while
retaining enough big-winner PnL that the pooled losing-month floor can
improve — earned on this name's own trades.

Change to test:
ONE entry refinement only (§8 liquidity condition). From the closed bars of
the same symbol and the same interval already loaded for Train-1 (do not
load another cache file, do not download, do not read *_20260901* or
*_20200325*):

  Use the native base `volume` column only. Do not convert to quote
  volume. Do not read `vol_ratio` or `vol_ma20`.

  For a signal bar at index i (the bar whose open time is the signal):
    window = volume[i-20 : i]   # 20 bars strictly before the signal bar
    if len(window) < 20: reject
    med = median(window)
    if med is not finite or med <= 0: reject
    keep iff volume[i] >= med

  The signal bar is not inside the window. Ties at the median are kept.
  A missing volume rejects.

Intersect with the existing one-shot entry mask (same pattern as
scripts/f006_ema_50_200_entry_htf_direction.py). No exit, sizing, symbol,
interval, long-only, breadth, ATR-threshold, candle-strength,
breakout-depth, or HTF-direction changes. NO_TRAIL unchanged. Exits
continue to use the ungated persistent signal (same as the HTF harness).
Do not use ATR. Do not use ema50 or ema200 for this gate. Do not read
bb_20_2.0_* or bb_20_2.5_*. Do not implement vol_ratio > 1.2. The lookback
20 is the licensed liquidity shape (prior 20 closed bars), not this name's
EMA period and not a copied measured cell. Binary gate. Do not grid the
multiple and do not grid the window.

Baseline:
Ungated EMA_50_200 NO_TRAIL on the frozen 5-symbol x 2-interval Train-1
basket. Control must reproduce this name's catalog / abs-ATR / xsym / candle
/ depth / HTF control figures before trusting the gated cell:
  - mean train1_net_pnl = +72.6693115 (10 series, sum +726.693115)
  - Train-1 entry cohort n = 330, entry net = +587.3851786486205
  - initial_sl share = 213/330 = 0.6454545454545455 (64.55%)
  - big-winner PnL at net>=29.9 = +843.7639016181568 (5 trades)
  - pooled losing entry-months = 7/12
Reference source: output/f006_ema_50_200_entry_htf_direction/cell_summary.csv
control row (matches the depth, candle, and abs-ATR control rows, diff 0).
Do NOT import +95.3217987. Do NOT import +82.900262. Do NOT import n=756 or
n=512. Do NOT import +97.2455987 or any other name's liquidity-cell mean,
n, initial_sl share, big-winner retention, floor, or pass/fail.

Metrics (pre-declared):
1. mean train1_net_pnl across 10 series (primary) / pooled net and net/trade
2. initial_sl share among closed Train-1-entry trades
3. n_trades (reject thin: mean n_trades/series < 10)
4. pooled losing-month floor (of 12, by entry-month). Confirm the control
   floor in this run. The HTF control measured 7/12; that is an observation
   to confirm, not an imported pass line from another name.
5. big-winner PnL retained vs this name's ungated baseline (freeze big winner
   = net>=29.9 before the gated cell). Recompute the set on this run's
   ungated blotter. The HTF freeze observed 5 trades /
   +843.7639016181568; confirm, do not import another name's set.
6. #symbols net-positive / per-symbol losing-month floor (informational)
7. number_of_trials = 1 (this gate is binary; do not add a multiple grid)

Expected improvement:
Mean train1_net_pnl > this name's control (+72.6693115) AND initial_sl
share down >=10pp AND >=50% of this name's big-winner PnL retained AND
pooled losing-month floor strictly below this name's ungated entry-month
floor AND mean trades/series >= 10. The 10pp and 50% figures are the same
pre-declared entry-gate checks already used on this name's abs-ATR, candle,
depth, and HTF cards. They are not another name's measured liquidity result.

Falsification condition (any one => FALSIFIED):
(a) mean train1_net_pnl <= baseline; OR
(b) the gate removes >50% of baseline big-winner PnL; OR
(c) initial_sl share fails to fall >=10pp; OR
(d) pooled losing-month floor does not improve (stays >= baseline floor); OR
(e) mean trades/series < 10.
Do not add a second multiple, a second window, or a quote-volume conversion
after seeing the result without a new written hypothesis.
Do not declare this falsified because another name's liquidity gate failed,
and do not declare it passed because some other name's liquidity cell moved
PnL.

Data split:
Train-1 only (2024-03-01 <= entry < 2025-03-01 UTC). No validation/holdout.
If the gate looks promising, schedule a separate validation run later — do
not tune on it now. Do not open a validation window in this run. A validation
window is allowed only if a later Decision says this arm passed.

Budget:
One gated cell plus the ungated control. number_of_trials = 1.
No parameter sweep. The prior-20 median of base volume is the licensed §8
liquidity shape. It is not a copy of another name's measured liquidity mean
(do not import one).
```

decision_if_pass: REFINE (update EMA_50_200 profile metrics; consider a separate validation later; do not open holdout in this run; do not FREEZE on the pass alone)
decision_if_fail: liquidity is the last open licensed axis this profile names, once HTF direction is closed. Worker must not set FREEZE and must not change profile status. The ungated Train-1 book stays aggregate-positive (control mean +72.6693115, n=330), so this is not level D REJECT. Protocol §4 level C allows FREEZE after an own-trades falsification of this last axis (keep the strategy and the results; stop further tuning). That FREEZE is written only in the later Decision of this experiment, not in this pre-registration and not by the worker. This commit stays CONDITIONAL. Portfolio combination is not a remaining axis: shared-losing months (`dc9818e`) fail the §8 precondition. Price-versus-range is not a separately named axis here (candle close-strength already tested location in the bar). Breakout depth, HTF direction, absolute ATR%, and the xsym formula are already closed on this name. Do not open `EMA3_13_50_200` inside this run. Do not start funding-carry, spread-capture, or catalog mean-reversion. Do not treat the BB_20_2 liquidity ruling (`776e167`, FALSIFIED (c), then FREEZE) as this name's result or as this name's FREEZE. Do not retune the window or the median rule inside this run. Do not start a new signal family.

## Result

(empty — worker fills after the run)

## Decision

(empty — coordinator only)
