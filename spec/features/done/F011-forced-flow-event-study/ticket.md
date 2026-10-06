# F011 · Forced-flow event study (T3, non-trading edge test)

## Outcome

A statistical verdict on whether forced-flow *state* carries a forward edge, so the coordinator
can decide if Stage 2 (strategy) is warranted or if the OI-only proxy is too coarse and
liquidation/order-flow data must be acquired first. This is an event study, **not a strategy** —
no orders, no PnL, no positions. It answers the two pre-registered hypotheses in
`spec/research/F011-forced-flow-lab.md` §9 (as amended 2026-10-06). Code under
`forced_flow_lab/`.

## Scope

- **Input:** `output/f011_forced_flow/states/<SYMBOL>.csv.gz` (T2, **5m** labels) for BTCUSDT +
  ETHUSDT, Train-1. Depends on T2; do not invent states.
- **Event = state entry**, not every bar in the state. Use non-overlapping events, or report
  explicitly how overlap is handled.
- `H-FORCEDFLOW-CONTINUATION-01`: for bars entering LONG_STRESS / LONG_LIQUIDATION_CASCADE (and
  the short mirror), measure the distribution of forward signed return at **+5m / +15m / +30m /
  +60m / +4h** vs the unconditional baseline for the same symbol/period.
- `H-FORCEDFLOW-EXHAUSTION-01`: for EXHAUSTION state entries, measure forward signed return at
  **+5m / +15m / +30m / +60m / +4h / +8h** vs baseline.
- **Cost band = 34 bps round trip** (10 commission + 5 half-spread + 2 slippage per side). An
  edge must beat the baseline by **more than** this band.
- Keep the **both-symbols** rule (edge must hold on BTC and ETH, not one symbol).
- Report per hypothesis × horizon × symbol: conditional vs unconditional mean/median, hit rate,
  dispersion, n events; and robustness across the small frozen state-threshold grid (no
  widening). **Report the number of cells tested.**
- Apply the §9 falsification rules and emit a one-line verdict per hypothesis (edge / no edge),
  plus the honest caveat that absence of liquidation/order-book data limits sharpness (taker
  flow is present on 5m; liquidations still null).
- Write to `output/f011_forced_flow/event_study/` and fill the `## Result` of the program note's
  §9 (leave the Decision for the coordinator).

## Out of scope

- Any trade, position, sizing, backtest, or PnL curve (that is Stage 2, and it is gated on this).
- Tuning thresholds to manufacture significance; the grid is frozen in T2's manifest.
- Multiple-testing laundering: report n hypotheses/horizons/symbols (cells) tested; do not
  cherry-pick one cell.
- Running before T2 states + committed manifest exist.

## Acceptance

- `output/f011_forced_flow/event_study/` holds the per-hypothesis × horizon × symbol tables and a
  verdict file; the program note §9 `## Result` is filled; cell count is reported.
- Events are state entries (non-overlapping or overlap policy documented); cost band 34 bps RT
  is applied; both-symbols rule enforced.
- Forward returns are strictly look-ahead-free (horizon windows end at or before data end);
  `python3 -m pytest -q` stays green.

## Notes

A clean "no edge" is a valid, kept result and the likely one on OI+taker-flow 5m data without
liquidations — it is the evidence that justifies (or not) acquiring liquidation feeds before
any strategy. Coordinator decision 2026-10-06: T3 runs on 5m states / 5m horizons, not hourly.
