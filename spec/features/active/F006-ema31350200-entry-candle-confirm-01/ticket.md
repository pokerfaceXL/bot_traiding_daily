# F006 · H-EMA3-13-50-200-ENTRY-CANDLE-CONFIRM-01 (T0-run)

## Outcome

Implement and run the pre-registered §8 candle-confirmation entry gate on
`EMA3_13_50_200` exactly per
`spec/research/F006-hypothesis-ema3-13-50-200-entry-candle-confirm.md`. Earn one
entry-structure axis on this name's own trades (entry-vol and the xsym sizing
formula are already closed). Fill `## Result`; leave `## Decision` blank for
the coordinator. Do not change profile `status:` (keep CONDITIONAL). Do not
FREEZE.

## Scope

- Write a thin sibling `scripts/f006_ema3_13_50_200_entry_candle_confirm.py`
  adapting the control-first / grid harness from
  `scripts/f006_ema3_13_50_200_abs_atr_gate.py` (preferred) and, for the OHLC
  close-strength gate only, the shape of
  `scripts/f006_ema_50_200_entry_candle_confirm.py`. Same basket, NO_TRAIL,
  max_sl_pct=0.03, one-shot. Strategy name is `EMA3_13_50_200`
  (`sig_ema3_cross(13, 50, 200)`). Not `EMA_50_200`. Not a BB name.
- Gate (ONE change): on the closed signal bar, keep only when directional
  close-strength >= T:
  - long: `(close - low) / (high - low) >= T`
  - short: `(high - close) / (high - low) >= T`
  - `high == low` => reject
  Intersect with the one-shot entry mask of `EMA3_13_50_200`. Exits use the
  ungated persistent signal (identical to the abs-ATR gate). Do not apply
  the closed xsym stake multiplier.
- T grid (frozen before gated cells): `{0.50, 0.60, 0.70, 0.80, 0.90}`.
  Control = ungated. `number_of_trials = 5`. Do not retune after seeing
  results. This grid shape is the licensed candle-confirm pattern. It is
  not BB_20_2's T=0.60 result, not BB_20_25's T=0.70 result, and not
  `EMA_50_200`'s failed best T=0.50 chosen as the answer. Report every T.
- Big-winner definition: freeze **net>=29.9** on this run's ungated blotter
  before gated cells. Abs-ATR freeze observed 9 trades /
  +1131.9561537333418. The xsym control confirmed 9 / +1131.956154. Confirm;
  do not import another name's set (not 5 / +843.7639016181568).
- Control must reproduce THIS name's ungated Train-1 baseline before trusting
  gated cells:
  - mean train1_net_pnl **+91.1483016** (sum **+911.483016**)
  - Train-1 entry n **423**, entry net **+771.283617**
  - initial_sl share **292/423 = 0.6903073286052009**
  - big-winner PnL **+1131.9561537333418** (9 trades)
  - pooled losing entry-months **7/12**
  Source: `output/f006_ema3_13_50_200_abs_atr_gate/` control, confirmed by
  `output/f006_ema3_13_50_200_xsym_agree_sizing/summary/cell_summary.json`.
  Checksums must match `output/f006_ema3_13_50_200_abs_atr_gate/grid_freeze.json`.
  Do **not** reuse another script's EXPECTED_CHECKSUMS. Do **not** import
  +72.6693115, +95.3217987, +82.900262, +126.744211, n=330, n=756, or n=512.
- Data: only the frozen Train-1 caches
  `*_20240126T000000Z_20250301T000000Z.csv`. Do not download. Do not load
  `*_20260901*` or `*_20200325*`. If the worktree has no `data_cache`, run
  against the main checkout's cache
  (`F006_DATA_CACHE=/home/limen/bot_traiding_daily/bot_traiding_daily/data_cache`)
  without copying validation ranges and without writing artifacts outside
  this worktree's `output/f006_ema3_13_50_200_entry_candle_confirm/`.
- Artifacts under `output/f006_ema3_13_50_200_entry_candle_confirm/` (results,
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
  breakout-depth / HTF / liquidity variants, funding-carry, spread-capture,
  catalog mean-reversion.
- Merging to main. Do not commit `.pi/config.json` or
  `spec/features/active/F006-catalog5-unfreeze-correction/`.

## Acceptance

- Control reproduces this name's ungated Train-1 baseline (report the matched
  figure and the max abs diff). Expected mean +91.1483016. Expected n=423.
- All 5 T cells reported; `number_of_trials = 5`.
- `## Result` filled; `## Decision` still empty; profile status still
  CONDITIONAL.
- Commit on the limen branch.

## Notes

Expect possible falsification (fat-tail runners may also have strong closes).
Run honestly. If any T lowers the pooled floor while keeping >=50% of this
name's big-winner PnL and >=10 trades/series mean, flag it clearly. Do not
invent a second change. Do not treat `778f373`, `88b0ee3`, or `e70161d` as
this result. Do not set FREEZE even if every falsifier fires. On this card
(b) is big-winner removal, not a flat month floor; the floor clause is (d)
and only applies at a T that otherwise passes (a)-(c).
