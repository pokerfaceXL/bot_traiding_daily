# F006 — H-CATALOG5-SHARED-LOSING-MONTHS-01 (pre-registered)

> Pre-registered **before** any new compute. This is a **diagnostic**, not a new entry /
> exit / regime signal family. It answers the RESEARCH_JOURNAL open question ("Are the
> losing months shared across the frozen/conditional families … or idiosyncratic?") that
> must be settled **before** any §8 portfolio-combination / F007 step. Prefer existing
> `output/f006_catalog5_*` / class_closure / autopsy monthly tables — no new engine, no
> new entry signal, Train-1 tables only. Licensed under protocol §2 (X→Y→Z), §7 item 7
> (correlation with other strategies as diagnosis before abandon/portfolio), §8 Portfolio
> combination precondition (test whether losses are strongly correlated).

experiment_id: H-CATALOG5-SHARED-LOSING-MONTHS-01
date: 2026-10-02
base_strategy: frozen catalog5 NO_TRAIL class — BB_20_25_EMA200, EMA_50_200,
  EMA3_13_50_200, BB_20_2_EMA200, EMA3_21_50_200 (all FREEZE after H-CATALOG5-CLASS-CLOSURE-01
  / breadth / long-only). Optional secondary panel: DONCHIAN_55_NO_TRAIL.

```text
Observation (X):
H-CATALOG5-CLASS-CLOSURE-01 CLOSED the catalog5 momentum class — every decisive OHLCV lever
(long-only, breadth veto) leaves each name's own pooled losing-month floor at or above its
baseline, because the same shared fat-tail / shared-regime mechanism makes both the losses
and the runners. The journal already records a within-name symbol co-occurrence hint
(EMA3_21 autopsy: 6/12 months with ≥4/5 symbols net-negative together) and a hand-picked
portfolio-diversification hint that the two worst months were correlated — but this has
never been tested systematically across all FREEZE catalog5 names (× symbols) from the
existing autopsy / monthly tables.

Problem:
Without knowing whether losing months are common across names (basket regime) or
idiosyncratic per name/symbol, the next licensed step is ambiguous: portfolio-level regime
/ F007 (§8 Portfolio combination requires "losses not strongly correlated") vs further
per-name entry autopsy. Inventing another OHLCV entry axis is forbidden (class closed).

Mechanism (Y):
If the class shares one basket-level failure regime, Train-1 losing months will co-occur
across the FREEZE catalog5 names (and likely Donchian) far above chance; if failures are
name- or symbol-specific microstructure, the month×name loss matrix will look idiosyncratic
(near-chance co-occurrence, low pairwise association).

Hypothesis (Z):
Losing months are common across the FREEZE catalog5 names (basket regime), not idiosyncratic.
Test via systematic co-occurrence / correlation of Train-1 losing months from existing
autopsy/monthly tables. Falsify if months are largely idiosyncratic.

Change to test (DIAGNOSTIC ONLY — no new signal):
Compute from existing artifacts only (do not re-run the family harness unless a table is
missing a needed column; prefer reuse):

PRIMARY sources (name-pooled, entry-month, Train-1):
- output/f006_catalog5_dual_autopsy/monthly/{BB_20_25_EMA200,EMA_50_200}_monthly.csv
- output/f006_catalog5_trio_autopsy/monthly/{EMA3_21_50_200,EMA3_13_50_200,BB_20_2_EMA200}_monthly.csv
  (columns include month, net, loss_m)

SECONDARY sources (name × symbol, for the journal's "per name/symbol" clause):
- output/f006_notrail_monthly_catalog5/raw/*_{NAME}.json → monthly[].net_pnl
  OR rebuild entry-month nets from dual/trio autopsy trades CSVs (prefer trades if interval
  pooling must match the autopsy definition; document which).

OPTIONAL panel:
- output/f006_donchian_autopsy/donchian55_notrail_monthly.csv (loss_m) — report alongside,
  do not let Donchian alone decide the catalog5 verdict.

Frozen analysis (no grid widening after seeing results):
1. Build month × name binary loss matrix L[m,n] = 1 iff that name's Train-1 net for month m
   is negative (use existing loss_m when present). 12 months × 5 names.
2. Co-occurrence counts: for k in {3,4,5}, #months with ≥k/5 names losing; list the months.
3. Pairwise association: Pearson corr of month-net across name pairs; phi / tetrachoric-style
   assoc of loss flags; mean pairwise value. Jaccard similarity of each name's losing-month set.
4. Symbol-level panel (secondary): same co-occurrence within each name across symbols, and
   cross-name same-symbol loss agreement — descriptive, not a second falsifier.
5. Chance baseline: under independent names with each name's empirical p_loss, expected
   #months with ≥4/5 losing (binomial / Monte Carlo, document method). Compare observed vs chance.

Metrics (pre-declared):
- observed #months with ≥4/5 names losing (of 12)
- observed #months with 5/5 names losing
- mean pairwise Pearson corr of month-net (5 names)
- mean pairwise phi of loss flags
- mean Jaccard of losing-month sets
- chance-expected #months ≥4/5 (and observed − expected)
- secondary: per-name #months with ≥4/5 symbols losing (reproduce EMA3_21's 6/12 as sanity)
- optional Donchian: corr / co-occurrence of Donchian loss_m with the catalog5 majority-loss months

Falsification (common-regime hypothesis):
FALSIFIED (months largely idiosyncratic) if ANY of:
(a) observed #months with ≥4/5 names losing ≤ chance expectation (observed − expected ≤ 0), OR
(b) mean pairwise phi of loss flags ≤ 0.10 AND mean pairwise month-net corr ≤ 0.20, OR
(c) mean Jaccard of losing-month sets ≤ 0.35.

CONFIRMED (common basket regime) if NONE of (a)(b)(c) trip — i.e. co-occurrence clearly above
chance and association clearly positive. Borderline / mixed → report numbers; coordinator
decides; do not invent a new threshold after seeing results.

What the answer licenses next (coordinator only — do not write decision):
- CONFIRMED → portfolio-level regime / F007 exploration is the licensed direction (§8), not
  another per-name OHLCV entry autopsy; still needs owner/non-correlated data per journal.
- FALSIFIED → losses are name/symbol idiosyncratic; per-name entry autopsy remains licensed
  before portfolio combination.

Data split: Train-1 tables only (2024-03 … 2025-02). Validation/holdout untouched.
No new entry signal, no new engine, no parameter grid on a trading rule.

number_of_trials: 1 (single frozen diagnostic; Donchian panel is descriptive only)
```

## Result

**CONFIRMED** — losing months are common across FREEZE catalog5 names (basket regime), not idiosyncratic.

Train-1 (2024-03 to 2025-02, 12 months) loss co-occurrence from existing autopsy monthly tables (BB_20_25_EMA200, EMA_50_200, EMA3_21_50_200, EMA3_13_50_200, BB_20_2_EMA200):

- **6/12 months** with ≥4/5 names losing (observed) vs **3.70** expected by chance (Monte Carlo, n=10,000)
- **6/12 months** with 5/5 names ALL losing: 2024-03, 2024-04, 2024-05, 2024-08, 2024-09, 2024-12
- **Mean pairwise phi** (loss flags): **0.79** (» 0.10 threshold)
- **Mean pairwise Pearson r** (month-net): **0.96** (» 0.20 threshold)
- **Mean Jaccard** (losing-month sets): **0.85** (» 0.35 threshold)
- **Observed − expected**: +2.30 months (» 0)

None of the pre-declared falsification criteria (a)(b)(c) trip:
- **(a)** observed − expected = +2.30 > 0 ✓
- **(b)** mean phi = 0.79 > 0.10 AND mean corr = 0.96 > 0.20 ✓
- **(c)** mean Jaccard = 0.85 > 0.35 ✓

Optional Donchian panel: 6/7 catalog5 majority-loss months (≥3/5 losing) also saw Donchian loss (86% agreement).

Computation: `scripts/f006_shared_losing_months_diagnostic.py` → `output/f006_shared_losing_months/{loss_matrix.csv,summary.json}` (reproducible, seed=42).

The common-regime hypothesis is confirmed — Train-1 losing months cluster tightly across all five FREEZE catalog5 names, far above what independent name-specific failures would produce.

## Decision

_(coordinator fills after review)_
