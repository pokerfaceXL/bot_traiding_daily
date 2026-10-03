# Coordinator Series Report — H-BB-20-2-XSYM-AGREE-SIZING-VAL3-01 (§15)

> **Date:** 2026-10-03 ~13:40 Europe/Warsaw
> **Experiment:** H-BB-20-2-XSYM-AGREE-SIZING-VAL3-01
> **Tip / merge:** `cf00663` (Claude review PASS `2026-10-03-f006-bb202-xsym-agree-sizing-val-607c9de9`, FF to origin/main from `7144b8f`)
> **Artifacts:** `output/f006_bb_20_2_xsym_agree_sizing_val3/` (`summary/cell_summary.json`)
> **Card:** `spec/research/F006-hypothesis-bb-20-2-xsym-agree-sizing-val3.md`

## Summary

Validation-3 of the frozen xsym-agree stake on `BB_20_2_EMA200` own trades is
**NOT FALSIFIED**. `decision_if_pass` is stay **CONDITIONAL** and continue to
Validation-4 of the same formula (F005 §3.2: 2025-12-01 ≤ entry < 2026-03-01).
Not holdout. Not FREEZE. No pre-registered margin floor. Gate PASS: Train-1
mean 95.463371 vs reference 95.3217987 (diff 0.141572 ≤ allowance
0.23830449675), n=756. Sized mean +8.007368 > control +1.772572. Losing
months 2≤2. Mult gap +0.179831. n 181/1407 invariant. stake_cv 0.455172
(series min 0.301511). (a)–(e) clear. `BB_20_25_EMA200` stays FREEZE on its
own loop; that result is not copied. Next =
`H-BB-20-2-XSYM-AGREE-SIZING-VAL4-01`.

Caveats, not extra falsifiers: means are thin (control +1.772572, sized
+8.007368). 6/10 series improve; per-series gap is negative on ETH/XRP/DOGE
240 and zero on BTC 240. Entry-net difference is 2025-09 −11.868494,
2025-10 +57.076733, 2025-11 +17.139716, so most of the gain is 2025-10 and
2025-09 is worse under sizing. `n_val3_end_of_data_exits` sums to 7.
Review note, not a falsifier: per-series Validation-3 metrics in the script
are computed before the gate call; publication stayed gated and the
independent replay matched.

## Q1–10

1. **Best strategy now?** None promotable. `BB_20_25_EMA200`, `EMA3_21_50_200`, and `DONCHIAN_55_NO_TRAIL` stay **FREEZE**. Active CONDITIONAL name is `BB_20_2_EMA200`, then `EMA_50_200`, then `EMA3_13_50_200`.
2. **Why that name?** Own-trades loop in progress. The frozen sizing arm cleared Train-1, Validation-1, Validation-2, and Validation-3 here and is not finished under §11. Screen is this name's, not a BB_20_25 transfer.
3. **Edge from many trades or few big wins?** Few big wins, and on this window the gain is one month. Control big winners at net≥29.9: 1 trade, sum 38.364839. Sized: 3 trades, sum 148.010545 (62.342863 on the control keys). Most of the entry-net gain is 2025-10 (+57.076733).
4. **Earns when?** `signal_reverse` runners, and on this window when stake scaled the 2025-10 basket. Winner mult above loser mult (1.2826086956521738 vs 1.1027777777777779, gap +0.179831).
5. **Loses when?** Both arms are small on the Validation-3 mean (control +1.772572, sized +8.007368). Sized lost more than control in 2025-09 (−11.868494). Shared basket regime and `initial_sl` are unchanged. Losing-month count did not rise (2≤2) but did not fall. 4/10 series do not improve.
6. **Rejected hypotheses?** Entry-vol **FALSIFIED (a)+(c)** `f7ac677`. Exit, long-only, breadth closed. This sizing formula is not rejected. BB_20_25 closures, including its Val-1 `89e936a` and its FREEZE, do not transfer.
7. **Unresolved problem?** Whether the weights keep helping on Validation-4. Monthly regularity is not solved. The Validation-3 gain is thin on the mean, 6/10 series, and concentrated in 2025-10, with 2025-09 worse under sizing. Seven positions are force-closed at the 2025-12-01 cut. §11 validation is not complete. In-class portfolio combination stays BLOCKED.
8. **Next experiment & why?** `H-BB-20-2-XSYM-AGREE-SIZING-VAL4-01`. The Val-3 card's `decision_if_pass` names Validation-4 of the same formula, not holdout and not a stop. Protocol §3.10 and §11: a promising arm gets the next frozen validation window before another axis. §7: do not abandon it for a new entry axis first. Window is F005 §3.2 Validation 4 (2025-12-01 ≤ entry < 2026-03-01). Not FREEZE. Not holdout.
9. **Why not a random search?** One licensed axis on this name has Train-1 through Validation-3 passes and an unused protocol window named by the card. Do not jump to `EMA_50_200` or `EMA3_13_50_200`. Do not open a new entry gate in parallel. Do not open holdout (§11: holdout only after a freeze, and this pass does not FREEZE).
10. **What result confirms/refutes the next hypothesis?** On the Val-4 card. Control gate: relative 0.25% of |+95.3217987| and Train-1-entry n=756 exact, before any Validation-4 scoring. Pass: sized mean above that window's own control, losing-month count not higher, mult gap > 0, n invariant, stake_cv > 0.05. Any of (a)–(e) fails it. Falsifiers are not loosened. A thin margin or one-month concentration is not a new falsifier unless the card says so. Holdout is not opened.
