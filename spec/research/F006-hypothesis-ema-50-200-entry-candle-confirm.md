# F006 — H-EMA-50-200-ENTRY-CANDLE-CONFIRM-01 (pre-registered)

> Pre-registered **before** implementing or running the gate. After
> `H-EMA-50-200-XSYM-AGREE-SIZING-01` **FALSIFIED (b)** (`48d03b0`), journal +
> profile close that xsym-agree formula on `EMA_50_200` and name the next
> open axis as a not-yet-run §8 **entry-structure** hypothesis on this name's
> own trades. Entry-vol/abs-ATR is closed (FALSIFIED (a)+(c), tip `80e7fa6` /
> Decision `67af347`); the xsym sizing *formula* is closed; exit / direction /
> breadth levers already closed. This card is **not** a Val-1 of the closed
> stake and does **not** retune it. `BB_20_2_EMA200` is **FREEZE** after its
> own liquidity result (`776e167`). Its candle result at `88b0ee3` (T=0.60)
> and `BB_20_25_EMA200` candle result at `e70161d` (T=0.70) are **not** this
> test. Do not copy either name's control mean (+95.3217987 or +82.900262),
> n, initial_sl share, big-winner set, or pass/fail onto this card as an
> expected result.

experiment_id: H-EMA-50-200-ENTRY-CANDLE-CONFIRM-01
date: 2026-10-03
base_strategy: EMA_50_200 (NO_TRAIL, max_sl_pct=0.03, one-shot entry, signal_reverse exit)

```text
Observation:
EMA_50_200 stays CONDITIONAL after H-EMA-50-200-XSYM-AGREE-SIZING-01
FALSIFIED (b) (tip 48d03b0). Control mean +72.6693115/series reproduced
(max abs diff 0.0). Sized mean +126.744211. Pooled losing entry-months
stayed 7/12, so falsifier (b) fired and the formula is closed. Entry-vol /
abs-ATR own-trades gate FALSIFIED (a)+(c) tip 80e7fa6. Exit-class /
partial-exit / long-only / breadth already closed on this name's own-trade
evidence. Autopsy and the abs-ATR control (Train-1 n=330): initial_sl
213/330 (64.55%) at 0% WR; signal_reverse carries profit. The signal is an
EMA 50/200 cross; it does not require the signal bar to close decisively
in the trade direction relative to its own high-low range. Abs-ATR rejected
high absolute volatility; the closed stake rejected a cross-symbol
agreement multiplier because the month floor did not improve. Neither asked
whether the signal candle's close location (candle confirmation) separates
stop-outs from runners on THIS name.

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
multiplier.

Hypothesis:
Adding a single causal entry gate that rejects an EMA_50_200 one-shot
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
scripts/f006_ema_50_200_abs_atr_gate.py). No exit, sizing, symbol, interval,
direction, breadth, or ATR-threshold changes. NO_TRAIL unchanged. Exits
continue to use the ungated persistent signal (same as the abs-ATR gate
harness).

Baseline:
Ungated EMA_50_200 NO_TRAIL on the frozen 5-symbol x 2-interval Train-1
basket. Control must reproduce this name's catalog / abs-ATR / xsym control
figures before trusting gated cells:
  - mean train1_net_pnl = +72.6693115 (10 series, sum +726.693115)
  - Train-1 entry cohort n = 330, entry net = +587.3851786486205
  - initial_sl share = 213/330 = 0.6454545454545455 (64.55%)
  - big-winner PnL at net>=29.9 = +843.7639016181568 (5 trades)
  - pooled losing entry-months = 7/12
Reference source: output/f006_ema_50_200_abs_atr_gate/ control row, confirmed
by output/f006_ema_50_200_xsym_agree_sizing/summary/cell_summary.json control.
Do NOT import +95.3217987. Do NOT import +82.900262. Do NOT import n=756 or
n=512.

Metrics (pre-declared):
1. mean train1_net_pnl across 10 series (primary) / pooled net and net/trade
2. initial_sl share among closed Train-1-entry trades
3. n_trades (reject thin: mean n_trades/series < 10)
4. pooled losing-month floor (of 12, by entry-month). Confirm the control
   floor in this run. The xsym control measured 7/12; that is an observation
   to confirm, not an imported pass line from another name.
5. big-winner PnL retained vs this name's ungated baseline (freeze big winner
   = net>=29.9 before run). Recompute the set on this run's ungated blotter.
   The abs-ATR freeze observed 5 trades / +843.7639016181568; confirm, do not
   import another name's set.
6. #symbols net-positive / per-symbol losing-month floor (informational)
7. number_of_trials = 5

Expected improvement:
Mean train1_net_pnl > this name's control (+72.6693115) AND initial_sl
share down >=10pp at the best-PnL T AND >=50% of this name's big-winner PnL
retained AND pooled losing-month floor strictly below this name's ungated
entry-month floor AND mean trades/series >= 10. The 10pp and 50% figures
are the same pre-declared entry-gate checks already used on this name's
abs-ATR card. They are not BB_20_2's measured SL drop and not BB_20_25's
measured SL drop.

Falsification condition (any one => FALSIFIED):
(a) mean train1_net_pnl <= baseline at every T; OR
(b) every non-thin T removes >50% of baseline big-winner PnL; OR
(c) initial_sl share fails to fall >=10pp at the best-PnL T; OR
(d) pooled losing-month floor does not improve (stays >= baseline floor) at
    every T that otherwise passes (a)-(c); OR
(e) improvement is only from collapsing to <10 trades/series mean.
Do not widen T after seeing results without a new written hypothesis.
Do not declare this falsified because BB_20_2 candle failed at 88b0ee3 or
because BB_20_25 candle failed at e70161d, and do not declare it passed
because either name's Train-1 T raised mean PnL.

Data split:
Train-1 only (2024-03-01 <= entry < 2025-03-01 UTC). No validation/holdout.
If a T looks promising, schedule a separate validation run later — do not
tune on it now.

Budget:
T grid fixed before run:
{0.50, 0.60, 0.70, 0.80, 0.90} — max 5 trials.
Control (ungated) + 5 gated cells. Report all cells. Pick at most one T for
any follow-up. The grid shape matches the licensed §8 candle-confirm pattern
used elsewhere; it is not a copy of another name's winning T (not 0.60 from
BB_20_2, not 0.70 from BB_20_25).
```

