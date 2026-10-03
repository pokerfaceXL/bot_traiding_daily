# Coordinator Series Report — H-BB-20-25-ENTRY-CANDLE-CONFIRM-01 (§15)

> **Date:** 2026-10-03 ~09:49 Europe/Warsaw
> **Experiment:** H-BB-20-25-ENTRY-CANDLE-CONFIRM-01
> **Tip / merge:** `e70161d` (FF to origin/main). Review PASS job
> `2026-10-03-f006-bb2025-entry-structure-revi-3883672f`.
> **Artifacts:** `output/f006_bb_20_25_entry_candle_confirm/cell_summary.csv`
> **Card:** `spec/research/F006-hypothesis-bb-20-25-entry-candle-confirm.md`

## Summary

Candle close-strength on `BB_20_25_EMA200` is **FALSIFIED (c)**. The ungated control
matched the frozen baseline (mean +$82.900262/series, cohort n=512 net +$709.849209,
initial-SL 58.01%, big-winner PnL $968.020732, floor 7/12). Best-PnL T=0.70 gained
+$6.38/series and kept 100% of pre-frozen big-winner PnL, but cut initial-SL share by
only 1.96pp against the required 10pp. No T passed all declared checks. Status stays
**CONDITIONAL**. Do not FREEZE. This closes one entry variant, not entry refinement
as a class. Breakout depth and HTF direction remain untested on this name's own trades.

## Q1–10

1. **Best strategy now?** None promotable. `BB_20_25_EMA200` stays the highest-priority CONDITIONAL name. This run did not clear §7.
2. **Why best?** Unchanged screen: best monthly floor in the catalog5 batch (one series 3/12) and 9/10 Train-1 series positive. Not validated.
3. **Edge from many trades or few big wins?** Few big wins. The pre-frozen big-winner set (net>=29.9, 10 trades, $968.02) is the whole retained tail at T=0.70. Cohort net/trade rose only to +$1.70.
4. **Earns when?** Still when a pierce runs to `signal_reverse`. A stronger close inside the signal bar did not identify those runs. T=0.70 kept every frozen big winner.
5. **Loses when?** Most remaining trades still die at the fixed initial stop (56.04% at the best T, from 58.01%). The pooled floor stays 7/12. T=0.90 reached 5/12 only by giving up mean PnL and 80.8% of big-winner PnL.
6. **Rejected hypotheses?** On this name's own trades: entry-vol FALSIFIED (a) `3788f11`; xsym sizing formula FALSIFIED (c) on Val-1 `89e936a`; candle close-strength FALSIFIED (c) `e70161d`. Exit, direction, and breadth stay closed on their own cells. Not closed: breakout depth, HTF direction.
7. **Unresolved problem?** Monthly regularity. Close location inside the signal bar does not separate stop-outs from runners. Whether penetration past the band does, on this name's own trades, is still open.
8. **Next experiment and why?** One §8 breakout-depth gate on this same name (close distance beyond the BB band, normalized by band width). Written after this decision, before any run. Not HTF in the same test, not a retune of T, not another catalog name, not FREEZE, not holdout.
9. **Why not a random search?** §13 is not met. One more own-trades variant just closed. The next test is the next named entry change on the same name. Candle failure is not evidence about the other catalog5 names.
10. **What would confirm or falsify the next hyp?** It must be pre-registered before the run. A pass needs mean Train-1 net above the ungated baseline, initial-SL share down at least 10pp at the best-PnL threshold, at least 50% of big-winner PnL retained, and a pooled losing-month floor strictly below 7/12, without thinning below 10 trades/series. Any one pre-registered falsifier fails it.
