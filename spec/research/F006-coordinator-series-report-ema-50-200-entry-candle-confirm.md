# Coordinator Series Report — H-EMA-50-200-ENTRY-CANDLE-CONFIRM-01 (§15)

> **Date:** 2026-10-03 ~17:58 Europe/Warsaw
> **Experiment:** H-EMA-50-200-ENTRY-CANDLE-CONFIRM-01
> **Tip / merge:** `778f373` (FF to origin/main; parent `5321033`). Review PASS job
> `2026-10-03-f006-ema50200-entry-candle-confi-ec9e0935` (engine claude).
> **Artifacts:** `output/f006_ema_50_200_entry_candle_confirm/`
> **Card:** `spec/research/F006-hypothesis-ema-50-200-entry-candle-confirm.md`

## Summary

Candle confirmation on `EMA_50_200` **FALSIFIED (a)+(c)**. Control mean
**+72.6693115** reproduced (max abs diff 0.0, n=330, initial_sl 213/330).
Best T=0.50 mean **+45.0267104** (delta **−27.6426011**/series). Initial_sl
share rose **2.9672358098754015 pp** to 133/197. Every T lowers the mean.
No T cuts the stop-out share. Status stays **CONDITIONAL**. Do not FREEZE.
Candle close-strength is closed on this name only. Not a Val window. Next =
`H-EMA-50-200-ENTRY-BREAKOUT-DEPTH-01` on this name's own reproduced baseline
+72.6693115. Do not copy +95.3217987 or +82.900262.

## Q1–10

1. **Best strategy now?** None promotable. `BB_20_2_EMA200`, `BB_20_25_EMA200`,
   `EMA3_21_50_200`, and `DONCHIAN_55_NO_TRAIL` stay **FREEZE**. Highest-priority
   unfinished name is still `EMA_50_200` (**CONDITIONAL**), then `EMA3_13_50_200`.
2. **Why that name?** It is the catalog5 name whose own-trades loop is open.
   Candle confirm did not raise the mean or cut stop-outs. The screen (mean
   +72.6693115 from this run's reproduced control, 7/10 series positive on the
   earlier catalog window, 0/10 clear §7) is this name's, not a transferred BB
   figure.
3. **Edge from many trades or few big wins?** Few big wins. Ungated Train-1
   entries: 5 trades with net>=29.9 sum to +843.7639016181568 against cohort
   net +587.3851786486205 (n=330). Best T=0.50 keeps 2 of those
   (+472.64056916581933, 56.0%) and still loses −27.6426011/series.
4. **Earns when?** `signal_reverse` runners. A stronger close inside the signal
   bar did not identify them. The best cell keeps a bare majority of big-winner
   PnL and still loses money versus control.
5. **Loses when?** Most remaining trades still die at the fixed `initial_sl`,
   and the share rises (64.55% to 67.51% at T=0.50). The pooled floor worsens
   7/12 to 8/12 on every non-thin T. Shared-losing
   (H-CATALOG5-SHARED-LOSING-MONTHS-01) still stands.
6. **Rejected hypotheses?** Add: **H-EMA-50-200-ENTRY-CANDLE-CONFIRM-01 =
   FALSIFIED (a)+(c)** at `778f373`. (b)(d)(e) did not fire. Already closed on
   this name: exit-class, partial-exit, long-only, breadth, abs-ATR
   FALSIFIED (a)+(c) at `80e7fa6`, xsym-agree formula FALSIFIED (b) at
   `48d03b0`. Not closed here: breakout depth, HTF direction, liquidity.
   BB_20_2 candle (`88b0ee3`) and BB_20_25 candle (`e70161d`) do not transfer.
7. **Unresolved problem?** §7 monthly regularity on this name. Filtering on
   where the signal bar closed inside its own range lowers the mean and does
   not reduce stop-outs. Breakout depth, HTF direction, and liquidity are
   still untested on these trades.
8. **Next experiment and why?** **H-EMA-50-200-ENTRY-BREAKOUT-DEPTH-01.**
   decision_if_fail names breakout depth, and the profile's open order after
   candle confirm is breakout structure, then HTF direction, then liquidity.
   The gate is how far the close has cleared ema200, not a retune of T, not
   an abs-ATR threshold, and not a retune of 0.5 / 0.375 / 2.0. The D grid
   `{0.02, 0.05, 0.10, 0.25, 0.50}` is the licensed breakout-depth shape. It
   is not another name's measured depth means.
9. **Why not random new strategies?** §7 develop-not-abandon and §13: licensed
   entry-structure axes on `EMA_50_200` are still open. Do not start
   `EMA3_13_50_200`. Do not start funding-carry or spread-capture. Do not
   retest catalog mean-reversion. Shared-losing blocks in-class portfolio
   combination; it does not license FREEZE of this name.
10. **What would confirm or falsify the next hyp?** Pre-registered before the
    run on `EMA_50_200` only. A pass needs this name's own mean Train-1 net
    above the reproduced control +72.6693115, initial_sl share down at least
    10pp at the best-PnL D, at least 50% of this name's big-winner PnL
    retained, a strictly lower pooled losing-month floor, and mean
    trades/series at least 10. Any one of (a)–(e) fails it.
    `number_of_trials = 5`. This candle result is not that test.
