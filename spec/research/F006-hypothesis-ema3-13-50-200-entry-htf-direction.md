# F006 — H-EMA3-13-50-200-HTF-DIRECTION-01 (pre-registered)

> Pre-registered **before** implementing or running the gate. After
> `H-EMA3-13-50-200-ENTRY-BREAKOUT-DEPTH-01` **FALSIFIED (c)** (tip
> `c388392`, this Decision), journal + profile close breakout depth on
> `EMA3_13_50_200` and name the next open axis as a not-yet-run §8 **HTF
> direction** hypothesis on this name's own trades. Entry-vol/abs-ATR is
> closed (FALSIFIED (a)+(c), tip `46e4509` / Decision `3318658`; (d) was
> not reachable). The xsym sizing *formula* is closed (FALSIFIED (b), tip
> `34e2c4a` / Decision `396a3c2`). Candle close-strength is closed
> (FALSIFIED (a)+(b)+(c), tip `9dbcf0d` / Decision `079b697`). Breakout
> depth is closed (FALSIFIED (c) only; (a)(b)(e) did not fire; (d) was not
> reachable). Exit / long-only direction / breadth already closed. This
> card is **not** a retune of D, **not** a Val-1 of the closed stake,
> **not** a candle retune, and **not** a liquidity filter. `EMA_50_200` is
> **FREEZE** after its own liquidity result (`48aef9f`). Its HTF-direction
> result is **not** this test. Do not copy that name's control mean
> (+72.6693115), n, initial_sl share, big-winner set, measured htf_4 mean,
> or pass/fail onto this card as an expected result. `BB_20_2_EMA200` and
> `BB_20_25_EMA200` HTF results are **not** this test. Do not use
> `bb_20_2.0_*` or `bb_20_2.5_*`. The same-timeframe `ema200` this stack
> already uses is not the higher-timeframe candle this gate reads. Do not
> import +20.7369913, +63.0343180, +45.0267104, +72.6693115, +95.3217987,
> +82.900262, +87.8448967, or +126.744211.

experiment_id: H-EMA3-13-50-200-HTF-DIRECTION-01
date: 2026-10-03
base_strategy: EMA3_13_50_200 (NO_TRAIL, max_sl_pct=0.03, one-shot entry, signal_reverse exit)