decision_if_pass: REFINE (update EMA_50_200 profile metrics; consider a separate validation later; do not open holdout in this run; do not FREEZE on the pass alone)
decision_if_fail: keep CONDITIONAL; mark candle-confirm entry-structure axis closed on this
  name's own trades; next open §8 entry-structure variant (breakout depth) with a new written
  mechanism — still develop-not-abandon on this name; do not FREEZE; do not start EMA3_13_50_200

## Result

Run: `F006_DATA_CACHE=<main checkout>/data_cache python3 scripts/f006_ema_50_200_entry_candle_confirm.py`
at the committed script (manifest `git_commit` = script commit). Artifacts:
`output/f006_ema_50_200_entry_candle_confirm/` (grid_freeze.json written after
the control check and before any gated cell; manifest.json, cell_summary.csv,
results.csv, run.log, per-cell raw/ + blotters/). Train-1 caches only
(`*_20240126T000000Z_20250301T000000Z.csv`); checksums equal
`output/f006_ema_50_200_abs_atr_gate/grid_freeze.json` (hard STOP otherwise).
Validation/holdout not loaded. number_of_trials = 5. A second run at the
committed script was byte-identical to the first except wall-clock `seconds`.

Control (ungated) reproduced this name's baseline exactly:
- 10/10 series vs catalog5 Train-1 table, max abs train1_net_pnl diff **0.0**
- mean **+72.6693115** (sum +726.693115); entry n **330**, entry net
  **+587.3851786486205**; initial_sl **213/330 = 0.6454545454545455**
- big winners (net>=29.9, frozen on this run's ungated blotter before gated
  cells): **5 trades / +843.7639016181568** (confirms the abs-ATR freeze)
- pooled losing entry-months **7/12**
- every figure matches `output/f006_ema_50_200_abs_atr_gate/cell_summary.csv`
  control row (diff 0)

| cell | mean net/series | pooled net | entry n | trades/series | entry net | net/trade | initial_sl share | SL drop pp | BW kept (n / PnL / frac) | losing months | net+ symbols |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| control | +72.6693 | +726.693 | 330 | 33.0 | +587.385 | +1.780 | 64.55% | 0.00 | 5 / +843.76 / 1.000 | 7/12 | 3/5 |
| T=0.50 | +45.0267 | +450.267 | 197 | 19.7 | +310.024 | +1.574 | 67.51% | -2.97 | 2 / +472.64 / 0.560 | 8/12 | 2/5 |
| T=0.60 | +28.1760 | +281.760 | 154 | 15.4 | +192.725 | +1.251 | 68.18% | -3.64 | 1 / +334.55 / 0.396 | 8/12 | 2/5 |
| T=0.70 | +36.8518 | +368.518 | 114 | 11.4 | +279.483 | +2.452 | 67.54% | -3.00 | 1 / +334.55 / 0.396 | 8/12 | 3/5 |
| T=0.80 | +9.0471 | +90.471 | 79 | 7.9 (thin) | +2.153 | +0.027 | 65.82% | -1.28 | 0 / 0.00 / 0.000 | 7/12 | 4/5 |
| T=0.90 | +6.2881 | +62.881 | 47 | 4.7 (thin) | -11.928 | -0.254 | 65.96% | -1.41 | 0 / 0.00 / 0.000 | 6/12 | 3/5 |

Big-winner retention is by trade identity (symbol/interval/entry_time/
direction); every retained trade's net_pnl / exit_time / exit_reason were
identical to the control (0 mismatches). 0 NO_TRAIL violations.

Pre-declared falsifiers:
- (a) mean <= baseline at every T: **FIRES** (best T=0.50 +45.03 < +72.67;
  every T lowers mean).
- (b) every non-thin T removes >50% BW PnL: does not fire (T=0.50 keeps 56.0%;
  T=0.60/0.70 keep 39.6%).
- (c) best-PnL T (0.50) fails the >=10pp initial_sl drop: **FIRES** (share
  *rises* 2.97pp to 67.51%; no T lowers the initial_sl share at all).
- (d) no T passes (a)-(c), so the floor clause is vacuous: does not fire.
  Informational: non-thin T worsen the floor to 8/12. Only thin T=0.90
  reaches 6/12, with 0% BW retained and negative entry net.
- (e) no T beats the control mean, so no thin-only improvement exists: does
  not fire.

Flag check (floor lowered AND >=50% BW AND >=10 trades/series): **no T
qualifies.** T=0.90 lowers the floor only while thin (4.7/series) and with
0 big winners kept.

Outcome vs falsifiers: **FALSIFIED (a)+(c)** on EMA_50_200's own Train-1
trades. Passing cells: none. Profile status unchanged (CONDITIONAL); no FREEZE.

## Decision

(empty — coordinator only)
