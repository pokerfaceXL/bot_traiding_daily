# F006 — H-EMA3-13-50-200-ENTRY-LIQUIDITY-01 (pre-registered)

> Pre-registered **before** implementing or running the gate. After
> `H-EMA3-13-50-200-HTF-DIRECTION-01` **FALSIFIED (a)+(c)+(d)** (tip
> `c70777a`, this Decision), journal + profile close HTF direction on
> `EMA3_13_50_200` and name the next open axis as a not-yet-run §8
> **liquidity** hypothesis on this name's own trades. Entry-vol/abs-ATR is
> closed (FALSIFIED (a)+(c), tip `46e4509` / Decision `3318658`; (d) was
> not reachable). The xsym sizing *formula* is closed (FALSIFIED (b), tip
> `34e2c4a` / Decision `396a3c2`). Candle close-strength is closed
> (FALSIFIED (a)+(b)+(c), tip `9dbcf0d` / Decision `079b697`). Breakout
> depth is closed (FALSIFIED (c) only, tip `c388392` / Decision `07fb827`;
> (d) was not reachable). HTF direction is closed (FALSIFIED (a)+(c)+(d),
> tip `c70777a`). Exit / long-only direction / breadth already closed. This
> card is **not** a retune of the 4-bar HTF length, **not** a Val-1 of the
> closed stake, **not** a candle retune, **not** a depth retune, and **not**
> `vol_ratio > 1.2`. `EMA_50_200` is **FREEZE** after its own liquidity
> result (`48aef9f` / Decision `d74c5dd`). That measured liquidity cell
> (mean, n, initial_sl share, big-winner retention, floor move, pass/fail)
> is **not** this test. Do not copy +66.5789284, +72.6693115, n=330,
> initial_sl 0.6454545454545455, 5/5 big winners, or a 7/12 floor onto this
> card as an expected result. Do not copy +97.2455987 or +95.3217987. Do
> not use `bb_20_2.0_*` or `bb_20_2.5_*` — this name's signal is
> `sig_ema3_cross(13, 50, 200)`, not a Bollinger band. The profile names
> liquidity as an axis and does not specify a formula. The licensed shape
> is the one already used on `EMA_50_200` / `BB_20_2_EMA200`: a one-shot
> keep on base volume versus the prior-20 median. The lookback 20 is that
> licensed shape, not this name's EMA length.

experiment_id: H-EMA3-13-50-200-ENTRY-LIQUIDITY-01
date: 2026-10-03
base_strategy: EMA3_13_50_200 (NO_TRAIL, max_sl_pct=0.03, one-shot entry, signal_reverse exit)

