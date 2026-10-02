# F006 · Shared losing-months diagnostic across FREEZE catalog5 (H-CATALOG5-SHARED-LOSING-MONTHS-01)

## Outcome

Answer the RESEARCH_JOURNAL open question: are Train-1 losing months **shared** across the
five FREEZE catalog5 names (basket regime) or **idiosyncratic** per name/symbol? Follow the
frozen pre-registration in
`spec/research/F006-hypothesis-catalog5-shared-losing-months.md` exactly — compute from
existing autopsy/monthly tables, apply the frozen falsifiers (a)(b)(c), fill `## Result`,
and leave `## Decision` for the coordinator. This is a diagnostic, not a new trading signal.

## Scope

- Read existing monthly tables (do not redesign the experiment):
  - `output/f006_catalog5_dual_autopsy/monthly/{BB_20_25_EMA200,EMA_50_200}_monthly.csv`
  - `output/f006_catalog5_trio_autopsy/monthly/{EMA3_21_50_200,EMA3_13_50_200,BB_20_2_EMA200}_monthly.csv`
  - optional panel: `output/f006_donchian_autopsy/donchian55_notrail_monthly.csv`
  - secondary name×symbol: `output/f006_notrail_monthly_catalog5/raw/` and/or dual/trio
    `trades/*_train1_trades.csv` (document which; prefer entry-month aggregation consistent
    with the autopsy `loss_m` definition).
- Implement a small reproducible script under `scripts/` (e.g.
  `f006_shared_losing_months_diagnostic.py`) that builds the month×name loss matrix, computes
  the pre-declared metrics (co-occurrence ≥3/4/5, pairwise month-net corr, phi, Jaccard,
  chance baseline, EMA3_21 symbol-level sanity 6/12), writes artifacts under
  `output/f006_shared_losing_months/`, and fills the note's `## Result` with a one-line
  statement of which falsifier(s) trip (or CONFIRMED).
- Train-1 only. No new entry/exit/regime signal, no harness re-sweep, no validation/holdout.

## Out of scope

- The `decision` / next-step / §15 / journal rewrite — coordinator only.
- Any new trading rule, parameter grid, or OHLCV axis; re-opening FREEZE names; editing
  other profiles or build.md.
- Replacing the frozen falsification thresholds after seeing results.

## Acceptance

- `output/f006_shared_losing_months/` holds the month×name matrix, pairwise tables, chance
  baseline, and a short summary JSON/CSV the Result section cites.
- `spec/research/F006-hypothesis-catalog5-shared-losing-months.md` `## Result` is filled with
  the pre-declared metrics and which of (a)(b)(c) trip (or none → CONFIRMED).
- Script regenerates the artifacts; `python3 -m pytest -q` stays green (add a tiny unit test
  only if helpful for the chance-baseline helper — do not invent strategy tests).

## Notes

Sanity: the EMA3_21 within-name symbol co-occurrence from the autopsy (6/12 months with
≥4/5 symbols net-negative) should reproduce on the secondary panel — if it does not, stop and
report a data/definition mismatch rather than forcing a verdict. Idiosyncratic (falsified) is
a valid, expected possible outcome; record it honestly.
