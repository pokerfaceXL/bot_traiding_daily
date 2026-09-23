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

(filled in after the run)

## Result

(filled in after the run)

## Decision

(filled in after the run)

## Tests

(filled in after the run)
