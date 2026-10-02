# Coordinator Series Report — H-BB-20-25-XSYM-AGREE-SIZING-01 (§15)

> **Date:** 2026-10-03 early (Europe/Warsaw)
> **Experiment:** H-BB-20-25-XSYM-AGREE-SIZING-01
> **Tip / merge:** `1c9ff7e` (FF to origin/main). Review PASS `2026-10-02-f006-bb2025-xsym-agree-sizing-re-ca2e09d0`.
> **Artifacts:** `output/f006_bb_20_25_xsym_agree_sizing/`
> **Card:** `spec/research/F006-hypothesis-bb-20-25-xsym-agree-sizing.md`

## Summary

Causal cross-symbol agreement sizing on `BB_20_25_EMA200` is **NOT FALSIFIED** on Train-1.
The first FALSIFIED (b) claim (floor 11/12) is withdrawn: that floor was a union of any-series
losing months, and the stake looked ahead one bar. After the fix, fill bar i uses agreement
from closed bar i-1. Control +82.90 / floor 7/12 / n=512; sized +147.71 / floor 5/12 /
mult gap +0.119 / stake_cv 0.526. Decision = **REFINE**. Status stays **CONDITIONAL**.
Do not FREEZE. Next = Validation-1 of the same frozen formula.

## Q1–10

1. **Best strategy now?** None promotable. `BB_20_25_EMA200` stays the highest-priority CONDITIONAL name. This run did not clear §7.
2. **Why best?** Unchanged screen, plus a Train-1 sizing pass that raised mean PnL and cut the pooled entry-month floor from 7/12 to 5/12 without dropping trades. Not validated.
3. **Edge from many trades or few big wins?** Few big wins. Baseline 10 trades with net>=29.9 sum to +968; the sized arm pays +1469 on those same entry keys.
4. **Earns when?** Queue-bar agreement is higher on winners than losers (pooled gap +0.119). November 2024 still dominates the pooled path.
5. **Loses when?** Five of twelve Train-1 entry-months stay negative after sizing. Two series floors worsen. Shared basket regime is not gone.
6. **Rejected hypotheses?** Entry-vol `H-BB-20-25-ABS-ATR-ENTRY-GATE-01` remains FALSIFIED (a), tip `3788f11`. This sizing formula is not rejected. Exit, direction, and breadth stay closed on this name's own-trade evidence.
7. **Unresolved problem?** Monthly regularity (floor still 5/12; 0/10 series clear §7) and the fact that the sizing pass is Train-1 only.
8. **Next experiment and why?** `H-BB-20-25-XSYM-AGREE-SIZING-VAL1-01`. §11 requires chronological validation of the one formula that passed before a new axis, another name, or FREEZE. Holdout stays closed.
9. **Why not random new strategies?** One frozen formula, already specified. A new entry structure or §13 would multiply trials before the pass is checked out of sample.
10. **What would confirm or falsify the next hyp?** On Validation-1 entries only (2025-03-01 <= entry < 2025-06-01): falsify if sized mean <= control, or the 3-month losing count is worse than control, or the pooled mult gap <= 0, or n_trades breaks, or stake_cv <= 0.05. Otherwise the formula survives Validation-1 and stays CONDITIONAL pending later windows. Do not open holdout.
