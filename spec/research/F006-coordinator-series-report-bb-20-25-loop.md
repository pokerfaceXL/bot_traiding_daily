# Coordinator Series Report — BB_20_25_EMA200 protocol loop (§15)

> **Date:** 2026-10-03 ~10:56 Europe/Warsaw
> **Closing experiment:** H-BB-20-25-ENTRY-HTF-DIRECTION-01
> **Tip / merge:** `3495b16` (FF to origin/main from `9eb87dd`). Review PASS job
> `2026-10-03-f006-bb2025-entry-htf-direction--364758a0`.
> **Artifacts:** `output/f006_bb_20_25_entry_htf_direction/cell_summary.csv`
> **Card:** `spec/research/F006-hypothesis-bb-20-25-entry-htf-direction.md`
> **Profile:** `spec/research/strategy_profiles/BB_20_25_EMA200.md` → **FREEZE**

## Summary

The `BB_20_25_EMA200` per-name loop is closed. HTF direction is **FALSIFIED
(a)+(c)+(d)** on this name's own trades. Ungated control matched the frozen
baseline (mean +$82.900262/series, cohort n=512 net +$709.849209, initial-SL
58.01%, big-winner PnL $968.020732, floor 7/12). The single gated cell
(prior fully closed 4-bar HTF candle agrees with the signal) mean
+$70.515667/series is −$12.38/series versus control. Initial-SL share rose
from 58.01% to 60.45% (+2.44 pp; required drop 10 pp). Big-winner PnL retained
96.4%. Pooled losing entry-months stayed 7/12. Mean trades/series 44.5, so
(e) did not fire. (b) did not fire. `number_of_trials = 1`.

Every axis the profile licensed on this name's own trades is now closed, with
a tip. Status is **FREEZE**, not REJECT: the ungated book stays
aggregate-Train-1-positive. This is not a class closure. The other CONDITIONAL
catalog5 names are not tested by these results.

## Axes closed on this name (citations)

| axis | hypothesis | result | tip |
| --- | --- | --- | --- |
| Exit, full-position grid | `H-CATALOG5-EXIT-CLASS-01` | FALSIFIED (a)(b)(c); NO_TRAIL best | `923de9c` |
| Exit, partial scale-out | `H-CATALOG5-PARTIAL-EXIT-01` | FALSIFIED (a)(b) | `3d4edd4` |
| Direction (long-only) | `H-CATALOG5-CLASS-CLOSURE-01` own-trade cell | floor not improved | `f420078` |
| Regime (breadth B40/B60/B80) | `H-CATALOG5-CLASS-CLOSURE-01` own-trade cell | floor not improved | `f420078` |
| Entry-vol / abs-ATR | `H-BB-20-25-ABS-ATR-ENTRY-GATE-01` | FALSIFIED (a); every T below control mean | `3788f11` |
| Position sizing (xsym-agree formula) | Train-1 `H-BB-20-25-XSYM-AGREE-SIZING-01` then Val-1 | Val-1 FALSIFIED (c); mult gap −0.026 | `89e936a` (Train-1 `1c9ff7e`) |
| Entry, candle close-strength | `H-BB-20-25-ENTRY-CANDLE-CONFIRM-01` | FALSIFIED (c); best T=0.70, SL drop 1.96 pp | `e70161d` |
| Entry, breakout depth | `H-BB-20-25-ENTRY-BREAKOUT-DEPTH-01` | FALSIFIED (a)+(c); best D=0.02 −$10.91/series | `0685ce5` |
| Entry, HTF direction | `H-BB-20-25-ENTRY-HTF-DIRECTION-01` | FALSIFIED (a)+(c)+(d); −$12.38/series, SL +2.44 pp, floor 7/12 | `3495b16` |

§8 portfolio combination was not left open: H-CATALOG5-SHARED-LOSING-MONTHS-01
(`dc9818e`) showed catalog5 losses are one basket (phi 0.79, Pearson 0.96), so
the §8 precondition fails. That diagnostic does not freeze the other names.
Liquidity and price-versus-range were §8 examples, not separately licensed
once this profile named HTF direction as the last open axis. Opening one of
them now would be a new search after the named loop, which §13 does not allow.

