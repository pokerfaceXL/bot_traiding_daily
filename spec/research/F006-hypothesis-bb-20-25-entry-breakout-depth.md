# F006 — H-BB-20-25-ENTRY-BREAKOUT-DEPTH-01 (pre-registered)

> Pre-registered **before** implementing or running the gate. After candle close-strength
> FALSIFIED (c) (`e70161d`), the profile keeps `BB_20_25_EMA200` CONDITIONAL. Candle
> confirmation closed one §8 entry variant on this name's own trades. It did not close
> breakout depth or HTF direction, and it is not a class closure. Entry-vol/abs-ATR is
> closed (FALSIFIED a, tip `3788f11`). The xsym sizing formula is closed (Val-1 FALSIFIED c,
> `89e936a`). This card is the next open axis: penetration of the close beyond the band.
> It is not a retune of T, not a Val-2 of the closed stake, and not the old width-expansion
> gate (that gate tested band width versus its own mean on `BB_20_25_breakout`, a different
> name and a different feature).

experiment_id: H-BB-20-25-ENTRY-BREAKOUT-DEPTH-01
date: 2026-10-03
base_strategy: BB_20_25_EMA200 (NO_TRAIL, max_sl_pct=0.03, one-shot entry, signal_reverse exit)

```text
Observation:
BB_20_25_EMA200 stays CONDITIONAL after H-BB-20-25-ENTRY-CANDLE-CONFIRM-01 FALSIFIED (c)
(tip e70161d). Best T=0.70 mean +$89.279908/series versus control +$82.900262
(+$6.38/series) but initial-SL share fell only 1.96pp (58.01% to 56.04%) against a
required 10pp. Big-winner PnL was fully retained and the pooled floor stayed 7/12.
Entry-vol and the xsym sizing formula are already closed on this name's own trades.
Exit / direction / breadth are already closed. The signal is close-beyond-band plus
EMA200 agree (`sig_bb_breakout_ema`, columns bb_20_2.5_upper / bb_20_2.5_lower). Any
close strictly outside the band is kept. The candle test asked where the close sat
inside the bar. It did not ask how far the close sits beyond the band.

Problem:
Most trades still die at the fixed initial_sl. A barely-outside close and a close
that has cleared a large fraction of the band width are treated as the same signal.
Candle location did not separate them. One remaining §8 entry change on THIS name,
orthogonal to absolute ATR% and to close-location inside the bar, written before the run.

Mechanism:
A close that only nicks the band is a shallow pierce: price has barely left the
envelope and is more likely to fall back into the fixed initial stop. A close that
sits a larger fraction of the current band width beyond the band has committed more
distance to the breakout side and is more likely to travel to the opposite structural
extreme (`signal_reverse`). Depth is computed only from the closed signal bar's close
and that bar's own Bollinger bands. It is causal, it is not an absolute ATR threshold,
and it is not `(close-low)/(high-low)`. Dividing by band width keeps the gate from
being another raw-volatility cutoff (the closed abs-ATR axis).

Hypothesis:
Adding a single causal entry gate that rejects a BB_20_25_EMA200 one-shot signal when
the signal bar's band-normalized breakout depth is below a pre-registered threshold D
will raise mean Train-1 net PnL versus the ungated NO_TRAIL baseline AND cut the
initial_sl share among remaining trades, while retaining enough big-winner PnL that
the pooled losing-month floor can improve — earned on this name's own trades.

Change to test:
ONE entry refinement only (§8 breakout depth / distance beyond the channel). On the
closed signal bar, using the same bands the signal already uses (period 20, k=2.5):

  upper = bb_20_2.5_upper
  lower = bb_20_2.5_lower
  width = upper - lower
  depth_long  = (close - upper) / width    # fail if width <= 0
  depth_short = (lower - close) / width
  keep iff:
    direction == +1 and depth_long  >= D
    direction == -1 and depth_short >= D
    (width <= 0 ⇒ reject)

Intersect with the existing one-shot entry mask (same pattern as
`scripts/f006_bb_20_25_entry_candle_confirm.py`). No exit, sizing, symbol, interval,
direction, breadth, ATR-threshold, or candle-strength changes. NO_TRAIL unchanged.
Exits continue to use the ungated persistent signal (same as the candle and abs-ATR
harnesses). Do not use ATR in the depth formula.

Baseline:
Ungated BB_20_25_EMA200 NO_TRAIL on the frozen 5-symbol × 2-interval Train-1 basket.
Control must reproduce the candle-confirm / abs-ATR / xsym control figures for this
name before gating: mean train1_net_pnl +82.900262 across 10 series; pooled Train-1
entry cohort n=512 net +709.849209; initial_sl share 0.580078125; big-winner PnL
968.020732; pooled losing entry-months 7/12. Report the matched figures exactly.

Metrics (pre-declared):
1. mean train1_net_pnl across 10 series (primary) / pooled net and net/trade
2. initial_sl share among closed Train-1-entry trades
3. n_trades (reject thin: mean n_trades/series < 10)
4. pooled losing-month floor (of 12, by entry-month)
5. big-winner PnL retained vs ungated baseline (freeze big winner = net≥29.9 before run)
6. #symbols net-positive / per-symbol losing-month floor (informational)
7. number_of_trials (threshold grid size)

Expected improvement:
Mean train1_net_pnl > baseline AND initial_sl share down ≥10pp AND ≥50% of big-winner
PnL retained AND pooled losing-month floor strictly below this name's ungated floor
(7/12 on the pooled control — confirm in the control cell before comparing).

Falsification condition (any one ⇒ FALSIFIED):
(a) mean train1_net_pnl ≤ baseline at every D; OR
(b) every non-thin D removes >50% of baseline big-winner PnL; OR
(c) initial_sl share fails to fall ≥10pp at the best-PnL D; OR
(d) pooled losing-month floor does not improve (stays ≥ baseline floor) at every D that
    otherwise passes (a)–(c); OR
(e) improvement is only from collapsing to <10 trades/series mean.
Do not widen D after seeing results without a new written hypothesis.

Data split:
Train-1 only (2024-03-01 ≤ entry < 2025-03-01 UTC). No validation/holdout. If a D looks
promising, schedule a separate validation run later — do not tune on it now.

Budget:
D grid fixed before run:
{0.02, 0.05, 0.10, 0.25, 0.50} — max 5 trials.
Units are fractions of the current band width beyond the band, not ATR and not
close-location. Control (ungated) + 5 gated cells. Report all cells. Pick at most
one D for any follow-up.
```

