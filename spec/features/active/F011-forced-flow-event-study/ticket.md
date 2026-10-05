# F011 · Forced-flow event study (T3, non-trading edge test)

## Outcome

A statistical verdict on whether forced-flow *state* carries a forward edge, so the coordinator
can decide if Stage 2 (strategy) is warranted or if the OI-only proxy is too coarse and
liquidation/order-flow data must be acquired first. This is an event study, **not a strategy** —
no orders, no PnL, no positions. It answers the two pre-registered hypotheses in
`spec/research/F011-forced-flow-lab.md` §9. Code under `forced_flow_lab/`.

## Scope

- Read `output/f011_forced_flow/states/<SYMBOL>.csv` (T2) for BTCUSDT + ETHUSDT, Train-1.
- `H-FORCEDFLOW-CONTINUATION-01`: for bars entering LONG_STRESS / LONG_LIQUIDATION_CASCADE (and
  the short mirror), measure the distribution of forward signed return at +1h/+4h vs the
  unconditional baseline for the same symbol/period.
- `H-FORCEDFLOW-EXHAUSTION-01`: for EXHAUSTION bars, measure forward signed return at +1h/+4h/+8h
  vs baseline.
- Report per hypothesis × horizon × symbol: conditional vs unconditional mean/median, hit rate,
  dispersion, n events; and robustness across the small frozen state-threshold grid (no widening).
- Apply the §9 falsification rules and emit a one-line verdict per hypothesis (edge / no edge),
  plus the honest caveat that absence of liquidation/order-flow data limits sharpness.
- Write to `output/f011_forced_flow/event_study/` and fill the `## Result` of the program note's
  §9 (leave the Decision for the coordinator).

## Out of scope

- Any trade, position, sizing, backtest, or PnL curve (that is Stage 2, and it is gated on this).
- Tuning thresholds to manufacture significance; the grid is frozen in T2's manifest.
- Multiple-testing laundering: report n hypotheses/horizons tested; do not cherry-pick one cell.

## Acceptance

- `output/f011_forced_flow/event_study/` holds the per-hypothesis × horizon × symbol tables and a
  verdict file; the program note §9 `## Result` is filled.
- Forward returns are strictly look-ahead-free (horizon windows end at or before data end);
  `python3 -m pytest -q` stays green.

## Notes

A clean "no edge" is a valid, kept result and the likely one on OI-only data — it is the
evidence that justifies (or not) acquiring liquidation/order-flow feeds before any strategy.
