# Coordinator Series Report — H-BB-20-2-ABS-ATR-ENTRY-GATE-01 (§15)

> **Date:** 2026-10-03 ~11:22 Europe/Warsaw
> **Experiment:** H-BB-20-2-ABS-ATR-ENTRY-GATE-01
> **Tip / merge:** `f7ac677` (review PASS `2026-10-03-f006-bb202-abs-atr-review-59bf2edf`, FF to main)
> **Artifacts:** `output/f006_bb_20_2_abs_atr_gate/`
> **Card:** `spec/research/F006-hypothesis-bb-20-2-abs-atr-entry-gate.md`

## Summary

Abs-ATR entry keep-gate on `BB_20_2_EMA200` **FALSIFIED (a)+(c)**. Control
mean +95.3217987 reproduced. Best T=t_2_0 mean +64.05. Initial-SL drop at
that T is 3.45pp. Status stays **CONDITIONAL**. Do not FREEZE. Entry-vol is
closed on this name only. Next = `H-BB-20-2-XSYM-AGREE-SIZING-01`.

## Q1–10

### 1. Best strategy now?

None promotable. `BB_20_25_EMA200`, `EMA3_21_50_200`, and
`DONCHIAN_55_NO_TRAIL` stay **FREEZE**. Highest-priority unfinished name is
still `BB_20_2_EMA200` (**CONDITIONAL**), then `EMA_50_200`, then
`EMA3_13_50_200`.

### 2. Why that name?

It is the catalog5 name whose own-trades loop is in progress, not a promoted
edge. This gate did not improve it. The screen (mean +95.32, 8/10 series
positive, 0/10 clear §7) is this name's, not a transferred BB_20_25 figure.

### 3. Edge from many trades or few big wins?

Few big wins, less concentrated than the other catalog5 names but still
fat-tail. Ungated Train-1 entries: 12 trades with net≥29.9 sum to
+1251.65, against cohort net +834.35 (n=756). Top-10 winners are 50.7% of
gross wins (autopsy).

### 4. Earns when?

`signal_reverse` exits (388/756, mean +4.67). Many of those runners sit at
lower entry ATR% than stop-outs (autopsy 1.08 vs 1.76), but a causal
keep-low-ATR gate still removes them faster than it removes losses.

### 5. Loses when?

`initial_sl` (358/756, 47.35%, 0% WR) and the shared basket regime.
Control entry-month floor is 7/12. t_2_0 worsens it to 9/12. Shared-losing
(H-CATALOG5-SHARED-LOSING-MONTHS-01) still stands.

### 6. Rejected hypotheses?

Add: **H-BB-20-2-ABS-ATR-ENTRY-GATE-01 = FALSIFIED (a)+(c)** at `f7ac677`.
(b) did not fire on the published retention metric. (d) was not reachable.
(e) did not fire. Already closed on this name: exit-class, partial-exit,
long-only, breadth. Not closed here: position sizing, other §8 entry
structure. BB_20_25 closures do not transfer.

### 7. Unresolved problem?

§7 monthly regularity on this name, without cutting the runners. Entry-vol
cannot separate stops from runners here. Sizing and non-ATR entry structure
are still untested on these trades.

### 8. Next experiment and why?

**H-BB-20-2-XSYM-AGREE-SIZING-01.** Sizing is the next open axis on the
profile. §8 allows it because the ungated signal is aggregate-positive.
Cross-symbol agreement reweights stake and keeps every trade, so it is not
another abs-ATR gate and not a sample-starvation filter. The map
`0.5 + 0.375 * n_agree` is the structural [0.5, 2.0] band on n_agree 0..4,
not a threshold copied from BB_20_25's result. Entry structure stays open,
so the name stays CONDITIONAL.

### 9. Why not random new strategies?

§7 develop-not-abandon and §13: one licensed axis on `BB_20_2_EMA200` is
still open. Do not jump to `EMA_50_200` or `EMA3_13_50_200`. Do not start a
catalog search. Shared-losing blocks in-class portfolio combination; it does
not license FREEZE of this name.

### 10. What would confirm or falsify the next hypothesis?

Confirm: sized mean Train-1 net > this name's uniform control (+95.3217987,
which the control arm must reproduce) AND pooled entry-month floor strictly
below that control's floor AND mean(mult|winner) > mean(mult|loser), with
n_trades unchanged on every series and stake_cv > 0.05. Falsify on any one
of (a)–(e) on the pre-registered card. Holdout stays closed.
