# F006 -- Hypothesis: restricting the cross-symbol agreement gate to the two names it
# helped, and sweeping MIN_AGREE, clears the monthly criterion for at least one series
# Train 1 only

> Sections "Observation" through "Falsification condition" (including the sample, the exact
> gate formula, the exact MIN_AGREE values swept, and the exact predicted effect) are written
> and committed to this file BEFORE `scripts/f006_entry_cross_symbol_refined_experiment.py` is
> written and before any backtest is run, per the same discipline as every prior F006
> hypothesis note. "Run_id", "Result", "Decision" and "Tests" are filled in after the run.
>
> TRAIN-1 ONLY, same window as every F006 slice: `[2024-03-01T00:00:00Z, 2025-03-01T00:00:00Z)`
> plus the protocol's 35-day warm-up buffer from `2024-01-26T00:00:00Z`. Validation 1-4 and the
> Holdout window are not loaded, not sliced and not looked at by any script in this slice.

## Observation

`F006-hypothesis-entry-cross-symbol-agreement.md` (just merged) tested a `MIN_AGREE=2`
directional-agreement gate (at least 2 of the other 4 basket symbols currently showing the
same-name signal in the same direction) against `DONCHIAN_55`, `BB_20_25_breakout`,
`DONCHIAN_PULLBACK_55` at `NO_TRAIL`, on the full 30-series sample. It was the first of four
mechanistically distinct filters/sizing schemes tried against this exact target
(0/30 genuine passes in every prior note too) to move pooled, trade-weighted win rate in the
predicted direction by more than a token amount: **+1.84 pp (25.07% -> 26.91%) against a 43.0%
trade-count cut**. But that pooled effect masked a per-name split, reported explicitly in that
note's Result table:

| Name | mean net PnL, unf. -> filt. | trade-weighted win%, unf. -> filt. | positive series (of 10) |
| --- | --- | --- | --- |
| `BB_20_25_breakout` | $48.78 -> **$62.51** | 25.66% -> 27.47% | 6 -> 8 |
| `DONCHIAN_55` | $58.39 -> $56.42 | 27.31% -> **33.58%** | 8 -> 8 |
| `DONCHIAN_PULLBACK_55` | $38.19 -> **-$9.32** | 20.57% -> **16.14%** | 6 -> 4 |

`BB_20_25_breakout` and `DONCHIAN_55` both showed the predicted signature (win rate up, mean PnL
held or improved). `DONCHIAN_PULLBACK_55` showed the opposite signature and dragged the pooled
mean-PnL figure down even though the pooled win-rate figure still rose. That note's Result
section argued this split is mechanistic, not noise: `DONCHIAN_PULLBACK_55`'s entry is itself a
lagged, already-confirmed re-cross of the breakout's midline (`donchian.py`'s state machine,
ARM -> TOUCH -> TRIGGER), so by the time it fires, a genuine coordinated cross-symbol move may
already have peaked or reversed on the other 4 symbols -- a same-bar cross-symbol read is
worse-timed for this specific entry shape than for the two raw-breakout names. That note's own
Decision section named the next step explicitly, not pursued in that slice: *"restricting the
gate to only the two names it helped (`BB_20_25_breakout`, `DONCHIAN_55`)"* combined with *"a
different threshold (e.g. `MIN_AGREE=1` or `3`)"* -- it tested exactly one threshold
(`MIN_AGREE=2`, a simple majority of the other 4) as "the single concrete hypothesis," explicitly
not a sweep. This note takes up both changes together, as one pre-registered hypothesis, on the
narrower 20-series subsample.

**What MIN_AGREE values were and weren't tried, stated explicitly before this note sweeps them.**
The prior note tried exactly one value, `MIN_AGREE=2`, out of the four possible nontrivial
values against 4 "other" symbols (`MIN_AGREE` can range 1-4; `MIN_AGREE=0` would gate on nothing,
degenerating to the unfiltered baseline, and is not a distinct condition worth a cell). `MIN_AGREE
=1`, `=3` and `=4` were named but not run. This note runs all four values (`1`, `2`, `3`, `4`) on
the 20-series subsample, both as the pre-registered sweep the ticket asks for and as an internal
consistency check: `MIN_AGREE=2` on this subsample's 20 series must reproduce the prior note's own
filtered results for exactly these 20 (name, symbol, interval) cells (`BB_20_25_breakout` and
`DONCHIAN_55` x 5 symbols x 2 intervals) bit-for-bit, since nothing about the gate construction or
engine parameters changes between the two notes for those cells -- checked as a harness control
below, not merely asserted.

