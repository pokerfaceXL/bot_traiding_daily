# F006 — H-EMA-50-200-ENTRY-BREAKOUT-DEPTH-01 (pre-registered)

> Pre-registered **before** implementing or running the gate. After
> `H-EMA-50-200-ENTRY-CANDLE-CONFIRM-01` **FALSIFIED (a)+(c)** (`778f373`),
> journal + profile close candle close-strength on `EMA_50_200` and name the
> next open axis as a not-yet-run §8 **breakout-depth** hypothesis on this
> name's own trades. Entry-vol/abs-ATR is closed (FALSIFIED (a)+(c), tip
> `80e7fa6` / Decision `67af347`); the xsym sizing *formula* is closed
> (FALSIFIED (b), tip `48d03b0` / Decision `f54e362`); candle close-strength
> is closed. Exit / direction / breadth already closed. This card is **not**
> a retune of T, **not** a Val-1 of the closed stake, and **not** HTF
> direction or a liquidity filter. `BB_20_2_EMA200` is **FREEZE** after its
> own liquidity result (`776e167`). Its breakout-depth result and
> `BB_20_25_EMA200`'s breakout-depth result are **not** this test. Do not
> copy either name's control mean (+95.3217987 or +82.900262), n, initial_sl
> share, big-winner set, measured depth-cell means, or a "winning D" onto
> this card as an expected result. Neither of those depth runs produced a
> D to copy. Do not use `bb_20_2.0_*` or `bb_20_2.5_*` — this name's signal
> is `sig_ema_cross(50, 200)`, columns `ema50` / `ema200`, not a Bollinger
> band.

experiment_id: H-EMA-50-200-ENTRY-BREAKOUT-DEPTH-01
date: 2026-10-03
base_strategy: EMA_50_200 (NO_TRAIL, max_sl_pct=0.03, one-shot entry, signal_reverse exit)

