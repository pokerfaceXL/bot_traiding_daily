# F006 · H-BB-20-2-ENTRY-BREAKOUT-DEPTH-01 (T0-run)

## Outcome

Implement and run the pre-registered §8 breakout-depth entry gate on
`BB_20_2_EMA200` exactly per
`spec/research/F006-hypothesis-bb-20-2-entry-breakout-depth.md`. Earn one
entry-structure axis on this name's own trades (entry-vol, the xsym sizing
formula, and candle close-strength are already closed). Fill `## Result`;
leave `## Decision` blank for the coordinator. Do not change profile
`status:` (keep CONDITIONAL). Do not FREEZE.

## Scope

- Write a thin sibling `scripts/f006_bb_20_2_entry_breakout_depth.py` adapting
  the control-first / grid harness from
  `scripts/f006_bb_20_2_entry_candle_confirm.py` (preferred). For the depth
  formula only, the shape of `scripts/f006_bb_20_25_entry_breakout_depth.py`
  is a reference — **columns must be this name's k=2.0 bands**, not
  `bb_20_2.5_*`. Same basket, NO_TRAIL, max_sl_pct=0.03, one-shot. Strategy
  name is `BB_20_2_EMA200`.
- Gate (ONE change): on the closed signal bar, keep only when
  band-normalized depth ≥ D:
  - `width = bb_20_2.0_upper - bb_20_2.0_lower`
  - long: `(close - bb_20_2.0_upper) / width >= D`
  - short: `(bb_20_2.0_lower - close) / width >= D`
  - `width <= 0` ⇒ reject
  Do **not** use `bb_20_2.0_width` (that column is `(2*k*std)/mid`, a
  different feature). Do **not** use `bb_20_2.5_upper` / `bb_20_2.5_lower`.
  Intersect with `entry_masks.one_shot_entry_mask` of `BB_20_2_EMA200`. Exits
  use the ungated persistent signal (identical to the candle gate).
- D grid (frozen before gated cells): `{0.02, 0.05, 0.10, 0.25, 0.50}`.
  Control = ungated. Do not retune after seeing results.
- Big-winner definition: freeze **net≥29.9** before the run. Retention is
  baseline big winners surviving by symbol/interval/entry_time/direction
  (same measure as the candle card on this name).
- Add a small unit test that the gate reads `bb_20_2.0_upper` /
  `bb_20_2.0_lower` (not `bb_20_2.5_*` and not `bb_20_2.0_width`) and that
  the card's baseline is +95.3217987, not +82.900262.
- Control must reproduce THIS name's ungated Train-1 baseline before trusting
  gated cells:
  - mean train1_net_pnl **+95.3217987**
  - Train-1 entry n **756**, entry net ≈ **+834.347778**
  - initial_sl share ≈ **0.473545**
  - big-winner PnL ≈ **1251.654084** (12 trades)
  - pooled losing entry-months **7/12**
  Source: `output/f006_bb_20_2_entry_candle_confirm/cell_summary.csv` control
  row. Do **not** import +82.900262, n=512, or any `BB_20_25_EMA200` figure.
- Artifacts under `output/f006_bb_20_2_entry_breakout_depth/` (results,
  cell_summary, grid_freeze, manifest, run.log, per-series raw / blotters as
  needed).
- Fill the pre-registration note's `## Result` with the control + 5-D table
  and pass/fail vs the pre-declared falsifiers (a)–(e). Do **not** write
  `## Decision` or change profile `status:`.
- If this worktree has no `data_cache` CSVs, point the run at the main
  checkout cache
  (`F006_DATA_CACHE=/home/limen/bot_traiding_daily/bot_traiding_daily/data_cache`).
  Do not commit `data_cache`.

## Out of scope

- Profile status / journal NOW / §15 / Decision — coordinator only.
- Other catalog5 names, ATR gates, sizing (incl. any retune of the closed
  xsym formula), candle-T retune, validation/holdout, grid widening, HTF /
  liquidity variants.
- Merging to main. Do not commit `.pi/config.json` or
  `spec/features/active/F006-catalog5-unfreeze-correction/`.

## Acceptance

- Control reproduces this name's ungated Train-1 baseline (report the matched
  figure).
- All 5 D cells reported; `number_of_trials = 5`.
- Depth uses `bb_20_2.0_upper` / `bb_20_2.0_lower` only.
- `## Result` filled; `python3 -m pytest -q` stays green.
- Commit on the limen branch.

## Notes

Expect possible falsification (fat-tail runners may also be deep pierces).
Run honestly — if any D lowers the pooled floor while keeping ≥50% big-winner
PnL and ≥10 trades/series mean, flag it clearly; do not bury an exception.
Do not invent a second change. Do not treat the other name's breakout-depth
FALSIFIED (a)+(c) at `0685ce5` as this result.
