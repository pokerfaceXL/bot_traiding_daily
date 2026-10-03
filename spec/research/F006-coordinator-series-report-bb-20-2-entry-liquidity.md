# Coordinator Series Report — H-BB-20-2-ENTRY-LIQUIDITY-01 (§15)

> **Date:** 2026-10-03 ~16:20 Europe/Warsaw
> **Experiment:** H-BB-20-2-ENTRY-LIQUIDITY-01
> **Tip / merge:** `776e167` (FF to origin/main; parent `df38f08`). Review PASS job
> `2026-10-03-f006-bb202-entry-liquidity-revie-ac02a80e` (engine claude).
> **Artifacts:** `output/f006_bb_20_2_entry_liquidity/cell_summary.csv`,
> `manifest.json`, `run.log`, Train-1 blotters under `control/` and `liq_med20/`.
> **Card:** `spec/research/F006-hypothesis-bb-20-2-entry-liquidity.md`

## Summary

Liquidity on `BB_20_2_EMA200` is **FALSIFIED (c) only**. The ungated control
matched this name's frozen baseline (mean +95.3217987/series, cohort n=756
net +834.347778, initial_sl 358/756 = 0.47354497354497355, big-winner PnL
1251.654084307187, floor 7/12). The single gated cell `liq_med20` mean
+97.2455987 is +1.923800/series. Initial_sl share rose +0.084856pp
(0.47354497354497355 → 0.4743935309973046, 358/756 → 352/742); the required
move was a drop of ≥10pp. Frozen big-winner PnL retained 100% (12/12,
1251.654084307187). Pooled losing entry-months went 7/12 → 6/12 (2024-04
flips −5.17 → +5.01). Mean trades/series 74.2, so (e) did not fire. (a),
(b), and (d) did not fire. `number_of_trials = 1`. The small mean rise does
not override falsifier (c).

Every licensed axis on this profile now has an own-trades citation, so the
profile is **FREEZE**. Not REJECT: the ungated Train-1 book stays
aggregate-positive (+95.3217987/series). Not a class closure, and not
evidence for `EMA_50_200`, `EMA3_13_50_200`, or any other name. §4 level C
permits stopping further tuning of this name: the book is positive but
unstable across symbols (entry-cohort symbols 3/5 net-positive), 0/10 series
pass the monthly promotion check, and the only sizing formula failed
Validation-4 (`139ed3d`). No licensed axis remains.

## Q1–10

1. **Best strategy now?** None promotable. `BB_20_2_EMA200` joins the FREEZE list on its own loop. Active CONDITIONAL name is `EMA_50_200`, then `EMA3_13_50_200`. This run did not clear §7.
2. **Why that name?** `BB_20_2_EMA200`'s licensed loop is closed. `EMA_50_200` is the next CONDITIONAL catalog name and still has open own-trades axes. Its screen is its own catalog5 mean +72.6693115, not this name's +95.3217987 and not `BB_20_25_EMA200`'s +82.900262.
3. **Edge from many trades or few big wins?** Few big wins. The pre-frozen set (net≥29.9, 12 trades, 1251.654084307187) was fully retained, and the cell still only gains +1.923800/series by dropping 14 closed trades, none of them big winners.
4. **Earns when?** Still when a band pierce runs to `signal_reverse`. A signal bar at or above the prior-20 median base volume did not identify those runs. Closed Train-1 entries only shrink 756 → 742, and the stop-out share does not fall.
5. **Loses when?** Most remaining trades still die at the fixed initial stop, and the share rises (47.35% ungated → 47.44% gated). The pooled floor improves by one month (2024-04) while 2024-09 worsens (−60.43 → −73.07). That is not the pre-registered stop-out separation.
6. **Rejected hypotheses?** On this name's own trades: entry-vol FALSIFIED (a)+(c) `f7ac677`; xsym sizing formula FALSIFIED (c) on Val-4 `139ed3d`; candle close-strength FALSIFIED (c) `88b0ee3`; breakout depth FALSIFIED (a)+(c) `27fa7f6`; HTF direction FALSIFIED (a)+(c)+(d) `dd86dd0`; liquidity FALSIFIED (c) `776e167`. Exit (`923de9c`, `3d4edd4`), long-only, and breadth (`f420078`, this name's cells) stay closed.
7. **Unresolved problem?** None licensed on this name. Monthly regularity is still unsolved, and no remaining §8 axis on this profile is open. Price-versus-range is not a separate axis (candle close-strength already tested location in the bar). Portfolio combination stays blocked by shared-losing months (`dc9818e`).
8. **Next experiment and why?** Stop this loop. One entry-vol / abs-ATR gate on `EMA_50_200`'s own Train-1 trades, the first still-open licensed axis on that profile, same sequencing as this loop's first axis. Written after this decision, before any run. Not a retune of the volume window, not a new family, not `EMA3_13_50_200`.
9. **Why not a random search?** §7 develop-not-abandon is satisfied for this name: the licensed axes are exhausted on its own trades, so §4 level C is FREEZE rather than another variant or a §13 new family. The next catalog name is developed on its own trades, not by copying this falsification.
10. **What would confirm or falsify the next hyp?** Pre-registered before the run on `EMA_50_200` only. A pass needs that name's own mean Train-1 net above +72.6693115, initial_sl share down at least 10pp at the best-PnL T, at least 50% of that name's big-winner PnL retained, and a pooled losing-month floor strictly below its own ungated floor, without thinning below 10 trades/series. Any one of (a)–(e) fails it. `number_of_trials = 5`. This liquidity result is not that test.