decision_if_pass: REFINE (update BB_20_25_EMA200 profile metrics; consider validation)
decision_if_fail: keep CONDITIONAL; mark breakout-depth closed on this name's own trades;
  next open §8 entry variant is HTF direction, with a new written mechanism — still
  develop-not-abandon on this name; do not FREEZE; do not treat this result as evidence
  about other catalog5 names

## Result

Train-1 run completed on the frozen 5-symbol × 2-interval basket. The ungated control
reproduced all 10 reference rows exactly: mean Train-1 net PnL **+$82.900262/series**
(+$829.002620 summed by series), while the pre-registered entry cohort reproduced
**n=512, +$709.849209**, initial-SL share **58.01%**, big-winner PnL **$968.020732**, and
**7/12** pooled losing entry-months. `number_of_trials = 5`.

| D | mean net/series | cohort net/trade | trades/series | initial-SL share (drop) | big-winner PnL retained | pooled losing months | net-positive symbols |
|---:|---:|---:|---:|---:|---:|---:|---:|
| control | +$82.90 | +$1.386 | 51.2 | 58.01% (0.00pp) | 100.0% | 7/12 | 4/5 |
| 0.02 | **+$71.99** | +$1.264 | 47.7 | 58.07% (-0.06pp) | 80.7% | 8/12 | 5/5 |
| 0.05 | +$67.80 | +$1.441 | 39.6 | 59.34% (-1.34pp) | 70.0% | 8/12 | 4/5 |
| 0.10 | +$57.86 | +$1.666 | 28.2 | 60.28% (-2.28pp) | 31.1% | 8/12 | 4/5 |
| 0.25 | +$2.05 | +$0.706 | 2.9 | 48.28% (9.73pp) | 0.0% | 5/12 | 4/5 |
| 0.50 | $0.00 | n/a | 0.0 | n/a | 0.0% | 0/12 | 0/5 |

**FALSIFIED by (a) and (c).** Every D reduced mean PnL below control; the best gated
cell, D=0.02, lost $10.91/series and increased rather than reduced initial-SL share.
Falsifier (b) did not trigger because the non-thin D=0.02 and D=0.05 cells retained
more than 50% of pre-frozen big-winner PnL. Falsifier (c) also triggered because the
best-PnL D missed the required 10pp initial-SL reduction. Falsifier (d) was not
independently applicable because no D passed (a)–(c). Falsifier (e) did not trigger:
there was no PnL improvement, thin or otherwise. D=0.25 lowered the pooled floor to
5/12 but collapsed to 2.9 trades/series, retained no big-winner PnL, and cut mean PnL
to +$2.05; D=0.50 made no trades. No threshold passed all declared checks. Artifacts:
`output/f006_bb_20_25_entry_breakout_depth/`.

## Decision

(empty — coordinator only)
