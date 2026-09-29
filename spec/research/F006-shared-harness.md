# F006 · shared experiment harness, frozen result schema, cross-family digest

This is infrastructure, not a new signal family: no candidate name here is a trading
hypothesis and nothing in this note is H1/H2-falsifiable. It exists because every
F006 family script since `f006_notrail_monthly` (and every closed-catalog indicator
family: Aroon, CCI, OBV, BB/Keltner squeeze, ...) hand-copied the same ~150-line
loop -- frozen symbol/interval basket, the same ten `data_cache` checksums, the same
Train-1 slice, the same NO_TRAIL exit geometry, the same DONCHIAN_55 harness-control
comparison, the same per-series raw/summary/manifest write, the same H1 aggregate
check and H2 monthly-promotion check. Each copy is a chance for the loop itself to
silently drift between families, which would make cross-family comparison meaningless
even when every individual family script is internally correct.

## Observation

`scripts/f006_obv_experiment.py` (`limen/2026-09-29-f006-obv-5611b77b`),
`scripts/f006_aroon_experiment.py` (merged, `74d5cdd`/`3f17a2d`/`17c5ad4`), the CCI
family (merged, `9b62759`/`61d810d`), and `scripts/f006_bb_kelt_squeeze_experiment.py`
(`limen/2026-09-29-f006-bb-kelt-squeeze-0bcce73b`) each reimplement: `SYMBOLS`,
`INTERVALS`, the ten `EXPECTED_CHECKSUMS`, `load_train1`, `_run_one` (engine call +
monthly regularity + promotion-pass check), `verify_harness_control` against
`output/f006_trailing_boundary/summary/results.csv`, and a `main()` that registers
runtime-only catalog entries, sweeps `symbols x intervals x names`, writes
`output/f006_<family>/{raw,summary}/`, and computes H1 (mean `train1_net_pnl` > 0 across the
10-series pool) then H2 (monthly promotion checklist, only for H1-passing names).
`net_pnl` includes warm-up and boundary diagnostics and must not be used for the H1
gate.
Nothing about that loop is family-specific; only `catalog_entries()`, the candidate
name list, and the hypothesis note text differ per family.

## Method (what this ticket builds, not a trading hypothesis)

1. `scripts/f006_family_runner.py`: an importable module (not a template to copy)
   exposing `run_family(family, candidate_names, *, catalog_entries=None,
   hypothesis_note=..., script_path=..., output_dir=None)`. It owns the frozen
   `SYMBOLS × INTERVALS` basket, `EXPECTED_CHECKSUMS`
   (`spec/research/F005-validation-protocol.md` section 6), and the module-level
   `CONTROL_NAME`/`CONTROL_REFERENCE_CSV` DONCHIAN_55 harness control; it always
   runs that control. The basket/control are deliberately not caller arguments:
   `symbols`, `intervals`, `control_name`, or `control_reference_csv` raise
   `TypeError`, and `CONTROL_NAME` as a candidate raises `ValueError`. This prevents a
   family from writing non-10-series or uncontrolled results while claiming the frozen
   schema. The module requests its local cache only from `WARMUP_START` through
   `TRAIN1_END` (warm-up included): validation and holdout bars are never loaded,
   sliced, or inspected by a Train-1 H1 run. It also owns the NO_TRAIL geometry
   (`activate_pct=10.0`, `max_sl_pct=0.03`, one-shot entry mask,
   `cooldown_candles=0`, `leverage=1`), the H1/H2 checks, and every file write under
   `output/f006_<family>/`. The API/unit portions of
   `tests/test_signal_family_contract.py` require no CSV cache. Its one live
   frozen-basket/control proof and the runner self-check require the ten bounded
   `data_cache/*_20240126T000000Z_20250301T000000Z.csv` files; CSVs are intentionally
   gitignored, so a clean worktree skips that live proof with an explicit reason.
   Prepare them offline from the main checkout's existing frozen cache (never fetch
   from the network) before requesting the live proof/self-check. A future family
   script's entire job is: define a signal module with
   `catalog_entries() -> dict[str, Callable[[pd.DataFrame], pd.Series]]`, freeze its
   candidate names and hypothesis note in its own `spec/research/F006-hypothesis-*.md`
   (unchanged discipline), and call `run_family(...)` once. It MUST NOT copy the loop.
2. `tests/test_signal_family_contract.py`: the shared, family-agnostic contract
   (catalog additivity/no-mutation-of-STRATEGY_CATALOG-count, causality/no-lookahead
   by prefix + future-perturbation, no input-frame mutation, signal domain is
   `{-1, 0, 1}` on every bar, one-shot-mask alignment, next-bar-open fill through the
   real engine) parametrized over every family module currently registered in
   production (`donchian.py`, `lorentzian.py` today) plus a synthetic dummy family
   defined inline in the test file, proving the contract does not silently depend on
   any one family's fixture shape. Family-specific formula tests (exact hand-derived
   values, edge cases, mirror directions, etc.) stay in `tests/test_<family>.py` and
   are not duplicated here.
