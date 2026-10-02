# Coordinator Series Report — H-BB-20-25-ABS-ATR-ENTRY-GATE-01 (§15)

> **Date:** 2026-10-02 night (Europe/Warsaw)  
> **Experiment:** H-BB-20-25-ABS-ATR-ENTRY-GATE-01  
> **Tip / merge:** `3788f11` (review PASS `2026-10-02-f006-bb2025-entry-vol-review-45b3ee8a`, FF to main)  
> **Artifacts:** `output/f006_bb_20_25_abs_atr_gate/`  
> **Card:** `spec/research/F006-hypothesis-bb-20-25-abs-atr-entry-gate.md`

## Summary

Abs-ATR entry keep-gate on `BB_20_25_EMA200` **FALSIFIED** under condition (a): all five
thresholds cut mean Train-1 net PnL below ungated control (+82.90). Strategy stays
**CONDITIONAL** (do not FREEZE). Entry-vol axis now closed on this name's own trades. Next =
position sizing orthogonal to ATR (`H-BB-20-25-XSYM-AGREE-SIZING-01`).

## Q1–10 (mandatory per §15)

### 1. Best strategy now?

Still **none promotable**. Among CONDITIONAL catalog5, `BB_20_25_EMA200` remains highest
priority (best series-positive rate 9/10; best single-series monthly floor 3/12 on SOLUSDT/60),
but 0/10 series clear §7 monthly promotion. This experiment did not improve that.

### 2. Why best?

Unchanged aggregate screen — not because of this gate. Gate made every cell worse on mean PnL.

### 3. Edge from many trades or few big wins?

Few big wins. Control: 10 big winners (net≥29.9) = +968 pooled PnL. Gate cells that cut stops
also cut those tails (T=1.0% retained 1/10 big winners, 35% of big-winner PnL).

### 4. Earns when?

`signal_reverse` runners on BB breakouts that eventually travel; many of those co-locate with
elevated entry ATR% — so a keep-low-ATR rule removes them.

### 5. Loses when?

`initial_sl` deaths (58% of control entries, 0% WR) and shared basket-regime losing months
(pooled floor 7/12 ungated; mostly unchanged under gate). Shared-losing diagnostic still stands.

### 6. Rejected hypotheses?

Add: **H-BB-20-25-ABS-ATR-ENTRY-GATE-01 = FALSIFIED (a)**. Prior closed on this name: exit-class,
partial-exit, class-closure direction/breadth cells. Donchian/EMA3_21 entry-vol remain FALSIFIED
on their own names.

### 7. Unresolved problem?

§7 monthly regularity (pooled floor ~7/12; best series 3/12) while preserving fat-tail runners.
Entry-vol cannot separate stops from runners on this name without destroying expectancy.

### 8. Next experiment and why?

**H-BB-20-25-XSYM-AGREE-SIZING-01** — position sizing by cross-symbol directional agreement via
`stake_series`. Sizing is the next open axis on this name; ATR-magnitude levers just failed
(gate here; vol-inverse on related leads). Cross-symbol agreement is orthogonal to volatility
and previously moved win rate the right way as an *entry gate* on related BB/Donchian leads —
as *sizing* it keeps all trades (no starve) and reweights toward basket-consensus bars.

### 9. Why not random new strategies?

Protocol: finish per-name loop on highest-priority CONDITIONAL before new catalog search or §13
non-correlated data. Shared-losing blocks in-class portfolio combo; it does not license abandon.

### 10. What would confirm/falsify the next hyp?

Confirm: sized mean Train-1 net PnL > uniform-stake baseline AND pooled losing-month floor
strictly below 7/12 AND mean stake mult on winners > losers (mechanism check), with
`n_trades` invariant. Falsify: mean PnL ≤ baseline at the pre-registered formula, or floor not
improved, or winner/loser mult gap ≤ 0 (mechanism absent).
