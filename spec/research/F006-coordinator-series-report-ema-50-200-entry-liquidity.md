# Coordinator Series Report — H-EMA-50-200-ENTRY-LIQUIDITY-01 (§15)

> **Date:** 2026-10-03 ~19:38 Europe/Warsaw
> **Experiment:** H-EMA-50-200-ENTRY-LIQUIDITY-01
> **Tip / merge:** `48aef9f` (FF to origin/main; parent `4f98274`; harness `57689fd`). Review PASS job
> `2026-10-03-f006-ema50200-entry-liquidity-re-1cb84b84` (engine claude) on branch
> `limen/2026-10-03-f006-ema50200-entry-liquidity-01-9bb6e0d9`.
> **Artifacts:** `output/f006_ema_50_200_entry_liquidity/cell_summary.csv`,
> `manifest.json`, `run.log`, Train-1 blotters under `control/` and `liq_med20/`.
> **Card:** `spec/research/F006-hypothesis-ema-50-200-entry-liquidity.md`

## Summary

Liquidity on `EMA_50_200` is **FALSIFIED (a)+(c)+(d)**. The ungated control
matched this name's frozen baseline (mean +72.6693115/series, cohort n=330,
entry net +587.3851786486205, initial_sl 213/330 = 0.6454545454545455,
big-winner PnL +843.7639016181568, floor 7/12). The single gated cell
`liq_med20` mean +66.5789284 is −6.0903831/series. Initial_sl share fell
1.1651728553137009 pp (0.6454545454545455 → 0.6338028169014085, 213/330 →
135/213); the required move was a drop of ≥10pp. Frozen big-winner PnL
retained 100% (5/5, +843.7639016181568). Pooled losing entry-months stayed
7/12. Mean trades/series 21.3, so (e) did not fire. (b) did not fire.
`number_of_trials = 1`. Applied sentences: "(a) mean train1_net_pnl <=
baseline"; "(c) initial_sl share fails to fall >=10pp"; "(d) pooled
losing-month floor does not improve (stays >= baseline floor)".

Every licensed axis on this profile now has an own-trades citation, so the
profile is **FREEZE**. Not REJECT: the ungated Train-1 book stays
aggregate-positive (+72.6693115/series). Not a class closure, and not
evidence for `EMA3_13_50_200` or any other name. §4 level C permits stopping
further tuning of this name: the book is positive but unstable across
symbols (3/5 net-positive), 0/10 series pass the monthly promotion check,
and the edge is a few big winners. No licensed axis remains. This FREEZE is
this name's own closed loop.

## Q1–10

1. **Best strategy now?** None promotable. `EMA_50_200` joins the FREEZE list on its own loop. Active CONDITIONAL name is `EMA3_13_50_200`. `BB_20_2_EMA200`, `BB_20_25_EMA200`, `EMA3_21_50_200`, and `DONCHIAN_55_NO_TRAIL` stay FREEZE. This run did not clear §7.
2. **Why that name?** `EMA_50_200`'s licensed loop is closed. `EMA3_13_50_200` is the next CONDITIONAL catalog name and still has open own-trades axes. Its screen is its own catalog5 mean +91.1483016 (sum +911.483016), not this name's +72.6693115 and not +95.3217987.
3. **Edge from many trades or few big wins?** Few big wins. The pre-frozen set (net≥29.9, 5 trades, +843.7639016181568) was fully retained, and the cell still loses −6.0903831/series. Cohort net +587.3851786486205 on n=330 is carried by those runners.
4. **Earns when?** Still when an EMA 50/200 cross runs to `signal_reverse`. A signal bar at or above the prior-20 median base volume kept all five big winners and did not identify a better set. Gated per-symbol Train-1 net: XRP +546.04, DOGE +166.74, SOL +26.09, ETH −18.09, BTC −54.99 (3/5 positive).
5. **Loses when?** Most remaining trades still die at the fixed initial stop (64.55% → 63.38%, 213/330 → 135/213). The pooled floor stays 7/12 (2024-03, -04, -05, -08, -09, -12, 2025-01). The primary mean falls even though the Train-1 entry-cohort net rises, because warm-up-opened trades are removed.
6. **Rejected hypotheses?** On this name's own trades: entry-vol FALSIFIED (a)+(c) `80e7fa6`; xsym sizing formula FALSIFIED (b) `48d03b0` (no Val-1); candle close-strength FALSIFIED (a)+(c) `778f373`; breakout depth FALSIFIED (a)+(c) `485de51`; HTF direction FALSIFIED (a)+(b)+(c)+(d) `3a7c094`; liquidity FALSIFIED (a)+(c)+(d) `48aef9f`. Exit (`923de9c`, `3d4edd4`), long-only, and breadth (`f420078`, this name's cells) stay closed. BB_20_2 liquidity (`776e167`) does not transfer.
7. **Unresolved problem?** None licensed on this name. Monthly regularity is still unsolved, and no remaining §8 axis on this profile is open. Price-versus-range is not a separate axis (candle close-strength already tested location in the bar). Portfolio combination stays blocked by shared-losing months (`dc9818e`).
8. **Next experiment and why?** Stop this loop. One entry-vol / abs-ATR gate on `EMA3_13_50_200`'s own Train-1 trades, the first still-open licensed axis on that profile (the profile prefers entry-vol before sizing). Written after this decision, before any run. Not a retune of the volume window, not a new family, not funding-carry, not spread-capture, not catalog mean-reversion.
9. **Why not a random search?** §7 develop-not-abandon is satisfied for this name: the licensed axes are exhausted on its own trades, so §4 level C is FREEZE rather than another variant or a §13 new family. The next catalog name is developed on its own trades, not by copying this falsification. This FREEZE is not a class freeze and is not evidence for `EMA3_13_50_200`.
10. **What would confirm or falsify the next hyp?** Pre-registered before the run on `EMA3_13_50_200` only. A pass needs that name's own mean Train-1 net above +91.1483016, initial_sl share down at least 10pp at the best-PnL T, at least 50% of that name's big-winner PnL retained, and a pooled losing-month floor strictly below its own ungated floor, without thinning below 10 trades/series. Any one of (a)–(e) fails it. `number_of_trials = 5`. This liquidity result is not that test.
