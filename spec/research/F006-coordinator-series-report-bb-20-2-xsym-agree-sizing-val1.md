# Coordinator Series Report — H-BB-20-2-XSYM-AGREE-SIZING-VAL1-01 (§15)

> **Date:** 2026-10-03 ~12:35 Europe/Warsaw
> **Experiment:** H-BB-20-2-XSYM-AGREE-SIZING-VAL1-01
> **Tip / merge:** `7e18786` (Claude review PASS `2026-10-03-f006-bb202-xsym-agree-sizing-val-ab5c3864`, FF to origin/main from `738b9ff`)
> **Artifacts:** `output/f006_bb_20_2_xsym_agree_sizing_val1/` (`summary/cell_summary.json`)
> **Card:** `spec/research/F006-hypothesis-bb-20-2-xsym-agree-sizing-val1.md`

## Summary

Validation-1 of the frozen xsym-agree stake on `BB_20_2_EMA200` own trades is
**NOT FALSIFIED**. `decision_if_pass` is stay **CONDITIONAL** and continue to
Validation-2 of the same formula. Gate PASS: Train-1 mean 95.463371 vs
reference 95.3217987 (diff 0.141572 ≤ allowance 0.2383045), n=756. Sized
mean −4.002329 > control −9.270577. Losing months 2≤2. Mult gap +0.026608.
n 211/1031 invariant. stake_cv 0.481509. (a)–(e) clear. Not a promotion and
not a FREEZE. Holdout stays closed. `BB_20_25_EMA200` stays FREEZE on its
own loop; that result is not copied. Next =
`H-BB-20-2-XSYM-AGREE-SIZING-VAL2-01`.

Caveats, not extra falsifiers: both means are negative. Sized was worse in
2025-03 (−24.137407) and 2025-04 (−13.665664). The entry-net gain is
2025-05 (+90.485553 on a +52.682482 total). The gap is small and negative
on 4/10 series.

## Q1–10

1. **Best strategy now?** None promotable. `BB_20_25_EMA200`, `EMA3_21_50_200`, and `DONCHIAN_55_NO_TRAIL` stay **FREEZE**. Active CONDITIONAL name is `BB_20_2_EMA200`, then `EMA_50_200`, then `EMA3_13_50_200`.
2. **Why that name?** Its own-trades loop is the one in progress. Entry-vol is FALSIFIED here (`f7ac677`). This sizing arm passed Train-1 (`1774a8a`) and Validation-1 (`7e18786`) and still has later protocol windows. The screen is this name's, not a transferred BB_20_25 figure.
3. **Edge from many trades or few big wins?** Few big wins. Val-1 sized blotter has 4 trades / +187.114893 at net≥29.9, against control 1 trade / +32.605488. The whole entry-net improvement is 2025-05.
4. **Earns when?** `signal_reverse` runners, and on this window when the stake scaled the May basket. Agreement raised winner mult only slightly (1.161765 vs 1.135156).
5. **Loses when?** Both arms lose on the Validation-1 mean. 2025-03 and 2025-04 got worse under sizing. Shared basket regime and `initial_sl` remain. The losing-month count stayed 2 of 3.
6. **Rejected hypotheses?** On this name: entry-vol **FALSIFIED (a)+(c)** `f7ac677`; exit, long-only, and breadth already closed. This sizing formula is **not** rejected. On `BB_20_25_EMA200` only, the same shape failed Val-1 (`89e936a`) and that name is FREEZE. That does not close this formula and does not close entry or sizing on `EMA_50_200` or `EMA3_13_50_200`.
7. **Unresolved problem?** Whether the stake weights keep helping after Validation-1. Monthly regularity is not solved. Both means are negative and the gain is one month. §11 says one validation window is not a finished finalist. In-class portfolio combination stays BLOCKED.
8. **Next experiment and why?** `H-BB-20-2-XSYM-AGREE-SIZING-VAL2-01`. Coordinator protocol §3.10 and §11 require the next chronological check of a promising arm before another axis. §7 says do not abandon this sizing arm for a new entry axis before that check. Same frozen formula. Window is F005 protocol §3.2 Validation 2, which the Val-1 card named without dates. Not an abs-ATR retune. Not FREEZE. Not holdout.
9. **Why not a random search?** §7 develop-not-abandon. One licensed axis on this name has two passes and a named unused window. Do not jump to `EMA_50_200` or `EMA3_13_50_200`. Do not open a new entry gate in parallel.
10. **What result confirms or falsifies the next hypothesis?** On the Val-2 card, scored only on this name's entries with 2025-06-01 ≤ entry < 2025-09-01. Before that scoring, the Train-1 slice of the longer control must sit within relative 0.25% of |+95.3217987| and Train-1-entry n=756 exactly. Pass: sized mean above that window's own control, losing-month count not higher, mult gap > 0, n_trades invariant, stake_cv > 0.05. Any one of (a)–(e) fails it. Do not loosen those five. Holdout is not opened.
