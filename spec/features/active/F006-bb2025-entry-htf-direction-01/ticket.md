# F006 · H-BB-20-25-ENTRY-HTF-DIRECTION-01 (T0-run)

## Outcome

Implement and run the pre-registered §8 HTF-direction entry gate on `BB_20_25_EMA200`
exactly per `spec/research/F006-hypothesis-bb-20-25-entry-htf-direction.md`. Earn the
remaining open entry axis on this name's own trades (entry-vol, the xsym sizing
formula, candle close-strength, and breakout depth are already closed). Fill
`## Result`; leave `## Decision` blank for the coordinator. Do not change profile
`status:` (keep CONDITIONAL). Do not FREEZE.

## Scope

- Write a thin sibling `scripts/f006_bb_20_25_entry_htf_direction.py` adapting the
  control-first harness from `scripts/f006_bb_20_25_entry_breakout_depth.py`.
  Same basket, NO_TRAIL, max_sl_pct=0.03, one-shot.
- Gate (ONE change): keep a one-shot signal only when the prior fully closed
  4-bar HTF candle agrees in direction. Rules are frozen on the card:
  - htf length = 4 native bars (60m → 240m buckets, 240m → 960m buckets)
  - Unix-epoch floor of bar open time
  - bucket close time <= signal bar open time (signal bar is not inside the bucket)
  - exactly 4 native bars required, else reject
  - direction = sign(htf_close − htf_open); flat rejects
  - long kept only if htf_dir == +1; short kept only if htf_dir == -1
  Intersect with `entry_masks.one_shot_entry_mask` of `BB_20_25_EMA200`. Exits use
  the ungated persistent signal. Do not use ATR, EMA, candle strength, or breakout
  depth. Do not drop all shorts (long-only is a closed axis).
- Binary gate. `number_of_trials = 1`. No strength grid and no second HTF length.
  Control = ungated. Write the freeze record before the gated cell.
- Big-winner definition: freeze **net≥29.9** before the gated cell.
- Control must reproduce mean Train-1 net PnL +82.900262 (n=512 cohort, initial-SL
  share 0.580078125, big-winner PnL 968.020732, floor 7/12) before trusting the gate.
- Use only the frozen Train-1 caches already in `data_cache/`
  (`*_20240126T000000Z_20250301T000000Z.csv`). Do not download. Do not load
  `*_20260901*` or `*_20200325*`. `data_cache` is gitignored and is read relative
  to the process cwd; if the worktree has no copy, run against the main checkout's
  cache without copying validation ranges and without writing artifacts outside
  this worktree's `output/f006_bb_20_25_entry_htf_direction/`.
- Artifacts under `output/f006_bb_20_25_entry_htf_direction/` (results, cell_summary,
  grid_freeze, manifest, run.log, per-series raw / blotters as the sibling script does).
- Tests: sibling of `tests/test_bb_20_25_entry_breakout_depth.py` covering agreement,
  flat reject, incomplete bucket reject, and that the signal bar is not inside the
  HTF bucket used (including when the signal bar is the last bar of its own bucket).
- Fill the pre-registration note's `## Result` with the control + gated cell and
  pass/fail vs falsifiers (a)–(e). Do **not** write `## Decision` or change profile
  `status:`.

## Out of scope

- Profile status / journal NOW / §15 / Decision — coordinator only.
- Other catalog5 names, ATR gates, candle-strength retune, breakout-depth retune,
  sizing (incl. any retune of the closed xsym formula), long-only, validation/holdout,
  a second HTF length, a strength threshold.
- Merging to main. Do not commit `.pi/config.json` or
  `spec/features/active/F006-catalog5-unfreeze-correction/`.

## Acceptance

- Control reproduces this name's ungated Train-1 baseline (report the matched figure).
- The single gated cell is reported; `number_of_trials = 1`.
- `## Result` filled; `python3 -m pytest -q` stays green.
- Commit on the limen branch.

## Notes

Expect possible falsification (HTF color may co-move with the same breakouts that
depth and candle location failed to separate). Run honestly. Do not invent a second
change. Do not set FREEZE even if the cell fails.