```text
Observation:
EMA3_13_50_200 stays CONDITIONAL after H-EMA3-13-50-200-HTF-DIRECTION-01
FALSIFIED (a)+(c)+(d) (tip c70777a). Control mean +91.1483016/series
reproduced (max abs diff 0.0, sum +911.483016, n=423). Gated htf_4 mean
+39.2303418 (delta -51.9179598/series), entry n=362. Initial_sl share rose
2.792471559369414 pp (292/423 = 0.6903073286052009 to
260/362 = 0.7182320441988951). Big-winner PnL kept 6 /
+628.9955850277897 / 0.5556713331636377, so (b) did not fire. Pooled
entry-month floor stayed 7/12. The card's (d) sentence is "pooled
losing-month floor does not improve (stays >= baseline floor)", so the
flat floor fires (d). Entry-vol / abs-ATR own-trades gate FALSIFIED
(a)+(c) tip 46e4509. The xsym sizing formula FALSIFIED (b) tip 34e2c4a
(floor stayed 7/12; no Val-1). Candle close-strength FALSIFIED (a)+(b)+(c)
tip 9dbcf0d. Breakout depth FALSIFIED (c) only tip c388392. Exit-class /
partial-exit / long-only / breadth already closed on this name's own-trade
evidence. HTF asked whether the prior completed coarser candle pointed the
same way. It did not ask whether the signal bar itself traded on
above-median base volume.

Problem:
Most trades still die at the fixed initial_sl (292/423, 69.03%, 0% WR on
the ungated Train-1 cohort); pooled Train-1 losing-month floor is 7/12;
0/10 series clear §7. Closed levers (vol gate as absolute ATR%, one sizing
formula, candle close-strength, breakout depth, HTF direction, exit,
direction, breadth) did not fix regularity. A stack alignment printed on a
quiet bar and one printed when base volume is at least the recent median
are treated as the same signal. One remaining §8 entry change on THIS
name, orthogonal to absolute ATR%, to close-location inside the bar, to
ema200-normalized depth, and to the closed HTF-direction lever, written
before the run. The profile only names the axis. The shape below is the
licensed liquidity rule, not another name's measured result.

Mechanism:
The fixed initial stop is where a stack alignment that prints without
participation dies. A one-shot signal whose bar has base volume at least
the median of the prior 20 closed bars is trading when the book is at
least as active as the recent past; a signal below that median is a quiet
print. The window is the 20 native bars strictly before the signal bar.
The signal bar is not inside it. The column is native base volume, not
quote volume, not vol_ratio, not vol_ma20, not ATR, not ema13/ema50/ema200,
not (close-low)/(high-low), not (close-ema200)/ema200, and not the sign of
a higher-timeframe candle. Long-only is already closed and is not this
test. Absolute ATR% is already closed and is not this test.

Hypothesis:
Adding a single causal entry gate that rejects an EMA3_13_50_200 one-shot
signal when the signal bar's base volume is below the median volume of the
prior 20 closed bars will raise mean Train-1 net PnL versus the ungated
NO_TRAIL baseline AND cut the initial_sl share among remaining trades,
while retaining enough big-winner PnL that the pooled losing-month floor
can improve — earned on this name's own trades.

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
scripts/f006_ema3_13_50_200_entry_htf_direction.py). No exit, sizing,
symbol, interval, long-only, breadth, ATR-threshold, candle-strength,
breakout-depth, or HTF-direction changes. NO_TRAIL unchanged. Exits
continue to use the ungated persistent signal (same as the HTF harness).
Do not use ATR. Do not use ema13, ema50, or ema200 for this gate. Do not
read bb_20_2.0_* or bb_20_2.5_*. Do not implement vol_ratio > 1.2. The
lookback 20 is the licensed liquidity shape (prior 20 closed bars), not
this name's EMA period and not a copied measured cell. Binary gate. Do not
grid the multiple and do not grid the window.

Baseline:
Ungated EMA3_13_50_200 NO_TRAIL on the frozen 5-symbol x 2-interval Train-1
basket. Control must reproduce this name's catalog / abs-ATR / xsym / candle
/ depth / HTF control figures before trusting the gated cell:
  - mean train1_net_pnl = +91.1483016 (10 series, sum +911.483016)
  - Train-1 entry cohort n = 423, entry net = +771.2836172145886
  - initial_sl share = 292/423 = 0.6903073286052009 (69.03%)
  - big-winner PnL at net>=29.9 = +1131.9561537333418 (9 trades)
  - pooled losing entry-months = 7/12
Reference source: output/f006_ema3_13_50_200_entry_htf_direction/cell_summary.csv
control row (matches the depth, candle, and abs-ATR control rows, diff 0).
Do NOT import +72.6693115. Do NOT import +66.5789284. Do NOT import
+97.2455987. Do NOT import +20.7369913. Do NOT import +63.0343180. Do NOT
import +45.0267104. Do NOT import +95.3217987. Do NOT import +82.900262.
Do NOT import n=330, n=756, or n=512. Do NOT import any other name's
liquidity-cell mean, n, initial_sl share, big-winner retention, floor, or
pass/fail.

Metrics (pre-declared):
1. mean train1_net_pnl across 10 series (primary) / pooled net and net/trade
2. initial_sl share among closed Train-1-entry trades
3. n_trades (reject thin: mean n_trades/series < 10)
4. pooled losing-month floor (of 12, by entry-month). Confirm the control
   floor in this run. The HTF control measured 7/12; that is an observation
   to confirm, not an imported pass line from another name.
5. big-winner PnL retained vs this name's ungated baseline (freeze big winner
   = net>=29.9 before the gated cell). Recompute the set on this run's
   ungated blotter. The HTF freeze observed 9 trades /
   +1131.9561537333418; confirm, do not import another name's set
   (not 5 / +843.7639016181568).
6. #symbols net-positive / per-symbol losing-month floor (informational)
7. number_of_trials = 1 (this gate is binary; do not add a multiple grid)

Expected improvement:
Mean train1_net_pnl > this name's control (+91.1483016) AND initial_sl
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
This is the binary liquidity-card shape: (d) is the floor sentence itself.
A flat floor falsifies (d) on this card. Do not add a second multiple, a
second window, or a quote-volume conversion after seeing the result without
a new written hypothesis. Do not declare this falsified because another
name's liquidity gate failed, and do not declare it passed because some
other name's liquidity cell moved PnL.

Data split:
Train-1 only (2024-03-01 <= entry < 2025-03-01 UTC). No validation/holdout.
If the gate looks promising, schedule a separate validation run later — do
not tune on it now. Do not open a validation window in this run. A
validation window is allowed only if a later Decision says this arm passed.

Budget:
One gated cell plus the ungated control. number_of_trials = 1.
No parameter sweep. The prior-20 median of base volume is the licensed §8
liquidity shape. It is not a copy of another name's measured liquidity mean
(do not import one).
```

