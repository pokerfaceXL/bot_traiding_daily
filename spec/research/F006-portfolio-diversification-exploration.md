# F006 — Exploratory: does combining several NO_TRAIL series into an equal-weighted portfolio clear the monthly criterion?

> **Scope note, stated up front, same framing discipline as
> `spec/research/F006-catalog-notrail-sweep.md`:** this is NOT a strict single falsifiable
> hypothesis test of a new trading strategy. It is an exploratory check of a specific claim in
> `spec/build.md`'s F006 scope section: that a preliminary combination/diversification
> justification across instruments/intervals/conditions is the hypothesis that should feed
> F007 (portfolio). This note tests that claim directly using only already-computed data — no
> new backtest, no engine re-run. A positive result here is **not** a validation pass; it is at
> most "worth a properly-scoped F007 hypothesis" (F007 owns the real shared-margin portfolio
> holdout test). This section, the Method, the subset-selection logic, and the aggregation
> formula below were all written BEFORE the aggregation script was run, per the same
> pre-registration discipline as every prior F006 note in this family. "Result" and "Decision"
> were filled in after running the aggregation.

## Observation

`spec/research/F006-hypothesis-notrail-monthly.md` (30 series, 3 names) and
`spec/research/F006-hypothesis-notrail-monthly-catalog5.md` (50 series, 5 more names) both
found **0/80 total `(name, symbol, interval)` series** clearing
`spec/research/F005-validation-protocol.md` section 7's zero-tolerance monthly criterion
individually — every series has 2 or more losing months out of 12, confirmed by six
independent slices to come from a low-win-rate-carried-by-fat-tail-winners mechanism, not a
concentrated-crash pattern (losing months are spread across the calendar year, not clustered).
`spec/build.md`'s F006 scope section states that for more than one finalist, a preliminary
combination/diversification justification is the hypothesis that feeds F007. This note tests
that claim directly: if different series' losing months land in different calendar months (not
perfectly correlated), an equal-weighted sum of several series' monthly PnL could have fewer
losing months than any single constituent — the classic diversification argument.

## Hypothesis

**H1.** A portfolio built from a small (3-5), diversified subset of the 80 already-measured
`NO_TRAIL` series, combined by summing per-calendar-month net PnL under a shared
`initial_equity=500` capital assumption, has **strictly fewer** losing Train-1 calendar months
than the best individual constituent in that subset has alone (best individual constituent in
the selected subset = 2 losing months out of 12, see Subset selection below).

There is no H2. This is a single aggregation question with a pre-registered subset and
pre-registered aggregation rule, not a search over subsets.

## Falsification condition (stated before running)

**H1 is falsified if the combined monthly series has 2 or more losing months** (i.e. does not
improve on the best constituent) **or if it has zero losing months but the improvement cannot
be attributed to non-coincident losing months** (i.e. if it turns out the constituents' losing
months already coincided closely and the "fewer losses" appeared only because a few strong
winning months this subset happens to share masked genuine overlap — checked explicitly by
reporting, for each Train-1 month, how many of the 5 constituents were individually negative
that month alongside the combined sign).

Separately and regardless of whether H1 holds: **the zero-tolerance monthly criterion itself
(0/12 losing months) is reported as cleared or not cleared** for the combined series, since
that is the actual question `spec/build.md`'s F006 scope section poses for F007 feed-in
purposes, and is reported honestly even if it differs from the strict H1 comparison above.

## Subset selection (pre-registered, before computing the combined series)

Selection logic, applied to the already-computed per-series `n_neg_months` (count of Train-1
calendar months with `is_valid=True` and `net_pnl < 0`) and `train1_net_pnl` from the 80 raw
JSON files in `output/f006_notrail_monthly/raw/*.json` and
`output/f006_notrail_monthly_catalog5/raw/*.json`:

**Best-per-symbol across the 5-symbol basket.** For each of the 5 symbols
(`BTCUSDT`/`ETHUSDT`/`SOLUSDT`/`XRPUSDT`/`DOGEUSDT`), select the single `(interval, strategy)`
series for that symbol with the fewest negative Train-1 months, tie-broken by highest
`train1_net_pnl`. This yields exactly 5 series, one per symbol, maximizing cross-asset
diversification (the stated mechanism for why losing months might not coincide — different
underlying assets have different price paths) while each individual constituent is already
among the closest-to-clearing series in its own symbol group. Picking the single global
best-5-by-n_neg instead (which includes two `DOGEUSDT/60` series of different strategy
families) was considered and rejected: two series on the same symbol/interval likely share
highly correlated entry signals and therefore correlated losing months, which would defeat the
diversification premise being tested here rather than genuinely test it.

