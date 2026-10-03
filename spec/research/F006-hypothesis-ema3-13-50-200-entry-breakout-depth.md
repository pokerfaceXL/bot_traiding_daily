# F006 — H-EMA3-13-50-200-ENTRY-BREAKOUT-DEPTH-01 (pre-registered)

> Pre-registered **before** implementing or running the gate. After
> `H-EMA3-13-50-200-ENTRY-CANDLE-CONFIRM-01` **FALSIFIED (a)+(b)+(c)** (`9dbcf0d`),
> journal + profile close candle close-strength on `EMA3_13_50_200` and name
> the next open axis as a not-yet-run §8 **breakout-depth** hypothesis on
> this name's own trades. Entry-vol/abs-ATR is closed (FALSIFIED (a)+(c),
> tip `46e4509` / Decision `3318658`; (d) was not reachable). The xsym sizing
> *formula* is closed (FALSIFIED (b), tip `34e2c4a` / Decision `396a3c2`;
> flat floor, no validation window). Candle close-strength is closed.
> Exit / direction / breadth already closed. This card is **not** a retune
> of T, **not** a Val-1 of the closed stake, and **not** HTF direction or a
> liquidity filter. `EMA_50_200` is **FREEZE** after its own liquidity result
> (`48aef9f`). Its breakout-depth result at `485de51` (best-but-failed D=0.02,
> mean +63.0343180, FALSIFIED (a)+(c)) is **not** this test. `BB_20_2_EMA200`
> depth at `27fa7f6` and `BB_20_25_EMA200` depth at `0685ce5` are **not** this
> test. Do not copy another name's control mean, n, initial_sl share,
> big-winner set, measured depth-cell means, or a winning D onto this card
> as an expected result. There is no winning D to copy. Do not use
> `bb_20_2.0_*` or `bb_20_2.5_*`. Do not import +72.6693115, +95.3217987,
> +82.900262, +126.744211, +45.0267104, +63.0343180, or +87.8448967.

experiment_id: H-EMA3-13-50-200-ENTRY-BREAKOUT-DEPTH-01
date: 2026-10-03
base_strategy: EMA3_13_50_200 (NO_TRAIL, max_sl_pct=0.03, one-shot entry, signal_reverse exit)

