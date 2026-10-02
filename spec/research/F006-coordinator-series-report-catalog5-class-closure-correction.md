# Coordinator Series Report — catalog5 class-closure correction (§15)

> **Date:** 2026-10-02 (evening, after FREEZE→CONDITIONAL correction)  
> **Series:** catalog5 class (five EMA/BB momentum names) + class-closure / shared-months arc  
> **Scope:** Covers the catalog5 / class-closure / shared-months work (2026-10-01 through 2026-10-02),
> including the FREEZE→CONDITIONAL correction and status as of 2026-10-02 evening.

## Purpose

This report documents the catalog5 class-closure arc and the 2026-10-02 evening correction that
withdrew FREEZE from four names. It answers the mandatory §15 questions (Q1–10) for the catalog5
series as currently understood after the correction. The earlier FREEZE (2026-10-02 morning) was
**withdrawn** — class-closure/shared-months testing does **not** substitute a full per-name
COORDINATOR_RESEARCH_PROTOCOL pass.

## Summary

- **Best now:** Among CONDITIONAL, `BB_20_25_EMA200` / `EMA_50_200` (best monthly floors 3/12 on
  one series each, best series-positive rates in catalog5). None promotable. `EMA3_21_50_200` and
  `DONCHIAN_55_NO_TRAIL` remain FREEZE (full protocol pass on own trades).
- **Status corrected:** Four names (`BB_20_25_EMA200`, `EMA_50_200`, `EMA3_13_50_200`,
  `BB_20_2_EMA200`) unfrozen to **CONDITIONAL** (2026-10-02 evening). Only axes independently
  exhausted under protocol on each name's own trades stay closed. Entry+sizing remain open on
  the four.
- **What was tested:** Class-closure levers (long-only direction, breadth regime B40/B60/B80) on
  the four remaining catalog5 names; shared-losing diagnostic (H-CATALOG5-SHARED-LOSING-MONTHS-01
  CONFIRMED basket regime). Exit axis closed earlier (H-CATALOG5-EXIT-CLASS-01,
  H-CATALOG5-PARTIAL-EXIT-01 ran on all five series).
- **What was wrongly concluded:** All-five FREEZE / §13-only gate. Class-closure does **not**
  exhaust the per-name protocol loop; only axes actually run on each name's own trades stay closed.
- **Corrected status:** Four names CONDITIONAL; `EMA3_21_50_200` FREEZE kept (full loop on own
  trades: entry-vol autopsy, long-only, breadth-regime).

## Q1–10 (mandatory per §15)

### 1. Best strategy now?

**None promotable.** Among CONDITIONAL, `BB_20_25_EMA200` / `EMA_50_200` have the best monthly
floors (3/12 on one series each) and best series-positive rates in the catalog5 class. But 0/10
series clear §7 monthly promotion checklist for either name. `EMA3_21_50_200` and
`DONCHIAN_55_NO_TRAIL` remain **FREEZE** (full protocol pass on own trades, all axes exhausted).

### 2. Why best?