3. Frozen result schema (below) so `output/f006_*/summary/{results.csv,manifest.json}`
   is stable and digestible without per-family parsing.
4. `scripts/f006_cross_family_digest.py`: globs `output/f006_*/summary/manifest.json`,
   reads any manifest matching the frozen schema (`h1_table`/`h1_falsified`/
   `h2_status` present) into one H1/H2-per-family/name table, and marks any manifest
   predating this schema (every `output/f006_*` directory on `main` today) as
   `schema: legacy` rather than crashing on a `KeyError`. Writes
   `output/f006_cross_family_digest.json` and a Markdown table for ~every-5-closed-
   families reporting.
5. This note plus a short pointer so future F006 tickets are told
   "use `scripts/f006_family_runner.py`; do not copy the harness loop" instead of
   being pointed at the nearest prior family script.

## Acceptance

- `run_family` reproduces `output/f006_trailing_boundary/summary/results.csv`'s
  stored DONCHIAN_55 NO_TRAIL rows exactly (0 mismatches) when run as its own
  self-check, using only already-merged catalog entries (`DONCHIAN_20` as the sole
  "candidate", `DONCHIAN_55` as the control) -- this is a harness self-check, not a
  new hypothesis, and authorizes nothing about `DONCHIAN_20` beyond "the shared loop
  reproduces the closed family's own historical numbers."
- `tests/test_signal_family_contract.py` passes against `donchian.py`, `lorentzian.py`,
  and the inline dummy family.
- `scripts/f006_cross_family_digest.py` runs to completion against whatever
  `output/f006_*` exists on `main` right now (all legacy-schema) without raising, and
  produces a digest file that says so rather than silently emitting an empty table.
- Full `pytest tests/` stays green (no regression in the pre-existing 170 passed /
  7 skipped baseline).
- No `spec/build.md` edit, no merge, no production `strategy.py`/`add_indicators`
  change, no holdout access, no network.

## Frozen result schema

`output/f006_<family>/raw/<SYMBOL>_<INTERVAL>_<STRATEGY>.json` -- one file per series,
the full per-series row (see below) including the `monthly` list (12 Train-1 months,
each `{year, month, is_valid, is_partial, net_pnl, positive_day_pct, deviation_pct,
target_met}`).

`output/f006_<family>/summary/results.csv` -- one row per series, the same per-series
row with `monthly` dropped (nested lists are not CSV-safe). Columns, in write order:
`symbol, interval, strategy, n_calls, net_pnl, gross_pnl, win_rate, n_trades, n_wins,
n_losses, avg_winner, avg_loser, breakeven_win_rate_pct, exit_trailing_sl,
max_drawdown_pct, final_equity, train1_net_pnl, warmup_net_pnl, boundary_net_pnl,
n_valid_months, all_valid_months_nonnegative, promotion_pass, seconds`.

`output/f006_<family>/summary/manifest.json` -- top-level keys: `family`, `script`,
`git_commit`, `run_started_utc`, `python`, `pandas`, `n_series`, `checksums_used`,
`params`, `candidate_names`, `control_name` (always `DONCHIAN_55`),
`hypothesis_note`, `harness_control` (always `{rows_compared, n_mismatches, source}`
from the non-skippable DONCHIAN_55 comparison), `no_trail_mechanism_check`,
`one_shot_violations`, `h1_table` (per-candidate-name
`{strategy, sum_net_pnl, mean_net_pnl, n_series, n_profitable_series, n_trades_total,
h1_pass}`; despite these frozen historical field names, `sum_net_pnl`, `mean_net_pnl`,
`n_profitable_series`, and `h1_pass` are calculated from `train1_net_pnl` only, with
H1 passing iff `mean(train1_net_pnl) > 0`), `h1_names_passing`, `h1_falsified`,
`h2_table`, `h2_names_with_a_passing_series`,
`h2_status` (`"not_applicable_h1_failed"` / `"falsified"` / `"cleared"`),
`elapsed_seconds`. A manifest missing `h1_falsified` predates this schema; the digest
must treat it as `schema: legacy`, not crash.

## For future F006 tickets

Use `scripts/f006_family_runner.py`; do not copy the harness loop. A new signal-family
ticket adds a signal module (with `catalog_entries()`), its candidate names, its own
frozen `spec/research/F006-hypothesis-<family>.md`, and formula tests in
`tests/test_<family>.py` -- then calls `f006_family_runner.run_family(...)` once. It
must not reimplement `SYMBOLS`/`INTERVALS`/`EXPECTED_CHECKSUMS`/`_run_one`/
`verify_harness_control`/the H1/H2 loop, and must not depend on any unmerged sibling
family module at runtime.
