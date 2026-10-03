# Coordinator Series Report — H-EMA-50-200-ENTRY-BREAKOUT-DEPTH-01 (§15)

> **Date:** 2026-10-03 ~18:26 Europe/Warsaw
> **Experiment:** H-EMA-50-200-ENTRY-BREAKOUT-DEPTH-01
> **Tip / merge:** `485de51` (FF to origin/main; git parent `a243176`; prior Decision `4e32994`). Review PASS job
> `2026-10-03-f006-ema50200-entry-breakout-dep-00ab01c3` (engine claude) on branch
> `limen/2026-10-03-f006-ema50200-entry-breakout-dep-bc3f314d`.
> **Artifacts:** `output/f006_ema_50_200_entry_breakout_depth/`
> **Card:** `spec/research/F006-hypothesis-ema-50-200-entry-breakout-depth.md`

## Summary

Breakout depth on `EMA_50_200` **FALSIFIED (a)+(c)**. Control mean
**+72.6693115** reproduced (max abs diff 0.0, n=330, initial_sl 213/330).
Best D=0.02 mean **+63.0343180** (delta **−9.6349935**/series). Initial_sl
share rose **9.600886917960082 pp** to 152/205. Every D lowers the mean.
No D cuts the stop-out share. D=0.25 and D=0.50 take zero trades (vacuous
floors). Status stays **CONDITIONAL**. Do not FREEZE. Breakout depth is
closed on this name only. Not a Val window. Next =
`H-EMA-50-200-ENTRY-HTF-DIRECTION-01` on this name's own reproduced baseline
+72.6693115 / n=330. Do not copy +95.3217987 or +82.900262. Do not copy
another name's depth means or pass/fail.

## Q1–10

1. **Best strategy now?** None promotable. `BB_20_2_EMA200`, `BB_20_25_EMA200`,
   `EMA3_21_50_200`, and `DONCHIAN_55_NO_TRAIL` stay **FREEZE**. Highest-priority
   unfinished name is still `EMA_50_200` (**CONDITIONAL**), then `EMA3_13_50_200`.
2. **Why that name?** It is the catalog5 name whose own-trades loop is open.
   Breakout depth did not raise the mean or cut stop-outs. The screen (mean
   +72.6693115 from this run's reproduced control, 7/10 series positive on the
   earlier catalog window, 0/10 clear §7) is this name's, not a transferred BB
   figure.
3. **Edge from many trades or few big wins?** Few big wins. Ungated Train-1
   entries: 5 trades with net>=29.9 sum to +843.7639016181568 against cohort
   net +587.3851786486205 (n=330). Best D=0.02 keeps 3 of those
   (+760.9812320976589, 90.2%) and still loses −9.6349935/series.
4. **Earns when?** `signal_reverse` runners. A close that has cleared a larger
   fraction of ema200 did not identify them. The best cell keeps most
   big-winner PnL and still loses money versus control, while stopping out
   more often.
5. **Loses when?** Most remaining trades still die at the fixed `initial_sl`,
   and the share rises (64.55% to 74.15% at D=0.02, 213/330 to 152/205). The
   pooled floor worsens 7/12 to 8/12 on the only non-thin D. Shared-losing
   (H-CATALOG5-SHARED-LOSING-MONTHS-01) still stands.
6. **Rejected hypotheses?** Add: **H-EMA-50-200-ENTRY-BREAKOUT-DEPTH-01 =
   FALSIFIED (a)+(c)** at `485de51`. (b) did not fire (only non-thin D keeps
   90.2%). (d) is vacuous (no D passes (a)-(c); empty D=0.25 and D=0.50
   floors are not improvements). (e) did not fire. Already closed on this
   name: exit-class, partial-exit, long-only, breadth, abs-ATR FALSIFIED
   (a)+(c) at `80e7fa6`, xsym-agree formula FALSIFIED (b) at `48d03b0`,
   candle confirm FALSIFIED (a)+(c) at `778f373`. Not closed here: HTF
   direction, liquidity. BB_20_2 depth (`27fa7f6`) and BB_20_25 depth
   (`0685ce5`) do not transfer.
7. **Unresolved problem?** §7 monthly regularity on this name. Filtering on
   how far the signal-bar close has cleared ema200 lowers the mean and raises
   stop-outs. HTF direction and liquidity are still untested on these trades.
8. **Next experiment and why?** **H-EMA-50-200-ENTRY-HTF-DIRECTION-01.**
   decision_if_fail names HTF direction, and the profile's open order after
   breakout depth is HTF direction, then liquidity. The gate is whether the
   prior fully closed 4-bar higher-timeframe candle agrees with the signal,
   not a retune of D, not an abs-ATR threshold, not candle close-strength,
   and not a retune of 0.5 / 0.375 / 2.0. The 4-bar bucket shape is the
   licensed HTF pattern. It is not another name's measured HTF mean or
   pass/fail. `number_of_trials = 1`.
9. **Why not random new strategies?** §7 develop-not-abandon and §13: licensed
   entry-structure axes on `EMA_50_200` are still open (HTF, then liquidity).
   Do not start `EMA3_13_50_200`. Do not start funding-carry or
   spread-capture. Do not retest catalog mean-reversion. Shared-losing blocks
   in-class portfolio combination; it does not license FREEZE of this name.
   If liquidity is later the last licensed axis, FREEZE is allowed only at
   that later experiment's own Decision, not now.
10. **What would confirm or falsify the next hyp?** Pre-registered before the
    run on `EMA_50_200` only. A pass needs this name's own mean Train-1 net
    above the reproduced control +72.6693115, initial_sl share down at least
    10pp, at least 50% of this name's big-winner PnL retained, a strictly
    lower pooled losing-month floor than this name's ungated floor, and mean
    trades/series at least 10. Any one of (a)–(e) fails it.
    `number_of_trials = 1`. This depth result is not that test.
