# Coordinator Series Report — H-EMA-50-200-ENTRY-HTF-DIRECTION-01 (§15)

> **Date:** 2026-10-03 ~18:56 Europe/Warsaw
> **Experiment:** H-EMA-50-200-ENTRY-HTF-DIRECTION-01
> **Tip / merge:** `3a7c094` (FF to origin/main; git parent `54706a6`; prior Decision `925eee1`). Review PASS job
> `2026-10-03-f006-ema50200-entry-htf-directio-1f19b4cb` (engine claude) on branch
> `limen/2026-10-03-f006-ema50200-entry-htf-directio-3631d55b`.
> **Artifacts:** `output/f006_ema_50_200_entry_htf_direction/`
> **Card:** `spec/research/F006-hypothesis-ema-50-200-entry-htf-direction.md`

## Summary

HTF direction on `EMA_50_200` **FALSIFIED (a)+(b)+(c)+(d)**. Control mean
**+72.6693115** reproduced (max abs diff 0.0, n=330, initial_sl 213/330).
Gated `htf_4` mean **+20.7369913** (delta **−51.9323202**/series), n=239.
Initial_sl share rose **2.818562190947127 pp**. Big-winner PnL kept
**44.0%** (3 / +371.1233324523375). Floor stayed **7/12**. The card's (d)
sentence says a non-improving floor falsifies (`stays >= baseline floor`),
so the flat floor fires (d). Status stays **CONDITIONAL**. Do not FREEZE.
HTF direction is closed on this name only. Not a Val window. Next =
`H-EMA-50-200-ENTRY-LIQUIDITY-01` on this name's own reproduced baseline
+72.6693115 / n=330. Liquidity is the last licensed axis. Do not copy
+95.3217987 or +82.900262. Do not copy another name's HTF means or
pass/fail.

## Q1–10

1. **Best strategy now?** None promotable. `BB_20_2_EMA200`, `BB_20_25_EMA200`,
   `EMA3_21_50_200`, and `DONCHIAN_55_NO_TRAIL` stay **FREEZE**. Highest-priority
   unfinished name is still `EMA_50_200` (**CONDITIONAL**), then `EMA3_13_50_200`.
2. **Why that name?** It is the catalog5 name whose own-trades loop is open.
   HTF direction did not raise the mean, did not cut stop-outs, and removed
   more than half of big-winner PnL. The screen (mean +72.6693115 from this
   run's reproduced control, n=330) is this name's, not a transferred BB
   figure.
3. **Edge from many trades or few big wins?** Few big wins. Ungated Train-1
   entries: 5 trades with net>=29.9 sum to +843.7639016181568 against cohort
   net +587.3851786486205 (n=330). `htf_4` keeps 3 of those
   (+371.1233324523375, 0.4398426286554843) and still loses −51.9323202/series.
4. **Earns when?** `signal_reverse` runners. Agreement with the prior closed
   4-bar HTF candle did not identify them. Gated per-symbol Train-1 net:
   XRPUSDT +221.99, DOGEUSDT +25.26, SOLUSDT +7.92, ETHUSDT −2.85,
   BTCUSDT −44.95 (3/5 positive).
5. **Loses when?** Most remaining trades still die at the fixed `initial_sl`,
   and the share rises (64.55% to 67.36%, 213/330 to 161/239). The pooled
   floor stays 7/12. Net/trade falls from +1.7800 to +0.6546. Shared-losing
   (H-CATALOG5-SHARED-LOSING-MONTHS-01) still stands.
6. **Rejected hypotheses?** Add: **H-EMA-50-200-ENTRY-HTF-DIRECTION-01 =
   FALSIFIED (a)+(b)+(c)+(d)** at `3a7c094`. (e) did not fire (23.9
   trades/series). Applied (d) sentence: "pooled losing-month floor does not
   improve (stays >= baseline floor)". Already closed on this name:
   exit-class, partial-exit, long-only, breadth, abs-ATR FALSIFIED (a)+(c)
   at `80e7fa6`, xsym-agree formula FALSIFIED (b) at `48d03b0`, candle
   confirm FALSIFIED (a)+(c) at `778f373`, breakout depth FALSIFIED (a)+(c)
   at `485de51`. Not closed here: liquidity. BB_20_2 HTF (`dd86dd0`) and
   BB_20_25 HTF (`3495b16`) do not transfer.
7. **Unresolved problem?** §7 monthly regularity on this name. Filtering on
   the prior closed 4-bar candle lowers the mean, raises stop-outs, and cuts
   runners. Liquidity is the last untested licensed axis on these trades.
8. **Next experiment and why?** **H-EMA-50-200-ENTRY-LIQUIDITY-01.**
   decision_if_fail names liquidity, and the profile's open order after HTF
   direction is liquidity and nothing else. The gate keeps a one-shot signal
   iff the signal bar's base volume is at least the median of the prior 20
   closed bars (signal bar excluded). Not `vol_ratio > 1.2`. Not a retune of
   the 4-bar length, not an abs-ATR threshold, not candle close-strength,
   not ema200 depth, and not a retune of 0.5 / 0.375 / 2.0. The 20-bar
   median is the licensed liquidity shape. It is not another name's measured
   liquidity mean or pass/fail. `number_of_trials = 1`.
9. **Why not random new strategies?** §7 develop-not-abandon and §13: one
   licensed entry axis remains on `EMA_50_200` (liquidity). Do not start
   `EMA3_13_50_200`. Do not start funding-carry or spread-capture. Do not
   retest catalog mean-reversion. Shared-losing blocks in-class portfolio
   combination; it does not license FREEZE in this commit. Liquidity is the
   last licensed axis. §4 level C allows FREEZE only at that experiment's
   own Decision if it is falsified on this name's own trades and the ungated
   book stays aggregate-positive. This commit does not set FREEZE.
10. **What would confirm or falsify the next hyp?** Pre-registered before the
    run on `EMA_50_200` only. A pass needs this name's own mean Train-1 net
    above the reproduced control +72.6693115, initial_sl share down at least
    10pp, at least 50% of this name's big-winner PnL retained, a strictly
    lower pooled losing-month floor than this name's ungated floor, and mean
    trades/series at least 10. Any one of (a)–(e) fails it.
    `number_of_trials = 1`. This HTF result is not that test. Do not open a
    validation window unless that arm passes.
