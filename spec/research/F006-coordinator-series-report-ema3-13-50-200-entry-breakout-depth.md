# Coordinator Series Report — H-EMA3-13-50-200-ENTRY-BREAKOUT-DEPTH-01 (§15)

> **Date:** 2026-10-03 ~21:42 Europe/Warsaw
> **Experiment:** H-EMA3-13-50-200-ENTRY-BREAKOUT-DEPTH-01
> **Tip / merge:** `c388392` (FF to origin/main; parent of this Decision). Review PASS job
> `2026-10-03-f006-ema31350200-entry-breakout--c183b475` (engine claude). Coding tip job `727375aa`. Duplicate `0e32cf89` stopped.
> **Artifacts:** `output/f006_ema3_13_50_200_entry_breakout_depth/`
> **Card:** `spec/research/F006-hypothesis-ema3-13-50-200-entry-breakout-depth.md`

## Summary

Breakout depth on `EMA3_13_50_200` **FALSIFIED (c) only**. Control mean
**+91.1483016** reproduced (max abs diff 0.0, n=423, initial_sl 292/423,
big winners 9 / +1131.9561537333418, floor 7/12). Best D=0.02 mean
**+94.4530527** (delta **+3.3047511**/series), n=322 (32.2/series).
Initial_sl share **rose 7.987900679852578 pp** (0.6903073286052009 to
0.7701863354037267, 248/322). Big-winner PnL retained
**0.894213522771771** (6 / +1012.2104998530759), so about 10.58% was
removed, not >50%. (a) does not fire because the mean rose. (b) does not
fire because not every non-thin D removes >50%. (c) fires because the
best-PnL D did not cut initial_sl share by ≥10pp. (d) is unreachable: no D
passes (a)-(c), even though the D=0.02 floor stayed 7/12. (e) does not
fire: the only D above control is not thin. Status stays **CONDITIONAL**.
Do not FREEZE. Not REJECT (ungated Train-1 book stays aggregate-positive).
Next = `H-EMA3-13-50-200-HTF-DIRECTION-01` on this name's reproduced
baseline +91.1483016 / n=423. This is not the `EMA_50_200` depth result
(that mean fell). Do not import +63.0343180 or +72.6693115.

## Q1–10

1. **Best strategy now?** None promotable. `EMA_50_200`, `BB_20_2_EMA200`,
   `BB_20_25_EMA200`, `EMA3_21_50_200`, and `DONCHIAN_55_NO_TRAIL` stay
   **FREEZE**. The only unfinished catalog5 name is `EMA3_13_50_200`
   (**CONDITIONAL**).
2. **Why that name?** Its own-trades loop is still open. Breakout depth
   raised the mean a little and kept most big-winner PnL, but it raised the
   stop-out share, so that axis is closed and the name is not. The screen
   (mean +91.1483016, n=423, 0/10 clear §7) is this name's. `EMA_50_200`
   FREEZE is not evidence here.
3. **Edge from many trades or few big wins?** Few big wins. Ungated Train-1
   entries: 9 trades with net≥29.9 sum to +1131.9561537333418 against cohort
   net +771.2836172145886 (n=423). Best D kept 6 of those trades
   (+1012.2104998530759, fraction 0.894213522771771).
4. **Earns when?** Ungated `signal_reverse` runners. Requiring the close to
   sit further beyond same-timeframe ema200 did not separate them from
   stop-outs. D=0.02's mean lift is +3.3047511/series and comes with a
   higher initial_sl share.
5. **Loses when?** The fixed `initial_sl` (0% WR) is a larger share of the
   best-D cohort (77.01863354037267%, 248/322) than of the control
   (69.03073286052009%, 292/423). Deeper D cells are thin or worse
   (D=0.05 mean −9.9990654, n=159; D=0.10 is thin at 4.8/series). The
   pooled floor at D=0.02 stays 7/12.
6. **Rejected hypotheses?** Add: **H-EMA3-13-50-200-ENTRY-BREAKOUT-DEPTH-01
   = FALSIFIED (c)** at `c388392`. (a)(b)(e) did not fire. (d) not
   reachable. Already closed on this name: abs-ATR **FALSIFIED (a)+(c)**
   `46e4509` / Decision `3318658` ((d) not reachable), xsym-agree formula
   **FALSIFIED (b)** `34e2c4a` / Decision `396a3c2` (flat floor, no Val),
   candle confirm **FALSIFIED (a)+(b)+(c)** `9dbcf0d` / Decision `079b697`,
   exit-class, partial-exit, long-only, breadth. Not closed here: HTF
   direction, then liquidity. Other names' depth results do not transfer.
   `EMA_50_200` depth mean fell; this name's best-D mean rose.
7. **Unresolved problem?** §7 monthly regularity on this name. Distance of
   the close beyond ema200 did not cut stop-outs. Whether the prior closed
   higher-timeframe candle agrees with the signal is still untested on
   these trades.
8. **Next experiment and why?** **H-EMA3-13-50-200-HTF-DIRECTION-01.**
   The depth card's decision_if_fail names HTF direction. One §8 change,
   Train-1, this name's control +91.1483016 / n=423. Not a depth retune.
   Not a candle retune. Not FREEZE. Not holdout. Not another name's
   measured htf_4 mean. Liquidity stays open after this axis.
9. **Why not random new strategies?** §7 develop-not-abandon and §13:
   licensed axes on `EMA3_13_50_200` still open are HTF direction, then
   liquidity. Do not FREEZE this name. Do not start funding-carry,
   spread-capture, catalog mean-reversion, a new family, or another catalog
   name. Shared-losing blocks in-class portfolio combination; it does not
   license FREEZE or REJECT of this name (ungated Train-1 stays
   aggregate-positive, §4 level C only later, at a falsified liquidity
   Decision that cites every licensed axis on these trades).
10. **What would confirm or falsify the next hyp?** Pre-registered before
    the run on `EMA3_13_50_200` only. Binary prior-closed 4-bar HTF gate,
    `number_of_trials = 1`. A pass needs mean Train-1 net above
    +91.1483016, initial_sl share down ≥10pp, ≥50% of this name's
    big-winner PnL retained (9 / +1131.9561537333418), pooled floor
    strictly below 7/12, and ≥10 trades/series. Any one of (a)–(e) fails
    it. On that card (d) is the standalone sentence "pooled losing-month
    floor does not improve (stays >= baseline floor)", unlike this depth
    card where (d) was unreachable. Do not import +20.7369913.