```text
Observation:
EMA_50_200 stays CONDITIONAL after H-EMA-50-200-ENTRY-CANDLE-CONFIRM-01
FALSIFIED (a)+(c) (tip 778f373). Control mean +72.6693115/series reproduced
(max abs diff 0.0). Best T=0.50 mean +45.0267104 (delta -27.6426011/series).
Initial_sl share rose 2.9672358098754015 pp (213/330 = 0.6454545454545455 to
133/197 = 0.6751269035532995). Every T lowered the mean. Entry-vol / abs-ATR
own-trades gate FALSIFIED (a)+(c) tip 80e7fa6. The xsym sizing formula
FALSIFIED (b) tip 48d03b0 (floor stayed 7/12; no Val-1). Exit-class /
partial-exit / long-only / breadth already closed on this name's own-trade
evidence. The signal is a persistent EMA 50/200 state; the one-shot entry is
the first bar of each call, which is the bar ema50 crosses ema200. Candle
confirm asked where that bar's close sat inside its own high-low range. It
did not ask how far that close has cleared the slow EMA the cross just broke.

Problem:
Most trades still die at the fixed initial_sl (213/330, 64.55%, 0% WR on the
ungated Train-1 cohort); pooled Train-1 losing-month floor is 7/12; 0/10
series clear §7. Closed levers (vol gate, one sizing formula, candle
close-strength, exit, direction, breadth) did not fix regularity. A cross
whose close is still hugging ema200 and a cross whose close has already
cleared a material fraction of ema200 are treated as the same signal. One
remaining §8 entry-structure change on THIS name, orthogonal to absolute
ATR%, to close-location inside the bar, and to the closed stake, written
before the run.

Mechanism:
On the one-shot bar, ema50 has just crossed ema200, so |ema50 - ema200| is
near zero by construction and cannot be the depth denominator (it would make
depth undefined). The level that was broken is ema200. A close that only
sits on that line is a shallow cross: price has barely cleared the slow
average and is more likely to fall back into the fixed initial stop. A close
that sits a larger fraction of ema200 beyond that line has committed more
distance to the trade side and is more likely to travel to the opposite
structural extreme (signal_reverse). Depth is computed only from the closed
signal bar's close and that bar's own ema200. It is causal, it is not an
absolute ATR% threshold, it is not (close-low)/(high-low), and it is not a
Bollinger width. Dividing by ema200 keeps the gate from being another raw
volatility cutoff (the closed abs-ATR axis) and from retesting candle
close-strength.

Hypothesis:
Adding a single causal entry gate that rejects an EMA_50_200 one-shot
signal when the signal bar's ema200-normalized breakout depth is below a
pre-registered threshold D will raise mean Train-1 net PnL versus the ungated
NO_TRAIL baseline AND cut the initial_sl share among remaining trades, while
retaining enough big-winner PnL that the pooled losing-month floor can
improve — earned on this name's own trades.

Change to test:
ONE entry refinement only (§8 breakout depth / distance beyond the slow EMA).
On the closed signal bar, using the slow EMA this signal already crosses:

  ema_slow = ema200
  depth_long  = (close - ema_slow) / ema_slow    # fail if ema_slow is missing or <= 0
  depth_short = (ema_slow - close) / ema_slow
  keep iff:
    direction == +1 and depth_long  >= D
    direction == -1 and depth_short >= D
    (ema_slow missing or <= 0 => reject)

Do not read bb_20_2.0_* or bb_20_2.5_*. Do not use atr14. Do not use
(close - low) / (high - low). Do not divide by |ema50 - ema200|. Intersect
with the existing one-shot entry mask (same pattern as
scripts/f006_ema_50_200_entry_candle_confirm.py). No exit, sizing, symbol,
interval, direction, breadth, ATR-threshold, or candle-strength changes.
NO_TRAIL unchanged. Exits continue to use the ungated persistent signal
(same as the candle and abs-ATR harnesses).

Baseline:
Ungated EMA_50_200 NO_TRAIL on the frozen 5-symbol x 2-interval Train-1
basket. Control must reproduce this name's catalog / abs-ATR / xsym / candle
control figures before trusting gated cells:
  - mean train1_net_pnl = +72.6693115 (10 series, sum +726.693115)
  - Train-1 entry cohort n = 330, entry net = +587.3851786486205
  - initial_sl share = 213/330 = 0.6454545454545455 (64.55%)
  - big-winner PnL at net>=29.9 = +843.7639016181568 (5 trades)
  - pooled losing entry-months = 7/12
Reference source: output/f006_ema_50_200_entry_candle_confirm/cell_summary.csv
control row (matches output/f006_ema_50_200_abs_atr_gate/ control row, diff 0).
Do NOT import +95.3217987. Do NOT import +82.900262. Do NOT import n=756 or
n=512. Do NOT import any other name's depth-cell mean or its best D.

Metrics (pre-declared):
1. mean train1_net_pnl across 10 series (primary) / pooled net and net/trade
2. initial_sl share among closed Train-1-entry trades
3. n_trades (reject thin: mean n_trades/series < 10)
4. pooled losing-month floor (of 12, by entry-month). Confirm the control
   floor in this run. The candle control measured 7/12; that is an observation
   to confirm, not an imported pass line from another name.
5. big-winner PnL retained vs this name's ungated baseline (freeze big winner
   = net>=29.9 before run). Recompute the set on this run's ungated blotter.
   The candle freeze observed 5 trades / +843.7639016181568; confirm, do not
   import another name's set.
6. #symbols net-positive / per-symbol losing-month floor (informational)
7. number_of_trials = 5

Expected improvement:
Mean train1_net_pnl > this name's control (+72.6693115) AND initial_sl
share down >=10pp at the best-PnL D AND >=50% of this name's big-winner PnL
retained AND pooled losing-month floor strictly below this name's ungated
entry-month floor AND mean trades/series >= 10. The 10pp and 50% figures
are the same pre-declared entry-gate checks already used on this name's
abs-ATR and candle cards. They are not another name's measured SL drop.

Falsification condition (any one => FALSIFIED):
(a) mean train1_net_pnl <= baseline at every D; OR
(b) every non-thin D removes >50% of baseline big-winner PnL; OR
(c) initial_sl share fails to fall >=10pp at the best-PnL D; OR
(d) pooled losing-month floor does not improve (stays >= baseline floor) at
    every D that otherwise passes (a)-(c); OR
(e) improvement is only from collapsing to <10 trades/series mean.
Do not widen D after seeing results without a new written hypothesis.
Do not declare this falsified because another name's breakout depth failed,
and do not declare it passed because some other name's depth cell moved PnL.

Data split:
Train-1 only (2024-03-01 <= entry < 2025-03-01 UTC). No validation/holdout.
If a D looks promising, schedule a separate validation run later — do not
tune on it now.

Budget:
D grid fixed before run:
{0.02, 0.05, 0.10, 0.25, 0.50} — max 5 trials.
Units are fractions of ema200 beyond the slow EMA (close vs ema200), not
ATR, not close-location inside the bar, and not a Bollinger band width.
The grid shape matches the licensed §8 breakout-depth pattern used
elsewhere. It is not a copy of another name's winning D (there is none to
copy). Control (ungated) + 5 gated cells. Report all cells. Pick at most
one D for any follow-up.
```

decision_if_pass: REFINE (update EMA_50_200 profile metrics; consider a separate validation later; do not open holdout in this run; do not FREEZE on the pass alone)
decision_if_fail: keep CONDITIONAL; mark breakout-depth closed on this name's own trades;
  next open §8 entry variant is HTF direction, with a new written mechanism — liquidity
  stays open after that; still develop-not-abandon on this name; do not FREEZE; do not
  start EMA3_13_50_200; do not start funding-carry, spread-capture, or catalog
  mean-reversion; do not treat this result as evidence about other catalog5 names

