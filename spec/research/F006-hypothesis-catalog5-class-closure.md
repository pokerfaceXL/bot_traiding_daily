# F006 — H-CATALOG5-CLASS-CLOSURE-01 (pre-registered)

> Pre-registered before the run. Closes the catalog5 momentum class on OWN evidence instead of
> by transfer from `EMA3_21_50_200`. EMA3_21 already went through the full protocol loop (autopsy
> + long-only + breadth-regime, all FALSIFIED → FREEZE). This runs the two decisive, cheap levers
> on the four remaining CONDITIONAL names so each is frozen (or kept) on its own trades, per the
> no-transfer discipline. Reuses `scripts/f006_breadth_regime_experiment.py` + the family harness;
> no new engine, no external data, Train-1 only.

experiment_id: H-CATALOG5-CLASS-CLOSURE-01
date: 2026-10-02
base_strategy: catalog5 NO_TRAIL class — BB_20_25_EMA200, EMA_50_200, EMA3_13_50_200, BB_20_2_EMA200
  (EMA3_21_50_200 already closed; it is the control reference, not re-tested)

```text
Observation:
EMA3_21_50_200 is FROZEN: entry-vol, direction (long-only), exit, and regime (breadth) are all
falsified on its own trades, because every expectancy-raising lever leaves the monthly floor at
or above its baseline while the shared basket regime makes both the losses and the runners. The
other four catalog5 names share the same lumpy-winner shape and 0/50 monthly clears
(notrail-monthly-catalog5), but their direction/regime levers were only ever closed by analogy.

Problem:
Freezing the four by transfer violates the no-transfer discipline. They need their own pass.

Mechanism:
If the catalog5 class has a single shared-regime failure mechanism, the two decisive levers that
raise expectancy on EMA3_21 (drop the short book; gate on basket breadth) will fail to lower each
name's OWN pooled losing-month floor without cutting its fat-tail winners — just as on EMA3_21.

Hypothesis (class exhaustion):
For every one of the four names, no decisive lever lowers that name's own pooled losing-month
floor below its baseline while retaining its winners — i.e. the class is exhausted on OHLCV data.

Change to test (per name, Train-1):
1. baseline (no gate, both directions) — record floor, net, big-winner PnL, per-symbol.
2. long-only (direction==1 table filter — faithful for NO_TRAIL one-shot, as in H-EMA3-21-LONG-ONLY-01).
3. breadth-regime veto B in {0.4, 0.6, 0.8} (causal basket breadth = frac of 5 symbols above own
   EMA200 at bar i; exactly the frozen definition in F006-hypothesis-catalog5-breadth-regime.md).

Metrics (per name × lever): pooled losing-month floor (of 12, by entry-month), net, mean/trade,
n_trades, big-winner PnL (net>=29.9) + retention vs that name's baseline, #symbols net-positive,
per-symbol losing-month floor.

Falsification (per name) — the name is NOT exhausted (stays CONDITIONAL / REFINE, pursue) iff
some lever lowers that name's own baseline pooled floor by >=1 month AND keeps >=50% of that
name's baseline big-winner PnL AND holds for >=2 of its baseline carrier symbols. Otherwise the
name is exhausted on OHLCV levers -> FREEZE.

Data split: Train-1 only. Validation/holdout untouched. No new data, no new engine, no grid widening.

number_of_trials: 4 names x (baseline + long-only + 3 breadth cells)
```

## Result

**Ran 2026-10-02.** Experiment ID: H-CATALOG5-CLASS-CLOSURE-01. Script: `scripts/f006_class_closure_experiment.py`.

All four names exhausted. No lever lowered any name's pooled losing-month floor below its baseline while meeting the retention criteria (>=50% big-winner PnL, >=2 baseline carriers).

### Per-name verdicts

**BB_20_25_EMA200** — FREEZE (exhausted)
- Baseline: 7 losing months (of 12), 512 trades, net +709.9, big-winner PnL 968.0
- Best lever: LONG_ONLY (7 losing months, 252 trades, net +723.4, 95.9% big PnL retained)
- Falsifier: does not lower floor (7 vs 7 baseline)
- Per-symbol floor: all levers equal or worsen the baseline floor on every carrier

**EMA_50_200** — FREEZE (exhausted)
- Baseline: 7 losing months, 330 trades, net +587.4, big-winner PnL 843.8
- Best lever: B40 (8 losing months, 199 trades, net +555.7, 83.6% big PnL retained)
- Falsifier: does not lower floor (8 vs 7 baseline, worsens it)
- Per-symbol floor: no lever lowers any carrier's floor; several worsen it

**EMA3_13_50_200** — FREEZE (exhausted)
- Baseline: 7 losing months, 423 trades, net +771.3, big-winner PnL 1132.0
- Best lever: B40 (8 losing months, 287 trades, net +643.2, 87.8% big PnL retained)
- Falsifier: does not lower floor (8 vs 7 baseline, worsens it)
- Per-symbol floor: breadth gates worsen or hold baseline on all carriers

**BB_20_2_EMA200** — FREEZE (exhausted)
- Baseline: 7 losing months, 756 trades, net +834.4, big-winner PnL 1251.7
- Best lever: LONG_ONLY (7 losing months, 367 trades, net +872.4, 94.2% big PnL retained)
- Falsifier: does not lower floor (7 vs 7 baseline)
- Per-symbol floor: LONG_ONLY holds or worsens; breadth gates worsen

### Shared mechanism confirmed

Every name exhibits the same pattern as EMA3_21_50_200:
1. Long-only filter: retains net/trade and big-winner PnL but does NOT lower the pooled floor — short-side trades contribute to losses AND runners symmetrically (the basket regime drives both).
2. Breadth-regime veto: raises entry quality (mean/trade) but either holds or WORSENS the floor — the basket breadth is itself the regime failure's cause, not a gate against it.

The four names share a single failure mode: the 5-symbol basket's macro regime creates both the losses (all five symbols below their EMA200 together) and the fat-tail runners (coordinated breakouts). No OHLCV lever isolates the runs from the regime that produces them.

**Class exhaustion: CONFIRMED.** All four catalog5 names reach the same OHLCV ceiling EMA3_21 did. The NO_TRAIL + lumpy-winner class is closed on own evidence.

Data: Train-1 only (2024-03-01 through 2025-03-01), 5 symbols × 2 intervals, NO_TRAIL exit geometry (activate_pct=10.0, trail_pct=0.04, max_sl_pct=0.03, cooldown=0). Output: `output/f006_class_closure/`.

## Decision

(filled by coordinator after review)
