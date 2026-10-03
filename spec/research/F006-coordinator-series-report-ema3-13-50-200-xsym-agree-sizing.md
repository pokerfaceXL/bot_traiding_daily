# Coordinator Series Report — H-EMA3-13-50-200-XSYM-AGREE-SIZING-01 (§15)

> **Date:** 2026-10-03 ~20:40 Europe/Warsaw
> **Experiment:** H-EMA3-13-50-200-XSYM-AGREE-SIZING-01
> **Tip / merge:** `34e2c4a` (FF to origin/main; parent `0f7b608`). Review PASS job
> `2026-10-03-f006-ema31350200-xsym-01-review-197231de` (engine claude).
> **Artifacts:** `output/f006_ema3_13_50_200_xsym_agree_sizing/`
> **Card:** `spec/research/F006-hypothesis-ema3-13-50-200-xsym-agree-sizing.md`

## Summary

Cross-symbol agreement sizing on `EMA3_13_50_200` **FALSIFIED (b)**. Control
mean **+91.1483016** reproduced (max abs diff 0.0). Sized mean
**+127.142706** (delta **+35.994404**/series). Pooled losing-month floor
stayed **7/12**. Mult gap **+0.085755**. Stake_cv **0.429331**. n=423
invariant. Series higher **6/10** (Result text said 7/10; `results.csv`
says 6; (b) does not use that count). The card's (b) sentence treats a
non-improving floor as falsification and closes the formula with no
validation window. Status stays **CONDITIONAL**. Do not FREEZE. Next =
`H-EMA3-13-50-200-ENTRY-CANDLE-CONFIRM-01` on this name's reproduced
baseline +91.1483016 / n=423. Do not copy +126.744211.

## Q1–10

1. **Best strategy now?** None promotable. `EMA_50_200`, `BB_20_2_EMA200`,
   `BB_20_25_EMA200`, `EMA3_21_50_200`, and `DONCHIAN_55_NO_TRAIL` stay
   **FREEZE**. The only unfinished catalog5 name is `EMA3_13_50_200`
   (**CONDITIONAL**).
2. **Why that name?** Its own-trades loop is still open. This sizing formula
   raised the mean and did not move the month floor, so the formula is
   closed and the name is not. The screen (mean +91.1483016, 6/10 series
   positive on the ungated Train-1 table, 0/10 clear §7) is this name's.
   `EMA_50_200` FREEZE is not evidence here.
3. **Edge from many trades or few big wins?** Few big wins. Ungated Train-1
   entries: 9 trades with net≥29.9 sum to +1131.956154 against cohort net
   +771.283617 (n=423). Sizing grew that set to 14 / +1678.744869 and the
   2024-11 runner month (+812.27 to +1299.61) without clearing a losing
   month.
4. **Earns when?** Consensus-weighted `signal_reverse` runners, especially
   2024-11 and 2025-02. Mean(mult|winner) 1.273438 > mean(mult|loser)
   1.187682. Six of ten series have a higher sized mean (BTC240, XRP240,
   SOL60, ETH60, BTC60, XRP60).
5. **Loses when?** The same seven entry-months lose in both arms (2024-03,
   -04, -05, -08, -09, -12, 2025-01). Sizing made six of those seven more
   negative. SOL240, ETH240, DOGE240, and DOGE60 are lower after sizing.
   Shared-losing (H-CATALOG5-SHARED-LOSING-MONTHS-01) still stands.
6. **Rejected hypotheses?** Add: **H-EMA3-13-50-200-XSYM-AGREE-SIZING-01 =
   FALSIFIED (b)** at `34e2c4a`. (a)(c)(d)(e) did not fire. Already closed
   on this name: abs-ATR **FALSIFIED (a)+(c)** `46e4509` ((d) not reachable),
   exit-class, partial-exit, long-only, breadth. Not closed here: candle
   confirm, breakout depth, HTF direction, liquidity. Other names' sizing
   results do not transfer.
7. **Unresolved problem?** §7 monthly regularity on this name. A stake map
   that keeps every trade raised the mean (+35.994404/series) and did not
   lower the 7/12 floor. Entry structure other than abs-ATR is still
   untested on these trades.
8. **Next experiment and why?** **H-EMA3-13-50-200-ENTRY-CANDLE-CONFIRM-01.**
   The card's decision_if_fail names candle confirm, and the profile's open
   order after a failed sizing formula is that axis. One §8 close-strength
   gate, Train-1, this name's control +91.1483016 / n=423. Not a Val-1.
   Not an abs-ATR retune. Not FREEZE. Not holdout.
9. **Why not random new strategies?** §7 develop-not-abandon and §13:
   licensed axes on `EMA3_13_50_200` are still open. Do not FREEZE this
   name. Do not start funding-carry, spread-capture, or catalog
   mean-reversion. Shared-losing blocks in-class portfolio combination; it
   does not license FREEZE of this name. Do not jump to a new catalog name.
10. **What would confirm or falsify the next hyp?** Pre-registered before
    the run on `EMA3_13_50_200` only. A pass needs mean Train-1 net above
    +91.1483016, initial_sl share down ≥10pp at the best-PnL T, ≥50% of
    this name's big-winner PnL retained (9 / +1131.956154), pooled floor
    strictly below 7/12, and ≥10 trades/series. Any one of (a)–(e) fails
    it. On that card (b) is big-winner removal, not a flat floor; the floor
    clause is (d) and only at a T that otherwise passes (a)–(c).
    `number_of_trials = 5`. T grid `{0.50, 0.60, 0.70, 0.80, 0.90}` is the
    licensed shape, not another name's winning T. This sizing result is
    not that test.
