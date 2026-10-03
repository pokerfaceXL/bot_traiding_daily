# Coordinator Series Report — H-EMA3-13-50-200-ENTRY-LIQUIDITY-01 (§15)

> **Date:** 2026-10-03 ~23:11 Europe/Warsaw
> **Experiment:** H-EMA3-13-50-200-ENTRY-LIQUIDITY-01
> **Tip:** `3d9d787` (FF on origin/main; git parent harness `c2fac30`; pre-registration Decision `a99a460`). Review PASS job `2026-10-03-f006-ema31350200-entry-liquidity-9a01df13` (engine claude). Coding job `2026-10-03-f006-ema31350200-entry-liquidity-c6583097` DONE. Duplicate `80897b4e` already stopped.
> **Artifacts:** `output/f006_ema3_13_50_200_entry_liquidity/`
> **Card:** `spec/research/F006-hypothesis-ema3-13-50-200-entry-liquidity.md`

## Summary

Liquidity on `EMA3_13_50_200` is **FALSIFIED (a)+(c)+(d)**. Control mean
**+91.1483016** reproduced (max abs diff 0.0, n=423, initial_sl
292/423 = 0.6903073286052009, big winners 9 / +1131.9561537333418, floor
7/12). Gated `liq_med20` mean **+65.550842** (artifact `65.55084200000002`,
delta **−25.5974596**/series), n=327 (32.7/series). Initial_sl share
**rose 2.5289001670028455 pp** (0.6903073286052009 to 0.7155963302752294,
234/327). Big-winner PnL retained **0.787784961973293** (6 / +891.7380355242556),
about 78.8%, so (b) does not fire. Pooled floor stayed 7/12. (d) stays in
the label because this card's own sentence is "pooled losing-month floor
does not improve (stays >= baseline floor)" and "A flat floor falsifies
(d) on this card." (e) does not fire (32.7 trades/series). Status is
**FREEZE** (§4 level C). Not REJECT: the ungated book stays
aggregate-positive. Not a class closure. No next card: every other
catalog5 name is already FREEZE, and the journal leaves the next name as
an owner decision.

## Q1–10

1. **Best strategy now?** None promotable. `EMA3_13_50_200` is now
   **FREEZE**, with `EMA_50_200`, `BB_20_2_EMA200`, `BB_20_25_EMA200`,
   `EMA3_21_50_200`, and `DONCHIAN_55_NO_TRAIL`. No CONDITIONAL catalog
   name remains.
2. **Why that name?** It was the last open catalog5 name, not a promote.
   Its own-trades loop is closed. The screen (mean +91.1483016, n=423,
   0/10 series clear §7) is this name's. `EMA_50_200` liquidity
   (+66.5789284) is not this result.
3. **Edge from many trades or few big wins?** Few big wins. Ungated
   Train-1 entries: 9 trades with net>=29.9 sum to +1131.9561537333418
   against cohort net +771.2836172145886 (n=423). The gate kept 6
   (+891.7380355242556, fraction 0.787784961973293).
4. **Earns when?** Ungated `signal_reverse` runners. Requiring the signal
   bar's base volume to be at least the prior-20 median did not separate
   them from stop-outs: the gated mean fell by 25.5974596/series.
5. **Loses when?** The fixed `initial_sl` (0% WR) is a larger share of the
   gated cohort (0.7155963302752294, 234/327) than of the control
   (0.6903073286052009, 292/423). The pooled floor stays 7/12.
6. **Rejected hypotheses?** Add: **H-EMA3-13-50-200-ENTRY-LIQUIDITY-01 =
   FALSIFIED (a)+(c)+(d)** at `3d9d787`. (b) and (e) did not fire. (d) is
   kept because this card says a flat floor falsifies. Already closed on
   this name: abs-ATR **FALSIFIED (a)+(c)** `46e4509` / Decision `3318658`
   (not (d)); xsym formula **FALSIFIED (b)** `34e2c4a` / Decision
   `396a3c2`; candle **FALSIFIED (a)+(b)+(c)** `9dbcf0d` / Decision
   `079b697`; breakout depth **FALSIFIED (c) only** `c388392` / Decision
   `07fb827`; HTF **FALSIFIED (a)+(c)+(d)** `c70777a` / Decision
   `a99a460`; exit `923de9c` and `3d4edd4`; long-only and breadth
   `f420078`. Other names' liquidity results do not transfer.
7. **Unresolved problem?** §7 monthly regularity, with no licensed axis
   left on this name. In-class portfolio combination stays BLOCKED
   (`dc9818e`). What to test next is an owner decision, not an open axis.
8. **Next experiment and why?** None in this commit. The journal says the
   next name, once this loop is the last open catalog name, is an owner
   decision (§13 non-correlated data, or a revisit of the calendar-green
   goal). No CONDITIONAL catalog name is waiting, and none has an unrun
   entry-axis loop. Do not invent one. Do not pre-register funding-carry,
   spread-capture, or catalog mean-reversion. Do not start a new family.
9. **Why not a random search?** §13: a new family needs a written
   justification the owner has not given. Every licensed axis on every
   catalog5 name is now closed on that name's own trades. Catalog
   mean-reversion is already aggregate-negative on Train-1. Shared-losing
   months block in-class portfolio combination; they do not license this
   FREEZE and they do not license REJECT (ungated Train-1 stays
   aggregate-positive).
10. **What would confirm or falsify the next hyp?** Nothing is
    pre-registered. There is no confirm/refute line until the owner names
    the next hypothesis. Do not import +66.5789284, +72.6693115,
    +97.2455987, or +95.3217987 as that future baseline.
