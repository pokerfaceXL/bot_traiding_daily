# F006 · H-EMA-50-200-ENTRY-CANDLE-CONFIRM-01 (T0-run)

## Outcome

Implement and run the pre-registered §8 candle-confirmation entry gate on
`EMA_50_200` exactly per
`spec/research/F006-hypothesis-ema-50-200-entry-candle-confirm.md`. Earn one
entry-structure axis on this name's own trades (entry-vol and the xsym sizing
formula are already closed). Fill `## Result`; leave `## Decision` blank for
the coordinator. Do not change profile `status:` (keep CONDITIONAL). Do not
FREEZE.

## Scope

- Write a thin sibling `scripts/f006_ema_50_200_entry_candle_confirm.py`
  adapting the control-first / grid harness from
  `scripts/f006_ema_50_200_abs_atr_gate.py` (preferred) and, for the OHLC
  close-strength gate only, the shape of
  `scripts/f006_bb_20_2_entry_candle_confirm.py`. Same basket, NO_TRAIL,
  max_sl_pct=0.03, one-shot. Strategy name is `EMA_50_200`.
- Gate (ONE change): on the closed signal bar, keep only when directional
  close-strength >= T:
  - long: `(close - low) / (high - low) >= T`
  - short: `(high - close) / (high - low) >= T`
  - `high == low` => reject
  Intersect with the one-shot entry mask of `EMA_50_200`. Exits use the
  ungated persistent signal (identical to the abs-ATR gate).
- T grid (frozen before gated cells): `{0.50, 0.60, 0.70, 0.80, 0.90}`.
  Control = ungated. `number_of_trials = 5`. Do not retune after seeing
  results. This grid shape is the licensed candle-confirm pattern. It is
  not BB_20_2's T=0.60 result and not BB_20_25's T=0.70 result.
- Big-winner definition: freeze **net>=29.9** on this run's ungated blotter
  before gated cells. Abs-ATR freeze observed 5 trades /
  +843.7639016181568. Confirm; do not import another name's set.
- Control must reproduce THIS name's ungated Train-1 baseline before trusting
  gated cells:
  - mean train1_net_pnl **+72.6693115** (sum **+726.693115**)
  - Train-1 entry n **330**, entry net **+587.3851786486205**
  - initial_sl share **213/330 = 0.6454545454545455**
  - big-winner PnL **+843.7639016181568** (5 trades)
  - pooled losing entry-months **7/12**
  Source: `output/f006_ema_50_200_abs_atr_gate/` control, confirmed by
  `output/f006_ema_50_200_xsym_agree_sizing/summary/cell_summary.json`.
  Checksums must match `output/f006_ema_50_200_abs_atr_gate/grid_freeze.json`.
  Do **not** reuse another script's EXPECTED_CHECKSUMS. Do **not** import
  +95.3217987, +82.900262, n=756, or n=512.
- Data: only the frozen Train-1 caches
  `*_20240126T000000Z_20250301T000000Z.csv`. Do not download. Do not load
  `*_20260901*` or `*_20200325*`. If the worktree has no `data_cache`, run
  against the main checkout's cache
  (`F006_DATA_CACHE=/home/limen/bot_traiding_daily/bot_traiding_daily/data_cache`)
  without copying validation ranges and without writing artifacts outside
  this worktree's `output/f006_ema_50_200_entry_candle_confirm/`.
- Artifacts under `output/f006_ema_50_200_entry_candle_confirm/` (results,
  cell_summary, grid_freeze written after the control check and before any
  gated cell, manifest, run.log, per-series raw / blotters as the abs-ATR
  sibling does).
- Fill the pre-registration note's `## Result` with the control + 5-T table
  and pass/fail vs the pre-declared falsifiers (a)-(e). Do **not** write
  `## Decision` or change profile `status:`.
- `python3 -m pytest -q` stays green. Add a focused test only if you add a
  new helper; do not retune an existing test to this name's numbers.

## Out of scope

- Profile status / journal NOW / §15 / Decision — coordinator only.
- Other catalog names, ATR gates, sizing (including any retune of the closed
  xsym formula 0.5 / 0.375 / 2.0), validation/holdout, grid widening,
  breakout-depth / HTF / liquidity variants, `EMA3_13_50_200`, funding-carry,
  spread-capture, catalog mean-reversion.
- Merging to main. Do not commit `.pi/config.json` or
  `spec/features/active/F006-catalog5-unfreeze-correction/`.

## Acceptance

- Control reproduces this name's ungated Train-1 baseline (report the matched
  figure and the max abs diff). Expected mean +72.6693115.
- All 5 T cells reported; `number_of_trials = 5`.
- `## Result` filled; `## Decision` still empty; profile status still
  CONDITIONAL.
- Commit on the limen branch.

## Notes

Expect possible falsification (fat-tail runners may also have strong closes).
Run honestly. If any T lowers the pooled floor while keeping >=50% of this
name's big-winner PnL and >=10 trades/series mean, flag it clearly. Do not
invent a second change. Do not treat `88b0ee3` or `e70161d` as this result.
Do not set FREEZE even if every falsifier fires.
