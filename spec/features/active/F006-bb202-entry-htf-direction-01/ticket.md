# F006 · H-BB-20-2-ENTRY-HTF-DIRECTION-01 (T0-run)

## Outcome

Implement and run the pre-registered §8 HTF-direction entry gate on
`BB_20_2_EMA200` exactly per
`spec/research/F006-hypothesis-bb-20-2-entry-htf-direction.md`. Earn one
entry-structure axis on this name's own trades (entry-vol, the xsym sizing
formula, candle close-strength, and breakout depth are already closed).
Fill `## Result`; leave `## Decision` blank for the coordinator. Do not
change profile `status:` (keep CONDITIONAL). Do not FREEZE.

## Scope

- Write a thin sibling `scripts/f006_bb_20_2_entry_htf_direction.py` adapting
  the control-first harness from
  `scripts/f006_bb_20_2_entry_breakout_depth.py` (preferred). For the HTF
  bucket rules only, the shape of
  `scripts/f006_bb_20_25_entry_htf_direction.py` is a reference — **the
  strategy, the baseline, and the bands are this name's**, not
  `BB_20_25_EMA200` and not `bb_20_2.5_*`. Same basket, NO_TRAIL,
  max_sl_pct=0.03, one-shot. Strategy name is `BB_20_2_EMA200`.
- Gate (ONE change): keep a one-shot signal only when the prior fully closed
  4-bar HTF candle agrees in direction. Rules are frozen on the card:
  - htf length = 4 native bars (60m → 240m buckets, 240m → 960m buckets)
  - Unix-epoch floor of bar open time
  - bucket close time <= signal bar open time (signal bar is not inside the bucket)
  - exactly 4 native bars required, else reject
  - direction = sign(htf_close − htf_open); flat rejects
  - long kept only if htf_dir == +1; short kept only if htf_dir == -1
  Intersect with `entry_masks.one_shot_entry_mask` of `BB_20_2_EMA200`.
  Exits use the ungated persistent signal (identical to the breakout-depth
  gate). Do not use ATR, EMA, candle strength, or breakout depth. Do not
  drop all shorts (long-only is a closed axis and is not this test).
- Binary gate. `number_of_trials = 1`. No strength grid and no second HTF
  length. Control = ungated. Write the freeze record before the gated cell.
- Big-winner definition: freeze **net≥29.9** before the gated cell.
  Retention is baseline big winners surviving by
  symbol/interval/entry_time/direction (same measure as the breakout-depth
  card on this name).
- Add a small unit test that the gate does not read `bb_20_2.5_*`, ATR,
  candle-strength, or breakout depth, and that the card's baseline is
  +95.3217987, not +82.900262.
- Control must reproduce THIS name's ungated Train-1 baseline before
  trusting the gated cell:
  - mean train1_net_pnl **+95.3217987**
  - Train-1 entry n **756**, entry net ≈ **+834.347778**
  - initial_sl share ≈ **0.473545** (358/756)
  - big-winner PnL ≈ **1251.654084** (12 trades)
  - pooled losing entry-months **7/12**
  Source: `output/f006_bb_20_2_entry_breakout_depth/cell_summary.csv`
  control row. Do **not** import +82.900262, n=512, initial_sl 0.580078,
  big-winner 968.020732, or the `BB_20_25_EMA200` HTF cell at `3495b16`.
- Use only the frozen Train-1 caches
  (`*_20240126T000000Z_20250301T000000Z.csv`). Do not download. Do not load
  `*_20260901*` or `*_20200325*`. If this worktree has no `data_cache`
  CSVs, point the run at the main checkout cache
  (`F006_DATA_CACHE=/home/limen/bot_traiding_daily/bot_traiding_daily/data_cache`).
  Do not commit `data_cache`. Artifacts stay under
  `output/f006_bb_20_2_entry_htf_direction/`.
- Tests: sibling of `tests/test_bb_20_2_entry_breakout_depth.py` covering
  agreement, flat reject, incomplete bucket reject, and that the signal bar
  is not inside the HTF bucket used (including when the signal bar is the
  last bar of its own bucket).
- Fill the pre-registration note's `## Result` with the control + gated
  cell and pass/fail vs falsifiers (a)–(e). Do **not** write `## Decision`
  or change profile `status:`.

## Out of scope

- Profile status / journal NOW / §15 / Decision — coordinator only.
- Other catalog5 names, ATR gates, sizing (incl. any retune of the closed
  xsym formula), candle-T retune, breakout-depth retune, long-only,
  liquidity, validation/holdout, a second HTF length, a strength threshold.
- Merging to main. Do not commit `.pi/config.json` or
  `spec/features/active/F006-catalog5-unfreeze-correction/`.

## Acceptance

- Control reproduces this name's ungated Train-1 baseline (report the
  matched figure). Do not report +82.900262 as this control.
- The single gated cell is reported; `number_of_trials = 1`.
- `## Result` filled; `python3 -m pytest -q` stays green.
- Commit on the limen branch.

## Notes

Expect possible falsification (HTF color may co-move with the same
breakouts that depth and candle location failed to separate on this name).
Run honestly. Do not invent a second change. Do not set FREEZE even if the
cell fails. Do not treat the other name's HTF FALSIFIED (a)+(c)+(d) at
`3495b16` as this result.