```text
Observation:
EMA3_13_50_200 stays CONDITIONAL after H-EMA3-13-50-200-ENTRY-CANDLE-CONFIRM-01
FALSIFIED (a)+(b)+(c) (tip 9dbcf0d). Control mean +91.1483016/series reproduced
(max abs diff 0.0, sum +911.483016). Best T=0.50 mean +51.7526015 (delta
-39.3957001/series). Initial_sl share rose 2.8047101774545946 pp (292/423 =
0.6903073286052009 to 227/316 = 0.7183544303797469). Big-winner PnL retained
0.48671028537156213, so 51.32897146284379% was removed and card (b) fired.
Floor stayed 7/12; (d) was not reachable because no T passed (a)-(c). (e)
did not fire. Entry-vol / abs-ATR own-trades gate FALSIFIED (a)+(c) tip
46e4509. The xsym sizing formula FALSIFIED (b) tip 34e2c4a (floor stayed
7/12; no Val-1). Exit-class / partial-exit / long-only / breadth already
closed on this name's own-trade evidence. The signal is
sig_ema3_cross(13, 50, 200): long when ema13 > ema50 > ema200, short when
ema13 < ema50 < ema200. The one-shot entry is the first bar of each call.
Candle confirm asked where that bar's close sat inside its own high-low
range. It did not ask how far that close has cleared the slow end of the
stack.

Problem:
Most trades still die at the fixed initial_sl (292/423, 69.03%, 0% WR on
the ungated Train-1 cohort); pooled Train-1 losing-month floor is 7/12;
0/10 series clear §7. Closed levers (vol gate, one sizing formula, candle
close-strength, exit, direction, breadth) did not fix regularity. A stack
alignment whose close is still hugging ema200 and one whose close has
already cleared a material fraction of ema200 are treated as the same
signal. One remaining §8 entry-structure change on THIS name, orthogonal
to absolute ATR%, to close-location inside the bar, and to the closed
stake, written before the run.

Mechanism:
On the one-shot bar the stack has just become true, so at least one of
ema13 ? ema50 or ema50 ? ema200 has just flipped. A pairwise EMA gap can
therefore be ~0 and is not a stable depth denominator (the same reason a
cross-gap denominator was rejected on the EMA_50_200 depth card). The slow
level that defines this stack is ema200, which this signal already
requires. A close that only sits on that line is a shallow alignment:
price has barely cleared the slow average and is more likely to fall back
into the fixed initial stop. A close that sits a larger fraction of ema200
beyond that line has committed more distance to the trade side and is more
likely to travel to the opposite structural extreme (signal_reverse).
Depth is computed only from the closed signal bar's close and that bar's
own ema200. It is causal, it is not an absolute ATR% threshold, it is not
(close-low)/(high-low), and it is not a Bollinger width. Dividing by
ema200 keeps the gate from being another raw volatility cutoff (the closed
abs-ATR axis) and from retesting candle close-strength.

Hypothesis:
Adding a single causal entry gate that rejects an EMA3_13_50_200 one-shot
signal when the signal bar's ema200-normalized breakout depth is below a
pre-registered threshold D will raise mean Train-1 net PnL versus the ungated
NO_TRAIL baseline AND cut the initial_sl share among remaining trades, while
retaining enough big-winner PnL that the pooled losing-month floor can
improve — earned on this name's own trades.

Change to test:
ONE entry refinement only (§8 breakout depth / distance beyond the slow EMA).
On the closed signal bar, using ema200 (the slow EMA this stack already uses):

  ema_slow = ema200
  depth_long  = (close - ema_slow) / ema_slow    # fail if ema_slow is missing or <= 0
  depth_short = (ema_slow - close) / ema_slow
  keep iff:
    direction == +1 and depth_long  >= D
    direction == -1 and depth_short >= D
    (ema_slow missing or <= 0 => reject)

Do not read bb_20_2.0_* or bb_20_2.5_*. Do not use atr14. Do not use
(close - low) / (high - low). Do not divide by |ema13 - ema50| or
|ema50 - ema200|. Do not look for an ema3 column: the catalog lambda is
sig_ema3_cross(13, 50, 200). Intersect with the existing one-shot entry
mask (same pattern as scripts/f006_ema3_13_50_200_entry_candle_confirm.py).
No exit, sizing, symbol, interval, direction, breadth, ATR-threshold, or
candle-strength changes. NO_TRAIL unchanged. Exits continue to use the
ungated persistent signal (same as the candle and abs-ATR harnesses). Do
not reuse the closed stake multiplier.

Baseline:
Ungated EMA3_13_50_200 NO_TRAIL on the frozen 5-symbol x 2-interval Train-1
basket. Control must reproduce this name's catalog / abs-ATR / xsym / candle
control figures before trusting gated cells:
  - mean train1_net_pnl = +91.1483016 (10 series, sum +911.483016)
  - Train-1 entry cohort n = 423, entry net = +771.2836172145888236
  - initial_sl share = 292/423 = 0.6903073286052009 (69.03%)
  - big-winner PnL at net>=29.9 = +1131.95615373334168 (9 trades)
  - pooled losing entry-months = 7/12
Reference source: output/f006_ema3_13_50_200_entry_candle_confirm/cell_summary.csv
control row (matches output/f006_ema3_13_50_200_abs_atr_gate/ control row,
diff 0). Do NOT import +72.6693115. Do NOT import +95.3217987. Do NOT import
+82.900262. Do NOT import +126.744211. Do NOT import +45.0267104. Do NOT
import +63.0343180. Do NOT import +87.8448967. Do NOT import n=330, n=756,
or n=512. Do NOT import any other name's depth-cell mean or its best D.

Metrics (pre-declared):
1. mean train1_net_pnl across 10 series (primary) / pooled net and net/trade
2. initial_sl share among closed Train-1-entry trades
3. n_trades (reject thin: mean n_trades/series < 10)
4. pooled losing-month floor (of 12, by entry-month). Confirm the control
   floor in this run. The candle control measured 7/12; that is an observation
   to confirm, not an imported pass line from another name.
5. big-winner PnL retained vs this name's ungated baseline (freeze big winner
   = net>=29.9 before run). Recompute the set on this run's ungated blotter.
   The candle freeze observed 9 trades / +1131.9561537333418; confirm, do not
   import another name's set (not 5 / +843.7639016181568).
6. #symbols net-positive / per-symbol losing-month floor (informational)
7. number_of_trials = 5

Expected improvement:
Mean train1_net_pnl > this name's control (+91.1483016) AND initial_sl
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
On this entry-gate card, (b) is the big-winner clause, not the month floor.
The month floor is (d), and (d) is reachable only at a D that otherwise
passes (a)-(c). A flat floor by itself is not (b) here. Do not widen D
after seeing results without a new written hypothesis. Do not declare this
falsified because EMA_50_200 depth failed at 485de51, because BB_20_2
depth failed at 27fa7f6, or because BB_20_25 depth failed at 0685ce5, and
do not declare it passed because any of those names' depth cells moved PnL.
Do not treat D=0.02 as a pre-picked answer.

Data split:
Train-1 only (2024-03-01 <= entry < 2025-03-01 UTC). No validation/holdout.
If a D looks promising, schedule a separate validation run later — do not
tune on it now. Do not open a validation window of the closed sizing formula.

Budget:
D grid fixed before run:
{0.02, 0.05, 0.10, 0.25, 0.50} — max 5 trials.
Units are fractions of ema200 beyond the slow EMA (close vs ema200), not
ATR, not close-location inside the bar, and not a Bollinger band width.
The grid shape matches the licensed §8 breakout-depth pattern used
elsewhere. It is not a copy of another name's winning D (there is none to
copy; EMA_50_200's best D=0.02 failed and is not selected here). Control
(ungated) + 5 gated cells. Report all cells. Pick at most one D for any
follow-up. No cell is pre-picked.
```