## Q1–10

1. **Best strategy now?** None promotable. `BB_20_25_EMA200` is **FREEZE**.
   Among remaining CONDITIONAL catalog5 names, `BB_20_2_EMA200` is next (journal
   order after this name: `BB_20_2_EMA200`, then `EMA_50_200`, then
   `EMA3_13_50_200`). `EMA3_21_50_200` and `DONCHIAN_55_NO_TRAIL` stay FREEZE.
2. **Why that name next?** It is the next CONDITIONAL catalog5 name whose
   entry-vol and sizing axes have never been run on its own trades. It is not
   "best" because this loop failed. Its own screen (8/10 Train-1 series
   positive, mean about +$95.32/series on the catalog5 monthly table, worst
   monthly floor of the five) is only why the journal ranked the unfinished
   names, not a transferred result.
3. **Edge from many trades or few big wins?** Few big wins, on this name and
   on the class. Here the frozen big-winner set is 10 trades, $968.02. The HTF
   gate kept 96.4% of that PnL and still lost $12.38/series. Four of this
   name's Train-1 trades sum to the pooled net in the autopsy. Same shape as
   the FREEZE names, now earned axis by axis on this name.
4. **Earns when?** When a close beyond the band runs to `signal_reverse`.
   Those runs were not identified by low absolute ATR%, by close location
   inside the signal bar, by how far the close sat beyond the band, or by
   agreement with the prior 4-bar HTF candle.
5. **Loses when?** Most trades die at the fixed initial stop (58.01% ungated;
   60.45% after the HTF gate) at 0% win rate by construction. Pooled losing
   entry-months stay 7/12. Losing months are the shared catalog5 basket, not
   a private BB_20_25 calendar.
6. **Rejected hypotheses?** The nine rows in the table above, each on this
   name's own trades or on a catalog5 hypothesis that included this name's
   series. Not rejected by those rows: entry-vol, sizing, candle location,
   breakout depth, and HTF direction on `BB_20_2_EMA200`, `EMA_50_200`, and
   `EMA3_13_50_200`. Those names still owe their own tests.
7. **Unresolved problem?** Monthly regularity. No licensed axis on this name
   separated stop-outs from runners without giving back the aggregate edge.
   The floor stayed at or above 7/12 whenever the book was not starved. That
   problem is unresolved for the strategy class. It is resolved as a research
   loop for this name: nothing licensed remains to tune.
8. **Next experiment and why?** `H-BB-20-2-ABS-ATR-ENTRY-GATE-01` on
   `BB_20_2_EMA200` only. That profile's first open own-trades axis is
   entry-vol / abs-ATR (still DNR-by-transfer). §7 says diagnose the losing
   trades before abandoning a positive book. This name's autopsy already shows
   higher entry ATR% on `initial_sl` than on `signal_reverse` (about 1.76 vs
   1.08). That observation is not a result. Exit stays closed on this name
   and is not reopened. One threshold grid, Train-1 only.
9. **Why not a random search?** §13 is not met for a new family. The BB_20_25
   loop is exhausted, so the protocol moves to the next CONDITIONAL catalog5
   name on its first open axis, one hypothesis, written before the run. A
   falsified HTF gate is not a test of `BB_20_2_EMA200` and is not a class
   FREEZE.
10. **What would confirm or falsify the next hypothesis?** Pre-registered on
    `H-BB-20-2-ABS-ATR-ENTRY-GATE-01` before any run. The control must
    reproduce this name's own catalog5 Train-1 rows (mean +$95.3217987/series),
    not the BB_20_25 figure +$82.90. A pass needs mean Train-1 net above that
    control, initial-SL share down at least 10 pp at the best-PnL T, at least
    50% of this name's big-winner PnL retained, and a pooled losing-month floor
    strictly below the control floor, without thinning below 10 trades/series.
    Any one of falsifiers (a)–(e) fails it. Holdout is not opened.