Best surviving screen + best monthly floor of the catalog5 class, not validated. `BB_20_25_EMA200`
has the best series-positive rate on Train-1 (9/10 series positive) and the best single-series
monthly floor (SOLUSDT/60 at 3/12 losing months, cited in
`spec/research/F006-hypothesis-notrail-monthly-catalog5.md` Result as "the closest any series in
this sample came to clearing the checklist"). `EMA_50_200` also reaches 3/12 floor on one series
and ties for best full-period series-positive rate (10/10 on full-slice sweep).

### 3. Edge from many trades or few big wins?

Few big wins (fat-tail dependent). All five catalog5 names share the same win structure:
- `EMA3_21_50_200`: 4 of 402 trades sum to full pooled net PnL (+817), top 10 winners = 64.2% of
  gross wins. 2024-11 alone = +813 of +817; top-3 winners = 97% of net.
- `BB_20_25_EMA200`: 4 of 512 trades = full net (+710), top 10 = 52.9% (least concentrated of the
  five, but still fat-tail).
- `EMA_50_200`: 2 of 330 trades = full net (+587), top 10 = 70.8% (most concentrated).
- `BB_20_2_EMA200`: 4 of 756 trades = full net (+834), top 10 = 50.7% (least concentrated, but
  still the same fat-tail/`initial_sl`-dominated shape).
- `EMA3_13_50_200`: 3 of 423 trades = full net (+771), top 10 = 63.8%.

### 4. Earns when / where is the edge?

High-conviction long breakouts that run to the opposite structural extreme (`signal_reverse`
exits), concentrated in Oct–Nov 2024 on Train-1. `signal_reverse` exits carry the profit across
all five names: WR 45.9%–59.8%, mean +4.67 to +13.28 per trade, while `initial_sl` exits (the
dominant exit mode at 47%–69% of trades) have 0% WR by construction (fixed 3% stop-out geometry).

For `EMA3_21_50_200` (full autopsy + direction test): longs carry all the aggregate PnL
(+875 / shorts −58), and all big winners are long. Long-only raises expectancy (+2.03→+4.61/trade)
and keeps 96.8% of fat tails, but worsens monthly regularity (7→9/12 losing months) because
shorts partially hedged long-losing months — expectancy and regularity are in tension.

### 5. Loses when / where does it lose?

**Shared basket regime** (now systematically confirmed, not just a hint). The losses cluster
across the five-symbol basket in common macro regime periods, not idiosyncratically.
H-CATALOG5-SHARED-LOSING-MONTHS-01 CONFIRMED: 6/12 Train-1 months have ≥4/5 catalog5 names
losing together (vs 3.70 expected by chance), mean pairwise phi 0.79, Pearson 0.96 (robust
ex-outlier 0.68), Jaccard 0.85. Symbol-level panel and optional Donchian sanity checks agree.

At trade level: 47%–69% of trades die at the fixed `initial_sl` (0% WR by construction, mean
-3.32 loss = the 3% stop-out geometry). The same high-ATR breakout entries that produce the
fat-tail runners also produce the highest stop-out rate — every expectancy-raising lever
(long-only, breadth regime veto, vol gates) that cuts the loss count also cuts the same fat
tails that carry all the aggregate PnL.

### 6. What has been rejected / what levers have been tried and failed?

**Exit axis (closed on all five catalog5 names):**
- `H-CATALOG5-EXIT-CLASS-01` (full-position TP/TRAIL vs NO_TRAIL) FALSIFIED (a)(b)(c) — NO_TRAIL
  best for all five names.
- `H-CATALOG5-PARTIAL-EXIT-01` (partial scale-out) FALSIFIED (a)(b) — full NO_TRAIL best.

**On `EMA3_21_50_200` own trades (full independent protocol pass):**
- Entry-vol / abs-ATR gate: independently FALSIFIED on this name's own trades
  (`F006-ema3-21-autopsy.md` §2). atr_percentile/calm identical for `initial_sl` vs
  `signal_reverse` (0.563 vs 0.560, 0.428 vs 0.436) — the raw-ATR gap is a cross-symbol scale
  artifact, not a causal gate.
- Direction lever (`H-EMA3-21-LONG-ONLY-01`): FALSIFIED for regularity. Long-only raises
  expectancy (+2.03→+4.61/trade) and keeps 96.8% of big-winner PnL, but worsens losing-month
  floor (7→9/12) because shorts partially hedged long-losing months. Kept as higher-EV F007
  portfolio-component input, not a regularity fix.
- Regime lever (`H-CATALOG5-BREADTH-REGIME-01`): FALSIFIED (a). Causal basket-breadth veto
  (frac of 5 symbols above own EMA200) at B∈{0.4,0.6,0.8} never lowers the pooled losing-month
  floor below 7/12 (best B80 = 7). Expectancy up (2.03→3.06), but tails cut (B80 keeps 59%
  big-winner PnL) and per-symbol floors mostly worsen. Breadth is another vol/trend proxy;
  regime axis closed on this name's own trades.

**On catalog5 class (class-closure, four names):**
- Long-only direction: ran on `BB_20_25_EMA200`, `EMA_50_200`, `EMA3_13_50_200`, `BB_20_2_EMA200`
  via H-CATALOG5-CLASS-CLOSURE-01. Own-trade numbers exist for each name. No name's pooled
  losing-month floor improved (all hold at 7/12 or worsen to 8–9/12). Long-only keeps 94–100%
  of big-winner PnL across all four, but pooled floor holds or worsens because shorts partially
  hedge long-losing months (same as `EMA3_21_50_200` own-trades result).
- Breadth regime B40/B60/B80: ran on the four via H-CATALOG5-CLASS-CLOSURE-01. Own-trade numbers
  exist for each name. No B lowers any name's pooled floor below baseline while meeting retention
  criteria (≥50% big-winner PnL, ≥2 baseline carriers). Best levers raise expectancy but cannot
  separate the regime-driven losing months from the regime-driven fat-tail runners.

**Wider class (tested on Donchian / catalog5 / swarm):**
- Take-profit (`H-DONCHIAN-ABS-ATR-ENTRY-GATE-01`, `H-CATALOG5-EXIT-CLASS-01` TP cells):
  FALSIFIED. Cuts fat-tail runners, worsens aggregate PnL.
- Trailing (`F006-hypothesis-trailing-sweep`, `F006-hypothesis-trailing-boundary`): FALSIFIED.
  NO_TRAIL beats every TP/TRAIL cell tested (18 cells in activate_pct × trail_pct grid).
- Entry-vol / abs-ATR gate: FALSIFIED on `DONCHIAN_55_NO_TRAIL` own trades
  (`H-DONCHIAN-ABS-ATR-ENTRY-GATE-01`), confirmed DNR by transfer to catalog5 (dual/trio autopsy
  found same ATR shape), now independently FALSIFIED on `EMA3_21_50_200` own trades.
- EMA-trend confirm, cross-symbol agreement, loss-cooldown, vol-inverse sizing: all FALSIFIED on
  earlier catalog names (H6, H14/H14-refined, H16, H17). BTC-ER permission filter (btc_filter,
  H2-falsified). ~20 swarm families (all H2-falsified).

### 7. What remains unresolved / what is the open problem?

**Monthly regularity.** On `EMA3_21_50_200` (full protocol pass), every expectancy-raising lever
leaves the losing-month floor ≥7/12 because the shared basket regime makes both the losses and
the runners. On the four CONDITIONAL catalog5 names (`BB_20_25_EMA200`, `EMA_50_200`,
`EMA3_13_50_200`, `BB_20_2_EMA200`), **entry+sizing axes remain open** — not independently
exhausted under protocol on each name's own trades. The class-closure long-only + breadth results
exist for these names, but running class levers does **not** substitute a full per-name protocol
pass.

**In-class portfolio combination (§8) is BLOCKED.** The shared-losing-months CONFIRMED result
(H-CATALOG5-SHARED-LOSING-MONTHS-01) blocks §8 in-class diversification — the precondition
"losses not strongly correlated" fails. Combining catalog5 names would not improve monthly
regularity because they lose together in the same regime periods.

**Open axes on the four CONDITIONAL names:**
- Entry refinement / entry-vol / abs-ATR gate: only ever marked DNR-by-transfer from
  Donchian/EMA3_21. The dual/trio autopsy showed the ATR shape, but no formal own-trades protocol
  hypothesis was run and decided for each name.
- Position sizing: never tested on any catalog5 name under protocol.
- Any other §8 entry structure (candle confirm, breakout structure, HTF direction, etc.) not yet
  pre-registered for these names.

### 8. Next experiment and why?

**Continue the protocol loop on CONDITIONAL catalog5** (one name, one hypothesis, one open axis).
Highest priority: `BB_20_25_EMA200` (best monthly floor 3/12 on SOLUSDT/60, best series-positive
rate 9/10, cited in catalog5 monthly note as nearest to checklist). Open axis = entry-vol /
abs-ATR own-trades gate (or position sizing).

**NOT owner §13-only gate.** The 2026-10-02 evening correction withdrew FREEZE from four names
because class-closure/shared-months do **not** substitute a full per-name protocol pass. Finish
the protocol loop on the CONDITIONAL names first (one name at a time, one hyp per name) before
moving to §13 non-correlated data.

### 9. Why not random search / why not just try many things?

§7 develop-before-abandon. Finish the per-name protocol loop first on CONDITIONAL catalog5
(entry+sizing axes open on four names). §13 (non-correlated data: order-flow / OI / liquidation /
cross-asset) remains an option after that, but requires a written non-correlated-mechanism
justification + budget + falsification, which depends on data not yet in the repo. Random
widening (another catalog name family, another signal class without exhausting the current one)
remains forbidden by §9/§13.

### 10. What result would confirm or refute the next hypothesis?

Same bar as every in-repo lever has faced: falsified unless, on the frozen Train-1 basket, it
lowers the pooled losing-month floor below baseline (7/12 for most catalog5 names under
class-closure; name-specific baseline from dual/trio autopsy) while keeping ≥50% of big-winner
PnL and holding for ≥2 carrying symbols.

For the next hypothesis (e.g., entry-vol/abs-ATR own-trades gate on `BB_20_25_EMA200`), if it
cannot lower that name's pooled losing-month floor below its baseline while meeting the retention
criteria, the entry-vol axis is independently FALSIFIED on that name (same as `EMA3_21_50_200`).
If it does lower the floor, move to the next open axis on that name or the next CONDITIONAL name
in priority order.

## What was tested (detail)

1. **H-CATALOG5-EXIT-CLASS-01** (all five catalog5 series): full-position TP/TRAIL vs NO_TRAIL.
   FALSIFIED (a)(b)(c). NO_TRAIL best for all five names. Exit axis closed.
2. **H-CATALOG5-PARTIAL-EXIT-01** (all five catalog5 series): partial scale-out. FALSIFIED (a)(b).
   Full NO_TRAIL best. Exit axis closed.
3. **`EMA3_21_50_200` entry-vol autopsy** (`F006-ema3-21-autopsy.md`): atr_percentile/calm
   identical for `initial_sl` vs `signal_reverse`. Entry-vol axis independently FALSIFIED on this
   name's own trades.
4. **H-EMA3-21-LONG-ONLY-01** (`EMA3_21_50_200` own trades): long-only raises expectancy but
   worsens monthly floor (7→9/12). Direction axis FALSIFIED for regularity on this name. Kept as
   higher-EV F007 portfolio-component input.
5. **H-CATALOG5-BREADTH-REGIME-01** (`EMA3_21_50_200` own trades): causal basket-breadth veto
   B∈{0.4,0.6,0.8} never lowers pooled floor below 7/12. FALSIFIED (a). Regime axis closed on
   this name's own trades.
6. **H-CATALOG5-CLASS-CLOSURE-01** (four remaining catalog5 names): long-only direction +
   breadth regime B40/B60/B80. Own-trade numbers exist for each name. No lever lowers any name's
   pooled losing-month floor below baseline (all hold at 7/12 or worsen to 8–9/12) while meeting
   retention criteria. Class exhaustion confirmed **for the tested levers only** — does **not**
   exhaust per-name protocol pass.
7. **H-CATALOG5-SHARED-LOSING-MONTHS-01** (diagnostic, all five catalog5 names): Train-1 losing
   months CONFIRMED shared / basket regime (6/12 months with ≥4/5 names losing vs 3.70 expected,
   phi 0.79, Pearson 0.96, Jaccard 0.85). Symbol-level panel + Donchian sanity checks PASS. This
   blocks §8 in-class portfolio combination (precondition "losses not strongly correlated" fails).

## What was wrongly concluded

**All-five FREEZE / §13-only gate** (2026-10-02 morning, now withdrawn). The coordinator wrongly
concluded that class-closure/shared-months testing exhausted the protocol loop for the four
remaining catalog5 names (`BB_20_25_EMA200`, `EMA_50_200`, `EMA3_13_50_200`, `BB_20_2_EMA200`).
This was **wrong** because the binding protocol loop (2026-10-01) requires a full per-name
Observation→Problem→Mechanism→Hypothesis pass. Class-closure ran long-only + breadth levers on
the four names (own-trade numbers exist), but that does **not** substitute a full protocol pass
on each name for every axis. Entry refinement / entry-vol / position sizing were never
independently tested on those four names under protocol — only DNR-by-transfer from
Donchian/EMA3_21.

The corrected understanding: FREEZE only when all axes are exhausted on that name's **own** trades
under protocol. `EMA3_21_50_200` remains FREEZE (full loop: entry-vol autopsy, long-only,
breadth-regime, exit-class/partial). The other four names are now CONDITIONAL (entry+sizing open).

## Corrected status (as of 2026-10-02 evening)

| strategy | status | why |
| --- | --- | --- |
| `EMA3_21_50_200` | **FREEZE** | Full independent protocol pass on own trades: entry-vol autopsy (FALSIFIED), long-only (FALSIFIED for regularity), breadth-regime (FALSIFIED), exit-class/partial (FALSIFIED). All axes exhausted. |
| `BB_20_25_EMA200` | **CONDITIONAL** | Only axes tested on own trades stay closed: exit (ran on these series), direction lever (long-only cell of class-closure has own-trade numbers), regime lever (breadth cells have own-trade numbers). Entry+sizing open. |
| `EMA_50_200` | **CONDITIONAL** | Same as `BB_20_25_EMA200`. Exit + class-closure levers closed; entry+sizing open. |
| `EMA3_13_50_200` | **CONDITIONAL** | Same as `BB_20_25_EMA200`. Exit + class-closure levers closed; entry+sizing open. |
| `BB_20_2_EMA200` | **CONDITIONAL** | Same as `BB_20_25_EMA200`. Exit + class-closure levers closed; entry+sizing open. |

## Next (mandatory action)

Continue the COORDINATOR_RESEARCH_PROTOCOL loop on CONDITIONAL catalog5. Next = one hypothesis on
**one name** (highest priority: `BB_20_25_EMA200`) on an **open** axis (prefer entry-vol /
abs-ATR own-trades gate, or position sizing). Do not run class-wide hypotheses; do not jump to
§13 non-correlated data before finishing the per-name loop. Shared-losing-months CONFIRMED still
stands as a diagnostic finding (basket regime), but it does **not** license class-wide FREEZE —
it only blocks in-class portfolio combination (§8 precondition fails).

---

**End of §15 report.** See `spec/RESEARCH_JOURNAL.md` for the current plan and
`spec/research/strategy_profiles/*.md` for per-name status.