Selected subset (from already-computed results, no new computation needed to identify these —
reading existing `n_neg_months`/`train1_net_pnl` counts already published in the two prior
notes):

| symbol | interval | strategy | n_neg_months (of 12) | train1_net_pnl |
| --- | ---: | --- | ---: | ---: |
| DOGEUSDT | 60 | DONCHIAN_55 | 2 | +197.91 |
| ETHUSDT | 60 | BB_20_25_breakout | 3 | +70.90 |
| SOLUSDT | 60 | BB_20_25_EMA200 | 3 | +85.52 |
| BTCUSDT | 240 | DONCHIAN_PULLBACK_55 | 5 | +56.43 |
| XRPUSDT | 240 | EMA3_21_50_200 | 5 | +300.02 |

Best individual constituent (fewest losing months alone): DOGEUSDT/60/DONCHIAN_55 at 2/12.

## Run_id

`scripts/f006_portfolio_diversification_experiment.py`, `.venv_test` (Python 3.9.25, pandas
2.3.3), single pass, reads only the 5 already-existing raw JSON files named above (no network,
no engine import). Output: `output/f006_portfolio_diversification/combined_monthly.csv` (12
month rows) and `output/f006_portfolio_diversification/summary.json`.

**Discriminating check, run before trusting the result**: hand-summed the 5 constituents'
stored `monthly[i].net_pnl` for the two months the script reported as combined-negative
(2024-05, 2024-07) independently of the script. 2024-05: `8.18 + (-8.24) + (-33.33) + (-6.64) +
(-14.02) = -54.06`, script reported `-54.0599` (float rounding, same value). 2024-07: `-18.94 +
1.46 + 5.49 + (-9.94) + 4.97 = -16.96`, script reported `-16.9620` (same value). Both match
exactly; the check specified in Method passes for the two months that decide this result.

## Result

**H1 is falsified. The combined portfolio has 2 losing Train-1 calendar months (2024-05 at
-$54.06, 2024-07 at -$16.96) out of 12 evaluated -- exactly the same count as the best
individual constituent alone (`DOGEUSDT/60/DONCHIAN_55`, also 2/12), not fewer.** The combined
series does NOT clear `spec/research/F005-validation-protocol.md` section 7's zero-tolerance
monthly criterion either (2 losing months, not 0).

The per-month breakdown shows why: in both losing months, a majority of the 5 constituents
were themselves negative that month (May: 4 of 5 negative -- only `DONCHIAN_55`/DOGEUSDT was
positive; July: 2 of 5 negative, `DONCHIAN_55`/DOGEUSDT and `DONCHIAN_PULLBACK_55`/BTCUSDT).
May in particular is close to a coincident-bad-month case, not a diversification success: four
of the five series being simultaneously negative overwhelms the one positive constituent. In
the 10 non-losing evaluated months, the number of individually-negative constituents ranges
0-2 (never a majority), so the portfolio's non-losing months are genuinely a diversification
effect (small individual losses offset by larger gains elsewhere), but the two calendar months
that matter most for this criterion -- the ones that decide pass/fail -- are exactly the months
where the assets' NO_TRAIL signals correlated negatively together rather than diversifying
away. This is consistent with these being momentum/breakout-family strategies
(Donchian/Bollinger-breakout/EMA-cross) across a basket of correlated crypto assets: broad
market-wide adverse conditions (a chop/reversal month) tend to hurt several of these signal
families simultaneously, which is exactly the scenario equal-weighted diversification across
assets is least able to fix, since the correlation that matters here is in the *signal
mechanism*, not just the asset price series.

## Decision

**The diversification argument, tested directly and honestly against the pre-registered
falsification condition, does not hold for this subset.** Combining 5 diversified
(one-per-symbol, three different strategy families) NO_TRAIL series under the optimistic
independent-$500-accounts-summed assumption produced no improvement over the single best
constituent's losing-month count, and still fails the zero-tolerance monthly criterion. This is
a genuinely negative exploratory result, not an inconclusive one: the pre-registered comparison
(strictly fewer losing months than the best constituent) is decisively false (equal, not
fewer), and the per-month diagnostic explains why -- the two bad months are majority-negative
across constituents, not idiosyncratic to one series.

This result does **not** rule out diversification working for a different subset, a different
combination rule (e.g. weighting away from the two DONCHIAN/BB-family series that share more
signal mechanism, or including a genuinely uncorrelated-mechanism strategy this catalog does
not yet contain), or a larger subset than 5. But it directly falsifies the specific,
pre-registered claim tested here, and the mechanism identified (correlated signal families
across a crypto basket experiencing correlated adverse conditions in the same calendar month)
is a plausible reason to expect the same negative result from other similarly-constructed
subsets of this same 80-series catalog, not a fluke of this particular choice of 5.

