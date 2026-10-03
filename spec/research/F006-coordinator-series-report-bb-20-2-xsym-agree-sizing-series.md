# Coordinator Series Report — BB_20_2 xsym-agree sizing series (§15)

> **Date:** 2026-10-03 ~14:05 Europe/Warsaw
> **Series:** H-BB-20-2-XSYM-AGREE-SIZING-01 → VAL1 → VAL2 → VAL3 → VAL4
> **Final tip / merge:** `139ed3d` (Val-4 Result; Decision this commit)
> **Artifacts:** `output/f006_bb_20_2_xsym_agree_sizing{,_val1,_val2,_val3,_val4}/`
> **Cards:** `spec/research/F006-hypothesis-bb-20-2-xsym-agree-sizing{,-val1,-val2,-val3,-val4}.md`

## Summary

The frozen causal stake `mult = clip(0.5 + 0.375 * n_agree, 0.5, 2.0)` on
`BB_20_2_EMA200` own trades cleared Train-1 and three validation windows, then
**FALSIFIED (c)** on Validation-4. Formula closed. Status stays **CONDITIONAL**.
Do not FREEZE. Do not spawn Val-5. Do not open holdout. Do not retune.

| stage | tip | verdict | mean control → sized | months | mult gap | n |
| --- | --- | --- | --- | --- | --- | --- |
| Train-1 | `1774a8a` | NOT FALSIFIED / REFINE | +95.3217987 → +146.632696 | 7→6/12 | +0.086642 | 756 |
| Val-1 | `7e18786` | NOT FALSIFIED | −9.270577 → −4.002329 | 2≤2 | +0.026608 | 211/1031 |
| Val-2 | `7798bbb` | NOT FALSIFIED | +2.331879 → +2.551244 | 2≤2 | +0.031667 | 195/1226 |
| Val-3 | `cf00663` | NOT FALSIFIED | +1.772572 → +8.007368 | 2≤2 | +0.179831 | 181/1407 |
| Val-4 | `139ed3d` | **FALSIFIED (c)** | +12.319196 → +16.221179 | 2≤2 | **−0.102941** | 164/1571 |

Val-4 gate PASS (95.463371 vs 95.3217987, n=756). (a)(b)(d)(e) clear; (c) fires
because losers got a larger average stake than winners (1.227941 vs 1.125000).
Mean still rose (+3.90/series) and months did not worsen — that does not override
the pre-registered gap test. Context only: Val-4 entry-net gain is mostly 2026-01
(+101.83); 2025-12 and 2026-02 are worse under sizing; 6/10 series improve on net.

`BB_20_25_EMA200` stays FREEZE on its own loop; its Val-1 FALSIFIED (c) at
`89e936a` is not this series. Next on this name = §8 candle close-strength
(`H-BB-20-2-ENTRY-CANDLE-CONFIRM-01`), not breakout depth / HTF yet, not
`EMA_50_200` / `EMA3_13_50_200`.

## Q1–10

1. **Best strategy now?** None promotable. FREEZE names unchanged (`BB_20_25_EMA200`, `EMA3_21_50_200`, `DONCHIAN_55_NO_TRAIL`). Active CONDITIONAL name is `BB_20_2_EMA200`, then `EMA_50_200`, then `EMA3_13_50_200`.
2. **Why that name?** Own-trades loop still open. Entry-vol and this sizing formula are closed here; candle / breakout / HTF / liquidity entry structure remain untested on these trades. Screen is this name's (+95.32 control), not a BB_20_25 transfer.
3. **Edge from many trades or few big wins?** Few big wins across the series. Val-4 control big winners at net≥29.9: 4 / 140.65; sized 7 / 302.05. Earlier windows were also fat-tail / one-month concentrated (Train-1 Nov-2024; Val-1 May-2025; Val-2 Jul-2025; Val-3 Oct-2025; Val-4 Jan-2026).
4. **Earns when?** `signal_reverse` runners when agreement happened to scale winners more than losers. That held on Train-1 through Val-3 (positive mult gaps) and flipped on Val-4.
5. **Loses when?** Shared basket regime and `initial_sl`. On Val-4 the formula overweighted losers (gap −0.102941). Losing-month counts never fell below the window's own control on validation. Monthly regularity unsolved.
6. **Rejected hypotheses?** Entry-vol **FALSIFIED (a)+(c)** `f7ac677`. This xsym-agree sizing formula **FALSIFIED (c)** on Val-4 `139ed3d` (after Train-1 REFINE and Val-1..3 NOT FALSIFIED). Exit, long-only, breadth closed. BB_20_25 closures do not transfer.
7. **Unresolved problem?** Whether any §8 entry-structure gate on this name's own trades can cut `initial_sl` without cutting the runners. Sizing formula closed. In-class portfolio combination stays BLOCKED (shared-losing CONFIRMED).
8. **Next experiment & why?** `H-BB-20-2-ENTRY-CANDLE-CONFIRM-01`. Per Val-4 `decision_if_fail` and profile open list: candle confirm is the first untested §8 entry-structure variant here. Orthogonal to absolute ATR% and to the closed stake. Train-1 only. Not FREEZE. Not holdout. Not Val-5.
9. **Why not a random search?** §7 develop-not-abandon on this name while licensed axes remain. Do not jump to `EMA_50_200` or `EMA3_13_50_200`. Do not retune the closed stake. Do not copy BB_20_25 T results onto this name.
10. **What result confirms/refutes the next hypothesis?** On the candle-confirm card. Control must reproduce this name's ungated Train-1 mean +95.3217987, n=756, initial_sl share ≈0.473545, big-winner PnL ≈1251.654084, floor 7/12. Pass needs mean above control AND initial_sl drop ≥10pp at best-PnL T AND ≥50% big-winner PnL retained AND floor strictly below 7/12, without collapsing below 10 trades/series. Any of (a)–(e) fails it.
