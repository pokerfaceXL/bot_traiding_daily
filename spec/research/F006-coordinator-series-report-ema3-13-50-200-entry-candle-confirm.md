# Coordinator Series Report — H-EMA3-13-50-200-ENTRY-CANDLE-CONFIRM-01 (§15)

> **Date:** 2026-10-03 ~21:17 Europe/Warsaw
> **Experiment:** H-EMA3-13-50-200-ENTRY-CANDLE-CONFIRM-01
> **Tip / merge:** `9dbcf0d` (FF to origin/main; parent `8145008`; pre-reg `396a3c2`). Review PASS job
> `2026-10-03-f006-ema31350200-entry-candle-co-c5a12ffc` (engine claude).
> **Artifacts:** `output/f006_ema3_13_50_200_entry_candle_confirm/`
> **Card:** `spec/research/F006-hypothesis-ema3-13-50-200-entry-candle-confirm.md`

## Summary

Candle close-strength on `EMA3_13_50_200` **FALSIFIED (a)+(b)+(c)**. Control
mean **+91.1483016** reproduced (max abs diff 0.0). Best T=0.50 mean
**+51.7526015** (delta **−39.3957001**/series), n=316. Initial_sl share
**rose 2.8047101774545946 pp** (292/423 to 227/316). Big-winner PnL retained
**0.48671028537156213** (4 / +550.9347026116507 of 9 / +1131.9561537333418),
so **51.32897146284379% was removed**. The card's (b) sentence is "every
non-thin T removes >50% of baseline big-winner PnL". That sentence matches
the measurement, so (b) stays in the label. Floor stayed **7/12**. (d) is
not reachable. (e) does not fire. Status stays **CONDITIONAL**. Do not
FREEZE. Next = `H-EMA3-13-50-200-ENTRY-BREAKOUT-DEPTH-01` on this name's
reproduced baseline +91.1483016 / n=423. Do not copy +45.0267104.

## Q1–10

1. **Best strategy now?** None promotable. `EMA_50_200`, `BB_20_2_EMA200`,
   `BB_20_25_EMA200`, `EMA3_21_50_200`, and `DONCHIAN_55_NO_TRAIL` stay
   **FREEZE**. The only unfinished catalog5 name is `EMA3_13_50_200`
   (**CONDITIONAL**).
2. **Why that name?** Its own-trades loop is still open. Candle
   close-strength lowered the mean, raised the stop-out share, and removed
   more than half of the big-winner PnL, so that axis is closed and the
   name is not. The screen (mean +91.1483016, n=423, 0/10 clear §7) is
   this name's. `EMA_50_200` FREEZE is not evidence here.
3. **Edge from many trades or few big wins?** Few big wins. Ungated Train-1
   entries: 9 trades with net≥29.9 sum to +1131.9561537333418 against cohort
   net +771.2836172145886 (n=423). Best T kept 4 of those trades
   (+550.9347026116507, 48.671%).
4. **Earns when?** Ungated `signal_reverse` runners. A strong close inside
   the signal bar did not mark them. Best T=0.50 still lost 39.3957001 per
   series versus control.
5. **Loses when?** The fixed `initial_sl` (0% WR) is a larger share of the
   gated cohort (71.83544303797468%, 227/316) than of the control
   (69.03073286052009%, 292/423). The same 7/12 entry-months lose at every
   T. T=0.90 is thin (9.4 trades/series) and still below control.
6. **Rejected hypotheses?** Add: **H-EMA3-13-50-200-ENTRY-CANDLE-CONFIRM-01 =
   FALSIFIED (a)+(b)+(c)** at `9dbcf0d`. (d) not reachable. (e) did not fire.
   Already closed on this name: abs-ATR **FALSIFIED (a)+(c)** `46e4509`
   ((d) not reachable), xsym-agree formula **FALSIFIED (b)** `34e2c4a`
   (flat floor, no Val), exit-class, partial-exit, long-only, breadth.
   Not closed here: breakout depth, HTF direction, liquidity. Other names'
   candle results do not transfer (`778f373` was (a)+(c) only).
7. **Unresolved problem?** §7 monthly regularity on this name. Close location
   inside the signal bar did not separate stop-outs from runners. Distance
   of the close beyond ema200 is still untested on these trades.
8. **Next experiment and why?** **H-EMA3-13-50-200-ENTRY-BREAKOUT-DEPTH-01.**
   The card's decision_if_fail names breakout depth, and the profile's open
   order after a failed candle gate is that axis. One §8 ema200-normalized
   depth gate, Train-1, this name's control +91.1483016 / n=423. Not a
   candle retune. Not an abs-ATR retune. Not FREEZE. Not holdout. Not a
   copied winning D.
9. **Why not random new strategies?** §7 develop-not-abandon and §13:
   licensed axes on `EMA3_13_50_200` are still open (breakout depth, then
   HTF direction, then liquidity). Do not FREEZE this name. Do not start
   funding-carry, spread-capture, or catalog mean-reversion. Shared-losing
   blocks in-class portfolio combination; it does not license FREEZE of
   this name. Do not jump to a new catalog name.
10. **What would confirm or falsify the next hyp?** Pre-registered before
    the run on `EMA3_13_50_200` only. A pass needs mean Train-1 net above
    +91.1483016, initial_sl share down ≥10pp at the best-PnL D, ≥50% of
    this name's big-winner PnL retained (9 / +1131.9561537333418), pooled
    floor strictly below 7/12, and ≥10 trades/series. Any one of (a)–(e)
    fails it. On that card (b) is "every non-thin D removes >50% of
    baseline big-winner PnL", not a flat floor; the floor clause is (d)
    and only at a D that otherwise passes (a)–(c). `number_of_trials = 5`.
    D grid `{0.02, 0.05, 0.10, 0.25, 0.50}` is the licensed shape, not
    another name's winning D. This candle result is not that test.
