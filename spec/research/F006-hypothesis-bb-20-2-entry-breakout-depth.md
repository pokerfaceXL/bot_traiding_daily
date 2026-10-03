# F006 — H-BB-20-2-ENTRY-BREAKOUT-DEPTH-01 (pre-registered)

> Pre-registered **before** implementing or running the gate. After
> `H-BB-20-2-ENTRY-CANDLE-CONFIRM-01` **FALSIFIED (c)** (`88b0ee3`), journal +
> profile close candle close-strength on `BB_20_2_EMA200` and name the next
> open axis as a not-yet-run §8 **breakout-depth** hypothesis on this name's
> own trades. Entry-vol/abs-ATR is closed (FALSIFIED (a)+(c), tip `f7ac677`);
> the xsym sizing *formula* is closed (Val-4 `139ed3d` FALSIFIED (c)); candle
> close-strength is closed. Exit / direction / breadth already closed. This
> card is **not** a retune of T, **not** a Val-5 of the closed stake, and
> **not** HTF direction or a liquidity filter. `BB_20_25_EMA200` is FREEZE on
> its own loop; its breakout-depth result at `0685ce5` (and that name's
> D=0.02 numbers, control +82.900262, n=512) is **not** this test. Do not
> copy that name's control mean, cohort, or pass/fail onto this card as an
> expected result. Do not use `bb_20_2.5_*` — this name's signal is k=2.0.

experiment_id: H-BB-20-2-ENTRY-BREAKOUT-DEPTH-01
date: 2026-10-03
base_strategy: BB_20_2_EMA200 (NO_TRAIL, max_sl_pct=0.03, one-shot entry, signal_reverse exit)