**Per this note's own scope discipline: this is an exploratory result, not a validation pass.**
It does not promote any series or portfolio to Validation, and it does not itself close off
F007 (a real shared-margin holdout test on a frozen finalist selection is a different, harder
question this note does not attempt). What it does say, honestly, is that the specific
version of the diversification hypothesis tested here -- equal-weighted, best-per-symbol,
independent-capital-summed, on the 80 already-measured NO_TRAIL series -- is **not** "worth a
properly-scoped F007 hypothesis" as currently constructed; a future F007 (or further F006)
hypothesis in this direction would need either a different subset-selection rule that
specifically targets low signal-mechanism correlation (not just different assets) or accept
that momentum/breakout strategies across a correlated crypto basket may not diversify away
calendar-month losses regardless of which specific instruments are chosen.

## Tests

No change to `backtest_engine.py`/`entry_masks.py`/`regularity.py`/`data_contract.py`/
`strategy.py` in this slice -- the new computation lives entirely in
`scripts/f006_portfolio_diversification_experiment.py`, a pure downstream aggregation of
already-computed, already-tested per-series results. The load-bearing check for this slice is
the hand-verified discriminating check above (both decisive months match exactly), not a new
unit test.

## Method

**Pure aggregation of already-computed monthly results — no engine re-run.** Each raw JSON
file already stores a `monthly` list with one entry per Train-1 calendar month
(`year`, `month`, `is_valid`, `net_pnl`). For the 5 selected series:

1. Load the `monthly` array from each series' raw JSON.
2. For each of the 12 Train-1 calendar months (2024-03 … 2025-02), sum `net_pnl` across the 5
   series for that month, **only if all 5 series report `is_valid=True` for that month** (no
   month is evaluated if any constituent has missing data that month — consistent with section
   7's "missing data invalidates the month" rule, extended conservatively to the whole
   portfolio: a portfolio month is only evaluated when every constituent's data for that month
   is complete).
3. This produces one combined monthly net-PnL series (portfolio-level), with a combined
   `n_neg_months` count.
4. Separately record, per month, how many of the 5 constituents were individually negative
   that month, to check the "months don't coincide" mechanism directly rather than just
   inferring it from the aggregate sign.

**Explicit capital-model limitation, stated prominently and not hidden:** this sums the 5
series' per-month net PnL under an assumption that each series runs on its own independent
`initial_equity=500`, i.e. **5 separate $500 accounts summed**, not one shared $500 (or $2500)
account with shared margin. This is the optimistic case for diversification — it assumes each
strategy always has the capital it needs regardless of what the others are doing, with no
cross-strategy margin contention, no shared drawdown limit, and no correlation in return
*magnitude* (only in monthly *sign* is diversification benefit actually measured here). A true
shared-margin portfolio (one pool of capital, position sizing and risk limits interacting
across the 5 strategies) is a materially different, harder question that only a real
correlated re-simulation could answer — that is explicitly F007's job, not this note's. If this
exploratory result is positive, the honest framing is "summing independent $500 accounts shows
X" not "a $500 portfolio would show X".

- **Script**: `scripts/f006_portfolio_diversification_experiment.py` — new script, pandas-only
  aggregation of the 5 already-existing raw JSON files listed above. Reads, does not modify,
  `output/f006_notrail_monthly/raw/*.json` and `output/f006_notrail_monthly_catalog5/raw/*.json`.
  No import of `backtest_engine.py`/`strategy.py`/`entry_masks.py`/`data_contract.py` — this is
  a downstream aggregation of results those modules already produced, not a new simulation.
- **Discriminating check**: for each of the 12 months, the combined `net_pnl` reported by the
  script must equal the hand-summed value of the 5 constituents' stored `monthly[i].net_pnl`
  for that `(year, month)` (exact equality on floats read from the same JSON, not a
  re-derivation) — verified for all 12 months before trusting the `n_neg_months` count.

## Sample

5 series (one per symbol, from the 80 already measured): `DOGEUSDT/60/DONCHIAN_55`,
`ETHUSDT/60/BB_20_25_breakout`, `SOLUSDT/60/BB_20_25_EMA200`,
`BTCUSDT/240/DONCHIAN_PULLBACK_55`, `XRPUSDT/240/EMA3_21_50_200`. Train-1 window only
(2024-03 … 2025-02, 12 calendar months), identical to both source notes — no new window, no
Validation or Holdout data touched.
