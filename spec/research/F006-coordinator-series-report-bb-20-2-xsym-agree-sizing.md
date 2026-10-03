# Coordinator Series Report — H-BB-20-2-XSYM-AGREE-SIZING-01 (§15)

> **Date:** 2026-10-03 ~11:57 Europe/Warsaw
> **Experiment:** H-BB-20-2-XSYM-AGREE-SIZING-01
> **Tip / merge:** `1774a8a` (review PASS `2026-10-03-f006-bb202-xsym-agree-sizing-rev-dff7bccd`, FF to origin/main)
> **Artifacts:** `output/f006_bb_20_2_xsym_agree_sizing/` (`summary/cell_summary.json`)
> **Card:** `spec/research/F006-hypothesis-bb-20-2-xsym-agree-sizing.md`

## Summary

Train-1 xsym-agree sizing on `BB_20_2_EMA200` own trades is **NOT FALSIFIED**.
`decision_if_pass` is **REFINE**. Control mean +95.3217987 reproduced (max abs
diff 0). Sized mean +146.632696. Pooled entry-month floor 7/12 → 6/12. Mult
gap +0.086642. n_trades invariant (820 / 756). stake_cv 0.491784. (a)–(e)
clear. This is not the `BB_20_25_EMA200` Val-1 verdict and not a promotion.
Status stays **CONDITIONAL**. Do not FREEZE. Holdout stays closed. Next =
`H-BB-20-2-XSYM-AGREE-SIZING-VAL1-01` (same frozen formula).

Caveats, not extra falsifiers: floor flip is one month (2024-06, −8.94 →
+8.74). Of the +452.92 Train-1-entry net gain, +497.75 is 2024-11 (~110%);
the other 11 months sum −44.83. The gap is small and negative on
DOGEUSDT/240 and XRPUSDT/60.

## Q1–10

1. **Best strategy now?** None promotable. `BB_20_25_EMA200`, `EMA3_21_50_200`, and `DONCHIAN_55_NO_TRAIL` stay **FREEZE**. Active CONDITIONAL name is `BB_20_2_EMA200`, then `EMA_50_200`, then `EMA3_13_50_200`.
2. **Why that name?** Its own-trades loop is the one in progress. Entry-vol is FALSIFIED here (`f7ac677`). This sizing arm passed Train-1 on these trades (`1774a8a`) and is not yet validated. The screen is this name's (+95.32 control, 8/10 series), not a transferred BB_20_25 figure.
3. **Edge from many trades or few big wins?** Few big wins. Ungated tail is 12 trades / +1251.654084 against cohort net +834.35 (n=756). The same 12 keys are +1581.53 under sizing. Sized blotter has 15 trades / +1761.85 at net≥29.9. About 110% of the entry-net gain is 2024-11.
4. **Earns when?** `signal_reverse` runners, and on this Train-1 window when stake is scaled up on the November basket. Agreement raised winner mult only slightly (1.084 vs 0.998).
5. **Loses when?** Shared basket regime and `initial_sl`. Control floor 7/12; sized floor 6/12. 2024-06 is the only sign flip. Several losing months got worse in magnitude (2024-03, 2024-08).
6. **Rejected hypotheses?** On this name: entry-vol **FALSIFIED (a)+(c)** `f7ac677`; exit, long-only, and breadth already closed. This sizing formula is **not** rejected. On `BB_20_25_EMA200` only, the same shape failed Val-1 (`89e936a`). That does not close this name's formula and does not close entry or sizing on `EMA_50_200` or `EMA3_13_50_200`.
7. **Unresolved problem?** Whether the Train-1 stake weights generalize. Monthly regularity is not solved (6/12, one-month flip, November concentration). §11 says a Train-1 pass is not enough. In-class portfolio combination stays BLOCKED.
8. **Next experiment and why?** `H-BB-20-2-XSYM-AGREE-SIZING-VAL1-01`. §3.10 and §11 require an independent chronological check of a promising Train-1 arm before another axis. §7 says do not abandon this passed sizing arm for a new entry axis before that check. Same frozen formula. Not an abs-ATR retune. Not FREEZE. Not holdout.
9. **Why not a random search?** §7 develop-not-abandon. One licensed axis on this name has a Train-1 pass and no validation. Do not jump to `EMA_50_200` or `EMA3_13_50_200`. Do not open a new entry gate in parallel.
10. **What result confirms or falsifies the next hypothesis?** On the Val-1 card, scored only on this name's entries with 2025-03-01 ≤ entry < 2025-06-01. Control Train-1 slice of the longer run must sit within relative 0.25% of |+95.3217987| and Train-1-entry n=756 exactly; absolute 1e-6 is not the gate. Pass: sized mean above that window's own control, losing-month count not higher, mult gap > 0, n_trades invariant, stake_cv > 0.05. Any one of (a)–(e) fails it. Holdout is not opened.
