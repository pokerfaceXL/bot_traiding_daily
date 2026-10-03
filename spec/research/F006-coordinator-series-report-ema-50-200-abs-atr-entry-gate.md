# Coordinator Series Report — H-EMA-50-200-ABS-ATR-ENTRY-GATE-01 (§15)

> **Date:** 2026-10-03 ~16:47 Europe/Warsaw
> **Experiment:** H-EMA-50-200-ABS-ATR-ENTRY-GATE-01
> **Tip / merge:** `80e7fa6` (FF to origin/main; parent `5fdd5a8`). Review PASS job
> `2026-10-03-f006-ema50200-abs-atr-01-review-b2995d9a` (engine claude).
> **Artifacts:** `output/f006_ema_50_200_abs_atr_gate/`
> **Card:** `spec/research/F006-hypothesis-ema-50-200-abs-atr-entry-gate.md`

## Summary

Abs-ATR entry keep-gate on `EMA_50_200` **FALSIFIED (a)+(c)**. Control mean
**+72.6693115** reproduced from this experiment's artifacts (identical to
catalog5). Best T=t_2_0 mean **+64.4604139**. Initial-SL drop at that T is
**6.73pp** (<10pp). Status stays **CONDITIONAL**. Do not FREEZE. This is the
first closed own-trades axis on this name in this loop. Entry-vol is closed
here only. Next = `H-EMA-50-200-XSYM-AGREE-SIZING-01` on this name's own
reproduced baseline +72.6693115. Do not copy +95.3217987 or +82.900262.

## Q1–10

1. **Best strategy now?** None promotable. `BB_20_2_EMA200`, `BB_20_25_EMA200`,
   `EMA3_21_50_200`, and `DONCHIAN_55_NO_TRAIL` stay **FREEZE**. Highest-priority
   unfinished name is still `EMA_50_200` (**CONDITIONAL**), then `EMA3_13_50_200`.
2. **Why that name?** It is the catalog5 name whose own-trades loop just opened.
   This gate did not improve it. The screen (mean +72.6693115 from this run's
   reproduced control, 7/10 series positive, 0/10 clear §7) is this name's, not
   a transferred BB figure.
3. **Edge from many trades or few big wins?** Few big wins. Ungated Train-1
   entries: 5 trades with net≥29.9 sum to +843.7639016181568 against cohort net
   +587.3851786486205 (n=330). Autopsy: 2 of 330 trades sum to the full pooled
   entry net.
4. **Earns when?** `signal_reverse` exits (112/330). Many of those runners sit at
   lower entry ATR% than stop-outs (autopsy 1.06 vs 1.75), but a causal
   keep-low-ATR gate still removes them faster than it removes losses on the
   mean-PnL metric (best gated mean +64.46 < +72.67).
5. **Loses when?** `initial_sl` (213/330, 64.55%, 0% WR) and the shared basket
   regime. Control entry-month floor is 7/12. No gated cell improves it; t_1_0
   worsens to 8/12. Shared-losing (H-CATALOG5-SHARED-LOSING-MONTHS-01) still
   stands.
6. **Rejected hypotheses?** Add: **H-EMA-50-200-ABS-ATR-ENTRY-GATE-01 =
   FALSIFIED (a)+(c)** at `80e7fa6`. (b) did not fire. (d) was not reachable.
   (e) did not fire. Already closed on this name: exit-class, partial-exit,
   long-only, breadth. Not closed here: position sizing, other §8 entry
   structure. BB_20_2 / BB_20_25 closures do not transfer.
7. **Unresolved problem?** §7 monthly regularity on this name, without cutting
   the runners. Entry-vol cannot separate stops from runners here on the
   pre-registered checks. Sizing and non-ATR entry structure are still
   untested on these trades.
8. **Next experiment and why?** **H-EMA-50-200-XSYM-AGREE-SIZING-01.** Sizing
   is the next open axis on the profile (BB_20_2 loop order after abs-ATR is a
   sequencing hint; the profile lists sizing as open). §8 allows it because
   the ungated signal is aggregate-positive. Cross-symbol agreement reweights
   stake and keeps every trade, so it is not another abs-ATR gate. The map
   `0.5 + 0.375 * n_agree` is the structural [0.5, 2.0] band on n_agree 0..4
   for this name's own signal — rewrite every threshold; do not inherit a
   BB pass/fail. If sizing fails, candle confirm is the following open axis.
9. **Why not random new strategies?** §7 develop-not-abandon and §13: licensed
   axes on `EMA_50_200` are still open. Do not start `EMA3_13_50_200`. Do not
   start funding-carry or spread-capture (owner parked). Do not retest catalog
   mean-reversion. Shared-losing blocks in-class portfolio combination; it does
   not license FREEZE of this name.
10. **What would confirm or falsify the next hyp?** Pre-registered before the
    run on `EMA_50_200` only. A pass needs this name's own mean Train-1 net
    above the reproduced control +72.6693115, a strictly lower pooled
    losing-month floor, mean(mult|winner) > mean(mult|loser), n_trades
    invariant, and stake_cv > 0.05. Any one of (a)–(e) fails it.
    `number_of_trials = 1`. This abs-ATR result is not that test.
