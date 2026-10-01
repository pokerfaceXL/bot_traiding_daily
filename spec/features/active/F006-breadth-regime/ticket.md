# F006 · Basket-breadth regime veto on EMA3_21_50_200, Train-1 only

## Outcome

Run the pre-registered experiment `H-CATALOG5-BREADTH-REGIME-01` and record whether a causal
basket-breadth entry veto lowers EMA3_21_50_200's losing-month floor without cutting its
fat-tail winners. The full, frozen spec (breadth definition, grid, metrics, falsification) is
`spec/research/F006-hypothesis-catalog5-breadth-regime.md` — follow it exactly; do not redesign
it. Fill that note's `## Result` section and leave the `## Decision` for the coordinator.

## Scope

- Add a causal basket-breadth signal: at decision bar i, fraction of {BTC,ETH,SOL,XRP,DOGE}
  whose close at i is above that symbol's own EMA200 at i, using only closes ≤ i, same interval.
  Warm-up / missing / unaligned symbol counts as not-above. No look-ahead.
- Apply it as an entry veto on `EMA3_21_50_200` (NO_TRAIL, both directions) in the existing
  shared F006 harness; grid B ∈ {0.4, 0.6, 0.8}; baseline = no gate. Exits unchanged.
- Train-1 cohort only (2024-03 … 2025-02), 5 symbols × {60,240}, same costs/capital as the
  catalog5 runs. Emit results.csv + monthly.csv + the pre-declared metrics; write `## Result`.
- Add a unit test proving the breadth signal is causal (truncating the frame at bar i does not
  change breadth(i)) and that EMA3_21's baseline signal is bit-identical when the gate is off.

## Out of scope

- Touching validation/holdout, or retuning B outside the frozen grid.
- Changing entry indicator, stop, exit geometry, sizing, costs, capital, or the basket.
- Editing other strategy profiles, the journal, or build.md (coordinator does the write-up).
- Promoting anything, or merging to main.

## Acceptance

- `spec/research/F006-hypothesis-catalog5-breadth-regime.md` `## Result` is filled with the
  per-B table (net, mean/trade, n_trades, pooled + per-symbol losing-month floor, big-winner
  PnL retained, #symbols positive) and a one-line statement of which falsifier(s) (a)-(d)
  trip, if any.
- A reproducible script under `scripts/` (e.g. `f006_breadth_regime_experiment.py`) regenerates
  the result; its output dir is under `output/f006_breadth_regime/`.
- New tests pass and `python3 -m pytest -q` stays green; the baseline-off path is byte-identical
  to the current EMA3_21 signal.

## Notes

Causality is the whole point — a subtle look-ahead in the EMA200/breadth alignment would
invalidate the result. If the result trips a falsifier, that is a valid, expected outcome:
record it honestly, do not widen the grid or tweak the definition to find a passing cell.
