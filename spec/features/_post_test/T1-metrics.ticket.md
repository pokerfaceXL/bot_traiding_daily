# {{EXPERIMENT_ID}} · T1 metrics & gates (§10)

## Outcome

A machine- and human-readable metric set for {{EXPERIMENT_ID}} that lets the coordinator judge
it against protocol §10 without recomputing anything. Pure computation from existing output —
no judgment, no decision, no new backtest.

## Scope

- Read `output/{{OUTPUT_DIR}}/results.csv` and `output/{{OUTPUT_DIR}}/trades.csv` (Train-1).
- Compute, per the §10 gate list: net PnL after costs, PnL per trade, n_trades, win rate,
  positive-month %, losing-month count (of 12), max drawdown, costs as % of gross, winner
  concentration (sum of top-1/3/5/10 net vs total net), and stability — net + mean/trade + WR
  broken down by symbol, by interval, and (if the frame spans them) by period.
- Compare every headline figure to `{{BASELINE}}`.
- Write `output/{{OUTPUT_DIR}}/posttest/metrics.json` (flat keys) and a `metrics.md` table.

## Out of scope

- Any `decision`, verdict, or whether a falsifier tripped — that is the coordinator's.
- Editing the profile, the registry, build.md, or the digest.
- Re-running or modifying the experiment; touching validation/holdout.

## Acceptance

- `metrics.json` + `metrics.md` exist under `output/{{OUTPUT_DIR}}/posttest/` and every §10 field
  above is present with a number (or an explicit `null` + reason if a column is unavailable).
- A one-line reproducer script under `scripts/` regenerates both files deterministically.
- Baseline-vs-candidate deltas are shown for net, mean/trade, losing-month count, big-winner PnL.

## Notes

Missing data is reported as unavailable, never silently zeroed (§3 data contract). No look-ahead:
use only columns already in the stored trade table.