```text
Observation:
EMA3_13_50_200 stays CONDITIONAL after H-EMA3-13-50-200-ENTRY-BREAKOUT-DEPTH-01
FALSIFIED (c) (tip c388392). Control mean +91.1483016/series reproduced
(max abs diff 0.0, sum +911.483016, n=423). Best D=0.02 mean +94.4530527
(delta +3.3047511/series). Initial_sl share rose 7.987900679852578 pp
(292/423 = 0.6903073286052009 to 248/322 = 0.7701863354037267). Big-winner
PnL retained 0.894213522771771 (6 / +1012.2104998530759 of 9 /
+1131.9561537333418), so (b) did not fire. Floor stayed 7/12; (d) was not
reachable because no D passed (a)-(c). (e) did not fire (32.2 trades/series
at the only D above control). Entry-vol / abs-ATR own-trades gate FALSIFIED
(a)+(c) tip 46e4509. The xsym sizing formula FALSIFIED (b) tip 34e2c4a
(floor stayed 7/12; no Val-1). Candle close-strength FALSIFIED (a)+(b)+(c)
tip 9dbcf0d. Exit-class / partial-exit / long-only / breadth already closed
on this name's own-trade evidence. The signal is sig_ema3_cross(13, 50, 200):
long when ema13 > ema50 > ema200, short when ema13 < ema50 < ema200. The
one-shot entry is the first bar of each call. Depth asked how far that
close had cleared same-timeframe ema200. It did not ask whether the prior
completed higher-timeframe candle pointed the same way. That ema200 is the
same timeframe as the signal, not a higher timeframe.

Problem:
Most trades still die at the fixed initial_sl (292/423, 69.03%, 0% WR on
the ungated Train-1 cohort); pooled Train-1 losing-month floor is 7/12;
0/10 series clear §7. Closed levers (vol gate, one sizing formula, candle
close-strength, breakout depth, exit, direction, breadth) did not fix
regularity. A stack alignment taken with the last completed coarser swing
and one taken against it are treated as the same signal. One remaining §8
entry change on THIS name, orthogonal to absolute ATR%, to close-location
inside the bar, to ema200-normalized depth, and to the closed long-only
lever, written before the run.

Mechanism:
The fixed initial stop is where a stack alignment that is already fighting
the coarser swing dies. A one-shot signal whose direction matches the
previous fully closed higher-timeframe candle is trading with that swing; a
signal against it is fading it. The higher-timeframe candle is built only
from native bars of the same loaded series that closed strictly before the
signal bar's open, so the signal bar is not inside it. Direction is the
sign of that candle's close minus its open. It is not an EMA (including
ema13, ema50, or ema200), not ATR, not (close-low)/(high-low), not
(close-ema200)/ema200, and not "drop all shorts". Long-only is already
closed and is not this test.

Hypothesis:
Adding a single causal entry gate that rejects an EMA3_13_50_200 one-shot
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
scripts/f006_ema3_13_50_200_entry_breakout_depth.py). No exit, sizing,
symbol, interval, long-only, breadth, ATR-threshold, candle-strength, or
breakout-depth changes. NO_TRAIL unchanged. Exits continue to use the
ungated persistent signal (same as the depth, candle, and abs-ATR
harnesses). Do not use ATR. Do not use ema13, ema50, or ema200 for this
gate. Do not read bb_20_2.0_* or bb_20_2.5_*. Do not reuse the closed
stake multiplier.

Baseline:
Ungated EMA3_13_50_200 NO_TRAIL on the frozen 5-symbol x 2-interval Train-1
basket. Control must reproduce this name's catalog / abs-ATR / xsym / candle
/ depth control figures before trusting the gated cell:
  - mean train1_net_pnl = +91.1483016 (10 series, sum +911.483016)
  - Train-1 entry cohort n = 423, entry net = +771.2836172145886
  - initial_sl share = 292/423 = 0.6903073286052009 (69.03%)
  - big-winner PnL at net>=29.9 = +1131.9561537333418 (9 trades)
  - pooled losing entry-months = 7/12
Reference source: output/f006_ema3_13_50_200_entry_breakout_depth/cell_summary.csv
control row (matches the candle and abs-ATR control rows, diff 0).
Do NOT import +72.6693115. Do NOT import +20.7369913. Do NOT import
+63.0343180. Do NOT import +45.0267104. Do NOT import +95.3217987. Do NOT
import +82.900262. Do NOT import n=330, n=756, or n=512. Do NOT import any
other name's HTF-cell mean, n, initial_sl share, or pass/fail.

Metrics (pre-declared):
1. mean train1_net_pnl across 10 series (primary) / pooled net and net/trade
2. initial_sl share among closed Train-1-entry trades
3. n_trades (reject thin: mean n_trades/series < 10)
4. pooled losing-month floor (of 12, by entry-month). Confirm the control
   floor in this run. The depth control measured 7/12; that is an observation
   to confirm, not an imported pass line from another name.
5. big-winner PnL retained vs this name's ungated baseline (freeze big winner
   = net>=29.9 before the gated cell). Recompute the set on this run's
   ungated blotter. The depth freeze observed 9 trades /
   +1131.9561537333418; confirm, do not import another name's set
   (not 5 / +843.7639016181568).
6. #symbols net-positive / per-symbol losing-month floor (informational)
7. number_of_trials = 1 (this gate is binary; do not add a strength grid)

Expected improvement:
Mean train1_net_pnl > this name's control (+91.1483016) AND initial_sl
share down >=10pp AND >=50% of this name's big-winner PnL retained AND
pooled losing-month floor strictly below this name's ungated entry-month
floor AND mean trades/series >= 10. The 10pp and 50% figures are the same
pre-declared entry-gate checks already used on this name's abs-ATR, candle,
and depth cards. They are not another name's measured SL drop.

Falsification condition (any one => FALSIFIED):
(a) mean train1_net_pnl <= baseline; OR
(b) the gate removes >50% of baseline big-winner PnL; OR
(c) initial_sl share fails to fall >=10pp; OR
(d) pooled losing-month floor does not improve (stays >= baseline floor); OR
(e) mean trades/series < 10.
This is the binary HTF-card shape: (d) is the floor sentence itself, not
the depth card's "only at a D that otherwise passes (a)-(c)". A flat floor
falsifies (d) on this card. Do not add a second threshold, a second HTF
length, or a strength filter after seeing the result without a new written
hypothesis. Do not declare this falsified because another name's HTF gate
failed, and do not declare it passed because some other name's HTF cell
moved PnL. Do not import +20.7369913.

Data split:
Train-1 only (2024-03-01 <= entry < 2025-03-01 UTC). No validation/holdout.
If the gate looks promising, schedule a separate validation run later — do
not tune on it now. Do not open a validation window of the closed sizing
formula.

Budget:
One gated cell plus the ungated control. number_of_trials = 1.
No parameter sweep. The 4-bar bucket is the licensed §8 HTF-direction shape.
It is not a copy of another name's measured HTF mean (do not import one).
```

