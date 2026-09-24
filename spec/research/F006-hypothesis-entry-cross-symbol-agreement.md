# F006 -- Hypothesis: does a cross-sectional signal-agreement gate across the other 4
# symbols in the basket clear the monthly criterion for the three NO_TRAIL lead names?
# Train 1 only

> Sections "Observation" through "Falsification condition" (including the sample, the exact
> gate formula and the exact predicted effect) are written and committed to this file BEFORE
> `scripts/f006_entry_cross_symbol_experiment.py` is written and before any backtest is run,
> per the same discipline as every prior F006 hypothesis note. "Run_id", "Result", "Decision"
> and "Tests" are filled in after the run.
>
> TRAIN-1 ONLY, same window as every F006 slice: `[2024-03-01T00:00:00Z, 2025-03-01T00:00:00Z)`
> plus the protocol's 35-day warm-up buffer from `2024-01-26T00:00:00Z`. Validation 1-4 and the
> Holdout window are not loaded, not sliced and not looked at by any script in this slice.

## Observation

`F006-hypothesis-notrail-monthly.md` established the baseline this whole sub-family targets:
0/30 `(name, symbol, interval)` series at `NO_TRAIL` (`activate_pct=10.0`, `max_sl_pct=0.03`)
clear `spec/research/F005-validation-protocol.md` section 7's monthly promotion checklist for
`DONCHIAN_55`, `BB_20_25_breakout`, `DONCHIAN_PULLBACK_55` -- every series has 2-9 losing months
out of 12, "spread thin" rather than concentrated, a structural consequence of a low win rate
(14-32% pooled) carried by occasional large winners.

Three mechanistically distinct filters/sizing schemes have since been tried against this exact
target and all three failed for the **same root reason**, restated once per note but converging
on one mechanism: this family's edge is concentrated specifically in the entries that a
volatility-*magnitude* measure -- whichever way it is applied -- systematically discounts.
`F006-hypothesis-entry-width-expansion.md` gated on channel/band-width magnitude (is volatility
currently expanding); win rate moved +0.42 pp against a 52% trade-count cut, and the one series
that technically cleared the checklist did so by trading zero times (starving the sample, not
selecting). `F006-hypothesis-entry-trend-confirm.md` gated on EMA50/EMA200 directional
agreement (a magnitude-adjacent, own-symbol-only trend read); win rate *fell* -3.16 pp because
the gate disproportionately removed the fresh, large-magnitude breakout moves this family's edge
depends on. `F006-hypothesis-position-sizing-vol-inverse.md` sized stake inversely to ATR%
(magnitude again, applied as a continuous weight instead of a boolean); the winner/loser
multiplier gap was statistically indistinguishable from zero (-0.0061, wrong sign) and mean PnL
fell. That note's Decision section named the three remaining untried, orthogonal-to-volatility
levers explicitly: *"recency of the last loss, cross-sectional signal agreement across symbols,
or an exit-side lever."* This note takes the second: **cross-sectional signal agreement across
symbols** -- a market-wide directional-agreement measure, mechanistically distinct from all three
falsified approaches because it is the only one of the four that reads *any* information from a
symbol other than the one being traded, and it measures agreement of *direction*, not magnitude
of anything on the traded symbol itself.

