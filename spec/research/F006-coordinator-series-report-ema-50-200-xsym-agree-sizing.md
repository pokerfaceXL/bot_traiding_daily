# Coordinator Series Report — H-EMA-50-200-XSYM-AGREE-SIZING-01 (§15)

> **Date:** 2026-10-03 ~17:25 Europe/Warsaw
> **Experiment:** H-EMA-50-200-XSYM-AGREE-SIZING-01
> **Tip / merge:** `48d03b0` (FF to origin/main; parent `5af9b88`). Review PASS job
> `2026-10-03-f006-ema50200-xsym-agree-sizing--f8969a7a` (engine claude).
> **Artifacts:** `output/f006_ema_50_200_xsym_agree_sizing/`
> **Card:** `spec/research/F006-hypothesis-ema-50-200-xsym-agree-sizing.md`

## Summary

Cross-symbol agreement sizing on `EMA_50_200` **FALSIFIED (b)**. Control mean
**+72.6693115** reproduced (max abs diff 0.0). Sized mean **+126.744211**
(delta **+54.0748995**/series). Pooled losing entry-months stay **7/12**.
Winner-loser mult gap **+0.132984**. Stake_cv **0.413344**. n_trades invariant
held (330 Train-1 entries). Status stays **CONDITIONAL**. Do not FREEZE. This
formula is closed on this name only. Not a Val window: the card opens
validation only if the sized arm passes, and (b) says a non-improving floor
falsifies. Next = `H-EMA-50-200-ENTRY-CANDLE-CONFIRM-01` on this name's own
reproduced baseline +72.6693115. Do not copy +95.3217987 or +82.900262.

## Q1–10

1. **Best strategy now?** None promotable. `BB_20_2_EMA200`, `BB_20_25_EMA200`,
   `EMA3_21_50_200`, and `DONCHIAN_55_NO_TRAIL` stay **FREEZE**. Highest-priority
   unfinished name is still `EMA_50_200` (**CONDITIONAL**), then `EMA3_13_50_200`.
2. **Why that name?** It is the catalog5 name whose own-trades loop is open.
   This sizing formula did not improve the monthly floor. The screen (mean
   +72.6693115 from this run's reproduced control, 7/10 series positive, 0/10
   clear §7) is this name's, not a transferred BB figure.
3. **Edge from many trades or few big wins?** Few big wins, and sizing made
   that more so. Ungated Train-1 entries: 5 trades with net>=29.9 sum to
   +843.763902 against cohort net +587.385179 (n=330). Sized arm: 10 trades /
   +1477.682389, and 2024-11 alone moves +816.808826 to +1308.876889.
4. **Earns when?** `signal_reverse` runners, and more when peer EMA_50_200
   signals agree. mean(mult|winner) 1.365809 > mean(mult|loser) 1.232824
   (gap +0.132984). That skew is real and is not falsifier (c). It did not
   fix the month floor.
5. **Loses when?** The same seven entry-months as the control (2024-03, -04,
   -05, -08, -09, -12, 2025-01). Six of those seven are slightly deeper under
   sizing; 2024-09 is slightly less deep (−28.73 to −25.87) and stays
   negative. Shared-losing (H-CATALOG5-SHARED-LOSING-MONTHS-01) still stands.
6. **Rejected hypotheses?** Add: **H-EMA-50-200-XSYM-AGREE-SIZING-01 =
   FALSIFIED (b)** at `48d03b0`. (a)(c)(d)(e) did not fire. Already closed on
   this name: exit-class, partial-exit, long-only, breadth, abs-ATR
   FALSIFIED (a)+(c) at `80e7fa6`. Not closed here: other §8 entry structure.
   BB_20_2 Train-1 REFINE (`1774a8a`, floor 7 to 6) and Val-4 FALSIFIED (c)
   (`139ed3d`) do not transfer. BB_20_25 closures do not transfer.
7. **Unresolved problem?** §7 monthly regularity on this name. Reweighting
   stake by cross-symbol agreement raises the mean and does not reduce the
   7/12 losing-month floor. Candle confirm and the later entry-structure
   axes are still untested on these trades.
8. **Next experiment and why?** **H-EMA-50-200-ENTRY-CANDLE-CONFIRM-01.**
   decision_if_fail names candle confirm. A flat floor is falsifier (b), so
   this is not Val-1 of the closed stake. The gate is directional close
   location on this name's own signal bar, not an abs-ATR threshold and not
   a retune of 0.5 / 0.375 / 2.0. The T grid is the licensed candle-confirm
   shape; it is not BB_20_2's T=0.60 result or BB_20_25's T=0.70 result.
9. **Why not random new strategies?** §7 develop-not-abandon and §13: licensed
   entry-structure axes on `EMA_50_200` are still open. Do not start
   `EMA3_13_50_200`. Do not start funding-carry or spread-capture (owner
   parked). Do not retest catalog mean-reversion. Shared-losing blocks
   in-class portfolio combination; it does not license FREEZE of this name.
10. **What would confirm or falsify the next hyp?** Pre-registered before the
    run on `EMA_50_200` only. A pass needs this name's own mean Train-1 net
    above the reproduced control +72.6693115, initial_sl share down at least
    10pp at the best-PnL T, at least 50% of this name's big-winner PnL
    retained, a strictly lower pooled losing-month floor, and mean
    trades/series at least 10. Any one of (a)–(e) fails it.
    `number_of_trials = 5`. This sizing result is not that test.
