# Coordinator Series Report — H-BB-20-2-ENTRY-CANDLE-CONFIRM-01 (§15)

> **Date:** 2026-10-03 ~14:36 Europe/Warsaw
> **Experiment:** H-BB-20-2-ENTRY-CANDLE-CONFIRM-01
> **Tip / merge:** `88b0ee3` (FF to origin/main from `89326fc`). Review PASS job
> `2026-10-03-f006-bb202-entry-candle-confirm--2b310688`.
> **Artifacts:** `output/f006_bb_20_2_entry_candle_confirm/cell_summary.csv`
> **Card:** `spec/research/F006-hypothesis-bb-20-2-entry-candle-confirm.md`

## Summary

Candle close-strength on `BB_20_2_EMA200` is **FALSIFIED (c)**. The ungated
control matched this name's frozen baseline (mean +95.3217987/series, cohort
n=756 net +834.347778, initial_sl share 0.473545, big-winner PnL 1251.654084,
floor 7/12). Best-PnL T=0.60 gained +0.449978/series and kept 100% of
pre-frozen big-winner PnL, but cut initial_sl share by only 0.548942pp against
the required 10pp. No T passed all declared checks. Status stays
**CONDITIONAL**. Do not FREEZE. This closes one entry variant, not entry
refinement as a class. Breakout depth, HTF direction, and liquidity remain
untested on this name's own trades. `BB_20_25_EMA200` candle FALSIFIED (c) at
`e70161d` is not this result.

## Q1–10

1. **Best strategy now?** None promotable. FREEZE names unchanged. Active CONDITIONAL name is `BB_20_2_EMA200`, then `EMA_50_200`, then `EMA3_13_50_200`. This run did not clear §7 (0/10 series still the catalog floor).
2. **Why that name?** Own-trades loop still open after entry-vol, the xsym formula, and now candle close-strength. Screen is this name's +95.32 control, not a BB_20_25 transfer.
3. **Edge from many trades or few big wins?** Few big wins. The pre-frozen set (net≥29.9, 12 trades, 1251.654084) is fully retained at T=0.60, and that cell still only adds +$0.45/series.
4. **Earns when?** Still when a pierce runs to `signal_reverse`. Close location inside the signal bar did not identify those runs.
5. **Loses when?** Most remaining trades still die at the fixed initial stop (46.81% at the best T, from 47.35%). The pooled floor stays 7/12. T=0.90 reached 6/12 only by cutting mean to 53.33 and keeping 22.4% of frozen big-winner PnL, and it raised the stop-out share by 8.39pp.
6. **Rejected hypotheses?** On this name's own trades: entry-vol FALSIFIED (a)+(c) `f7ac677`; xsym sizing formula FALSIFIED (c) on Val-4 `139ed3d`; candle close-strength FALSIFIED (c) `88b0ee3`. Exit, direction, and breadth stay closed. Not closed: breakout depth, HTF direction, liquidity.
7. **Unresolved problem?** Monthly regularity. Close location inside the signal bar does not separate stop-outs from runners. Whether penetration past this name's k=2.0 band does is still open.
8. **Next experiment and why?** One §8 breakout-depth gate on this same name (close distance beyond `bb_20_2.0`, normalized by that band's width). Written after this decision, before any run. Not HTF in the same test, not a retune of T, not another catalog name, not FREEZE, not holdout.
9. **Why not a random search?** §7 develop-not-abandon. One more own-trades variant just closed; licensed axes remain. Do not jump to `EMA_50_200` or `EMA3_13_50_200`. Candle failure here is not evidence about other catalog5 names, and `e70161d` is not evidence about this one.
10. **What would confirm or falsify the next hyp?** Pre-registered before the run. A pass needs mean Train-1 net above +95.3217987, initial_sl share down at least 10pp at the best-PnL D, at least 50% of big-winner PnL retained, and a pooled losing-month floor strictly below 7/12, without thinning below 10 trades/series. Any one of (a)–(e) fails it.
