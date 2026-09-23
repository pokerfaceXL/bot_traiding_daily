# F006 — Hypothesis: does a directional higher-order-trend confirmation gate (not a
# volatility-magnitude gate) clear the monthly criterion for the three NO_TRAIL lead
# names? Train 1 only

> Sections "Observation" through "Falsification condition" (including the sample and the exact
> predicted effect) are written and committed to this file BEFORE
> `scripts/f006_entry_trend_confirm_experiment.py` is written and before any backtest is run,
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
`DONCHIAN_55`, `BB_20_25_breakout`, `DONCHIAN_PULLBACK_55` — the three names
`F006-hypothesis-trailing-boundary.md` identified as the only ones with positive aggregate
Train-1 net PnL at that exit-geometry cell. `F006-hypothesis-donchian.md`'s decomposition
explains why: pooled win rate 14-32% against a breakeven requirement 20-27 points higher, driven
by avg loser running 1.7-2.3x avg winner — a low-win-rate-carried-by-occasional-large-winners
edge that, per the monthly note's own finding, produces losing months "spread thin" across the
year (mode 7/12) rather than concentrated, which a zero-tolerance monthly rule cannot admit no
matter how positive the full-period sum is.

Two entry-side filters have since been tried against this exact target and both failed the same
way. `F006-hypothesis-entry-regime-filter.md` gated on ADX14 magnitude (old exit geometry, whole
catalog, not targeted at these three names — cited here only as the first data point of the
pattern). `F006-hypothesis-entry-width-expansion.md` gated `DONCHIAN_55`/`BB_20_25_breakout`/
`DONCHIAN_PULLBACK_55` at `NO_TRAIL` on their own channel/band width being above its trailing
30-bar mean (a volatility-*magnitude* condition: is the channel currently wide, regardless of
which way price is moving). That note's Result is unambiguous and is the direct predecessor of
this one: trade count fell 52.1% (1,695 → 812 trades) while pooled win rate moved only +0.42 pp
(25.07% → 25.49%) — an order of magnitude too small to explain any month flipping sign — and mean
net PnL per series *fell* ($48.45 → $15.21). The one series that technically cleared the checklist
(`DONCHIAN_55`/DOGEUSDT/4h) did so by having the gate reject all 18 of its directional calls,
producing zero trades and therefore trivially "zero losing months" — a degenerate pass the note's
own falsification condition failed to exclude, flagged explicitly in that note's Result and
Decision sections as a gap that "must not recur." No series with any trading activity cleared the
checklist. The mechanism in both failed filters is identical: the gate is a **threshold on a
scalar magnitude** (ADX strength, channel width) applied independent of the entry signal's own
direction, so it shrinks the sample without changing *which* calls — good or bad — survive. The
width-expansion note's Decision section named the next step in exactly these words: *"a filter
that changes which calls are entered without simply shrinking the sample (e.g. a
directional/multi-timeframe confirmation rather than a magnitude-of-volatility threshold)."*

**What this slice reuses.** `strategy.add_indicators` (called on every one of these three names'
own frame already, inside `entry_masks.strategy_signal_series` and inside `run_backtest` itself —
no new computation is introduced) computes `ema50` and `ema200` on every symbol/interval, columns
none of the three target names currently reads. `ema50` vs `ema200` — the "golden/death cross"
relationship — is a standard slower-horizon trend filter: whether the market's own medium-term
average sits above or below its long-term average at the moment of entry. This is categorically
different from both prior gates: it is not a magnitude (it says nothing about how strong or wide
anything is), and it does not shrink the sample by a blanket threshold — it removes only the calls
whose own direction *disagrees* with the slower trend, which is exactly the "does the direction of
this signal agree with a slower, independent read of direction" shape the width-expansion note's
Decision section asked for. A genuine higher-*timeframe* confirmation (resampling to a slower bar
interval than the dataset provides) is not available for half the sample: `data_contract`'s cache
only holds `240` and `60` minute bars per symbol, and `240` is already the slowest interval in
this project — there is no higher timeframe to resample the 4h series up to without fetching new
data, which is out of scope and would silently violate the frozen-dataset checksum discipline
every F006 note has followed. Restricting a true HTF filter to only the 15 `60`-interval series
would also repeat exactly the sample-shrinking failure mode this slice exists to avoid, only at
the design stage instead of the filter stage. The EMA50/EMA200 relationship is therefore used as
the directional confirmation: available uniformly on all 30 series, computed from data already
loaded for every one of them, and orthogonal on its face to both magnitude gates already
falsified.

