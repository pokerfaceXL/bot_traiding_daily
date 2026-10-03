# Coordinator Series Report — H-BB-20-2-ENTRY-HTF-DIRECTION-01 (§15)

> **Date:** 2026-10-03 ~15:41 Europe/Warsaw
> **Experiment:** H-BB-20-2-ENTRY-HTF-DIRECTION-01
> **Tip / merge:** `dd86dd0` (FF to origin/main). Review PASS job
> `2026-10-03-f006-bb202-entry-htf-direction-r-911650ed`.
> **Artifacts:** `output/f006_bb_20_2_entry_htf_direction/cell_summary.csv`,
> `results.csv`, Train-1 blotters under `control/` and `htf_4/`.
> **Card:** `spec/research/F006-hypothesis-bb-20-2-entry-htf-direction.md`

## Summary

HTF direction on `BB_20_2_EMA200` is **FALSIFIED (a)+(c)+(d)**. The ungated
control matched this name's frozen baseline (mean +95.3217987/series, cohort
n=756 net +834.347778, initial_sl 358/756 = 0.473545, big-winner PnL
1251.654084, floor 7/12). The single gated cell `htf_4` mean +75.8615895 is
−19.4602092/series. Initial_sl share rose +2.790851pp (0.473545 → 0.501453,
345/688); the required move was a drop of ≥10pp. Frozen big-winner PnL
retained 83.0% (9/12, 1038.611233 of 1251.654084). Pooled losing
entry-months went 7/12 → 8/12 (2025-01 flips +10.23 → −15.42). Mean
trades/series 68.8, so (e) did not fire. (b) did not fire.
`number_of_trials = 1`. Status stays **CONDITIONAL**. Do not FREEZE. This
closes HTF direction, not entry refinement as a class. Liquidity remains
the last named open axis on this name's own trades. `BB_20_25_EMA200` HTF
FALSIFIED (a)+(c)+(d) at `3495b16` (control +82.900262, n=512, gated
+70.515667) is not this result.

## Q1–10

1. **Best strategy now?** None promotable. FREEZE names unchanged. Active CONDITIONAL name is `BB_20_2_EMA200`, then `EMA_50_200`, then `EMA3_13_50_200`. This run did not clear §7 (0/10 series still the catalog floor).
2. **Why that name?** Own-trades loop still open after entry-vol, the xsym formula, candle close-strength, breakout depth, and now HTF direction. Screen is this name's +95.3217987 control, not a BB_20_25 transfer.
3. **Edge from many trades or few big wins?** Few big wins. The pre-frozen set (net≥29.9, 12 trades, 1251.654084) is only partly retained (9/12, 1038.611233, 83.0%), and that cell still loses −19.4602092/series.
4. **Earns when?** Still when a pierce runs to `signal_reverse`. Agreement with the prior closed 4-bar HTF candle did not identify those runs.
5. **Loses when?** Most remaining trades still die at the fixed initial stop, and the share rises (47.35% ungated → 50.15% gated). The pooled floor worsens 7/12 → 8/12. 2024-04 goes from −5.17 to −79.86. No month turns from losing to winning.
6. **Rejected hypotheses?** On this name's own trades: entry-vol FALSIFIED (a)+(c) `f7ac677`; xsym sizing formula FALSIFIED (c) on Val-4 `139ed3d`; candle close-strength FALSIFIED (c) `88b0ee3`; breakout depth FALSIFIED (a)+(c) `27fa7f6`; HTF direction FALSIFIED (a)+(c)+(d) `dd86dd0`. Exit, direction (long-only), and breadth stay closed. Not closed: liquidity.
7. **Unresolved problem?** Monthly regularity. The prior completed higher-timeframe bar's direction does not separate stop-outs from runners. Whether the signal bar's base volume versus the prior-20 median does is still open, and it is the last axis this profile names.
8. **Next experiment and why?** One §8 liquidity gate on this same name (signal-bar base volume ≥ median of the prior 20 closed bars). Written after this decision, before any run. Not a retune of the HTF length, not `vol_ratio > 1.2`, not another catalog name, not FREEZE, not holdout.
9. **Why not a random search?** §7 develop-not-abandon. One more own-trades variant just closed; the profile still names liquidity. Do not jump to `EMA_50_200` or `EMA3_13_50_200`. HTF failure here is not evidence about other catalog5 names, and `3495b16` is not evidence about this one. On `BB_20_25_EMA200`, liquidity was an unlicensed §8 example because that profile's last named axis was HTF; this profile still names liquidity, so it is in scope here and not a §13 new family.
10. **What would confirm or falsify the next hyp?** Pre-registered before the run. A pass needs mean Train-1 net above +95.3217987, initial_sl share down at least 10pp, at least 50% of big-winner PnL retained, and a pooled losing-month floor strictly below 7/12, without thinning below 10 trades/series. Any one of (a)–(e) fails it. The gate is binary (`number_of_trials = 1`). If it fails on this name's own trades, §4 level C allows FREEZE at that Decision (not REJECT: the ungated book stays aggregate-positive). That FREEZE is not set in this commit.
