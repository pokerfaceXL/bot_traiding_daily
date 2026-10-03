# F006 — H-EMA-50-200-ENTRY-HTF-DIRECTION-01 (pre-registered)

> Pre-registered **before** implementing or running the gate. After
> `H-EMA-50-200-ENTRY-BREAKOUT-DEPTH-01` **FALSIFIED (a)+(c)** (`485de51`),
> journal + profile close breakout depth on `EMA_50_200` and name the next
> open axis as a not-yet-run §8 **HTF direction** hypothesis on this name's
> own trades. Entry-vol/abs-ATR is closed (FALSIFIED (a)+(c), tip `80e7fa6` /
> Decision `67af347`); the xsym sizing *formula* is closed (FALSIFIED (b),
> tip `48d03b0` / Decision `f54e362`); candle close-strength is closed
> (FALSIFIED (a)+(c), tip `778f373` / Decision `4e32994`); breakout depth is
> closed. Exit / long-only direction / breadth already closed. This card is
> **not** a retune of D, **not** a Val-1 of the closed stake, **not** a
> candle retune, and **not** a liquidity filter. `BB_20_2_EMA200` is
> **FREEZE** after its own liquidity result (`776e167`). Its HTF-direction
> result and `BB_20_25_EMA200`'s HTF-direction result are **not** this test.
> Do not copy either name's control mean (+95.3217987 or +82.900262), n,
> initial_sl share, big-winner set, measured HTF-cell mean, or a pass/fail
> onto this card as an expected result. Do not use `bb_20_2.0_*` or
> `bb_20_2.5_*` — this name's signal is `sig_ema_cross(50, 200)`, columns
> `ema50` / `ema200`, not a Bollinger band. The same-timeframe `ema200` is
> not the higher-timeframe candle this gate reads.

experiment_id: H-EMA-50-200-ENTRY-HTF-DIRECTION-01
date: 2026-10-03
base_strategy: EMA_50_200 (NO_TRAIL, max_sl_pct=0.03, one-shot entry, signal_reverse exit)

