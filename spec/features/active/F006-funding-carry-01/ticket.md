# F006 · H-FUNDING-CARRY-01 (T0)

Add funding to the harness, else the test is invalid.

## Outcome

Implement and run the pre-registered funding-carry rule in
`spec/research/F006-hypothesis-funding-carry.md`. Fill `## Result`. Leave
`## Decision` blank. Do not close or reopen any catalog profile.

A carry backtest that does not pass cached Bybit funding events into
`backtest_engine.run_backtest` is invalid. Do not run one. If the
reconciliation in the card fails, stop and write `INVALID`.

## Scope

- One new script `scripts/f006_funding_carry.py`. Do not change the
  default of `scripts/f006_family_runner.py` `_run_one` for older
  families. This script passes `funding_events` itself.
- Cache settled linear funding history for SOLUSDT, ETHUSDT, BTCUSDT,
  XRPUSDT, DOGEUSDT from `2024-01-26T00:00:00Z` through the last
  settlement strictly before `2025-03-01T00:00:00Z`. Write a checksum
  manifest next to the cache. Public Bybit v5 funding history only.
- Price bars: existing `data_cache` 60-minute Train-1 contract via
  `f006_family_runner.load_train1`. No 240-minute arm. No validation or
  holdout bars. No network fetch of OHLCV.
- One rule, `number_of_trials = 1`, exactly as the card. Previous
  settlement sign only. One settlement per hold. Costs stay 10 / 5 / 2
  bps. `max_sl_pct` stays 0.03. No threshold grid, no hold-length grid.
- Control arm: empty entry mask, funding events loaded, must reproduce
  0 trades and primary metric 0 before the carry arm is scored.
- Reconciliation arm before the score, as the card specifies.
- Primary metric M = funding_pnl - total_costs. Price gross PnL is
  reported and cannot turn a failing M into a pass.
- Runtime catalog registration only. Do not edit `strategy.py`.

## Out of scope

- Any backtest with `funding_events` omitted or empty.
- Spread-capture, catalog mean-reversion, a new family, a catalog
  unfreeze, holdout, Val-1.
- `.pi/config.json` and `F006-catalog5-unfreeze-correction/`.
- `git reset --hard`. Do not retune fees or the stop.

## Result

FALSIFIED (a)+(b). Funding was applied and reconciled. Details are in
`spec/research/F006-hypothesis-funding-carry.md` `## Result`. Artifacts are
in `output/f006_funding_carry/`; the funding cache and its checksum manifest
are in `data_cache/funding/`.

- Control: 0 trades and net 0 on all five symbols, with 1200 events loaded each.
- Reconciliation: 5,418 single-settlement holds. funding and net identity
  error is 0.0 on each. No hold contains more than one settlement.
- Mean M = -318.858103 (funding about +10 per symbol against costs of
  about 270 to 350). (a) fired.
- G = 0 (no green symbol-day); W = -1.038216. (b) fired.
- Decision: blank (owner).