## Result

Run: `scripts/f006_ema_50_200_entry_breakout_depth.py` at harness commit
`a243176` (manifest `git_commit`), Train-1 caches
`*_20240126T000000Z_20250301T000000Z.csv` from the main checkout's
`data_cache` (`F006_DATA_CACHE`); checksums equal
`output/f006_ema_50_200_abs_atr_gate/grid_freeze.json`. No validation /
holdout loaded. Artifacts: `output/f006_ema_50_200_entry_breakout_depth/`
(`grid_freeze.json` written after the control check and before any gated
cell; `cell_summary.csv`, `results.csv`, `manifest.json`, `run.log`,
per-cell `raw/` + `blotters/`).

Control: reproduces this name's ungated Train-1 baseline exactly. Mean
+72.6693115 (sum +726.693115); entry n 330, entry net +587.3851786486205;
initial_sl 213/330 = 0.6454545454545455; big winners (net>=29.9, frozen on
this run's ungated blotter) 5 trades / +843.7639016181568 (candle freeze
confirmed); pooled losing entry-months 7/12. Max abs diff vs the catalog5
per-series table is 0.0 (10/10 rows, train1_net_pnl + n_trades). Every
metric matches the candle-confirm control row (diff 0).

`number_of_trials = 5`. D = fraction of ema200 that the signal-bar close sits
beyond ema200 in the trade direction.

| cell | mean/series | entry n (per series) | entry net | initial_sl share (drop pp) | big-winner kept (n / PnL / frac) | losing months /12 | net+ symbols |
|---|---:|---:|---:|---:|---:|---:|---:|
| control | +72.6693115 | 330 (33.0) | +587.3852 | 0.6455 (0.00) | 5 / +843.7639 / 1.000 | 7 | 3/5 |
| D=0.02 | +63.0343180 | 205 (20.5) | +615.5695 | 0.7415 (−9.60) | 3 / +760.9812 / 0.902 | 8 | 2/5 |
| D=0.05 | −10.1819257 | 70 (7.0) | −101.8193 | 0.8571 (−21.17) | 0 / 0.0 / 0.000 | 10 | 1/5 |
| D=0.10 | +0.5031110 | 15 (1.5) | +5.0311 | 0.8000 (−15.45) | 0 / 0.0 / 0.000 | 7 | 2/5 |
| D=0.25 | 0.0 | 0 (0.0) | 0.0 | n/a | 0 / 0.0 / 0.000 | 0 (empty) | 0/5 |
| D=0.50 | 0.0 | 0 (0.0) | 0.0 | n/a | 0 / 0.0 / 0.000 | 0 (empty) | 0/5 |

Best-PnL D = 0.02 (mean +63.0343180, delta −9.6349935/series). Every D
lowered the mean. Initial_sl share **rose** at every non-empty D (best-PnL D:
+9.60 pp, 0.6455 → 0.7415). D=0.02 kept 90.2% of big-winner PnL (3/5 trades)
but the floor worsened to 8/12. D>=0.05 is thin (<10 trades/series) and kept
none of the 5 big winners. D=0.25 and D=0.50 admit zero trades: the largest
one-shot-bar depth in any series is 0.2175 (SOLUSDT 240). The 60m maximums
run from 0.0736 to 0.1286. No D lowered the pooled floor while keeping >=50%
big-winner PnL and >=10 trades/series. Nothing to flag.

Falsifiers (pre-declared):
- (a) mean <= baseline at every D — **FIRES** (best +63.0343180 < +72.6693115).
- (b) every non-thin D removes >50% big-winner PnL — does not fire (only
  non-thin D=0.02 keeps 90.2%).
- (c) best-PnL D fails a >=10pp initial_sl drop — **FIRES** (share rose 9.60 pp).
- (d) floor does not improve at D passing (a)-(c) — not triggered (no D passes
  (a)-(c), so it is vacuous).
- (e) improvement only from thin cells — does not fire (no cell beats control).

**Result: FALSIFIED (a)+(c)** on this name's own Train-1 trades. No passing
cell. The mechanism inverted: crosses whose close sits further beyond ema200
stopped out at the fixed initial_sl *more* often, not less.

Checks run: in-run control replay asserts (catalog5 table, candle control row,
checksum freeze); in-run matched-trade economics identity (net / exit_time /
exit_reason unchanged for every retained trade, all cells); an independent
recount of one-shot cross bars with directional depth >= D, recomputed from
raw ema50/ema200. It matched `n_calls` on all 50 series x cell pairs (0
mismatches). `python3 -m pytest -q`: 489 passed, 8 skipped. Profile `status:`
was not changed (still CONDITIONAL).

## Decision

(empty — coordinator only)