```text
Observation:
EMA_50_200 stays CONDITIONAL after H-EMA-50-200-ENTRY-BREAKOUT-DEPTH-01
FALSIFIED (a)+(c) (tip 485de51). Control mean +72.6693115/series reproduced
(max abs diff 0.0, n=330). Best D=0.02 mean +63.0343180 (delta
-9.6349935/series). Initial_sl share rose 9.600886917960082 pp (213/330 =
0.6454545454545455 to 152/205 = 0.7414634146341463). Every D lowered the
mean. D=0.25 and D=0.50 took zero trades (vacuous floors). Entry-vol /
abs-ATR own-trades gate FALSIFIED (a)+(c) tip 80e7fa6. The xsym sizing
formula FALSIFIED (b) tip 48d03b0 (floor stayed 7/12; no Val-1). Candle
close-strength FALSIFIED (a)+(c) tip 778f373. Exit-class / partial-exit /
long-only / breadth already closed on this name's own-trade evidence. The
signal is a persistent EMA 50/200 state; the one-shot entry is the first
bar of each call, which is the bar ema50 crosses ema200. Depth asked how
far that close had cleared ema200. It did not ask whether the prior
completed higher-timeframe bar pointed the same way. That ema200 is the
same timeframe as the signal, not a higher timeframe.

Problem:
Most trades still die at the fixed initial_sl (213/330, 64.55%, 0% WR on the
ungated Train-1 cohort); pooled Train-1 losing-month floor is 7/12; 0/10
series clear §7. Closed levers (vol gate, one sizing formula, candle
close-strength, breakout depth, exit, direction, breadth) did not fix
regularity. A cross taken with the last completed coarser swing and a cross
taken against it are treated as the same signal. One remaining §8 entry
change on THIS name, orthogonal to absolute ATR%, to close-location inside
the bar, to ema200-normalized depth, and to the closed long-only lever,
written before the run.

Mechanism:
The fixed initial stop is where a cross that is already fighting the coarser
swing dies. A one-shot signal whose direction matches the previous fully
closed higher-timeframe candle is trading with that swing; a signal against
it is fading it. The higher-timeframe candle is built only from native bars
of the same loaded series that closed strictly before the signal bar's open,
so the signal bar is not inside it. Direction is the sign of that candle's
close minus its open. It is not an EMA (including ema50/ema200), not ATR,
not (close-low)/(high-low), not (close-ema200)/ema200, and not "drop all
shorts". Long-only is already closed and is not this test.

Hypothesis:
Adding a single causal entry gate that rejects an EMA_50_200 one-shot
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
scripts/f006_ema_50_200_entry_breakout_depth.py). No exit, sizing, symbol,
interval, long-only, breadth, ATR-threshold, candle-strength, or
breakout-depth changes. NO_TRAIL unchanged. Exits continue to use the
ungated persistent signal (same as the depth, candle, and abs-ATR
harnesses). Do not use ATR. Do not use ema50 or ema200 for this gate.
Do not read bb_20_2.0_* or bb_20_2.5_*.

Baseline:
Ungated EMA_50_200 NO_TRAIL on the frozen 5-symbol x 2-interval Train-1
basket. Control must reproduce this name's catalog / abs-ATR / xsym / candle
/ depth control figures before trusting the gated cell:
  - mean train1_net_pnl = +72.6693115 (10 series, sum +726.693115)
  - Train-1 entry cohort n = 330, entry net = +587.3851786486205
  - initial_sl share = 213/330 = 0.6454545454545455 (64.55%)
  - big-winner PnL at net>=29.9 = +843.7639016181568 (5 trades)
  - pooled losing entry-months = 7/12
Reference source: output/f006_ema_50_200_entry_breakout_depth/cell_summary.csv
control row (matches the candle and abs-ATR control rows, diff 0).
Do NOT import +95.3217987. Do NOT import +82.900262. Do NOT import n=756 or
n=512. Do NOT import any other name's HTF-cell mean, n, initial_sl share,
or pass/fail.

Metrics (pre-declared):
1. mean train1_net_pnl across 10 series (primary) / pooled net and net/trade
2. initial_sl share among closed Train-1-entry trades
3. n_trades (reject thin: mean n_trades/series < 10)
4. pooled losing-month floor (of 12, by entry-month). Confirm the control
   floor in this run. The depth control measured 7/12; that is an observation
   to confirm, not an imported pass line from another name.
5. big-winner PnL retained vs this name's ungated baseline (freeze big winner
   = net>=29.9 before the gated cell). Recompute the set on this run's
   ungated blotter. The depth freeze observed 5 trades /
   +843.7639016181568; confirm, do not import another name's set.
6. #symbols net-positive / per-symbol losing-month floor (informational)
7. number_of_trials = 1 (this gate is binary; do not add a strength grid)

Expected improvement:
Mean train1_net_pnl > this name's control (+72.6693115) AND initial_sl
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
Do not add a second threshold, a second HTF length, or a strength filter
after seeing the result without a new written hypothesis.
Do not declare this falsified because another name's HTF gate failed, and
do not declare it passed because some other name's HTF cell moved PnL.

Data split:
Train-1 only (2024-03-01 <= entry < 2025-03-01 UTC). No validation/holdout.
If the gate looks promising, schedule a separate validation run later — do
not tune on it now.

Budget:
One gated cell plus the ungated control. number_of_trials = 1.
No parameter sweep. The 4-bar bucket is the licensed §8 HTF-direction shape.
It is not a copy of another name's measured HTF mean (do not import one).
```

decision_if_pass: REFINE (update EMA_50_200 profile metrics; consider a separate validation later; do not open holdout in this run; do not FREEZE on the pass alone)
decision_if_fail: keep CONDITIONAL; mark HTF direction closed on this name's own trades;
  next open §8 entry variant is liquidity, with a new written mechanism. Liquidity
  would then be the last licensed axis on this name. FREEZE is allowed only at that
  later liquidity experiment's own Decision, not in this run and not on this card.
  Still develop-not-abandon until that Decision. Do not FREEZE now. Do not start
  EMA3_13_50_200. Do not start funding-carry, spread-capture, or catalog
  mean-reversion. Do not treat this result as evidence about other catalog5 names.
  Do not copy another name's HTF pass/fail.

## Result

