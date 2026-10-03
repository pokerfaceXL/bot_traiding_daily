# F006 · H-EMA-50-200-ENTRY-BREAKOUT-DEPTH-01 (T0-run)

## Outcome

Implement and run the pre-registered §8 breakout-depth entry gate on
`EMA_50_200` exactly per
`spec/research/F006-hypothesis-ema-50-200-entry-breakout-depth.md`. Earn one
entry-structure axis on this name's own trades (entry-vol, the xsym sizing
formula, and candle confirm are already closed). Fill `## Result`; leave
`## Decision` blank for the coordinator. Do not change profile `status:`
(keep CONDITIONAL). Do not FREEZE.

## Scope

- Write a thin sibling `scripts/f006_ema_50_200_entry_breakout_depth.py`
  adapting the control-first / grid harness from
  `scripts/f006_ema_50_200_entry_candle_confirm.py` (preferred). For the
  gate shape only, follow the structure of
  `scripts/f006_bb_20_2_entry_breakout_depth.py`, but the formula is this
  name's ema200 depth, not a Bollinger band. Same basket, NO_TRAIL,
  max_sl_pct=0.03, one-shot. Strategy name is `EMA_50_200`.
- Gate (ONE change): on the closed signal bar, keep only when
  ema200-normalized depth >= D:
  - long: `(close - ema200) / ema200 >= D`
  - short: `(ema200 - close) / ema200 >= D`
  - `ema200` missing or `<= 0` => reject
  Intersect with the one-shot entry mask of `EMA_50_200`. Exits use the
  ungated persistent signal (identical to the candle gate).
- Do not read `bb_20_2.0_*` or `bb_20_2.5_*`. Do not use ATR. Do not use
  `(close - low) / (high - low)`. Do not divide by `|ema50 - ema200|`
  (that gap is ~0 on the one-shot bar).
- D grid (frozen before gated cells): `{0.02, 0.05, 0.10, 0.25, 0.50}`.
  Units are fractions of ema200. Control = ungated.
  `number_of_trials = 5`. Do not retune after seeing results. This grid
  shape is the licensed breakout-depth pattern. It is not another name's
  measured depth means and not a copied winning D (there is none).
- Big-winner definition: freeze **net>=29.9** on this run's ungated blotter
  before gated cells. Candle freeze observed 5 trades /
  +843.7639016181568. Confirm; do not import another name's set.
- Control must reproduce THIS name's ungated Train-1 baseline before trusting
  gated cells:
  - mean train1_net_pnl **+72.6693115** (sum **+726.693115**)
  - Train-1 entry n **330**, entry net **+587.3851786486205**
  - initial_sl share **213/330 = 0.6454545454545455**
  - big-winner PnL **+843.7639016181568** (5 trades)
  - pooled losing entry-months **7/12**
  Source: `output/f006_ema_50_200_entry_candle_confirm/` control, which
  matches `output/f006_ema_50_200_abs_atr_gate/` control (diff 0).
  Checksums must match `output/f006_ema_50_200_abs_atr_gate/grid_freeze.json`.
  Do **not** reuse another script's EXPECTED_CHECKSUMS. Do **not** import
  +95.3217987, +82.900262, n=756, or n=512.
- Data: only the frozen Train-1 caches
  `*_20240126T000000Z_20250301T000000Z.csv`. Do not download. Do not load
  `*_20260901*` or `*_20200325*`. If the worktree has no `data_cache`, run
  against the main checkout's cache
  (`F006_DATA_CACHE=/home/limen/bot_traiding_daily/bot_traiding_daily/data_cache`)
  without copying validation ranges and without writing artifacts outside
  this worktree's `output/f006_ema_50_200_entry_breakout_depth/`.
- Artifacts under `output/f006_ema_50_200_entry_breakout_depth/` (results,
  cell_summary, grid_freeze written after the control check and before any
  gated cell, manifest, run.log, per-series raw / blotters as the candle
  sibling does).
- Fill the pre-registration note's `## Result` with the control + 5-D table
  and pass/fail vs the pre-declared falsifiers (a)-(e). Do **not** write
  `## Decision` or change profile `status:`.
- `python3 -m pytest -q` stays green. Add a focused test only if you add a
  new helper; do not retune an existing test to this name's numbers.

## Out of scope

- Profile status / journal NOW / §15 / Decision — coordinator only.
- Other catalog names, ATR gates, sizing (including any retune of the closed
  xsym formula 0.5 / 0.375 / 2.0), candle-strength retune, validation/holdout,
  grid widening, HTF / liquidity variants, `EMA3_13_50_200`, funding-carry,
  spread-capture, catalog mean-reversion.
- Merging to main. Do not commit `.pi/config.json` or
  `spec/features/active/F006-catalog5-unfreeze-correction/`.

## Acceptance

- Control reproduces this name's ungated Train-1 baseline (report the matched
  figure and the max abs diff). Expected mean +72.6693115.
- All 5 D cells reported; `number_of_trials = 5`.
- `## Result` filled; `## Decision` still empty; profile status still
  CONDITIONAL.
- Commit on the limen branch.

## Notes

Expect possible falsification (fat-tail runners may also clear ema200 by a
wide margin). Run honestly. If any D lowers the pooled floor while keeping
>=50% of this name's big-winner PnL and >=10 trades/series mean, flag it
clearly. Do not invent a second change. Do not treat BB_20_2 or BB_20_25
depth results as this result. Do not set FREEZE even if every falsifier fires.