decision_if_pass: REFINE (update EMA3_13_50_200 profile metrics; consider a separate validation later; do not open holdout in this run; do not FREEZE on the pass alone; status stays CONDITIONAL)
decision_if_fail: liquidity is the last open licensed axis this profile names, once HTF direction is closed. Worker must not set FREEZE and must not change profile status. If the liquidity experiment is falsified on this name's own trades AND every licensed axis above is cited (abs-ATR tip `46e4509` / Decision `3318658` FALSIFIED (a)+(c); xsym tip `34e2c4a` / Decision `396a3c2` FALSIFIED (b); candle tip `9dbcf0d` / Decision `079b697` FALSIFIED (a)+(b)+(c); breakout-depth tip `c388392` / Decision `07fb827` FALSIFIED (c) only; HTF tip `c70777a` / this Decision FALSIFIED (a)+(c)+(d); plus exit / long-only / breadth) AND the ungated Train-1 book stays aggregate-positive (control mean +91.1483016, n=423), status may become FREEZE at protocol §4 level C (keep the strategy and the results; stop further tuning; not REJECT / level D). That FREEZE is written only in the later Decision of this experiment, not in this pre-registration and not by the worker. If a cell passes, stay CONDITIONAL and do not FREEZE. This commit stays CONDITIONAL. Portfolio combination is not a remaining axis: shared-losing months (`dc9818e`) fail the §8 precondition. Price-versus-range is not a separately named axis here (candle close-strength already tested location in the bar). Breakout depth, HTF direction, absolute ATR%, and the xsym formula are already closed on this name. Do not open another catalog name inside this run. Do not start funding-carry, spread-capture, or catalog mean-reversion. Do not treat the EMA_50_200 liquidity ruling (`48aef9f`, FALSIFIED (a)+(c)+(d), then FREEZE) or the BB_20_2 liquidity ruling (`776e167`) as this name's result or as this name's FREEZE. Do not retune the window or the median rule inside this run. Do not start a new signal family.

## Result

(empty — worker fills after the run)

## Decision

(empty — coordinator only)
