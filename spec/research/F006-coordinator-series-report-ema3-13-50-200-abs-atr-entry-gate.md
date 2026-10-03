# Coordinator Series Report — H-EMA3-13-50-200-ABS-ATR-ENTRY-GATE-01 (§15)

> **Date:** 2026-10-03 ~20:10 Europe/Warsaw
> **Experiment:** H-EMA3-13-50-200-ABS-ATR-ENTRY-GATE-01
> **Tip / merge:** `46e4509` (FF to origin/main; parent `d74c5dd`). Review PASS job
> `2026-10-03-f006-ema31350200-abs-atr-01-revi-850be7e5` (engine claude).
> **Artifacts:** `output/f006_ema3_13_50_200_abs_atr_gate/`
> **Card:** `spec/research/F006-hypothesis-ema3-13-50-200-abs-atr-entry-gate.md`

## Summary

Abs-ATR entry keep-gate on `EMA3_13_50_200` **FALSIFIED (a)+(c)**. (d) is not
reachable and is not in the label. Control mean **+91.1483016** reproduced
from this experiment's artifacts (identical to catalog5). Best T=t_2_0 mean
**+83.4087526** (delta **−7.739549**/series). Initial-SL drop at that T is
**4.04557 pp** (<10 pp). Floor stays **7/12**; that is informational only.
Status stays **CONDITIONAL**. Do not FREEZE. This is the first closed
own-trades axis on this name in this loop. Entry-vol is closed here only.
Next = `H-EMA3-13-50-200-XSYM-AGREE-SIZING-01` on this name's own reproduced
baseline +91.1483016. Do not copy +72.6693115, +95.3217987, or +126.744211.

## Q1–10

1. **Best strategy now?** None promotable. `EMA_50_200`, `BB_20_2_EMA200`,
   `BB_20_25_EMA200`, `EMA3_21_50_200`, and `DONCHIAN_55_NO_TRAIL` stay
   **FREEZE**. Highest-priority unfinished name is `EMA3_13_50_200`
   (**CONDITIONAL**).
2. **Why that name?** It is the catalog5 name whose own-trades loop just
   opened. This gate did not improve it. The screen (mean +91.1483016 from
   this run's reproduced control, 6/10 series positive, 0/10 clear §7) is
   this name's, not a transferred `EMA_50_200` or BB figure. The
   `EMA_50_200` FREEZE is not evidence here.
3. **Edge from many trades or few big wins?** Few big wins. Ungated Train-1
   entries: 9 trades with net≥29.9 sum to +1131.9561537333418 against cohort
   net +771.2836172145886 (n=423). Autopsy: 3 of 423 trades sum to the full
   pooled entry net.
4. **Earns when?** `signal_reverse` exits (122/423). Many of those runners sit
   at lower entry ATR% than stop-outs (autopsy 1.0993 vs 1.7666), but a causal
   keep-low-ATR gate still removes them faster than it removes losses on the
   mean-PnL metric (best gated mean +83.4087526 < +91.1483016). t_2_0 keeps
   85.1% of big-winner PnL and still loses 7.739549/series.
5. **Loses when?** `initial_sl` (292/423, 69.03%, 0% WR) and the shared basket
   regime. Control entry-month floor is 7/12. No gated cell improves that
   count; t_1_0 swaps 2025-01 for 2024-11 and is still 7/12. Shared-losing
   (H-CATALOG5-SHARED-LOSING-MONTHS-01) still stands. The flat floor does not
   fire (d): no T passes (a)–(c).
6. **Rejected hypotheses?** Add: **H-EMA3-13-50-200-ABS-ATR-ENTRY-GATE-01 =
   FALSIFIED (a)+(c)** at `46e4509`. (b) did not fire. (d) was not reachable.
   (e) did not fire. Already closed on this name: exit-class, partial-exit,
   long-only, breadth. Not closed here: position sizing, other §8 entry
   structure. `EMA_50_200` / BB closures do not transfer.
7. **Unresolved problem?** §7 monthly regularity on this name, without cutting
   the runners. Entry-vol cannot separate stops from runners here on the
   pre-registered checks. Sizing and non-ATR entry structure are still
   untested on these trades.
8. **Next experiment and why?** **H-EMA3-13-50-200-XSYM-AGREE-SIZING-01.**
   Sizing is the next open axis on this profile (the `EMA_50_200` order after
   abs-ATR is a sequencing hint; the profile lists sizing as open and still
   untested). §8 allows it because the ungated signal is aggregate-positive
   (+91.1483016/series). Cross-symbol agreement reweights stake and keeps
   every trade, so it is not another abs-ATR gate. The map
   `0.5 + 0.375 * n_agree` is the structural [0.5, 2.0] band on n_agree 0..4
   for this name's own signal — rewrite every threshold; do not inherit
   `EMA_50_200`'s +126.744211 or any BB pass/fail. If sizing fails, candle
   confirm is the following open axis, and the name stays CONDITIONAL.
9. **Why not random new strategies?** §7 develop-not-abandon and §13: licensed
   axes on `EMA3_13_50_200` are still open. Do not FREEZE this name. Do not
   start funding-carry, spread-capture, or catalog mean-reversion. Shared-losing
   blocks in-class portfolio combination; it does not license FREEZE of this
   name.
10. **What would confirm or falsify the next hyp?** Pre-registered before the
    run on `EMA3_13_50_200` only. A pass needs this name's own mean Train-1 net
    above the reproduced control +91.1483016, a strictly lower pooled
    losing-month floor, mean(mult|winner) > mean(mult|loser), n_trades
    invariant, and stake_cv > 0.05. Any one of (a)–(e) fails it. A flat floor
    falsifies (b) on that card and closes the formula with no validation
    window. `number_of_trials = 1`. This abs-ATR result is not that test.
