# F006 · H-EMA-50-200-ENTRY-LIQUIDITY-01 (T0-run)

## Outcome

Implement and run the pre-registered §8 liquidity entry gate on
`EMA_50_200` exactly per
`spec/research/F006-hypothesis-ema-50-200-entry-liquidity.md`. Earn one
entry-structure axis on this name's own trades (entry-vol, the xsym sizing
formula, candle confirm, breakout depth, and HTF direction are already
closed). Fill `## Result`; leave `## Decision` blank for the coordinator.
Do not change profile `status:` (keep CONDITIONAL). Do not FREEZE.

## Scope

- Write a thin sibling `scripts/f006_ema_50_200_entry_liquidity.py`
  adapting the control-first harness from
  `scripts/f006_ema_50_200_entry_htf_direction.py` (preferred). For the
  volume-window rules only, the shape of
  `scripts/f006_bb_20_2_entry_liquidity.py` is a reference — **the
  strategy, the baseline, and the columns are this name's**, not
  `BB_20_2_EMA200`, not `BB_20_25_EMA200`, and not `bb_20_*`. Same basket,
  NO_TRAIL, max_sl_pct=0.03, one-shot. Strategy name is `EMA_50_200`.
- Gate (ONE change): keep a one-shot signal iff the signal bar's native
  base `volume` is >= the median volume of the prior 20 closed bars
  (signal bar excluded). Rules are frozen on the card:
  - native base `volume` only; no quote volume; do not read `vol_ratio`
    or `vol_ma20`
  - window = volume[i-20:i]; fewer than 20 prior bars rejects
  - median not finite or median <= 0 rejects
  - missing volume rejects
  - ties at the median are kept
  - not `vol_ratio > 1.2`
  Intersect with the one-shot entry mask of `EMA_50_200`. Exits use the
  ungated persistent signal (identical to the HTF gate). Do not use ATR,
  ema50, ema200, candle strength, breakout depth, or HTF direction. Do not
  drop all shorts (long-only is a closed axis and is not this test).
- Binary gate. `number_of_trials = 1`. No multiple grid and no second
  window. Control = ungated. Write the freeze record after the control
  check and before the gated cell. This shape is the licensed liquidity
  pattern. It is not another name's measured liquidity mean and not a
  copied pass/fail. Do not import +97.2455987.
- Big-winner definition: freeze **net>=29.9** on this run's ungated blotter
  before the gated cell. HTF freeze observed 5 trades /
  +843.7639016181568. Confirm; do not import another name's set.
- Control must reproduce THIS name's ungated Train-1 baseline before trusting
  the gated cell:
  - mean train1_net_pnl **+72.6693115** (sum **+726.693115**)
  - Train-1 entry n **330**, entry net **+587.3851786486205**
  - initial_sl share **213/330 = 0.6454545454545455**
  - big-winner PnL **+843.7639016181568** (5 trades)
  - pooled losing entry-months **7/12**
  Source: `output/f006_ema_50_200_entry_htf_direction/` control, which
  matches `output/f006_ema_50_200_entry_breakout_depth/`,
  `output/f006_ema_50_200_entry_candle_confirm/`, and
  `output/f006_ema_50_200_abs_atr_gate/` control (diff 0).
  Checksums must match `output/f006_ema_50_200_abs_atr_gate/grid_freeze.json`.
  Do **not** reuse another script's EXPECTED_CHECKSUMS. Do **not** import
  +95.3217987, +82.900262, n=756, or n=512. Do **not** import another name's
  liquidity-cell mean or its pass/fail.
- Data: only the frozen Train-1 caches
  `*_20240126T000000Z_20250301T000000Z.csv`. Do not download. Do not load
  `*_20260901*` or `*_20200325*`. If the worktree has no `data_cache`, run
  against the main checkout's cache
  (`F006_DATA_CACHE=/home/limen/bot_traiding_daily/bot_traiding_daily/data_cache`)
  without copying validation ranges and without writing artifacts outside
  this worktree's `output/f006_ema_50_200_entry_liquidity/`.
- Artifacts under `output/f006_ema_50_200_entry_liquidity/` (results,
  cell_summary, grid_freeze written after the control check and before the
  gated cell, manifest, run.log, per-series raw / blotters as the HTF
  sibling does).
- Fill the pre-registration note's `## Result` with the control + gated
  table and pass/fail vs the pre-declared falsifiers (a)-(e). Do **not**
  write `## Decision` or change profile `status:`.
- `python3 -m pytest -q` stays green. Add a focused test only if you add a
  new helper; do not retune an existing test to this name's numbers.

## Out of scope

- Profile status / journal NOW / §15 / Decision — coordinator only.
- Other catalog names, ATR gates, sizing (including any retune of the closed
  xsym formula 0.5 / 0.375 / 2.0), candle-strength retune, depth retune,
  HTF-length retune, validation/holdout, a second volume window,
  `vol_ratio > 1.2`, `EMA3_13_50_200`, funding-carry, spread-capture,
  catalog mean-reversion.
- Merging to main. Do not commit `.pi/config.json` or
  `spec/features/active/F006-catalog5-unfreeze-correction/`.
- Setting FREEZE. This is the last licensed axis. FREEZE, if the falsifiers
  fire on this name's own trades and no licensed axis remains, is only at
  this experiment's later Decision. The worker does not set it. The ungated
  book staying aggregate-positive is not a pass and is not a FREEZE in this
  run.

## Acceptance

- Control reproduces this name's ungated Train-1 baseline (report the matched
  figure and the max abs diff). Expected mean +72.6693115, n=330.
- The one gated cell is reported; `number_of_trials = 1`.
- `## Result` filled; `## Decision` still empty; profile status still
  CONDITIONAL.
- Commit on the limen branch.

## Notes

Expect possible falsification (quiet and loud bars can both hold the
runners and the stop-outs). Run honestly. If the gate lowers the pooled
floor while keeping >=50% of this name's big-winner PnL and >=10
trades/series mean, flag it clearly. Do not invent a second change. Do not
treat BB_20_2 liquidity (`776e167`) as this result. Do not set FREEZE even
if every falsifier fires.