decision_if_pass: REFINE (update EMA3_13_50_200 profile metrics; consider a separate validation later; do not open holdout in this run; do not FREEZE on the pass alone; status stays CONDITIONAL)
decision_if_fail: keep CONDITIONAL; mark breakout-depth entry-structure axis closed on this
  name's own trades; next open §8 entry variant is HTF direction, with a new written
  mechanism — liquidity stays open after that; still develop-not-abandon on this name;
  do not FREEZE; do not retune D; do not reopen abs-ATR; do not reopen the closed xsym
  formula; do not reopen candle confirm; do not start funding-carry, spread-capture,
  or catalog mean-reversion

## Result

Run: `F006_DATA_CACHE=/home/limen/bot_traiding_daily/bot_traiding_daily/data_cache python3 scripts/f006_ema3_13_50_200_entry_breakout_depth.py`
(harness commit `099a496`; artifacts `output/f006_ema3_13_50_200_entry_breakout_depth/`).
The gate function is imported unchanged from
`scripts/f006_ema_50_200_entry_breakout_depth.py` (`breakout_depth_gate`:
direction-signed `(close - ema200) / ema200 >= D`, ema200 missing or <= 0
rejects) and intersected with the `EMA3_13_50_200` one-shot mask; exits use
the ungated signal; no xsym stake. Only the frozen Train-1 caches
`*_20240126T000000Z_20250301T000000Z.csv` were loaded; checksums equal
`output/f006_ema3_13_50_200_abs_atr_gate/grid_freeze.json`.
`grid_freeze.json` was written after the control check and before any gated
cell. `number_of_trials = 5`.

