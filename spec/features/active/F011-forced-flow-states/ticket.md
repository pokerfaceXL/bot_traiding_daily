# F011 · Forced-flow state machine (T2, non-trading)

## Outcome

Each bar of the T1 frame is assigned exactly one causal participant-stress state, so the event
study (T3) can condition forward returns on state. Deterministic labelling from frozen rules —
no trading, no forward-looking information, no outcome fitting. Spec:
`spec/research/F011-forced-flow-lab.md` §3,§6. Code under `forced_flow_lab/`.

## Scope

- Read `output/f011_forced_flow/frame/<SYMBOL>.csv`. Assign one of:
  `NORMAL, LONG_CROWDING, SHORT_CROWDING, LONG_STRESS, SHORT_STRESS,
  LONG_LIQUIDATION_CASCADE, SHORT_LIQUIDATION_CASCADE, LONG_EXHAUSTION, SHORT_EXHAUSTION`.
- Frozen rule sketch (record exact thresholds in a manifest BEFORE running; crowding ≠ timing):
  CROWDING = Forced Positioning Score high (OI_zscore + funding_zscore, long/short by sign);
  STRESS = crowded side + adverse return + OI starting to fall; CASCADE = stress + OI collapsing
  per ATR (fuel high) + return accelerating against the crowd; EXHAUSTION = within/after a
  cascade, OI deceleration + price_impact collapsing while adverse volume persists; else NORMAL.
- Emit `output/f011_forced_flow/states/<SYMBOL>.csv` (bar → state + the triggering values) and a
  state-count summary. Unit test: states are a pure function of past/current bars (causal), and
  every bar gets exactly one state.

## Out of scope

- Any trade, position, PnL, or forward return (that is T3).
- Tuning thresholds to produce a desired state distribution; use frozen, documented values.
- Using liquidation/order-book data (absent) — use the OI/price fuel proxy per §3.

## Acceptance

- `output/f011_forced_flow/states/{BTCUSDT,ETHUSDT}.csv` label every bar with one state; the
  manifest lists the frozen thresholds set before the run.
- Causality + single-label tests pass; `python3 -m pytest -q` stays green.

## Notes

The states must be defensible economically, not chosen to look good later. If a state is almost
never triggered on BTC/ETH, report that — it is information about the OI-only proxy's limits.
