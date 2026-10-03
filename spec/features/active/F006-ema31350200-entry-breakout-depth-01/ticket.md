# F006 · H-EMA3-13-50-200-ENTRY-BREAKOUT-DEPTH-01 (T0-run)

## Outcome

Implement and run the pre-registered §8 breakout-depth entry gate on
`EMA3_13_50_200` exactly per
`spec/research/F006-hypothesis-ema3-13-50-200-entry-breakout-depth.md`. Earn one
entry-structure axis on this name's own trades (entry-vol, the xsym sizing
formula, and candle confirm are already closed). Fill `## Result`; leave
`## Decision` blank for the coordinator. Do not change profile `status:`
(keep CONDITIONAL). Do not FREEZE.

## Scope

- Write a thin sibling `scripts/f006_ema3_13_50_200_entry_breakout_depth.py`
  adapting the control-first / grid harness from
  `scripts/f006_ema3_13_50_200_entry_candle_confirm.py` (preferred). For the
  gate shape only, follow the structure of
  `scripts/f006_ema_50_200_entry_breakout_depth.py`, but the formula is this
  name's ema200 depth on `sig_ema3_cross(13, 50, 200)`, not a Bollinger band
  and not `EMA_50_200`. Same basket, NO_TRAIL, max_sl_pct=0.03, one-shot.
  Strategy name is `EMA3_13_50_200`. Columns are `ema13`, `ema50`, `ema200`.
  There is no `ema3` column in this signal.
- Gate (ONE change): on the closed signal bar, keep only when
  ema200-normalized depth >= D:
  - long: `(close - ema200) / ema200 >= D`
  - short: `(ema200 - close) / ema200 >= D`
  - `ema200` missing or `<= 0` => reject
  Intersect with the one-shot entry mask of `EMA3_13_50_200`. Exits use the
  ungated persistent signal (identical to the candle gate). Do not apply
  the closed xsym stake multiplier.
- Do not read `bb_20_2.0_*` or `bb_20_2.5_*`. Do not use ATR. Do not use
  `(close - low) / (high - low)`. Do not divide by `|ema13 - ema50|` or
  `|ema50 - ema200|` (a pairwise gap can be ~0 on the one-shot bar).
- D grid (frozen before gated cells): `{0.02, 0.05, 0.10, 0.25, 0.50}`.
  Units are fractions of ema200. Control = ungated.
  `number_of_trials = 5`. Do not retune after seeing results. This grid
  shape is the licensed breakout-depth pattern. It is not another name's
  measured depth means and not a copied winning D (there is none; do not
  pre-pick 0.02 because `EMA_50_200` printed it).
- Big-winner definition: freeze **net>=29.9** on this run's ungated blotter
  before gated cells. Candle freeze observed 9 trades /
  +1131.9561537333418. Confirm; do not import another name's set (not 5 /
  +843.7639016181568).
- Control must reproduce THIS name's ungated Train-1 baseline before trusting
  gated cells:
  - mean train1_net_pnl **+91.1483016** (sum **+911.483016**)
  - Train-1 entry n **423**, entry net **+771.2836172145888236**
  - initial_sl share **292/423 = 0.6903073286052009**
  - big-winner PnL **+1131.95615373334168** (9 trades)
  - pooled losing entry-months **7/12**
  Source: `output/f006_ema3_13_50_200_entry_candle_confirm/` control, which
  matches `output/f006_ema3_13_50_200_abs_atr_gate/` control (diff 0).
  Checksums must match `output/f006_ema3_13_50_200_abs_atr_gate/grid_freeze.json`.
  Do **not** reuse another script's EXPECTED_CHECKSUMS. Do **not** import
  +72.6693115, +95.3217987, +82.900262, +126.744211, +45.0267104,
  +63.0343180, +87.8448967, n=330, n=756, or n=512.
- Data: only the frozen Train-1 caches
  `*_20240126T000000Z_20250301T000000Z.csv`. Do not download. Do not load
  `*_20260901*` or `*_20200325*`. If the worktree has no `data_cache`, run
  against the main checkout's cache
  (`F006_DATA_CACHE=/home/limen/bot_traiding_daily/bot_traiding_daily/data_cache`)
  without copying validation ranges and without writing artifacts outside
  this worktree's `output/f006_ema3_13_50_200_entry_breakout_depth/`.
- Artifacts under `output/f006_ema3_13_50_200_entry_breakout_depth/` (results,
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
  grid widening, HTF / liquidity variants, funding-carry, spread-capture,
  catalog mean-reversion.
- Merging to main. Do not commit `.pi/config.json` or
  `spec/features/active/F006-catalog5-unfreeze-correction/`.

## Acceptance

- Control reproduces this name's ungated Train-1 baseline (report the matched
  figure and the max abs diff). Expected mean +91.1483016. Expected n=423.
- All 5 D cells reported; `number_of_trials = 5`.
- `## Result` filled; `## Decision` still empty; profile status still
  CONDITIONAL.
- Commit on the limen branch.

## Notes

Expect possible falsification (fat-tail runners may also clear ema200 by a
wide margin). Run honestly. If any D lowers the pooled floor while keeping
>=50% of this name's big-winner PnL and >=10 trades/series mean, flag it
clearly. Do not invent a second change. Do not treat `485de51`, `27fa7f6`,
or `0685ce5` as this result. Do not set FREEZE even if every falsifier
fires. On this card (b) is big-winner removal ("removes >50%"), not a flat
month floor; the floor clause is (d) and only applies at a D that otherwise
passes (a)-(c).