Control reproduced exactly (max abs train1 diff vs catalog5 = 0.0, 10/10 rows,
n_trades equal): mean +91.1483016 (sum +911.483016), Train-1 entry n=423,
entry net +771.283617, initial_sl 292/423 = 0.6903073286052009, big winners
(net>=29.9, frozen on this run's ungated blotter) 9 trades / +1131.9561537333418,
pooled losing entry-months 7/12. All match the candle-confirm control row
(diff 0).

| cell | D | mean train1 net | n entry (mean/series) | initial_sl share (drop pp) | big-winner retained (by key) | cohort net>=29.9 PnL | losing months | +symbols |
|---|---|---|---|---|---|---|---|---|
| control | — | +91.148302 | 423 (42.3) | 292/423 = 69.03% (0.0) | 9 / +1131.956 (100%) | +1131.956 | 7/12 | 3/5 |
| d_0_02 | 0.02 | +94.453053 | 322 (32.2) | 248/322 = 77.02% (-7.99) | 6 / +1012.210 (89.4%) | +1047.597 | 7/12 | 3/5 |
| d_0_05 | 0.05 | -9.999065 | 159 (15.9) | 138/159 = 86.79% (-17.76) | 0 / 0.000 (0.0%) | +88.176 | 9/12 | 1/5 |
| d_0_1 | 0.10 | +6.375522 | 48 (4.8, thin) | 41/48 = 85.42% (-16.39) | 0 / 0.000 (0.0%) | +88.176 | 7/12 | 4/5 |
| d_0_25 | 0.25 | -0.663100 | 2 (0.2, thin) | 2/2 = 100% (-30.97) | 0 / 0.000 (0.0%) | 0.000 | 2/12 | 0/5 |
| d_0_5 | 0.50 | 0.000000 | 0 (0.0, thin) | n/a | 0 / 0.000 (0.0%) | 0.000 | 0/12 | 0/5 |

Negative drop = initial_sl share rose. Best-PnL D = 0.02 (+94.453053,
delta +3.3047511/series; entry net/trade +2.5027 vs control +1.8234).
"Big-winner retained" is the pre-declared metric (baseline net>=29.9 trades
surviving by symbol/interval/entry_time/direction with identical economics);
"cohort net>=29.9 PnL" is informational only. The 2/12 and 0/12 floors at
D=0.25/0.50 are empty-cohort artifacts (2 and 0 trades), not improvements.
D=0.02 per-symbol train1 net: XRP +544.09, DOGE +428.74, SOL +32.34,
BTC -13.83, ETH -46.82; per-symbol losing entry-months SOL 6, ETH 8, BTC 8,
XRP 7, DOGE 5 (control: SOL 6, ETH 7, BTC 6, XRP 9, DOGE 6).

Independent check: recomputing ema200 via `strategy.add_indicators` on the
closed bars, every kept trade clears D on the closed bar before its entry
bar (D=0.02 342/342, D=0.05 164/164, D=0.10 48/48 incl. warmup trades).
Re-running at the harness commit reproduced `cell_summary.csv` byte-for-byte.

Falsifiers:
- (a) does not fire — D=0.02 beats control mean (+94.453053 vs +91.148302).
  Every other D is below control.
- (b) does not fire — non-thin D=0.02 retains 89.4% of baseline big-winner
  PnL (D=0.05 retains 0%).
- (c) FIRES — at best-PnL D=0.02 initial_sl share rose 7.99pp (69.03% ->
  77.02%) instead of falling >=10pp.
- (d) not reachable — no D passes (a)-(c); the pooled floor at D=0.02 is
  7/12 anyway (no change).
- (e) does not fire — the only D above control (0.02) is non-thin (32.2/series).

No D lowers the pooled floor while keeping >=50% big-winner PnL and >=10
trades/series (D=0.02 keeps 89.4% and 32.2/series but stays 7/12). The
D=0.02 mean lift is small (+3.30/series) and comes with a higher initial_sl
share, so it is a cohort-trim, not the pre-declared mechanism. Outcome
against the pre-declared falsifiers: FALSIFIED (c). Decision left to
coordinator.

## Decision

(empty — coordinator only)