**What this slice reuses, unmodified.** `entry_masks.normalized_signal` (NaN -> 0, integer,
already used by every prior filter note) applied to
`entry_masks.strategy_signal_series(df, name, interval, now)` for a `(name, symbol, interval)`
gives a **persistent-state** directional series: `donchian.py`'s own docstring for
`sig_donchian_breakout` states this explicitly ("Persistent state ... the value only changes
when the OPPOSITE extreme is breached, so one contiguous run = one directional call"), and
`strategy.py`'s `sig_bb_breakout` is a plain `close > upper -> +1` / `close < lower -> -1`
comparison, also persistent bar-to-bar until price re-crosses a band. `sig_donchian_pullback`
(the `DONCHIAN_PULLBACK_55` signal) is a state machine over the same breakout direction, also
persistent (`held` is carried forward in `donchian.py`'s `sig_donchian_pullback` loop, "HOLD --
carried forward until the next ARM"). All three target names' own signal is therefore already,
by construction, a well-defined "which way is this symbol currently leaning" state at every bar
-- exactly the quantity a cross-sectional agreement measure needs, with no new indicator
invented.

**Confirmed, not assumed, before designing the gate**: probed directly in this worktree
(`data_contract.load_dataset` for all 5 basket symbols, both intervals, the full
`[2024-01-26T00:00:00Z, 2026-09-01T00:00:00Z)` range) -- all 5 symbols share an **identical**
`DatetimeIndex` at each interval (`240`: 5,695 bars each, `2024-01-26T00:00:00Z` ..
`2026-09-01T00:00:00Z`; `60`: 22,777 bars each, same range; `pd.Index.equals` is `True` for every
symbol against `BTCUSDT`'s index at both intervals). Cross-symbol agreement can therefore be
computed by direct positional/index alignment -- no resampling, no nearest-neighbour join, no
partial-overlap handling is needed for this basket, and the gate's own code still reindexes
defensively (as `entry_regime_mask` and every prior gate does) so a future basket change that
breaks this fact fails loud rather than silently misaligning bars.

## Hypothesis

**H1.** Gating new entries of `DONCHIAN_55`, `BB_20_25_breakout` and `DONCHIAN_PULLBACK_55` on
at least **2 of the other 4** basket symbols (`SOLUSDT`/`ETHUSDT`/`BTCUSDT`/`XRPUSDT`/`DOGEUSDT`,
excluding the symbol being traded) currently showing the **same-name signal in the same
direction**, at the same bar and the same interval, at the moment of entry -- applied via
`backtest_engine.run_backtest`'s existing `entry_regime_mask` hook, on top of the existing
one-shot mask, at `NO_TRAIL` (`activate_pct=10.0`, `max_sl_pct=0.03`) -- causes **at least 1 of
the 30** `(name, symbol, interval)` series to **genuinely** clear
`spec/research/F005-validation-protocol.md` section 7's monthly promotion checklist (identical
three criteria to every prior note in this family: full-run max drawdown <= 50%, net PnL >= 0 in
every `is_valid` Train-1 calendar month, net PnL >= 0 over the full Train-1 period), where that
checklist has been 0/30 genuine in every prior note that measured it (unfiltered baseline, width
gate, trend gate, vol-inverse sizing).

**"Genuinely clears" is a precondition of the falsification condition, not merely reported
alongside it, exactly as every prior filter note in this family required (the recurring flagged
gap this ticket names): `n_trades_filtered > 0` for that series.**

**Threshold, fixed before running, not swept.** `MIN_AGREE = 2` (at least 2 of the other 4
symbols agree, i.e. at least 3 of the 5 basket symbols -- the traded one plus 2 others -- lean
the same direction at that bar). This is the one concrete pre-registered hypothesis the ticket
asks for, not a parameter search: `MIN_AGREE=1` (any single other symbol agreeing) is a weak
filter unlikely to remove much of the sample given 3-valued signals are already sign-correlated
across a crypto basket by market beta alone; `MIN_AGREE=4` (unanimity) is very likely to reproduce
the starving-the-sample failure the width-expansion note's Decision section explicitly warned
against repeating (this ticket's own falsification-condition requirement). `MIN_AGREE=2` -- a
simple majority of the other four -- is the middle, best-justified single choice and is the only
threshold tested in this note; no sweep is run.

**Mechanism, stated before running.** A breakout that fires on one symbol while the rest of the
basket shows no directional lean is more likely an idiosyncratic, single-asset event (a local
liquidity gap, a symbol-specific news flash, noise) than a genuine directional move -- these are
exactly the low-conviction entries a low win rate carried by rare large winners would predict get
stopped out. A breakout that fires while a majority of the rest of the basket already leans the
same direction is more likely part of a genuine market-wide move (crypto assets are known to be
highly beta-correlated; a coordinated cross-symbol lean is evidence of a real regime, not of this
symbol's own recent volatility, which is exactly why this measure is orthogonal to the three
failed volatility-magnitude mechanisms: it says nothing about how wide, expanded, or extreme
*this* symbol's own channel/band/ATR currently is, only about what the *rest of the basket* is
doing). Because the gate reads no information about the traded symbol's own magnitude, it should
not reproduce the starving-the-sample or select-against-the-edge failure modes of the three
falsified mechanisms, which all discounted entries in proportion to how large/fresh/volatile the
traded symbol's own breakout was.

## Distinguishing genuine selection from starving the sample (the ticket's explicit requirement)

Reported for every series, not falsifying by itself but load-bearing for whether a checklist pass
(if any) is substantive: **win rate among surviving trades, pooled and per name, filtered vs.
unfiltered** -- the direct test the width-expansion note's Result section retroactively
identified as the one that would have caught its own degenerate pass. A pass produced by a filter
that shrinks the sample without raising win rate above what trade-count reduction alone would
predict is the same failure mode already seen three times, restated with a fourth mechanism; a
pass produced by a filter that *does* raise surviving-trade win rate materially is a genuinely
different outcome. Specifically, before running, this note commits to computing and reporting
(not merely eyeballing): pooled win rate filtered vs. unfiltered (comparable directly against the
width-expansion note's own +0.42 pp-against-52%-cut and the trend-confirm note's -3.16 pp, both
already-established reference points for "not real"); per-name win rate filtered vs. unfiltered;
and, for every series with `promotion_pass_filtered=True`, an explicit
`degenerate_pass` flag (`n_trades_filtered == 0`) computed in code, exactly the guard the
width-expansion note's own Decision section said should exist from the start and every note since
has carried forward.

## Sources

This repo's own prior findings and pre-existing, unmodified code only:
`F006-hypothesis-notrail-monthly.md` (the 0/30 baseline, the monthly checklist definition),
`F006-hypothesis-entry-width-expansion.md` (the falsified magnitude gate, its degenerate
zero-trade pass, the `n_trades > 0` guard pattern), `F006-hypothesis-entry-trend-confirm.md` (the
falsified own-symbol direction gate, confirming the edge is concentrated in fresh/large moves),
`F006-hypothesis-position-sizing-vol-inverse.md` (the falsified ATR%-inverse sizing scheme and
its Decision section naming this note's exact lever), `F006-hypothesis-trailing-boundary.md` (the
`NO_TRAIL` cell definition and the three names), `F006-hypothesis-donchian.md` (the win/loss
decomposition motivating why fresh/large moves carry this family's edge),
`spec/research/F005-validation-protocol.md` section 7 (the monthly promotion criterion,
verbatim), `entry_masks.py` (`normalized_signal`/`strategy_signal_series`/`one_shot_entry_mask`,
unmodified), `donchian.py`/`strategy.py` (the three names' own persistent-state signal
definitions, unmodified).

## Sample (identical set of series to every prior note in this family, not re-derived)

30 series: `DONCHIAN_55`, `BB_20_25_breakout`, `DONCHIAN_PULLBACK_55` x
`SOLUSDT`/`ETHUSDT`/`BTCUSDT`/`XRPUSDT`/`DOGEUSDT` x `240`/`60`. For each traded series, the
"other 4 symbols" are exactly the other 4 members of this same basket at the same interval --
the gate needs all 5 symbols' own signal loaded for a given `(name, interval)`, but the traded
series themselves are unchanged from every prior note. `DONCHIAN_55` and `DONCHIAN_PULLBACK_55`
need `donchian.py` (pure pandas); `BB_20_25_breakout` is a plain `strategy.STRATEGY_CATALOG`
entry. No Lorentzian dependency -- single pass on `.venv_test` (Python 3.9) covers all 30 series.

## Method

**Engine parameters: identical to `F006-hypothesis-notrail-monthly.md`'s cell, unchanged.**
`activate_pct=10.0` (NO_TRAIL), `trail_pct=0.04` (moot, `None`), `max_sl_pct=0.03`,
`atr_multiplier=1.5`, `cooldown_candles=0`, `leverage=1.0`, `commission_rate_bps=10.0`,
`half_spread_bps=5.0`, `slippage_bps=2.0`, `initial_equity=500.0`, `stake=100.0`, `now` pinned to
`2025-03-01T00:00:00Z`. **No change to `backtest_engine.py`, `strategy.py`, `entry_masks.py`,
`donchian.py`, `regularity.py`.** The cross-symbol gate needs no engine change at all (unlike the
position-sizing note's additive `stake_series` hook): it is a boolean mask computed entirely in
the new script from already-existing per-symbol signal series and handed to the existing
`entry_regime_mask` parameter, exactly the pattern the width-expansion and trend-confirm notes
established.

**Cross-symbol agreement gate, computed in the new script, not by editing any module.** For a
given `(name, interval)`, and for each of the 5 basket symbols `s`:

* `own_signal[s] = entry_masks.normalized_signal(entry_masks.strategy_signal_series(df[s], name,
  interval, now))` -- the persistent +1/-1/0 directional state, identical construction to every
  prior filter note, computed once per `(name, symbol, interval)` and reused for both the traded
  role and the "other symbol" voting role.
* For the series where `s` is the **traded** symbol, `others = [own_signal[s2] for s2 in SYMBOLS
  if s2 != s]` (the other 4), each `.reindex(own_signal[s].index).fillna(0)` (defensive; the
  index-equality fact above means this reindex is a no-op on this basket, but the code does not
  assume it).
* `agreement_count[i] = sum(1 for o in others if int(o[i]) == int(own_signal[s][i]) and
  own_signal[s][i] != 0)` -- counts only the other symbols whose own current directional state
  exactly matches the traded symbol's own current directional state, evaluated only where the
  traded symbol itself has a nonzero stance (a bar where the traded symbol is flat is never an
  entry-eligible bar under the existing one-shot mask regardless, so `agreement_count` at a flat
  bar is moot and not used).
* `cross_symbol_gate[i] = agreement_count[i] >= MIN_AGREE` (`MIN_AGREE = 2`, fixed, not swept).
* `entry_regime_mask = one_shot_entry_mask(own_signal[s]) & cross_symbol_gate`, reindexed by
  `run_backtest` onto its own post-filter/post-indicator frame (existing engine behaviour,
  unchanged). A call whose start bar fails the agreement condition is never entered at all -- the
  mask does not re-arm later in that same call, matching the one-shot semantics the rest of F006
  uses.

- **Script**: `scripts/f006_entry_cross_symbol_experiment.py`. Single pass, `.venv_test` only.
- **Data**: identical checksum-verified load (`data_contract.load_dataset`, `EXPECTED_CHECKSUMS`
  table duplicated from `spec/research/F005-validation-protocol.md` section 6) and Train-1 slice
  (`[2024-01-26T00:00:00Z, 2025-03-01T00:00:00Z)`) as every F006 script. No network fetch. Unlike
  every prior note in this family, this script loads **all 5 basket symbols** for a given
  interval before scoring any single series (needed to build the "other 4" vote), but still
  scores and reports each of the 30 `(name, symbol, interval)` series independently.
- **Aggregation**: `regularity.py`, unchanged, called exactly as every prior note in this family
  calls it, with the identical `promotion_pass` definition (drawdown <= 50%, all 12 Train-1
  calendar months `is_valid` and net PnL >= 0, full Train-1 net PnL >= 0), plus
  `promotion_pass_genuine = promotion_pass_filtered AND n_trades_filtered > 0`.
- **Recorded per series**: everything the trend-confirm note recorded for its filtered/unfiltered
  arms (`n_trades`, Train-1 net PnL, 12 monthly rows, `promotion_pass`, `promotion_pass_genuine`,
  win rate, `n_calls_gated_out`), plus `n_months_flipped_to_zero_trade` (same artefact guard as
  every prior filter note in this family) and an explicit `degenerate_pass` boolean.

**Discriminating checks:**

1. **Index-equality precondition, checked not assumed**: for every interval, all 5 symbols'
   loaded Train-1-slice frames must have an identical `DatetimeIndex` (`pd.Index.equals`) --
   already confirmed true in this worktree's data (see Observation) but re-asserted in the script
   itself; any mismatch stops the run rather than silently misaligning bars via a reindex that
   introduces NaN-filled gaps.
2. **Subset invariant**: `n_trades_filtered <= n_trades_unfiltered` for all 30 series (the
   cross-symbol gate can only remove entries the one-shot mask already allowed, never add one) --
   checked in script, any violation stops the run.
3. **Harness control against the unfiltered baseline**: the `n_trades_unfiltered` /
   `train1_net_pnl_unfiltered` column, produced by re-running this script's own pipeline with the
   gate forced to all-True, must match `output/f006_notrail_monthly/summary/results.csv`'s stored
   `train1_net_pnl`/`n_trades` for all 30 series (0 mismatches expected) -- validates the new
   script's engine-call plumbing against the already-verified prior note.
4. **No lookahead in the agreement gate**: `own_signal`/`others` are built entirely from
   `entry_masks.strategy_signal_series`, whose own docstring states it reproduces the engine's
   exact causal pipeline; `agreement_count[i]` reads only `others[k][i]` at the same bar `i`,
   never a future bar. A new fixture test asserts truncating a 5-symbol synthetic panel at a later
   bar does not change `agreement_count`/`cross_symbol_gate` at any already-computed earlier bar,
   mirroring the causality-check pattern every prior filter note in this family uses.
5. **Genuineness guard enforced in code, not only in prose**: `promotion_pass_genuine` is a
   computed column; any series with `promotion_pass_filtered=True` and `n_trades_filtered=0` is
   flagged `degenerate_pass=True` separately, and the Result section reports both counts
   explicitly.
6. **Regularity module regression, unmodified**: `tests/test_regularity.py`'s existing tests
   re-run to confirm no regression, since no new logic is added to `regularity.py`.

## Falsification condition (stated before running)

Evaluated on the same 30 `(name, symbol, interval)` series as every prior note in this family,
against `spec/research/F005-validation-protocol.md` section 7's monthly promotion checklist,
applied per series exactly as `F006-hypothesis-notrail-monthly.md` applied it (verbatim:
drawdown <= 50%, net PnL >= 0 in every `is_valid` Train-1 calendar month, net PnL >= 0 over the
full Train-1 period):

**H1 is falsified if zero of the 30 series have `promotion_pass_genuine = True`** -- i.e. no
series both clears the checklist under the filtered arm AND has `n_trades_filtered > 0`. A series
that clears the checklist only by trading zero times is reported as `degenerate_pass=True`,
exactly the guard every prior note in this family carries, and does **not** count toward H1
surviving, regardless of how the condition is read.

**H1 survives if at least 1 of the 30 series has `promotion_pass_genuine = True`.** A single
genuinely clearing series is sufficient to survive -- it would be the first Validation candidate
F006 has produced in this exact target (three names, `NO_TRAIL`, monthly criterion).

**Distinguishing genuine selection from starving the sample is not a separate pass/fail gate on
H1's own survival, but is mandatory reporting, stated before running, per the ticket's explicit
requirement**: regardless of whether H1 survives or is falsified, this note reports pooled win
rate filtered vs. unfiltered and per-name win rate filtered vs. unfiltered, and states explicitly
whether any observed improvement (checklist pass or otherwise) is better explained by "win rate
rose materially" (genuine selection) or by "trade count fell without win rate rising
correspondingly" (the starving-the-sample failure mode all three prior mechanisms showed) --
using the width-expansion note's own +0.42 pp/-52% and the trend-confirm note's -3.16 pp/-48% as
the two already-established reference points for "not real," so this note's own win-rate delta
is judged against a concrete precedent rather than in isolation.

## Run_id

`scripts/f006_entry_cross_symbol_experiment.py`, `git_commit_parent` = the pre-registration
commit above, single pass, `.venv_test` (Python 3.9, pandas 2.2.3, rebuilt in this worktree from
the cached offline wheelhouse at `/tmp/mine-strategy-wheels` plus `/tmp/pipdl`/
`/tmp/pip-unpack-aa92hd6x`/`/tmp/pip-unpack-qe5fl2rp`, since this worktree's `.venv_test` did not
pre-exist; no network access). This worktree's `data_cache/*.csv` (git-ignored) were also missing
and were copied unmodified from the main checkout's `data_cache/` before the first run; the
checksum verification against `spec/research/F005-validation-protocol.md` section 6 confirms the
copy is byte-identical to the frozen dataset every other F006 note uses. Filled in after running.

## Result

Filled in after running.

## Decision

Filled in after running.

## Tests

Filled in after running.