## Hypothesis

**H1.** Gating new entries of `DONCHIAN_55`, `BB_20_25_breakout` and `DONCHIAN_PULLBACK_55` on
the entry signal's direction agreeing with the sign of `ema50 - ema200` at the entry bar (long
entries only when `ema50 > ema200`, short entries only when `ema50 < ema200`) — applied via
`backtest_engine.run_backtest`'s `entry_regime_mask` hook, on top of the existing one-shot mask,
at `NO_TRAIL` (`activate_pct=10.0`, `max_sl_pct=0.03`) — causes **at least 1 of the 30**
`(name, symbol, interval)` series to **genuinely** clear
`spec/research/F005-validation-protocol.md` section 7's monthly promotion checklist (identical
three criteria to `F006-hypothesis-notrail-monthly.md`: full-run max drawdown ≤ 50%, net PnL ≥ 0
in every `is_valid` Train-1 calendar month, net PnL ≥ 0 over the full Train-1 period) —
where that note found 0/30 without any filter and `F006-hypothesis-entry-width-expansion.md`
found 0/30 genuine passes (1/30 degenerate) with the volatility-width filter. **"Genuinely
clears" here means, and is checked as an explicit precondition of the falsification condition
below, not merely reported alongside it: `n_trades_filtered > 0`.** A series that clears the
checklist by trading zero times does not count as clearing it, per the width-expansion note's
own flagged gap.

