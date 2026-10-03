# Coordinator Series Report — H-BB-20-2-XSYM-AGREE-SIZING-VAL2-01 (§15)

> **Date:** 2026-10-03 ~13:13 Europe/Warsaw
> **Experiment:** H-BB-20-2-XSYM-AGREE-SIZING-VAL2-01
> **Tip / merge:** `7798bbb` (Claude review PASS `2026-10-03-f006-bb202-xsym-agree-sizing-val-c1c25e2f`, FF to origin/main from `1eced44`)
> **Artifacts:** `output/f006_bb_20_2_xsym_agree_sizing_val2/` (`summary/cell_summary.json`)
> **Card:** `spec/research/F006-hypothesis-bb-20-2-xsym-agree-sizing-val2.md`

## Summary

Validation-2 of the frozen xsym-agree stake on `BB_20_2_EMA200` own trades is
**NOT FALSIFIED**. `decision_if_pass` is stay **CONDITIONAL** and continue to
Validation-3 of the same formula (F005 §3.2: 2025-09-01 ≤ entry < 2025-12-01).
Not holdout. Not FREEZE. No pre-registered margin floor. Gate PASS: Train-1
mean 95.463371 vs reference 95.3217987 (diff 0.141572 ≤ allowance
0.23830449675), n=756. Sized mean +2.551244 > control +2.331879. Losing
months 2≤2. Mult gap +0.031667. n 195/1226 invariant. stake_cv 0.514115
(series min 0.428358). (a)–(e) clear. `BB_20_25_EMA200` stays FREEZE on its
own loop; that result is not copied. Next =
`H-BB-20-2-XSYM-AGREE-SIZING-VAL3-01`.

Caveats, not extra falsifiers: margin +0.219365 per series (+2.193652 on
195 entries). 5/10 series improve; per-series gap negative on 5/10. The
entry-net difference is 2025-07 only (+12.112764; June −9.345914, August
−0.573199). ETH 60 (+48.829580) exceeds the pooled gain. Both means are
near zero. Result's "seven" `end_of_data` exits is six in `results.csv`;
that count is not a falsifier.

## Q1–10

1. **Best strategy now?** None promotable. `BB_20_25_EMA200`, `EMA3_21_50_200`, and `DONCHIAN_55_NO_TRAIL` stay **FREEZE**. Active CONDITIONAL name is `BB_20_2_EMA200`, then `EMA_50_200`, then `EMA3_13_50_200`.
2. **Why that name?** Own-trades loop in progress. The frozen sizing arm cleared Train-1, Validation-1, and Validation-2 here and is not finished under §11. Screen is this name's, not a BB_20_25 transfer.
3. **Edge from many trades or few big wins?** Few big wins, and on this window the sized edge is thin. Control big winners at net≥29.9: 4 trades, sum 199.523967. Sized: 3 trades, sum 161.542970 (168.273303 on the control keys). The whole entry-net gain is 2025-07, and ETH 60 alone exceeds the pooled gain.
4. **Earns when?** `signal_reverse` runners, and on this window when stake scaled the 2025-07 basket. Winner mult only slightly above loser mult (1.0666666666666667 vs 1.035, gap +0.031667).
5. **Loses when?** Both arms are near zero on the Validation-2 mean (control +2.331879, sized +2.551244). Sized lost more than control in 2025-06 and 2025-08. Shared basket regime and `initial_sl` are unchanged. Losing-month count did not rise (2≤2) but did not fall.
6. **Rejected hypotheses?** Entry-vol **FALSIFIED (a)+(c)** `f7ac677`. Exit, long-only, breadth closed. This sizing formula is not rejected. BB_20_25 closures, including its Val-1 `89e936a` and its FREEZE, do not transfer.
7. **Unresolved problem?** Whether the weights keep helping on the next chronological window. Monthly regularity is not solved. The Validation-2 margin is thin and one-month concentrated. §11 validation is not complete. In-class portfolio combination stays BLOCKED.
8. **Next experiment & why?** `H-BB-20-2-XSYM-AGREE-SIZING-VAL3-01`. The Val-2 card's `decision_if_pass` names Validation-3 of the same formula, not holdout and not a stop. Protocol §3.10 and §11: a promising arm gets the next frozen validation window before another axis. §7: do not abandon it for a new entry axis first. Window is F005 §3.2 Validation 3 (2025-09-01 ≤ entry < 2025-12-01). Not FREEZE. Not holdout.
9. **Why not a random search?** One licensed axis on this name has Train-1, Validation-1, and Validation-2 passes and an unused protocol window named by the card. Do not jump to `EMA_50_200` or `EMA3_13_50_200`. Do not open a new entry gate in parallel.
10. **What result confirms/refutes the next hypothesis?** On the Val-3 card. Control gate: relative 0.25% of |+95.3217987| and Train-1-entry n=756 exact, before any Validation-3 scoring. Pass: sized mean above that window's own control, losing-month count not higher, mult gap > 0, n invariant, stake_cv > 0.05. Any of (a)–(e) fails it. Falsifiers are not loosened. A thin margin is not a new falsifier unless the card says so. Holdout is not opened.