Run: `scripts/f006_ema_50_200_entry_htf_direction.py` at harness commit
`54706a6` (manifest `git_commit`), Train-1 caches
`*_20240126T000000Z_20250301T000000Z.csv` from the main checkout's
`data_cache` (`F006_DATA_CACHE`); checksums equal
`output/f006_ema_50_200_abs_atr_gate/grid_freeze.json`. No validation /
holdout loaded. Artifacts: `output/f006_ema_50_200_entry_htf_direction/`
(`grid_freeze.json` written after the control check and before the gated
cell; `cell_summary.csv`, `results.csv`, `manifest.json`, `run.log`,
per-cell `raw/` + `blotters/`).

Control: reproduces this name's ungated Train-1 baseline exactly. Mean
+72.6693115 (sum +726.693115); entry n 330, entry net +587.3851786486205;
initial_sl 213/330 = 0.6454545454545455; big winners (net>=29.9, frozen on
this run's ungated blotter) 5 trades / +843.7639016181568 (depth freeze
confirmed); pooled losing entry-months 7/12. Max abs diff vs the catalog5
per-series table is 0.0 (10/10 rows, train1_net_pnl + n_trades). Every
metric matches the breakout-depth control row (diff 0).

`number_of_trials = 1`. Gate: keep a one-shot signal only when the prior
fully closed 4-native-bar epoch-floored HTF bucket (240m on 60m, 960m on
240m) has sign(close − open) equal to the signal direction; incomplete or
flat buckets reject. Exits use the ungated signal.

| cell | mean/series | entry n (per series) | entry net | initial_sl share (drop pp) | big-winner kept (n / PnL / frac) | losing months /12 | net+ symbols |
|---|---:|---:|---:|---:|---:|---:|---:|
| control | +72.6693115 | 330 (33.0) | +587.3852 | 0.6455 (0.00) | 5 / +843.7639 / 1.000 | 7 | 3/5 |
| htf_4 | +20.7369913 | 239 (23.9) | +156.4515 | 0.6736 (−2.82) | 3 / +371.1233 / 0.440 | 7 | 3/5 |

The gate kept 239 of 330 Train-1 entries (72.4%) and cut the mean by
−51.9323202/series. Initial_sl share **rose** 2.82 pp (0.6455 → 0.6736).
Two of the five big winners were rejected, so 44.0% of big-winner PnL was
kept (+371.1233 of +843.7639). The pooled floor stayed at 7/12. Net/trade
fell from +1.7800 to +0.6546. Per-symbol Train-1 net (gated): XRP +221.99,
DOGE +25.26, SOL +7.92, ETH −2.85, BTC −44.95. The flag case (lower floor
with >=50% big-winner PnL and >=10 trades/series) did not occur. Nothing to
flag.

Falsifiers (pre-declared):
- (a) mean <= baseline — **FIRES** (+20.7369913 <= +72.6693115).
- (b) removes >50% big-winner PnL — **FIRES** (kept 44.0%).
- (c) initial_sl share fails a >=10pp drop — **FIRES** (share rose 2.82 pp).
- (d) pooled floor does not improve — **FIRES** (7/12, equal to control).
- (e) mean trades/series < 10 — does not fire (23.9).

**Result: FALSIFIED (a)+(b)+(c)+(d)** on this name's own Train-1 trades. No
passing cell. Agreeing with the prior closed 4-bar candle did not lower the
fixed-stop death rate. It mainly removed runners.

Checks run: in-run control replay asserts (catalog5 table, breakout-depth
control row, checksum freeze); in-run matched-trade economics identity
(net / exit_time / exit_reason unchanged for every retained trade). An
independent recount used `DataFrame.resample(4*interval, origin="epoch")`
in place of the harness's ns-floor arithmetic. It recomputed the prior
bucket's direction and 4-bar completeness for every one-shot bar and
matched the gated `n_calls` on all 10 series (0 mismatches; 240m
6–13 kept, 60m 34–46 kept). Focused unit test
`tests/test_ema_50_200_entry_htf_direction.py` (6 cases: prior bucket only,
signal bar last in its bucket, flat, incomplete, 960m epoch alignment,
one-shot intersection) passes. Profile `status:` was not changed (still
CONDITIONAL).

## Decision

(empty — coordinator only)
