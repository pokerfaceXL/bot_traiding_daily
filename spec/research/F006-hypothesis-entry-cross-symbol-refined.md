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