decision_if_pass: REFINE (update EMA3_13_50_200 profile metrics; consider a separate validation later; do not open holdout in this run; do not FREEZE on the pass alone; status stays CONDITIONAL)
decision_if_fail: keep CONDITIONAL; mark HTF direction closed on this name's own trades;
  next open §8 entry variant is liquidity, with a new written mechanism. Liquidity
  would then be the last licensed axis on this name. FREEZE is allowed only at that
  later liquidity experiment's own Decision, and only if that experiment is falsified,
  every licensed axis is cited on this name's own trades, and the ungated Train-1 book
  stays aggregate-positive (§4 level C, not REJECT). Do not FREEZE now. Do not start
  funding-carry, spread-capture, catalog mean-reversion, a new family, or another
  catalog name. Do not treat this result as evidence about other catalog5 names.
  Do not copy another name's HTF pass/fail. Do not retune the 4-bar length.

## Result

Run: `F006_DATA_CACHE=/home/limen/bot_traiding_daily/bot_traiding_daily/data_cache python3 scripts/f006_ema3_13_50_200_entry_htf_direction.py`
(harness commit `4f02415`; artifacts `output/f006_ema3_13_50_200_entry_htf_direction/`).
The gate is imported unchanged from
`scripts/f006_ema_50_200_entry_htf_direction.py` (`htf_direction_entry_mask`:
prior fully closed 4-native-bar bucket, Unix-epoch floor of bar open, bucket
close <= signal bar open, exactly 4 native bars else reject, direction =
sign(htf_close - htf_open), flat rejects) and intersected with the
`EMA3_13_50_200` one-shot mask; exits use the ungated signal; no xsym stake;
no ATR / ema13 / ema50 / ema200 / candle strength / depth read by the gate.
Only the frozen Train-1 caches `*_20240126T000000Z_20250301T000000Z.csv`
were loaded; checksums equal
`output/f006_ema3_13_50_200_abs_atr_gate/grid_freeze.json`.
`grid_freeze.json` was written after the control check and before the gated
cell. `number_of_trials = 1`.

Control reproduced exactly (max abs train1 diff vs catalog5 = 0.0, 10/10 rows,
n_trades equal): mean +91.1483016 (sum +911.483016), Train-1 entry n=423,
entry net +771.2836172145886, initial_sl 292/423 = 0.6903073286052009, big
winners (net>=29.9, frozen on this run's ungated blotter) 9 trades /
+1131.9561537333418, pooled losing entry-months 7/12. All match the
breakout-depth control row (diff 0).

| cell | mean train1 net | n entry (mean/series) | initial_sl share (drop pp) | big-winner retained (by key) | entry net/trade | losing months | +symbols |
|---|---|---|---|---|---|---|---|
| control | +91.148302 | 423 (42.3) | 292/423 = 69.03% (0.0) | 9 / +1131.956 (100%) | +1.8234 | 7/12 | 3/5 |
| htf_4 | +39.230342 | 362 (36.2) | 260/362 = 71.82% (-2.79) | 6 / +628.996 (55.6%) | +0.7289 | 7/12 | 3/5 |

Negative drop = initial_sl share rose. Gated mean delta -51.9179598/series
(pooled +392.303418 vs +911.483016; entry net +263.868277 vs +771.283617).
htf_4 per-symbol train1 net: DOGE +258.10, XRP +130.61, BTC +5.26,
ETH -0.31, SOL -1.35 (control: XRP +515.63, DOGE +410.05, SOL +36.47,
BTC -5.58, ETH -45.08). Per-symbol losing entry-months htf_4: SOL 6, ETH 7,
BTC 6, XRP 10, DOGE 7 (control: SOL 6, ETH 7, BTC 6, XRP 9, DOGE 6).
Losing months htf_4: 2024-03, -04, -05, -08, -09, -12, 2025-01 (same seven as
control). Dropped big winners (signal against the prior 4-bar candle):
XRPUSDT 240 2024-11-10 long +334.548, DOGEUSDT 60 2024-11-05 long +138.093,
SOLUSDT 60 2024-03-06 long +30.320; 2024-11 entry net fell +812.27 -> +346.62.

Independent check: a naive per-bar recomputation of the prior 4-bar bucket
(epoch floor, completeness, sign of close-open, bucket strictly before the
signal bar) over all 882 one-shot entries (warmup included) kept 640 and
disagreed with the harness mask on 0. Re-running at the harness commit
reproduced the same cell figures.

Falsifiers:
- (a) FIRES — gated mean +39.230342 <= control +91.148302.
- (b) does not fire — retains 55.6% of baseline big-winner PnL (6 of 9).
- (c) FIRES — initial_sl share rose 2.79pp (69.03% -> 71.82%) instead of
  falling >=10pp.
- (d) FIRES — pooled losing-month floor stays 7/12 (not strictly below 7).
- (e) does not fire — 36.2 trades/series.

The gate does not lower the pooled floor (stays 7/12) while keeping >=50%
big-winner PnL and >=10 trades/series, so the flag condition in the ticket
is not met. Outcome against the pre-declared falsifiers: FALSIFIED
(a)+(c)+(d). Decision left to the coordinator; profile status unchanged
(CONDITIONAL).

## Decision

(empty — coordinator only)
