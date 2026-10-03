# Coordinator Series Report — H-BB-20-25-ENTRY-BREAKOUT-DEPTH-01 (§15)

> **Date:** 2026-10-03 ~10:20 Europe/Warsaw
> **Experiment:** H-BB-20-25-ENTRY-BREAKOUT-DEPTH-01
> **Tip / merge:** `0685ce5` (FF to origin/main). Review PASS job
> `2026-10-03-f006-bb2025-entry-breakout-depth-2dd8bcfc`.
> **Artifacts:** `output/f006_bb_20_25_entry_breakout_depth/cell_summary.csv`
> **Card:** `spec/research/F006-hypothesis-bb-20-25-entry-breakout-depth.md`

## Summary

Breakout depth on `BB_20_25_EMA200` is **FALSIFIED (a)+(c)**. The ungated control
matched the frozen baseline (mean +$82.900262/series, cohort n=512 net +$709.849209,
initial-SL 58.01%, big-winner PnL $968.020732, floor 7/12). Best-PnL D=0.02 mean
+$71.985313/series is −$10.91/series versus control, and initial-SL share rose
0.06pp instead of falling 10pp. D=0.50 took zero trades. No D passed all declared
checks. Status stays **CONDITIONAL**. Do not FREEZE. This closes breakout depth,
not entry refinement as a class, and not HTF direction.

## Q1–10

1. **Best strategy now?** None promotable. `BB_20_25_EMA200` stays the highest-priority CONDITIONAL name. This run did not clear §7.
2. **Why best?** Unchanged screen: best monthly floor in the catalog5 batch (one series 3/12) and 9/10 Train-1 series positive. Not validated.
3. **Edge from many trades or few big wins?** Few big wins. The pre-frozen big-winner set (net≥29.9, 10 trades, $968.02) is still the tail. D=0.02 kept 80.7% of that PnL and still lost money versus control.
4. **Earns when?** Still when a pierce runs to `signal_reverse`. A deeper close beyond the band did not identify those runs. Every depth cut mean PnL.
5. **Loses when?** Most remaining trades still die at the fixed initial stop (58.07% at the best D, from 58.01%). The pooled floor went from 7/12 to 8/12 at D=0.02–0.10. D=0.25 reached 5/12 only by collapsing to 2.9 trades/series and keeping none of the big-winner PnL. D=0.50 made no trades.
6. **Rejected hypotheses?** On this name's own trades: entry-vol FALSIFIED (a) `3788f11`; xsym sizing formula FALSIFIED (c) on Val-1 `89e936a`; candle close-strength FALSIFIED (c) `e70161d`; breakout depth FALSIFIED (a)+(c) `0685ce5`. Exit, long-only direction, and breadth stay closed on their own cells. Not closed: HTF direction.
7. **Unresolved problem?** Monthly regularity. Distance of the close beyond the band does not separate stop-outs from runners on this name. Whether the prior higher-timeframe bar's direction does, on this name's own trades, is still open.
8. **Next experiment and why?** One §8 HTF-direction gate on this same name (prior fully closed 4-bar HTF candle must agree with the signal). Written after this decision, before any run. Not a retune of D, not long-only, not another catalog name, not FREEZE, not holdout.
9. **Why not a random search?** §13 is not met. One more own-trades variant just closed. The next test is the remaining named entry axis on the same name. Depth failure is not evidence about the other catalog5 names and is not a class FREEZE.
10. **What would confirm or falsify the next hyp?** Pre-registered on `H-BB-20-25-ENTRY-HTF-DIRECTION-01` before the run. A pass needs mean Train-1 net above +82.900262, initial-SL share down at least 10pp, at least 50% of big-winner PnL retained, and a pooled losing-month floor strictly below 7/12, without thinning below 10 trades/series. Any one of falsifiers (a)–(e) fails it.