```text
Observation:
BB_20_2_EMA200 stays CONDITIONAL after H-BB-20-2-ENTRY-CANDLE-CONFIRM-01
FALSIFIED (c) (tip 88b0ee3). Best T=0.60 mean +95.771777 versus control
+95.3217987 (+0.449978/series) but initial_sl share fell only 0.548942pp
(0.473545 to 0.468056) against a required 10pp. Frozen big-winner PnL was
fully retained (1251.654084) and the pooled floor stayed 7/12. Entry-vol and
the xsym sizing formula and candle close-strength are already closed on this
name's own trades. Exit / direction / breadth are already closed. The signal
is close-beyond-band + EMA200 agree (`sig_bb_breakout_ema`, period 20, k=2.0,
columns bb_20_2.0_upper / bb_20_2.0_lower). Any close strictly outside that
band is kept. The candle test asked where the close sat inside the bar. It
did not ask how far the close sits beyond this name's own band.

Problem:
Most trades still die at the fixed initial_sl (358/756, 47.35%, 0% WR on the
ungated Train-1 cohort). A barely-outside close and a close that has cleared
a large fraction of the k=2.0 band width are treated as the same signal.
Candle location did not separate them (stop-out share flat or rising as T
tightened). One remaining §8 entry change on THIS name, orthogonal to
absolute ATR%, to close-location inside the bar, and to the closed stake,
written before the run.

Mechanism:
A close that only nicks the k=2.0 band is a shallow pierce: price has barely
left the envelope and is more likely to fall back into the fixed initial
stop. A close that sits a larger fraction of the current band width beyond
the band has committed more distance to the breakout side and is more likely
to travel to the opposite structural extreme (signal_reverse). Depth is
computed only from the closed signal bar's close and that bar's own
Bollinger bands (the same bb_20_2.0 columns the signal already uses). It is
causal, it is not an absolute ATR threshold, it is not
(close-low)/(high-low), and it is not the stored ratio column
bb_20_2.0_width (that column is (2*k*std)/mid, a different feature, and is
not this gate). Dividing by (upper-lower) keeps the gate from being another
raw-volatility cutoff (the closed abs-ATR axis).

Hypothesis:
Adding a single causal entry gate that rejects a BB_20_2_EMA200 one-shot
signal when the signal bar's band-normalized breakout depth is below a
pre-registered threshold D will raise mean Train-1 net PnL versus the ungated
NO_TRAIL baseline AND cut the initial_sl share among remaining trades, while
retaining enough big-winner PnL that the pooled losing-month floor can
improve — earned on this name's own trades.

Change to test:
ONE entry refinement only (§8 breakout depth / distance beyond the channel).
On the closed signal bar, using the same bands the signal already uses
(period 20, k=2.0):

  upper = bb_20_2.0_upper
  lower = bb_20_2.0_lower
  width = upper - lower
  depth_long  = (close - upper) / width    # fail if width <= 0
  depth_short = (lower - close) / width
  keep iff:
    direction == +1 and depth_long  >= D
    direction == -1 and depth_short >= D
    (width <= 0 ⇒ reject)

Do not read bb_20_2.5_upper / bb_20_2.5_lower. Do not use bb_20_2.0_width.
Intersect with the existing one-shot entry mask (same pattern as
scripts/f006_bb_20_2_entry_candle_confirm.py). No exit, sizing, symbol,
interval, direction, breadth, ATR-threshold, or candle-strength changes.
NO_TRAIL unchanged. Exits continue to use the ungated persistent signal
(same as the candle and abs-ATR harnesses). Do not use ATR in the depth
formula.

Baseline:
Ungated BB_20_2_EMA200 NO_TRAIL on the frozen 5-symbol × 2-interval Train-1
basket. Control must reproduce this name's catalog / abs-ATR / xsym / candle
control figures before trusting gated cells:
  - mean train1_net_pnl = +95.3217987 (10 series)
  - Train-1 entry cohort n = 756, entry net ≈ +834.347778
  - initial_sl share ≈ 0.473545 (47.35%)
  - big-winner PnL at net≥29.9 ≈ 1251.654084 (12 trades)
  - pooled losing entry-months = 7/12
Reference source: output/f006_bb_20_2_entry_candle_confirm/cell_summary.csv
control row (and the matching abs-ATR control row). Do NOT import
+82.900262, n=512, initial_sl 0.580078, or any BB_20_25 depth cell.

Metrics (pre-declared):
1. mean train1_net_pnl across 10 series (primary) / pooled net and net/trade
2. initial_sl share among closed Train-1-entry trades
3. n_trades (reject thin: mean n_trades/series < 10)
4. pooled losing-month floor (of 12, by entry-month)
5. big-winner PnL retained vs ungated baseline (freeze big winner = net≥29.9 before run)
6. #symbols net-positive / per-symbol losing-month floor (informational)
7. number_of_trials (threshold grid size)

Expected improvement:
Mean train1_net_pnl > baseline AND initial_sl share down ≥10pp AND ≥50% of
big-winner PnL retained AND pooled losing-month floor strictly below this
name's ungated floor (7/12 on the pooled control — confirm in the control
cell before comparing).

Falsification condition (any one ⇒ FALSIFIED):
(a) mean train1_net_pnl ≤ baseline at every D; OR
(b) every non-thin D removes >50% of baseline big-winner PnL; OR
(c) initial_sl share fails to fall ≥10pp at the best-PnL D; OR
(d) pooled losing-month floor does not improve (stays ≥ baseline floor) at
    every D that otherwise passes (a)–(c); OR
(e) improvement is only from collapsing to <10 trades/series mean.
Do not widen D after seeing results without a new written hypothesis.
Do not declare this falsified because BB_20_25 breakout depth failed, and do
not declare it passed because some other name's depth cell moved PnL.

Data split:
Train-1 only (2024-03-01 ≤ entry < 2025-03-01 UTC). No validation/holdout.
If a D looks promising, schedule a separate validation run later — do not
tune on it now.

Budget:
D grid fixed before run:
{0.02, 0.05, 0.10, 0.25, 0.50} — max 5 trials.
Units are fractions of the current k=2.0 band width (upper-lower) beyond the
band, not ATR, not close-location, and not the bb_20_2.0_width ratio. The
grid shape matches the licensed §8 breakout-depth pattern used elsewhere; it
is not a copy of another name's winning D (that other name had none).
Control (ungated) + 5 gated cells. Report all cells. Pick at most one D for
any follow-up.
```

decision_if_pass: REFINE (update BB_20_2_EMA200 profile metrics; consider validation)
decision_if_fail: keep CONDITIONAL; mark breakout-depth closed on this name's own trades;
  next open §8 entry variant is HTF direction, with a new written mechanism — liquidity
  stays open after that; still develop-not-abandon on this name; do not FREEZE; do not
  jump to EMA_50_200 / EMA3_13_50_200; do not treat this result as evidence about other
  catalog5 names

## Result

(empty — worker fills after the run)

## Decision

(empty — coordinator only)
