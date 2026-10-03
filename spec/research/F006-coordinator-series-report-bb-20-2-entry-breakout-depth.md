# Coordinator Series Report — H-BB-20-2-ENTRY-BREAKOUT-DEPTH-01 (§15)

> **Date:** 2026-10-03 ~15:08 Europe/Warsaw
> **Experiment:** H-BB-20-2-ENTRY-BREAKOUT-DEPTH-01
> **Tip / merge:** `27fa7f6` (FF to origin/main). Review PASS job
> `2026-10-03-f006-bb202-entry-breakout-depth--14238167`.
> **Artifacts:** `output/f006_bb_20_2_entry_breakout_depth/cell_summary.csv`,
> `results.csv`, Train-1 blotters under `control/` and `d_0_02/`.
> **Card:** `spec/research/F006-hypothesis-bb-20-2-entry-breakout-depth.md`

## Summary

Breakout depth on `BB_20_2_EMA200` is **FALSIFIED (a)+(c)**. The ungated
control matched this name's frozen baseline (mean +95.3217987/series, cohort
n=756 net +834.347778, initial_sl 358/756 = 0.473545, big-winner PnL
1251.654084, floor 7/12). Best D=0.02 mean +87.8448967 is −7.476902/series.
Initial_sl share rose at every D (best D +1.010625pp, 0.473545 → 0.483651);
the required move was a drop of ≥10pp. No D passed all declared checks.
D=0.02 and D=0.05 lowered the pooled floor 7/12 → 6/12 while keeping ≥50%
of frozen big-winner PnL, but both lose mean PnL and raise the stop-out
share, so that floor move is not otherwise qualifying. Status stays
**CONDITIONAL**. Do not FREEZE. This closes one entry variant, not entry
refinement as a class. HTF direction and liquidity remain untested on this
name's own trades. `BB_20_25_EMA200` breakout-depth FALSIFIED (a)+(c) at
`0685ce5` (control +82.900262, n=512) is not this result.

## Q1–10

1. **Best strategy now?** None promotable. FREEZE names unchanged. Active CONDITIONAL name is `BB_20_2_EMA200`, then `EMA_50_200`, then `EMA3_13_50_200`. This run did not clear §7 (0/10 series still the catalog floor).
2. **Why that name?** Own-trades loop still open after entry-vol, the xsym formula, candle close-strength, and now breakout depth. Screen is this name's +95.3217987 control, not a BB_20_25 transfer.
3. **Edge from many trades or few big wins?** Few big wins. The pre-frozen set (net≥29.9, 12 trades, 1251.654084) is only partly retained at D=0.02 (9/12, 1029.065151, 82.2%), and that cell still loses −7.476902/series.
4. **Earns when?** Still when a pierce runs to `signal_reverse`. How far the close sits beyond this name's k=2.0 band did not identify those runs.
5. **Loses when?** Most remaining trades still die at the fixed initial stop, and the share rises as D tightens (47.35% ungated → 48.37% at D=0.02, 50.29% at D=0.05). The pooled floor can print 6/12 at D=0.02 and D=0.05, but only by trimming small losing months while mean PnL falls and stop-outs become more common.
6. **Rejected hypotheses?** On this name's own trades: entry-vol FALSIFIED (a)+(c) `f7ac677`; xsym sizing formula FALSIFIED (c) on Val-4 `139ed3d`; candle close-strength FALSIFIED (c) `88b0ee3`; breakout depth FALSIFIED (a)+(c) `27fa7f6`. Exit, direction (long-only), and breadth stay closed. Not closed: HTF direction, liquidity.
7. **Unresolved problem?** Monthly regularity. Band-normalized penetration past the k=2.0 band does not separate stop-outs from runners. Whether the prior completed higher-timeframe bar's direction does is still open.
8. **Next experiment and why?** One §8 HTF-direction gate on this same name (prior fully closed 4-bar HTF candle must agree with the signal). Written after this decision, before any run. Not liquidity in the same test, not a retune of D, not another catalog name, not FREEZE, not holdout.
9. **Why not a random search?** §7 develop-not-abandon. One more own-trades variant just closed; licensed axes remain. Do not jump to `EMA_50_200` or `EMA3_13_50_200`. Breakout-depth failure here is not evidence about other catalog5 names, and `0685ce5` / `3495b16` are not evidence about this one.
10. **What would confirm or falsify the next hyp?** Pre-registered before the run. A pass needs mean Train-1 net above +95.3217987, initial_sl share down at least 10pp, at least 50% of big-winner PnL retained, and a pooled losing-month floor strictly below 7/12, without thinning below 10 trades/series. Any one of (a)–(e) fails it. The gate is binary (`number_of_trials = 1`).
