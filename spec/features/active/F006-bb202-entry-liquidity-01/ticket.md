# F006 · H-BB-20-2-ENTRY-LIQUIDITY-01 (T0-run)

## Outcome

Implement and run the pre-registered §8 liquidity entry gate on
`BB_20_2_EMA200` exactly per
`spec/research/F006-hypothesis-bb-20-2-entry-liquidity.md`. Earn the last
named entry-structure axis on this name's own trades (entry-vol, the xsym
sizing formula, candle close-strength, breakout depth, and HTF direction
are already closed). Fill `## Result`; leave `## Decision` blank for the
coordinator. Do not change profile `status:` (keep CONDITIONAL). Do not
FREEZE.

## Scope

- Write a thin sibling `scripts/f006_bb_20_2_entry_liquidity.py` adapting
  the control-first harness from
  `scripts/f006_bb_20_2_entry_htf_direction.py`. Same basket, NO_TRAIL,
  max_sl_pct=0.03, one-shot. Strategy name is `BB_20_2_EMA200`.
- Gate (ONE change): keep a one-shot signal only when the signal bar's
  native base `volume` is >= the median `volume` of the prior 20 fully
  closed native bars. Rules are frozen on the card:
  - window = the 20 bars strictly before the signal bar (signal bar excluded)
  - fewer than 20 prior bars → reject
  - median not finite or median <= 0 → reject
  - missing volume → reject
  - keep iff signal-bar volume >= median (ties kept)
  Intersect with `entry_masks.one_shot_entry_mask` of `BB_20_2_EMA200`.
  Exits use the ungated persistent signal (identical to the HTF gate).
  Do not use ATR, EMA, candle strength, breakout depth, or HTF direction.
  Do not read `vol_ratio` or `vol_ma20`. Do not implement `vol_ratio > 1.2`
  (`BB_20_2_VOL12` / `sig_bb_breakout_vol`). Do not drop all shorts
  (long-only is a closed axis and is not this test).
- Binary gate. `number_of_trials = 1`. No multiple grid and no second
  window. Control = ungated. Write the freeze record before the gated cell.
- Big-winner definition: freeze **net≥29.9** before the gated cell.
  Retention is baseline big winners surviving by
  symbol/interval/entry_time/direction (same measure as the HTF card on
  this name).
- Add a small unit test that the gate does not read `bb_20_2.5_*`, ATR,
  `vol_ratio`, candle-strength, breakout depth, or HTF direction, and that
  the card's baseline is +95.3217987, not +82.900262. Also test: below
  median rejects, equal to median keeps, short window rejects, zero median
  rejects, and the signal bar is not inside the window.
- Control must reproduce THIS name's ungated Train-1 baseline before
  trusting the gated cell:
  - mean train1_net_pnl **+95.3217987**
  - Train-1 entry n **756**, entry net ≈ **+834.347778**
  - initial_sl share ≈ **0.47354497354497355** (358/756)
  - big-winner PnL ≈ **1251.654084307187** (12 trades)
  - pooled losing entry-months **7/12**
  Source: `output/f006_bb_20_2_entry_htf_direction/cell_summary.csv`
  control row. Do **not** import +82.900262, n=512, initial_sl 0.580078,
  big-winner 968.020732, or the `BB_20_25_EMA200` HTF cell at `3495b16`.
- Use only the frozen Train-1 caches
  (`*_20240126T000000Z_20250301T000000Z.csv`). Do not download. Do not load
  `*_20260901*` or `*_20200325*`. If this worktree has no `data_cache`
  CSVs, point the run at the main checkout cache
  (`F006_DATA_CACHE=/home/limen/bot_traiding_daily/bot_traiding_daily/data_cache`).
  Do not commit `data_cache`. Artifacts stay under
  `output/f006_bb_20_2_entry_liquidity/`.
- Tests: sibling of `tests/test_bb_20_2_entry_htf_direction.py`.
- Fill the pre-registration note's `## Result` with the control + gated
  cell and pass/fail vs falsifiers (a)–(e). Do **not** write `## Decision`
  or change profile `status:`.

## Out of scope

- Profile status / journal NOW / §15 / Decision — coordinator only.
- Other catalog5 names, ATR gates, sizing (incl. any retune of the closed
  xsym formula), candle-T retune, breakout-depth retune, HTF-length retune,
  long-only, validation/holdout, a second window, a volume multiple, quote
  volume, `RVOL_RE_*`, `liq_range_eqh`.
- Merging to main. Do not commit `.pi/config.json` or
  `spec/features/active/F006-catalog5-unfreeze-correction/`.
- Do not set FREEZE even if the cell fails. FREEZE, if the protocol allows
  it after a falsification, is the coordinator's Decision on this
  experiment, not this run.

## Acceptance

- Control reproduces this name's ungated Train-1 baseline (report the
  matched figure). Do not report +82.900262 as this control.
- The single gated cell is reported; `number_of_trials = 1`.
- `## Result` filled; `python3 -m pytest -q` stays green.
- Commit on the limen branch.

## Notes

Expect possible falsification (base volume may co-move with the same
breakouts that HTF direction, depth, and candle location failed to
separate on this name). Run honestly. Do not invent a second change. Do
not set FREEZE even if the cell fails. Do not treat `BB_20_2_VOL12` or the
closed `RVOL_RE_*` family as this result.