**Mechanism, stated before running.** A Donchian/BB breakout that fires *against* the slower
EMA50/EMA200 trend is, by construction, either a counter-trend move likely to fail (mean-revert
back through the 3% initial stop before the slower trend catches up) or the leading edge of a
trend reversal the EMA200 has not yet recognised — in either case a lower-conviction entry than
one that fires *with* an already-established slower trend. Unlike the width gate (which asks "is
volatility currently expanding," a question orthogonal to which way price is going), this gate
asks a question directly about the same axis the signal itself measures — direction — using an
independent, slower-moving estimate of it. If the monthly note's "spread thin" losing-month
pattern is driven partly by counter-trend breakouts failing inside an otherwise-favourable slower
trend, removing them should raise win rate on the *surviving* trades specifically (not merely
shrink the sample uniformly), which is the discriminator this slice is built to measure and the
width-expansion note's filter conspicuously failed to produce.

**Predicted effect**, reported regardless of whether H1 survives: pooled win rate across the 30
filtered series is higher than the 30 unfiltered series by a margin large relative to the
trade-count reduction (unlike the width-expansion note's +0.42 pp against a 52% cut); mean number
of losing months per series (out of 12) is lower for series that still trade a non-trivial number
of times, not merely for series pushed toward zero trades; and n_trades falls (the gate is
strictly a subset of the existing one-shot mask, so `n_trades_filtered <= n_trades_unfiltered` for
every one of the 30 series, checked as a harness invariant, not just predicted). Because the width
gate already demonstrated that raw trade-count reduction alone can produce a degenerate pass, this
slice additionally reports, for every series (not only ones that clear the checklist), whether any
of its "months that turned non-negative under the filter" did so because the month had zero trades
rather than a non-negative sum of real trades — the same artefact the width-expansion note's
Result section diagnosed after the fact, checked here proactively.

## Sources

This repo's own prior findings only, plus the pre-existing, unmodified `strategy.add_indicators`
columns this slice reuses: `F006-hypothesis-notrail-monthly.md` (the 0/30 baseline, the monthly
checklist definition), `F006-hypothesis-entry-width-expansion.md` (the falsified
magnitude-of-volatility gate, its degenerate zero-trade pass, and the Decision section that names
this slice's direction as the next step, verbatim), `F006-hypothesis-trailing-boundary.md` (the
`NO_TRAIL` cell definition and the three names), `F006-hypothesis-donchian.md` (the win/loss
decomposition motivating the mechanism, and the causal `donchian_channel` this slice reuses
unmodified), `spec/research/F005-validation-protocol.md` section 7 (the monthly promotion
criterion, verbatim).

## Sample (identical set of series to every prior note in this family, not re-derived)

30 series: `DONCHIAN_55`, `BB_20_25_breakout`, `DONCHIAN_PULLBACK_55` ×
`SOLUSDT`/`ETHUSDT`/`BTCUSDT`/`XRPUSDT`/`DOGEUSDT` × `240`/`60`. `DONCHIAN_55` and
`DONCHIAN_PULLBACK_55` need `donchian.py` (pure pandas); `BB_20_25_breakout` is a plain
`strategy.STRATEGY_CATALOG` entry. `ema50`/`ema200` come from `strategy.add_indicators`, already
called on every one of these frames by `entry_masks.strategy_signal_series`. No Lorentzian
dependency — single pass on `.venv_test` (Python 3.9) covers all 30 series.

## Method

**Engine parameters: identical to `F006-hypothesis-notrail-monthly.md`'s cell, unchanged.**
`activate_pct=10.0` (NO_TRAIL), `trail_pct=0.04` (moot, `None`), `max_sl_pct=0.03`,
`atr_multiplier=1.5`, `cooldown_candles=0`, `leverage=1.0`, `commission_rate_bps=10.0`,
`half_spread_bps=5.0`, `slippage_bps=2.0`, `initial_equity=500.0`, `stake=100.0`, `now` pinned to
`2025-03-01T00:00:00Z`. **No change to `backtest_engine.py`, `strategy.py`, `entry_masks.py`,
`donchian.py`, `regularity.py`.**

**Trend-direction gate, computed in the new script, not by editing `strategy.py`.** Built as a
standalone entry mask, combined with the existing one-shot mask via `entry_regime_mask`, exactly
the pattern `F006-hypothesis-entry-width-expansion.md` established, so the only thing this slice
changes is which call-start bars are allowed to open a position:

* `trend[i] = +1` if `ema50[i] > ema200[i]`, `-1` if `ema50[i] < ema200[i]`, else `0` (only in the
  ema200 warm-up window, handled by `.rolling`/`.ewm` NaN propagation — no bar with a defined
  `ema200` value is ever `0`, since strict inequality resolves one way or the other for any two
  distinct floats and a tie is measure-zero on real price data).
* `direction_at_entry[i]` = the signal's own value at bar `i` (`+1`/`-1`), read directly off the
  same normalized signal `entry_masks.one_shot_entry_mask` is built from — no new derivation.
* `trend_gate[i] = (direction_at_entry[i] == trend[i])`.
* `entry_regime_mask = one_shot_entry_mask(signal) & trend_gate`, reindexed by `run_backtest` onto
  its own post-filter/post-indicator frame (existing engine behaviour, unchanged). A call whose
  start bar fails the direction-agreement condition is never entered at all — the mask does not
  re-arm later in that same call, matching the one-shot semantics the rest of F006 uses.

- **Script**: `scripts/f006_entry_trend_confirm_experiment.py`. Single pass, `.venv_test` only.
- **Data**: identical checksum-verified load (`data_contract.load_dataset`, `EXPECTED_CHECKSUMS`
  table duplicated from `spec/research/F005-validation-protocol.md` section 6) and Train-1 slice
  (`[2024-01-26T00:00:00Z, 2025-03-01T00:00:00Z)`) as every F006 script. No network fetch.
- **Aggregation**: `regularity.py`, unchanged, called exactly as
  `scripts/f006_entry_width_expansion_experiment.py` calls it, with the identical `promotion_pass`
  definition (drawdown ≤ 50%, all 12 Train-1 calendar months `is_valid` and net PnL ≥ 0, full
  Train-1 net PnL ≥ 0).
- **Recorded per series**: everything the width-expansion note recorded (`n_trades`, Train-1 net
  PnL, 12 monthly rows, `promotion_pass`, both filtered and unfiltered arms, `n_calls_gated_out`),
  **plus `promotion_pass_genuine` = `promotion_pass_filtered AND n_trades_filtered > 0`** (the
  guard this note's falsification condition requires) and, for every series, a
  `n_months_flipped_to_zero_trade` count: among the Train-1 calendar months whose net PnL is
  negative in the unfiltered arm and non-negative (because the month contains 0 filtered trades)
  in the filtered arm, how many are "genuine improvement" (month still has ≥1 filtered trade,
  summing non-negative) vs. "artefact" (month has 0 filtered trades) — computed directly from the
  per-trade timestamps already available in `result.trades`, not inferred from the monthly PnL
  alone.

**Discriminating checks:**

1. **Subset invariant**: `n_trades_filtered <= n_trades_unfiltered` for all 30 series (the trend
   gate can only remove entries the one-shot mask already allowed, never add one) — checked in
   script, any violation stops the run.
2. **Harness control against the unfiltered baseline**: the `n_trades_unfiltered` /
   `train1_net_pnl_unfiltered` column, produced by re-running this script's own pipeline with the
   gate forced to all-True, must match `output/f006_notrail_monthly/summary/results.csv`'s stored
   `train1_net_pnl`/`n_trades` for all 30 series (0 mismatches expected) — validates the new
   script's engine-call plumbing against the already-verified prior note.
3. **No lookahead in the trend gate**: `ema50`/`ema200` are `pandas.Series.ewm(...).mean()` over
   past-and-current bars only (`strategy.add_indicators`, unmodified, already relied on by every
   EMA-based catalog entry without a dedicated causality test in this repo) — but a new fixture
   test asserts truncating a frame does not change the trend-gate boolean at any already-computed
   bar, mirroring `tests/test_entry_width_expansion.py`'s causality-check pattern, so this slice's
   *use* of the columns (not just the columns themselves) is pinned.
4. **n_trades>0 guard is enforced in code, not only in prose**: `promotion_pass_genuine` is a
   computed column, not a post-hoc filter applied by hand when reading `results.csv` — any series
   with `promotion_pass_filtered=True` and `n_trades_filtered=0` is flagged in the manifest as a
   `degenerate_pass`, separate from `genuine_pass`, and the Result section below reports both
   counts explicitly rather than only the genuine one.
5. **Regularity module regression, unmodified**: `tests/test_regularity.py`'s existing tests
   re-run to confirm no regression, since no new logic is added to `regularity.py`.

## Falsification condition (stated before running)

Evaluated on the same 30 `(name, symbol, interval)` series as every prior note in this family,
against `spec/research/F005-validation-protocol.md` section 7's monthly promotion checklist,
applied per series exactly as `F006-hypothesis-notrail-monthly.md` applied it (verbatim: drawdown
≤ 50%, net PnL ≥ 0 in every `is_valid` Train-1 calendar month, net PnL ≥ 0 over the full Train-1
period):

**H1 is falsified if zero of the 30 series clear the checklist WITH `n_trades_filtered > 0`** —
i.e. `promotion_pass_genuine` is `False` for all 30 series. **A series with
`promotion_pass_filtered=True` and `n_trades_filtered=0` does NOT count toward survival under any
reading of this condition** — this is the explicit guard the width-expansion note's Decision
section said should have been in its own falsification condition from the start. Such a series is
reported as a `degenerate_pass` in the Result section, exactly as the prior note's single
degenerate case was, but it does not change the falsification verdict.

**H1 survives if at least 1 of the 30 series has `promotion_pass_genuine = True`** (clears the
checklist with at least one trade in the filtered arm). A single genuinely clearing series is
sufficient to survive — it would be the first Validation candidate F006 has produced.

Reported either way, not falsifying by itself (mechanism checks, per the predicted effect above):
pooled win rate with vs. without the gate; mean number of losing months per series with vs.
without the gate, computed separately for series whose `n_trades_filtered` stays above half its
unfiltered value (a check that the improvement, if any, is not concentrated entirely in
near-zero-trade series); n_trades reduction per name (is the gate removing a similar fraction of
calls from all three names or concentrated in one); and the `n_months_flipped_to_zero_trade`
artefact-vs-genuine breakdown described in Method, for every series regardless of whether it
clears the checklist.

## Run_id

`scripts/f006_entry_trend_confirm_experiment.py`, `git_commit_parent = 6f58528efcaed040b5ff8f4623de3b0cb7ab6f9a`
(the pre-registration commit above), single pass, `.venv_test` (Python 3.9.25, pandas 2.2.3 --
rebuilt in this worktree from a cached offline wheelhouse at `/tmp/mine-strategy-wheels` plus
`/tmp/pipdl` (pyyaml) and `/tmp/pip-unpack-aa92hd6x` (python-dotenv), since this worktree's
`.venv_test` did not pre-exist; no network access), 30 series, 21.4s. This worktree's
`data_cache/*.csv` files (git-ignored, symbol/interval OHLCV) were also missing and were copied
unmodified from the main checkout's `data_cache/` before the first run -- the checksum
verification against `spec/research/F005-validation-protocol.md` section 6 (0/10 mismatches, see
below) confirms the copied files are byte-identical to the frozen dataset every other F006 note
uses, not a different or re-fetched dataset. Per-series results and monthly tables:
`output/f006_entry_trend_confirm/raw/*.json` (30 files, filtered + unfiltered monthly breakdown
each). Summary table: `output/f006_entry_trend_confirm/summary/results.csv`. Manifest, checksums,
harness-control and subset-invariant records: `output/f006_entry_trend_confirm/summary/manifest.json`.
Re-run once after a sabotage-and-restore pass on `trend_gate` (see Tests) to confirm determinism:
identical `results.csv` and manifest figures both times.

## Result

**Falsified. 0 of 30 series is even a degenerate pass, let alone a genuine one.**
`promotion_pass_genuine` is `False` for all 30 series, `promotion_pass_filtered` (before the
`n_trades > 0` guard) is also `False` for all 30 -- unlike the width-expansion note, this slice
produced **zero** degenerate zero-trade passes at all, so there is no ambiguity between a literal
and substantive reading of the falsification condition this time; both readings agree.

**Harness control and subset invariant both clean.** The gate-forced-all-True rerun matches
`output/f006_notrail_monthly/summary/results.csv`'s stored `train1_net_pnl`/`n_trades` for all 30
series -- **0/30 mismatches** -- and all 10 dataset checksums verified against
`spec/research/F005-validation-protocol.md` section 6 before any run. The subset invariant
(`n_trades_filtered <= n_trades_unfiltered`) holds for **30/30** series.

**The predicted mechanism is not just unsupported, it is inverted: pooled win rate falls under
the filter, and by more than trade-count alone would predict.** Trade count fell 48.0% (1,695
unfiltered -> 881 filtered, comparable in scale to the width-expansion note's 52.1% cut), but the
trade-weighted pooled win rate **fell** from 25.07% (reproducing the width-expansion note's own
unfiltered baseline exactly, confirming both notes measure the same population) to **21.91%** --
a **-3.16 pp** move, the opposite direction of H1's prediction and seven times larger in
magnitude than the width gate's +0.42 pp (itself judged "an order of magnitude too small to be
real"). Mean net PnL per series fell from $48.45 to **$18.47** (62% of the deficit is a straight
loss, not a wash), and the count of series with positive Train-1 net PnL fell from 18/30 to
**13/30**. Mean losing months per series also moved the wrong way: **6.47 -> 6.93** (worse), where
H1 predicted lower.

**Per name, the direction filter is not selective -- it removes calls in proportion to how often
the signal already disagreed with the slower trend, which for `DONCHIAN_55` is most of the time,
and the removal correlates with destroying the name's own edge rather than concentrating it:**

| Name | mean net PnL, unfiltered | mean net PnL, filtered | mean neg months, unf. | mean neg months, filt. | total trades unf. -> filt. | total calls gated out / total calls |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `DONCHIAN_55` | $58.39 | **-$3.57** | -- | -- | 476 -> 147 (-69%) | 329/476 (69%) |
| `BB_20_25_breakout` | $48.78 | $40.59 | -- | -- | 869 -> 506 (-42%) | 733/1722 (43%) |
| `DONCHIAN_PULLBACK_55` | $38.19 | $18.39 | -- | -- | 350 -> 228 (-35%) | 127/372 (34%) |

`DONCHIAN_55` is hit hardest and worst: 69% of its calls disagree with the slower EMA50/EMA200
trend at the moment they fire, and the filter erases essentially all of its aggregate edge ($58.39
mean net PnL falls to -$3.57, a near-total wipeout, worse even than the width-expansion note did
to this same name at $0.06). This is the opposite of a coincidence: a Donchian breakout fires
*at* a new N-bar extreme, which is mechanically the moment price is furthest from its own recent
average and therefore most likely to be running ahead of a slower-moving EMA50/EMA200 pair that
has not yet caught up -- so the direction filter disqualifies a large fraction of exactly the
fresh breakouts that carry this family's edge (per `F006-hypothesis-donchian.md`'s own
decomposition, a low win rate carried by occasional large winners; a fresh breakout that runs far
is exactly the kind of move this family depends on, and it is exactly the kind of move that
temporarily disagrees with a 200-bar-lagged average). `BB_20_25_breakout` and
`DONCHIAN_PULLBACK_55` are hit less hard (43% and 34% of calls gated respectively, since a
Bollinger breakout and a pullback-triggered entry are both less extreme relative to their own
recent range than a raw Donchian breakout) and keep more of their PnL, but neither shows the
predicted win-rate improvement either (per-name pooled win rate: `DONCHIAN_55` 27.31% ->
**21.09%**, `BB_20_25_breakout` 25.66% -> **24.11%**, `DONCHIAN_PULLBACK_55` 20.57% -> **17.54%**
-- every single name's win rate falls under the filter, not just the pooled figure).

**The `n_trades > 0` guard, checked proactively rather than after the fact, found no degenerate
case to guard against here -- but the near-miss pattern it was built to catch is visible anyway.**
9 of the 30 series have at least one Train-1 month that was negative unfiltered and flipped to
non-negative filtered *because that month had zero filtered trades* (`n_months_flipped_to_zero_trade`
> 0, 14 such months total, concentrated in `DONCHIAN_55`'s 4h series: 6 of the 9 affected series
are `DONCHIAN_55`/`240`, each losing 1-2 months to this artefact). None of these 9 series comes
anywhere close to clearing the checklist regardless (each still has 4-8 genuinely-evaluated
losing months after removing the artefact ones), so the guard did not change this run's verdict --
but it confirms the artefact is not unique to the width gate: any entry-side filter aggressive
enough to empty out individual months on this basket will produce a few "months" that look clean
only because they are empty, and a future, more selective filter that gets closer to the checklist
will need this guard to avoid the same false read the width-expansion note caught by hand.

**No name and no series shows the predicted signature (win rate up, PnL preserved, losing months
down) on any measure.** Compared to the width-expansion note's result -- which at least kept
`BB_20_25_breakout`'s PnL roughly intact even as its monthly profile worsened -- this filter is
uniformly worse: every name loses PnL, every name's win rate falls, and the pooled losing-months
average rises rather than falls. A slower-EMA trend-agreement filter is not merely unhelpful for
this basket, it is actively counter-productive, and the mechanism is traceable rather than
mysterious: these three names' edge (per `F006-hypothesis-donchian.md`) comes specifically from
fresh, large-magnitude breakout moves, and a slower trend filter systematically excludes the
freshest of those moves because a 50/200-period average has not yet turned by the time a genuine
new extreme is made.

## Decision

**No promotion.** H1 is falsified cleanly, without the literal/substantive split the
width-expansion note had to navigate: no series clears the checklist under any reading, filtered
or genuine. The pre-registered mechanism -- that direction-agreement with a slower trend would
raise win rate on the calls that survive -- is not just unsupported but contradicted: win rate
falls for every one of the three names individually and for the pool, by a margin (-3.16 pp)
larger than the width-expansion gate's own change was in the *opposite*, hoped-for direction.

**This closes out both tested "changes which calls are entered" mechanisms for this exact target
(three names, `NO_TRAIL`, monthly criterion) without a Validation candidate.** The
width-expansion note (a magnitude-of-volatility gate) and this note (a directional trend-agreement
gate) are mechanistically distinct, cover the two concrete examples the width-expansion note's own
Decision section named, and both fail -- the first by shrinking the sample without changing
selection quality, the second by actively selecting *against* the entries that carry this
family's edge. Two structurally different entry-side filters have now both failed for the same
underlying reason stated two different ways: any filter that removes the fresh, large, low-win-rate
breakout moves these three names' edge depends on will look like "fewer bad months" in aggregate
only by trading less, never by trading better.

**What this suggests for any future entry-side hypothesis on this exact target.** A filter that
instead *preserves or favours* fresh breakout moves -- rather than gating on volatility magnitude
or on agreement with a slower trend -- is the remaining unexplored shape in this family, but there
is no obvious mechanism left in the codebase (per this slice's own scoping paragraph: no genuine
higher timeframe exists beyond `240` in `data_contract`'s cache, and both the magnitude and
direction axes readily available from `strategy.add_indicators`/`donchian.py` are now exhausted).
A different lever entirely -- exit-side, position-sizing, or a genuinely new data source -- is
more likely to be productive than a third variation on "filter the entry mask." This is reported
as a scoping observation, not a new hypothesis; the ticket that commissioned this slice asked for
one pre-registered test, not a further search.

**What is reusable regardless of this outcome:**
`scripts/f006_entry_trend_confirm_experiment.py`'s pattern (filtered + unfiltered arm from the
same call, harness control against `f006_notrail_monthly`, and the `promotion_pass_genuine` /
`n_months_flipped_to_zero_trade` columns that operationalise the `n_trades > 0` guard as data
rather than prose) is reusable by any future entry-filter slice on this sample without
modification. `tests/test_entry_trend_confirm.py`'s causality and flat-signal checks are the
load-bearing checks for this slice's one piece of new logic; no engine, strategy, or Donchian
module change was needed.

## Tests

`tests/test_entry_trend_confirm.py` (6 new tests: causality of `trend_series` at three truncation
points, that `trend_gate` never opens before `ema200` warms up, that `trend_gate` is exactly
`(sig == trend) & (sig != 0)` -- checked both for false positives and false negatives against a
randomised signal -- and that the gate stays `False` when both the signal and the trend are flat)
is the load-bearing check for this slice's one piece of new logic (`trend_series`/`trend_gate` in
the new script) -- no existing module (`backtest_engine.py`, `strategy.py`, `entry_masks.py`,
`donchian.py`, `regularity.py`) was changed. **Sabotage-and-restore performed on the one
non-obvious line** (`trend_gate`'s `& (sig != 0)` clause): removing it did not fail the original
three tests (the flat-vs-flat case they exercised happened not to collide with the random-seed
fixture used), so a fourth test
(`test_trend_gate_false_when_both_signal_and_trend_are_flat`) was added specifically to close that
gap, confirmed to fail under the sabotage and pass after restoring the line -- the same discipline
`F006-hypothesis-donchian.md`'s sabotage table used, applied here to catch a test that looked
sufficient but was not. `tests/test_regularity.py`'s existing tests re-run to confirm no
regression, since no new logic is added to `regularity.py` in this slice.

This worktree's `.venv_test` and `data_cache/*.csv` did not pre-exist and were built/copied before
any test or script ran in this slice (see Run_id) -- not a code change, but recorded here because
it shifted the "before this slice" full-suite baseline from what an empty worktree would show.
Measured directly in this worktree, before and after this slice's one new test file, both with
`.venv_test` and `data_cache` already in place:

| | Before this slice | With this slice |
| --- | --- | --- |
| `pytest tests/` (`.venv_test`, Python 3.9.25, pandas 2.2.3) | 143 passed, 9 skipped | **149 passed, 9 skipped** |

Exactly the 6 new tests, no behaviour change in any existing test. The Python 3.11
`.venv_lorentzian` interpreter was not needed and not used: no Lorentzian dependency in this
sample, matching every prior note in this exact sub-family.
