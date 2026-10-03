# Coordinator Series Report — H-BB-20-25-XSYM-AGREE-SIZING-VAL1-01 (§15)

> **Date:** 2026-10-03 morning (Europe/Warsaw)
> **Experiment:** H-BB-20-25-XSYM-AGREE-SIZING-VAL1-01
> **Tip / merge:** `89e936a` (FF to origin/main). Gate-stop review PASS `d255f0e` (`d8413e48`). Rescore review PASS `89e936a` (`9a56d56a`).
> **Artifacts:** `output/f006_bb_20_25_xsym_agree_sizing_val1/`
> **Card:** `spec/research/F006-hypothesis-bb-20-25-xsym-agree-sizing-val1.md`

## Summary

Validation-1 of the frozen causal xsym-agree stake on `BB_20_25_EMA200` is **FALSIFIED (c)**.
The Train-1 sanity stop (mean 83.048644 vs 82.900262, n=512) was the short-run
`end_of_data` force-close inside the 2025-02 bucket on 240m only. Before scoring,
that absolute 1e-6 gate was relaxed to relative 0.25% of |reference mean|
(n=512 exact). Falsifiers were not changed. On Validation-1 entries the sized mean
(-0.40) beat control (-1.37) and the 2/3 losing-month count did not worsen, but the
pooled winner-minus-loser multiplier gap was **-0.026**. The formula is closed on
this name. Status stays **CONDITIONAL**. Do not FREEZE. Holdout stays closed.

## Q1–10

1. **Best strategy now?** None promotable. `BB_20_25_EMA200` stays the highest-priority CONDITIONAL name. This run did not clear §7 or §11.
2. **Why best?** Unchanged screen. The Train-1 sizing pass did not survive the next window.
3. **Edge from many trades or few big wins?** Still a few big wins. Validation-1 has 2 trades with net>=29.9 (control sum +65; sized +106 on the same keys). The sized mean is less negative only because those runners were scaled up.
4. **Earns when?** Not on Validation-1 agreement. Train-1 had a positive mult gap (+0.119); this window reversed it.
5. **Loses when?** 2025-03 and 2025-04 are losing for both arms. Sized April is worse (-91 vs -54). Losers received the higher average stake (mult 1.033 vs 1.007).
6. **Rejected hypotheses?** Entry-vol `H-BB-20-25-ABS-ATR-ENTRY-GATE-01` remains FALSIFIED (a), tip `3788f11`. This sizing formula is now FALSIFIED (c) on Validation-1. Exit, direction, and breadth stay closed on this name.
7. **Unresolved problem?** Monthly regularity, and whether any entry-time structure (not stake) can separate `initial_sl` deaths from runners without being another volatility proxy. Sizing did not.
8. **Next experiment and why?** One not-yet-run §8 entry-structure hypothesis on this same name, written before it is run. Not Validation-2 of this formula, not another catalog name, not FREEZE, not holdout. Not spawned in this endgame.
9. **Why not random new strategies?** §13 is not met. One axis closed (this formula). The next test is the smallest remaining entry change on the same name, after a written mechanism.
10. **What would confirm or falsify the next hyp?** It is not pre-registered yet. It must name one entry change, a Train-1 falsifier written before the run, and must not retune this stake formula.
