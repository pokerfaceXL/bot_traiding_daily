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

(filled by worker run)

## Decision

(filled by coordinator after review)