## Hypothesis

**H1.** Restricting the cross-symbol agreement gate (identical formula to the prior note:
`entry_regime_mask = one_shot_entry_mask(own) & cross_symbol_gate(own, others, MIN_AGREE)`, same
`entry_masks`-derived persistent +1/-1/0 signal series, same defensive reindex) to only
`DONCHIAN_55` and `BB_20_25_breakout` (dropping `DONCHIAN_PULLBACK_55` from this mechanism, per
the prior note's own argument that its lagged/confirmed entry shape is mechanistically
mismatched to a same-bar cross-symbol read), swept over `MIN_AGREE in {1, 2, 3, 4}`, causes **at
least 1 of the 20** `(name, symbol, interval)` series, at **at least one** of the four `MIN_AGREE`
values, to **genuinely** clear `spec/research/F005-validation-protocol.md` section 7's monthly
promotion checklist (full-run max drawdown <= 50%, net PnL >= 0 in every `is_valid` Train-1
calendar month, net PnL >= 0 over the full Train-1 period) -- where "genuinely" requires
`n_trades_filtered > 0` as a precondition, exactly as `F006-hypothesis-entry-cross-symbol-
agreement.md` required and as this ticket explicitly names as the recurring guard not to regress
on: **a series that clears the checklist only by trading zero times at a given `MIN_AGREE` does
not count toward H1 surviving, at any threshold.**

**Mechanism, stated before running.** Two independent changes, tested together because they
target the same failure mode from two directions and the ticket asks for both in one slice:

1. **Dropping `DONCHIAN_PULLBACK_55`** removes the one name whose per-name signature was actively
   harmful in the prior note, on the argument that its own entries are already lagged/confirmed
   and therefore a worse fit for a same-bar cross-symbol read (established, not re-derived, in the
   prior note's Result section). This should raise the *pooled* trade-weighted win-rate delta
   above the prior note's blended +1.84 pp, since the pooled figure was demonstrably being dragged
   down by the one name being removed (`DONCHIAN_55`'s own trade-weighted win rate rose the most
   of the three, +6.27 pp; `BB_20_25_breakout` rose +1.81 pp; `DONCHIAN_PULLBACK_55` fell -4.43
   pp).
2. **Sweeping `MIN_AGREE`** tests whether a stricter or looser threshold than the fixed majority
   vote used before better balances the trade-count cut against the win-rate gain for these two
   specific names. A stricter threshold (`MIN_AGREE=3` or `4`) is expected to raise win rate
   further at the cost of a steeper trade-count cut (more starving-the-sample risk, the guard this
   note's falsification condition explicitly protects against by requiring `n_trades_filtered >
   0`); a looser threshold (`MIN_AGREE=1`) is expected, per the prior note's own reasoning, to be a
   weak filter that removes little of the sample and therefore produces a smaller win-rate
   movement in either direction, closer to the unfiltered baseline.

Neither change is expected, on its own, to be sufficient to flip any series' full 12-month
record clean -- the prior note's best series (`BTCUSDT/60/BB_20_25_breakout` and
`BTCUSDT/240/DONCHIAN_PULLBACK_55`, the latter now excluded) needed to close a 3-month gap even
where the mechanism worked as predicted. This note's hypothesis is that removing the actively
harmful name and searching the threshold space gives this mechanism its best remaining chance to
close that specific gap on at least one series, not a certainty that it will.

## Distinguishing genuine selection from starving the sample (the ticket's explicit requirement,
## carried forward unchanged)

Reported for every series at every `MIN_AGREE` value, exactly as the prior note reported it for
its single value: pooled trade-weighted win rate filtered vs. unfiltered, per-name win rate
filtered vs. unfiltered, mean negative months per series filtered vs. unfiltered, and an explicit
`degenerate_pass` flag (`n_trades_filtered == 0` while `promotion_pass_filtered == True`) computed
in code for every `(name, symbol, interval, MIN_AGREE)` cell, not merely eyeballed. The stricter
`MIN_AGREE` values (3, 4) are the ones most likely to produce a degenerate pass, per the
width-expansion note's own precedent (a tight filter starving a low-trade-count series to zero
entries) -- this note watches for that specifically at those two values.

## Sources

This repo's own prior findings and pre-existing, unmodified code only:
`F006-hypothesis-entry-cross-symbol-agreement.md` (the `MIN_AGREE=2` result and its per-name
split, the exact gate formula and script pattern this note reuses),
`F006-hypothesis-notrail-monthly.md` (the 0/30 baseline, the monthly checklist definition, the
unfiltered `n_trades`/`train1_net_pnl` reference values used for this note's own harness
control), `F006-hypothesis-entry-width-expansion.md` and `F006-hypothesis-entry-trend-confirm.md`
(the degenerate-zero-trade-pass guard and the falsified magnitude/trend mechanisms this
sub-family has already ruled out), `spec/research/F005-validation-protocol.md` section 7 (the
monthly promotion criterion, verbatim), `entry_masks.py`
(`normalized_signal`/`strategy_signal_series`/`one_shot_entry_mask`, unmodified), `donchian.py`/
`strategy.py` (the two remaining names' own persistent-state signal definitions, unmodified).

## Sample

20 series: `DONCHIAN_55`, `BB_20_25_breakout` x `SOLUSDT`/`ETHUSDT`/`BTCUSDT`/`XRPUSDT`/
`DOGEUSDT` x `240`/`60` -- exactly the prior note's 30-series sample minus every
`DONCHIAN_PULLBACK_55` series. For each traded series, the "other 4 symbols" vote is still built
from the traded series' own name's signal across all 5 basket symbols (identical construction to
the prior note; `DONCHIAN_PULLBACK_55`'s own signal is not loaded at all in this slice, since it
is no longer a candidate and its signal plays no role in the other two names' votes -- the "other
4" for `DONCHIAN_55` are the other 4 symbols' own `DONCHIAN_55` signal, never
`DONCHIAN_PULLBACK_55`'s, exactly as in the prior note). `DONCHIAN_55` needs `donchian.py` (pure
pandas); `BB_20_25_breakout` is a plain `strategy.STRATEGY_CATALOG` entry. No Lorentzian
dependency -- single pass on `.venv_test` (Python 3.9) covers all 20 series x 4 `MIN_AGREE`
values.

## Method

**Engine parameters: identical to `F006-hypothesis-entry-cross-symbol-agreement.md`'s cell,
unchanged.** `activate_pct=10.0` (NO_TRAIL), `trail_pct=0.04` (moot, `None`), `max_sl_pct=0.03`,
`atr_multiplier=1.5`, `cooldown_candles=0`, `leverage=1.0`, `commission_rate_bps=10.0`,
`half_spread_bps=5.0`, `slippage_bps=2.0`, `initial_equity=500.0`, `stake=100.0`, `now` pinned to
`2025-03-01T00:00:00Z`. **No change to `backtest_engine.py`, `strategy.py`, `entry_masks.py`,
`donchian.py`, `regularity.py`.** The gate construction itself (`cross_symbol_gate`) is
byte-identical logic to the prior note's script, imported/reused rather than reimplemented (see
below), with only `NAMES` narrowed to the two names and `MIN_AGREE` promoted from a fixed constant
to a swept list.

**Gate formula, identical to the prior note, restated for completeness.** For a given `(name,
interval)` and each of the 5 basket symbols `s`: `own_signal[s] =
entry_masks.normalized_signal(entry_masks.strategy_signal_series(df[s], name, interval, now))`;
for the traded symbol, `others = [own_signal[s2] for s2 in SYMBOLS if s2 != s]`; `agreement_count
= sum(1 for o in others if o == own_signal[s] and own_signal[s] != 0)`; `cross_symbol_gate =
agreement_count >= MIN_AGREE`; `entry_regime_mask = one_shot_entry_mask(own_signal[s]) &
cross_symbol_gate`. Swept over `MIN_AGREE in [1, 2, 3, 4]`, one full pass through all 20 series
per value (80 filtered backtests total, plus 20 unfiltered baseline runs shared across all four
`MIN_AGREE` values since the unfiltered arm does not depend on `MIN_AGREE`).

- **Script**: `scripts/f006_entry_cross_symbol_refined_experiment.py`. Single pass, `.venv_test`
  only. Reuses `scripts/f006_entry_cross_symbol_experiment.py`'s harness pattern directly (loaded
  via `importlib`, not copy-pasted, for the `cross_symbol_gate` function and the monthly-scoring
  helpers `_run_and_score`/`_net_pnl_for_month`/`_net_pnl_for_months`/`_n_trades_by_month`, all
  unmodified) -- only the `NAMES` list, the `MIN_AGREE` sweep loop, and the output paths are new.
- **Data**: identical checksum-verified load (`data_contract.load_dataset`, the same
  `EXPECTED_CHECKSUMS` table duplicated from `spec/research/F005-validation-protocol.md` section
  6) and Train-1 slice as every F006 script. No network fetch. All 5 basket symbols loaded per
  interval (needed for the "other 4" vote), only 2 of the 5 names' signals scored as traded
  series.
- **Aggregation**: `regularity.py`, unchanged, identical `promotion_pass` definition, plus
  `promotion_pass_genuine = promotion_pass_filtered AND n_trades_filtered > 0`, computed
  per-`(name, symbol, interval, MIN_AGREE)` cell (80 filtered cells total).
- **Recorded per cell**: everything the prior note recorded per series (`n_trades`, Train-1 net
  PnL, 12 monthly rows, `promotion_pass`, `promotion_pass_genuine`, win rate,
  `n_calls_gated_out`), plus `min_agree` as an explicit column and `degenerate_pass`.

**Discriminating checks:**

1. **Index-equality precondition**, identical to the prior note, re-asserted in this script.
2. **Subset invariant**: `n_trades_filtered <= n_trades_unfiltered` for all 80 filtered cells.
3. **Harness control against the prior note's own results, at `MIN_AGREE=2` specifically**: this
   note's `MIN_AGREE=2` filtered results for these 20 cells must match
   `output/f006_entry_cross_symbol/summary/results.csv`'s stored `n_trades_filtered`/
   `train1_net_pnl_filtered` for the same 20 `(symbol, interval, name)` rows, exactly (0
   mismatches expected) -- this is the internal consistency check named in the Observation section
   above, validating that narrowing `NAMES` and reusing the imported gate function reproduces the
   prior note's own numbers bit-for-bit before this note's new `MIN_AGREE` values are trusted.
4. **Harness control against the unfiltered baseline**: the shared unfiltered arm (`n_trades`,
   `train1_net_pnl`) must match `output/f006_notrail_monthly/summary/results.csv` for these 20
   series (0 mismatches expected), same check every note in this family runs.
5. **Monotonicity sanity check, reported not enforced as a hard stop**: `n_trades_filtered` at
   `MIN_AGREE=k` should be non-increasing in `k` for a fixed series (a stricter agreement
   threshold can only remove more entries, never fewer, since the set of bars satisfying
   `agreement_count >= k` shrinks as `k` rises) -- checked in script and reported as a monotonicity
   violation count; a violation would indicate a bug in the sweep loop (e.g. stale mask reuse
   across `MIN_AGREE` values) and is investigated, not silently reported alongside the results if
   found nonzero.
6. **Genuineness guard enforced in code**: `promotion_pass_genuine` computed per cell; any cell
   with `promotion_pass_filtered=True` and `n_trades_filtered=0` flagged `degenerate_pass=True`
   separately, reported explicitly for every `MIN_AGREE` value, not just the one (if any) that
   produces a pass.
7. **Regularity module regression, unmodified**: `tests/test_regularity.py`'s existing tests
   re-run to confirm no regression.

## Falsification condition (stated before running)

Evaluated on the 20 `(name, symbol, interval)` series x 4 `MIN_AGREE` values (80 filtered cells),
against `spec/research/F005-validation-protocol.md` section 7's monthly promotion checklist,
applied per cell exactly as every prior note in this family applied it:

**H1 is falsified if zero of the 80 filtered cells have `promotion_pass_genuine = True`** -- i.e.
no `(name, symbol, interval)` series, at any of the four swept `MIN_AGREE` values, both clears the
checklist under the filtered arm AND has `n_trades_filtered > 0`. A cell that clears the checklist
only by trading zero times is `degenerate_pass=True` and does **not** count toward H1 surviving,
regardless of `MIN_AGREE`.

**H1 survives if at least 1 of the 80 filtered cells has `promotion_pass_genuine = True`.** A
single genuinely clearing cell is sufficient -- it would be the first Validation candidate this
whole F006 sub-family (three/now-two names, `NO_TRAIL`, monthly criterion) has produced, and is
flagged prominently as such in the Result/Decision sections below if it occurs.

**Distinguishing genuine selection from starving the sample is mandatory reporting regardless of
H1's outcome**, per the ticket's explicit requirement and unchanged from the prior note: pooled
trade-weighted win rate and mean negative months per series, filtered vs. unfiltered, reported for
every `MIN_AGREE` value, judged against this sub-family's established reference points (width
gate +0.42 pp/-52% trade cut; trend gate -3.16 pp/-48%; the prior cross-symbol note's own +1.84
pp/-43.0% on the full 30-series sample).

## Run_id

`scripts/f006_entry_cross_symbol_refined_experiment.py`, `git_commit_parent = 6a8127b` (the
pre-registration commit above), single pass, `.venv_test` (Python 3.9.25, pandas 2.2.3, rebuilt
in this worktree from the cached offline wheelhouse at `/tmp/mine-strategy-wheels` plus
`/tmp/pipdl` for `pyyaml`, since this worktree's `.venv_test` did not pre-exist; no network
access), 20 series x 4 `MIN_AGREE` values = 80 filtered cells, 30.2s. This worktree's
`data_cache/*.csv` (git-ignored) were also missing and were copied unmodified from the main
checkout's `data_cache/` before the first run; the harness controls below (0/20 mismatches
against both `output/f006_entry_cross_symbol/summary/results.csv` and
`output/f006_notrail_monthly/summary/results.csv`) confirm the copy reproduces both prior notes'
numbers exactly, which would not happen if the checksum-verified load were pulling different
bytes. Per-cell results and monthly tables: `output/f006_entry_cross_symbol_refined/raw/*.json`
(80 files). Summary table: `output/f006_entry_cross_symbol_refined/summary/results.csv`.
Manifest, checksums, harness-control, index-equality, subset-invariant and monotonicity records:
`output/f006_entry_cross_symbol_refined/summary/manifest.json`.

## Result

**Falsified. 0 of 80 filtered cells is even a degenerate pass, let alone a genuine one --
`promotion_pass_filtered` is `False` for all 20 series at all 4 `MIN_AGREE` values.** Both
discriminating checks that gate trust in this note's own numbers are clean: the index-equality
precondition holds at both intervals; the subset invariant (`n_trades_filtered <=
n_trades_unfiltered`) and the monotonicity invariant (`n_trades_filtered` non-increasing in
`MIN_AGREE` for every one of the 20 series) both hold with **zero violations** across all 80
cells; the harness control against the prior cross-symbol note's own `MIN_AGREE=2` results
(reusing the unmodified `cross_symbol_gate` function via `importlib` rather than
reimplementing it) matches **0/20 mismatches** on both `n_trades_filtered` and
`train1_net_pnl_filtered`; the harness control against `f006_notrail_monthly`'s unfiltered
baseline matches **0/20 mismatches** on `n_trades`/`train1_net_pnl`.

**One incidental finding surfaced by this note's own harness control, reported because it bears
on how the prior note's headline per-name number should be read going forward.** The prior
note's Result table stated `DONCHIAN_55`'s pooled trade-weighted win rate at `MIN_AGREE=2` rose
"27.31% -> 33.58%" from "130.002 -> 89.998" wins out of "476 -> 268" trades. Recomputing the
identical trade-weighted aggregation directly from that note's own stored
`output/f006_entry_cross_symbol/summary/results.csv` (not from this note's rerun) gives
**476 -> 318 trades filtered (not 268) and a trade-weighted win rate of 27.31% -> 28.30% (not
33.58%)** -- this note's own rerun at `MIN_AGREE=2` reproduces the corrected 318/28.30% figures
exactly (the harness control above), so the discrepancy is an arithmetic/transcription error
internal to the prior note's Result prose, not a data or plumbing difference between the two
notes. `DONCHIAN_55`'s real per-name win-rate gain at `MIN_AGREE=2` (27.31% -> 28.30%, +0.99 pp)
is therefore noticeably smaller than previously reported, though still in the predicted
direction; this does not change the prior note's Decision (still 0/30 genuine, still falsified),
but is flagged here so the corrected figure, not the original one, is what any future note cites.

**MIN_AGREE=2 remains the best-performing single threshold on both win rate and mean PnL among
the four swept, consistent with the prior note's choice of it as "the middle, best-justified
single choice" even though that note did not compare it against alternatives.**

| MIN_AGREE | trades (unf->filt) | trade-cut % | pooled trade-wtd win% (unf->filt) | mean net PnL/series (unf->filt) | mean neg months/series (unf->filt) | positive series (of 20) |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 1345 -> 1037 | 22.9% | 26.25% -> 26.81% | $53.59 -> $51.51 | 6.15 -> 6.55 | 14 -> 15 |
| **2** | 1345 -> 788 | 41.4% | 26.25% -> **29.06%** | $53.59 -> **$59.46** | 6.15 -> 6.50 | 14 -> **16** |
| 3 | 1345 -> 552 | 59.0% | 26.25% -> 26.99% | $53.59 -> $43.47 | 6.15 -> 6.55 | 14 -> 13 |
| 4 | 1345 -> 258 | 80.8% | 26.25% -> 27.52% | $53.59 -> $28.59 | 6.15 -> **5.20** | 14 -> 12 |

`MIN_AGREE=1` (a weak filter) behaves as predicted: smallest trade-count cut (22.9%), smallest
win-rate movement (+0.56 pp), closest to the unfiltered baseline on every measure. `MIN_AGREE=2`
gives the largest win-rate gain (+2.82 pp) and the only value where mean net PnL per series rises
rather than falls (+$5.88). `MIN_AGREE=3` is dominated by `MIN_AGREE=2` on every measure reported
(smaller win-rate gain, lower mean PnL, worse mean negative months, fewer positive series, for a
steeper trade cut) -- not a useful threshold on this subsample. `MIN_AGREE=4` is the one value
where **mean negative months per series actually improves** (6.15 -> 5.20, the first improvement
on this specific measure anywhere in this whole sub-family across all four mechanisms and now five
thresholds tried), but at an 80.8% trade-count cut and with `DONCHIAN_55`'s own mean net PnL
collapsing to $4.83/series (from $58.39 unfiltered) -- a name-level effect similar in shape to
`DONCHIAN_PULLBACK_55`'s collapse in the prior note, now reproduced within one of the two "kept"
names at the strictest threshold, and the reason this note does not read `MIN_AGREE=4`'s
neg-months improvement as straightforwardly positive.

**Per-name breakdown confirms `BB_20_25_breakout` is the more robust of the two names under this
mechanism; `DONCHIAN_55` degrades sharply at the strictest threshold.**

| Name, MIN_AGREE | trades unf->filt | win% unf->filt | mean PnL unf->filt | mean neg months unf->filt | pos. series (of 10) |
| --- | --- | --- | --- | --- | --- |
| `BB_20_25_breakout`, 2 | 869->470 | 25.66%->29.57% | $48.78->$62.51 | 5.80->6.20 | 8 |
| `DONCHIAN_55`, 2 | 476->318 | 27.31%->28.30% | $58.39->$56.42 | 6.50->6.80 | 8 |
| `BB_20_25_breakout`, 4 | 869->146 | 25.66%->26.71% | $48.78->$52.34 | 5.80->**5.60** | 7 |
| `DONCHIAN_55`, 4 | 476->112 | 27.31%->28.57% | $58.39->**$4.83** | 6.50->**4.80** | 5 |

`BB_20_25_breakout` holds up across the full sweep (mean PnL never falls below its unfiltered
baseline at any `MIN_AGREE`); `DONCHIAN_55` is the stronger performer at `MIN_AGREE=2` (matching
the prior note's finding that it had the largest per-name win-rate gain of the three original
names) but is the name whose mean PnL collapses at `MIN_AGREE=4`, losing 5 of its 10 series to
net-negative and dropping its own mean neg-months figure only by starving 4 of its thinnest
series down to 2-4 total trades each (not zero -- `promotion_pass_genuine`'s guard correctly does
not flag these `degenerate_pass=True`, since `n_trades_filtered > 0` holds everywhere in this run
-- but thin enough that a handful of stop-outs or wins swing the whole 12-month record).

**No series clears the checklist, but the family's closest approach so far is now 2 negative
months (previously 3), and it comes with a load-bearing caveat.** Three cells reach 2 negative
months out of 12 -- the fewest anywhere in this whole F006 sub-family across all mechanisms and
thresholds tried to date (the prior cross-symbol note's own best was 3): `BTCUSDT/240/
BB_20_25_breakout` at `MIN_AGREE=4` (5 trades, 80.0% win rate, $44.92 net PnL, 2.54% max
drawdown, both negative months driven by a single losing trade or a fee-only zero-trade month),
`XRPUSDT/240/BB_20_25_breakout` at `MIN_AGREE=4` (3 trades, 33.33% win rate, $307.08 net PnL --
carried by one very large winner -- 13.02% max drawdown, both negative months again driven by a
single trade each), and `DOGEUSDT/240/DONCHIAN_55` at `MIN_AGREE=4` (2 trades total over 12
months, net PnL still negative at -$3.15, so it fails the full-period-PnL criterion regardless of
its negative-month count). **All three are thin-sample near-misses, not robust selections**: with
2-5 total trades across a full year, each cell's monthly record is set almost entirely by whether
one or two individual trades happened to win or lose, which is the same underlying fragility this
sub-family's `n_trades_filtered > 0` guard is designed to catch at the zero-trade extreme but
cannot catch at 2-5 trades -- these pass the letter of the genuineness guard but not its spirit,
and are reported here as the closest approach on record while being explicitly flagged as not
substantively different from the starving-the-sample failure mode this whole sub-family has
repeatedly found.

## Decision

**No promotion. No series in this note's 20-series x 4-`MIN_AGREE` sweep is a genuine Validation
candidate.** H1 is falsified: 0 of 80 filtered cells has `promotion_pass_genuine = True`, and
(unlike the width-expansion note) there is no ambiguity to resolve -- 0 of 80 is `promotion_pass
= True` at all, degenerate or otherwise.

**Both halves of this note's combined change moved a real metric in the predicted direction on
the pooled measures, and `MIN_AGREE=2` is confirmed as the best single threshold for these two
names specifically** (win rate +2.82 pp, mean PnL +$5.88/series, both the largest positive
movements of the four thresholds swept) -- **but neither change was strong enough, alone or
combined, to flip a single series' full 12-month record clean, and the sweep's most
aggressive value (`MIN_AGREE=4`) reproduces this sub-family's recurring failure mode
(`DONCHIAN_55`'s own mean PnL collapsing) inside one of the two names this note kept, rather than
eliminating it.** Restricting to the two better-behaved names did raise the pooled win-rate
ceiling relative to the prior note's three-name blend (peak +2.82 pp here at `MIN_AGREE=2` vs.
the prior note's blended +1.84 pp at the same threshold across three names), confirming the
mechanism argued in the prior note's Decision section -- but the ceiling is still well short of
what closing a 12-month record with zero losing months requires, and the strictest threshold
tested does not monotonically improve things: it helps the monthly-smoothing measure in aggregate
while actively harming one of the two names it was supposed to help.

**This note's one genuinely new empirical finding**: the three closest-to-clearing cells found
anywhere in this whole F006 sub-family to date (2 negative months, versus the family's prior best
of 3) all occur at `MIN_AGREE=4`, all on `BB_20_25_breakout` or `DONCHIAN_55`, and all trade fewer
than 6 times over the full Train-1 year -- **this is reported prominently, per the ticket's
instruction, but is explicitly NOT flagged as a Validation candidate**: none has
`promotion_pass_genuine = True` (two still have a negative month; the third has negative
full-period PnL), and even if one had cleared the checklist on its face, a 2-5 trade sample over
12 months is not a substantively different evidentiary basis than the zero-trade degenerate passes
this sub-family's guard already rejects -- it would need explicit additional scrutiny (a minimum
trade-count floor, not currently part of the promotion checklist) before being treated as
equivalent to a checklist pass on a normally-trading series.

**Scope of what this closes out.** This note tested the two changes the prior note's Decision
section named as the explicit next step -- name restriction and a `MIN_AGREE` sweep -- together,
on the narrower 20-series subsample, per this ticket's instruction. Both are now closed out for
this exact target (`BB_20_25_breakout`/`DONCHIAN_55`, `NO_TRAIL`, monthly criterion): no further
`MIN_AGREE` value between the four tested (1, 2, 3, 4 are the only integer values possible against
4 "other" symbols) remains untried, and no further name subset is available to restrict to
without going to a single name. The two levers named in `F006-hypothesis-position-sizing-vol-
inverse.md`'s Decision section that remain untried across this whole magnitude/agreement family --
**recency of the last loss** and **an exit-side lever** -- are the two orthogonal directions this
sub-family has not yet tried and are the natural next step for whichever future note the
coordinator scopes; a minimum-trade-count floor added to the promotion checklist itself (motivated
directly by this note's thin-sample near-misses) is a separate, protocol-level question outside
this note's scope to decide.

**What is reusable regardless of this outcome.**
`scripts/f006_entry_cross_symbol_refined_experiment.py` demonstrates that
`scripts/f006_entry_cross_symbol_experiment.py`'s `cross_symbol_gate`/`own_signal_series`/
`load_train1`/`_run_and_score`/`_n_months_flipped_to_zero_trade` are cleanly reusable via
`importlib` for a narrower-sample, swept-parameter follow-up without any copy-paste or
reimplementation -- a pattern any future F006 slice narrowing an existing note's sample or
sweeping one of its fixed constants can reuse directly.

## Tests

No new pure-function logic was added in this slice (`cross_symbol_gate` is imported unmodified
from the prior note's script and is already covered by `tests/test_entry_cross_symbol.py`'s 5
tests); this note's only new logic is the `MIN_AGREE` sweep loop, the two additional harness
controls (vs. the prior cross-symbol note's own `MIN_AGREE=2` results, vs. `f006_notrail_monthly`),
and the monotonicity invariant check -- all three verified empirically by this run itself
(0/20, 0/20, 0 violations respectively, reported in the Result section above) rather than by a
separate unit test, since each is a property of this run's own output that a synthetic fixture
cannot check more directly than rerunning the real 20-series sample already does.
`tests/test_regularity.py`'s and `tests/test_entry_cross_symbol.py`'s existing tests re-run to
confirm no regression, since no existing module or test file was changed.

Full suite, Python 3.9 `.venv_test` (no Lorentzian dependency in this sample):

| | Before this slice | With this slice |
| --- | --- | --- |
| `pytest tests/` | 161 passed, 10 skipped | **161 passed, 10 skipped** |

No test file changed or added in this slice -- all discriminating checks for this slice's own new
logic (the sweep loop, harness controls, monotonicity check) are enforced in-script as hard stops
(`SystemExit`) and verified against this run's own clean output, per the pattern above.

