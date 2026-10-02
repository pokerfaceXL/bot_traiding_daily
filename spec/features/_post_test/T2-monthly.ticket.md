# {{EXPERIMENT_ID}} · T2 monthly table & losing-month classification (§6)

## Outcome

The §6 monthly table for {{EXPERIMENT_ID}} plus a data-driven (not judgmental) answer to the §6
loss questions, so the coordinator can form a hypothesis from regime structure without
recomputing. Pure computation from existing output.

## Scope

- Read `output/{{OUTPUT_DIR}}/trades.csv` (and `monthly.csv` if present), Train-1 cohort.
- Build the monthly table with: net PnL, gross PnL, total costs, n_trades, win rate, avg win,
  avg loss, max drawdown, `initial_sl` share, `signal_reverse` share, median bars_held, and the
  per-symbol net for each month.
- Answer §6 Q1–Q8 **descriptively, from the data only**: false-break proxy (`initial_sl` with
  MFE<1% share), small-and-frequent vs large-and-concentrated losses, volatility shift
  (atr_percentile by month), single-symbol vs basket (count symbols net-negative per month),
  whether losing months also contain eventual big winners, entry/exit/sizing/allocation locus.
- Write `output/{{OUTPUT_DIR}}/posttest/monthly.md` (table + the eight bullet answers).

## Out of scope

- Any hypothesis, fix, or decision; parameter tuning to specific months (§6 forbids it).
- Editing the profile, registry, build.md, digest; re-running the experiment.

## Acceptance

- `monthly.md` exists with the full table (all columns above) and a one-line evidence-based
  answer to each of §6 Q1–Q8, each citing a number from the table.
- A one-line reproducer script under `scripts/` regenerates it deterministically.

## Notes

Report, do not optimize: months are for discovering a shared loss mechanism, not for removing
specific periods. No look-ahead; stored columns only.
