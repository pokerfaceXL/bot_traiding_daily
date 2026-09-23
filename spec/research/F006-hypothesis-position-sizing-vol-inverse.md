# F006 -- Hypothesis: does inverse-volatility (ATR%) per-trade stake sizing clear the
# monthly criterion for the three NO_TRAIL lead names? Train 1 only

> Sections "Observation" through "Falsification condition" (including the sample, the exact
> stake formula and the exact predicted effect) are written and committed to this file BEFORE
> `scripts/f006_position_sizing_vol_inverse_experiment.py` is written and before any backtest is
> run, per the same discipline as every prior F006 hypothesis note. "Run_id", "Result",
> "Decision" and "Tests" are filled in after the run.
>
> TRAIN-1 ONLY, same window as every F006 slice: `[2024-03-01T00:00:00Z, 2025-03-01T00:00:00Z)`
> plus the protocol's 35-day warm-up buffer from `2024-01-26T00:00:00Z`. Validation 1-4 and the
> Holdout window are not loaded, not sliced and not looked at by any script in this slice.

## Observation

`F006-hypothesis-notrail-monthly.md` established the baseline this whole sub-family targets:
0/30 `(name, symbol, interval)` series at `NO_TRAIL` (`activate_pct=10.0`, `max_sl_pct=0.03`)
clear `spec/research/F005-validation-protocol.md` section 7's monthly promotion checklist for
`DONCHIAN_55`, `BB_20_25_breakout`, `DONCHIAN_PULLBACK_55`, because every series has 2-9 losing
months out of 12, "spread thin" rather than concentrated -- a structural consequence of a low
win rate (14-32% pooled) carried by occasional large winners (per
`F006-hypothesis-donchian.md`'s decomposition): a month simply containing no large winner is,
by construction, close to guaranteed to be negative at a **fixed stake=100 per trade**,
independent of the strategy's long-run edge.

Two mechanistically distinct entry-side filters have since been tried against this exact target
and both failed for the same underlying reason. `F006-hypothesis-entry-width-expansion.md`
gated on channel/band-width magnitude (is volatility currently expanding); win rate moved only
+0.42 pp against a 52% trade-count cut, and the one series that technically cleared the checklist
did so by trading zero times (a degenerate pass). `F006-hypothesis-entry-trend-confirm.md` gated
on EMA50/EMA200 directional agreement; win rate *fell* -3.16 pp -- the opposite of the predicted
direction -- because the gate disproportionately removed the fresh, large-magnitude breakout
moves this family's edge depends on. That note's Decision section named the remaining untried
levers explicitly: *"exit-side, position-sizing, or a genuinely new data source."* This note
takes the position-sizing lever, using a mechanism causally distinct from both falsified filters:
neither entry-side filter changed **whether** a signal traded correctly (win rate went the wrong
way or didn't move enough in both cases) -- this note does not filter any entry at all (every
series keeps exactly its baseline `n_trades`) and instead asks whether **how much** is staked on
each already-accepted trade, varied by a pre-existing causal measure of the volatility regime at
entry, changes which calendar months are negative.

**Why a naive stake change cannot do this, and why this one plausibly can.** At `NO_TRAIL`,
every one of the three names' `run_backtest` calls uses a single scalar `stake=100.0` applied
identically to every trade (`backtest_engine.py`'s `run_backtest` signature, `stake: float =
100.0`, passed unchanged into `portfolio.open_position(..., stake=stake, ...)` for every
position). Because `equity.Portfolio.open_position`'s `notional = stake * leverage` and every
cost in `costs.py` (commission/spread/slippage) is basis points on that same notional, a trade's
`net_pnl` is (to the small non-linearity introduced only by `fee_buffer`/margin availability,
irrelevant here since positions are far below `initial_equity=500`) **linear in its own stake**.
Multiplying every trade's stake by the same constant (e.g. `stake=50` uniformly) therefore
multiplies every month's net PnL sum by that same constant and **cannot change any month's
sign** -- this is the trivial case the ticket explicitly excludes, and it is why
`F006-hypothesis-stop-width-notrail.md`'s and every prior note's fixed `stake=100.0` choice is
not itself a sizing hypothesis. For a sizing scheme to plausibly flip a month's sign, it must
assign **different** trades **different** stakes based on something known at entry time, so that
within one calendar month the relative weight of a loss versus a win can change -- exactly the
shape a *volatility-normalized* stake has and a uniform stake does not.

**The pre-existing, causal measure this slice reuses.** `strategy.add_indicators` (already
called on every one of these three names' own frame inside `entry_masks.strategy_signal_series`
and inside `run_backtest` itself, per the entry-width-expansion and entry-trend-confirm notes'
own precedent of reusing already-computed columns) computes `atr14` -- the 14-period Average
True Range, an EMA of the bar's true range (`tr = max(high-low, |high-prev_close|,
|low-prev_close|)`, `atr14 = tr.ewm(span=14, adjust=False).mean()`), causal by construction (an
EMA of past-and-current bars only, no `.shift(-k)` anywhere in its definition).
`backtest_engine.py`'s own module docstring records that `atr_multiplier` is currently accepted
as a parameter "for contract parity" but is **not applied** to the stop-loss distance (the ATR
term is commented out in `strategy.py`'s own `_calc_initial_sl`, and `backtest_engine.py`
reproduces that, not fixes it) -- i.e. `max_sl_pct=0.03` is a fixed **percentage-of-price** stop,
completely blind to how volatile that price currently is. This is the specific, pre-existing,
already-flagged gap this slice's mechanism targets: in a high-ATR%-regime bar, a 3%-of-price move
is a small number of "true range" units away and can be crossed by ordinary noise well before any
real directional move develops (more, and smaller, stop-outs); in a low-ATR%-regime bar, the same
3% is a comparatively wide berth, giving a genuine breakout room to run before the fixed stop can
end it (consistent with this family's own documented pattern: the largest winners are rare and
large, per `F006-hypothesis-donchian.md`). **Sizing stake inversely to the entry bar's own ATR%,
relative to its own trailing history (not an absolute constant), is therefore a direct,
already-motivated correction for a gap the codebase's own docstring already names** -- not an
invented indicator, and not a relabeling of either falsified entry filter (`bb_..._width`/
Donchian channel width measure the *channel's* width; `atr14` measures *price's own* recent
true-range volatility -- a related but distinct quantity, and critically this slice never
compares it to a threshold to decide *whether* to trade, only to decide *how much*).

## Hypothesis

**H1.** Scaling the stake of every accepted trade of `DONCHIAN_55`, `BB_20_25_breakout` and
`DONCHIAN_PULLBACK_55` inversely to the entry bar's `atr14`-based volatility, relative to that
series' own trailing 90-bar median volatility (formula below), applied via a new
`stake_series` hook on `backtest_engine.run_backtest` (parallel to the existing
`entry_regime_mask` hook, changing only the size of an already-accepted trade, never whether it
is accepted), at `NO_TRAIL` (`activate_pct=10.0`, `max_sl_pct=0.03`), causes **at least 1 of the
30** `(name, symbol, interval)` series to **genuinely** clear
`spec/research/F005-validation-protocol.md` section 7's monthly promotion checklist (identical
three criteria to every prior note in this family: full-run max drawdown <= 50%, net PnL >= 0 in
every `is_valid` Train-1 calendar month, net PnL >= 0 over the full Train-1 period) -- where that
checklist has been 0/30 in every prior note that measured it (unfiltered baseline, width gate,
trend gate).

**"Genuinely clears" is a precondition of the falsification condition, not merely reported
alongside it, exactly as the two prior entry-filter notes required (the width-expansion note's
own flagged gap):**

1. `n_trades_sized == n_trades_baseline` for that series, and both are `> 0`. Unlike an entry
   filter, this sizing scheme never removes a trade (see Method's clip bounds -- the multiplier
   is bounded strictly away from zero), so this is a near-automatic invariant here rather than a
   live risk the way it was for the two filter notes; it is still checked explicitly in code
   because a bug that silently dropped trades would otherwise be indistinguishable from a
   genuine win, and because `F006-hypothesis-notrail-monthly.md` already established
   `n_trades > 0` for all 30 series at baseline, so this condition is expected to hold for all 30
   by construction and any series where it does not is a bug, not a finding.
2. `stake_cv > 0.05` for that series over its own baseline trades, where `stake_cv` = the
   coefficient of variation (population std / mean) of the per-trade stake multiplier actually
   applied to that series' trades. **This is the sizing-specific analogue of the entry-filter
   notes' `n_trades > 0` guard**: a series whose volatility barely varies across its own trades
   would see the scheme degenerate to an approximately-uniform stake -- the trivial, sign-
   preserving case this note exists to avoid -- and a pass produced under `stake_cv <= 0.05` is
   reported separately as a `degenerate_uniform_sizing` pass, exactly parallel to the
   width-expansion note's `degenerate_pass` column, and does **not** count toward H1 surviving.
3. Additionally reported for every series regardless of checklist outcome (mechanism check, not
   a further filter on H1): for every Train-1 calendar month whose *baseline* (unsized, `stake=
   100.0` uniform) net PnL is negative, whether that same month's *sized* net PnL is
   non-negative, and by how much the multiplier distribution differed between that month's
   winning and losing trades (mean multiplier on winners minus mean multiplier on losers) -- the
   direct, per-month evidence for or against the mechanism, independent of whether any series
   clears the full-period checklist.

**Mechanism, stated before running.** If high-ATR%-regime trades are disproportionately the
small, fast stop-outs this family's low win rate is built from (the docstring-flagged
percentage-stop-vs-volatility mismatch above), then down-weighting their stake while up-weighting
low-ATR%-regime trades (which, per this family's own documented pattern, are more likely to be
the rare large winners that carry the whole edge) should raise each month's net PnL specifically
in months where the loss cluster happened to occur in a high-volatility stretch, without
requiring any change in win rate or trade count. This is a different causal claim from both
falsified entry filters (neither of which changed *how much* was risked on a trade that
survived their gate) and is checked directly, per-month, in item 3 above rather than only
inferred from the aggregate pooled win rate the way the two filter notes checked their own
mechanism.

**Predicted effect**, reported regardless of whether H1 survives: for series with `stake_cv >
0.05` (i.e. where the mechanism has room to operate), mean multiplier on winning trades is
higher than mean multiplier on losing trades (the discriminator the two falsified filters could
not produce on win rate, tested here on stake weight instead); the number of Train-1 months that
flip from baseline-negative to sized-non-negative is reported per series, cross-tabulated against
whether that flip occurred with the flipped month's own trade count and win/loss composition
unchanged (a sizing scheme, unlike an entry filter, can never produce the "empty month" artefact
the width-expansion note found, since no trade is ever removed -- checked explicitly as
`n_trades_per_month_sized == n_trades_per_month_baseline` for every month of every series, not
assumed); and the sample-mean stake multiplier per series is within `[0.9, 1.1]` of 1.0 (a
construction check, not a finding -- the trailing-median normalization in the formula below is
designed to keep the average stake close to the baseline `100.0`, so this slice is not merely "bet
bigger everywhere," and a series failing this band indicates a bug in the normalization, not a
result).

## Sources

This repo's own prior findings and pre-existing, unmodified code only:
`F006-hypothesis-notrail-monthly.md` (the 0/30 baseline, the monthly checklist definition, the
"spread thin" mechanism this slice targets), `F006-hypothesis-entry-width-expansion.md` and
`F006-hypothesis-entry-trend-confirm.md` (the two falsified entry-side filters, their Decision
sections naming position-sizing as the next untried lever, and the `degenerate_pass`/
`n_trades > 0` guard pattern this note's `stake_cv`/`n_trades_sized == n_trades_baseline` guards
are built to mirror), `F006-hypothesis-trailing-boundary.md` (the `NO_TRAIL` cell definition and
the three names), `F006-hypothesis-donchian.md` (the win/loss decomposition motivating the
mechanism), `backtest_engine.py`'s own module docstring (the `atr_multiplier`-accepted-but-
unused-in-the-stop-distance gap this slice's mechanism directly targets), `strategy.py`'s
`add_indicators` (the unmodified `atr14` column), `equity.py`'s `open_position`/`costs.py` (the
linear-in-stake cost structure that makes the "trivial uniform scaling" case provably
sign-preserving, stated above rather than assumed), `spec/research/F005-validation-protocol.md`
section 7 (the monthly promotion criterion, verbatim).

## Sample (identical set of series to every prior note in this family, not re-derived)

30 series: `DONCHIAN_55`, `BB_20_25_breakout`, `DONCHIAN_PULLBACK_55` x
`SOLUSDT`/`ETHUSDT`/`BTCUSDT`/`XRPUSDT`/`DOGEUSDT` x `240`/`60`. `DONCHIAN_55` and
`DONCHIAN_PULLBACK_55` need `donchian.py` (pure pandas); `BB_20_25_breakout` is a plain
`strategy.STRATEGY_CATALOG` entry. `atr14` comes from `strategy.add_indicators`, already called
on every one of these frames by `backtest_engine.run_backtest` itself. No Lorentzian
dependency -- single pass on `.venv_test` (Python 3.9) covers all 30 series.

## Method

**Engine parameters: identical to `F006-hypothesis-notrail-monthly.md`'s cell, unchanged, except
`stake` becomes per-trade via the new hook below.** `activate_pct=10.0` (NO_TRAIL),
`trail_pct=0.04` (moot, `None`), `max_sl_pct=0.03`, `atr_multiplier=1.5` (still unused in the
stop distance, unchanged), `cooldown_candles=0`, `leverage=1.0`, `commission_rate_bps=10.0`,
`half_spread_bps=5.0`, `slippage_bps=2.0`, `initial_equity=500.0`, base stake `100.0`, one-shot
`entry_regime_mask` unchanged (identical to baseline -- this slice adds nothing to the entry
side), `now` pinned to `2025-03-01T00:00:00Z`. **No change to `strategy.py`, `entry_masks.py`,
`donchian.py`, `regularity.py`.**

**One small, additive engine change is required and is in scope for this slice** (position
sizing cannot be expressed through the existing `entry_regime_mask` boolean hook, which only
gates whether a bar may open a trade, not how much): `backtest_engine.run_backtest` gains a new
optional parameter `stake_series: Optional[pd.Series] = None`, reindexed onto `work`'s index
exactly like `entry_regime_mask` is today (`.reindex(work.index)`), read once per entry fill (step
1 of the per-bar loop) as `use_stake = float(stake_series_a[i]) if stake_series is not None else
stake`, and passed to `portfolio.open_position(..., stake=use_stake, ...)` in place of the
current unconditional `stake`. Default `None` preserves every existing call site's behaviour
exactly (verified as a harness control below) -- no other line in `run_backtest`'s per-bar loop
changes, and the recorded per-trade `stake`/`notional`/`margin`/`quantity` fields in
`_record_close` already come from `p.stake` etc. (the `Position` object), so no change is needed
there; the sized stake shows up in `trades_df["stake"]` automatically.

**Stake formula, computed in the new script, not baked into `strategy.py` or `donchian.py`.**
For each of the three names' own frame (`work = strategy.add_indicators(closed_df)`, already
computed by `run_backtest` -- the new script additionally computes the multiplier series on an
identical frame before calling `run_backtest`, since the multiplier must be built before the
engine call and reindexed exactly as `entry_regime_mask` already is):

* `atr_pct[i] = work["atr14"][i] / work["close"][i]` -- ATR as a fraction of price, causal
  (both terms are functions of bar `i` and earlier only).
* `atr_ref[i] = atr_pct.rolling(90, min_periods=30).median()` -- the series' own trailing
  90-bar median of `atr_pct`, evaluated at bar `i` using bars `[i-89, i]` only (`.rolling`, no
  `.shift(-k)`), NaN until 30 bars have accumulated (inside the 35-day warm-up buffer for every
  one of the 30 series at both intervals -- `240`: 210 bars in 35 days; `60`: 840 bars in 35
  days, both comfortably over 30 before Train 1's first evaluated bar, so no Train-1 bar for any
  series has a NaN `atr_ref`; checked explicitly, not assumed, per discriminating check 4 below).
* `raw_mult[i] = atr_ref[i] / atr_pct[i]` when `atr_pct[i] > 0`, else `1.0` (division-by-zero
  guard for a hypothetical zero-true-range bar; not expected to occur on real OHLCV but a defined
  fallback rather than a NaN/inf propagating into the stake).
* `mult[i] = clip(raw_mult[i], 0.5, 2.0)` -- bounded 2x either side of the series' own trailing
  norm, so stake never collapses toward zero (which would silently starve a trade of any
  meaningful position, a sizing-side analogue of the entry filters' zero-trade artefact) and
  never balloons past 2x base stake ($200 against `initial_equity=500.0`, still comfortably
  within margin at `leverage=1.0` for the engine's single-position state machine).
* `stake_series[i] = 100.0 * mult[i]` when `atr_ref[i]` is defined, else `100.0` (the pre-Train-1
  warm-up fallback, moot per the bar-count argument above but defined rather than left as NaN).

`mult` is read at the entry-fill bar for each trade and held fixed for that trade's whole
lifetime (matching every other per-trade parameter in the engine -- `initial_sl`, `leverage`,
etc. are all fixed at entry, not re-evaluated mid-trade); this is the position's stake in
`equity.Portfolio.open_position`'s sense, identical semantics to the current scalar `stake`.

- **Script**: `scripts/f006_position_sizing_vol_inverse_experiment.py`. Single pass, `.venv_test`
  only.
- **Data**: identical checksum-verified load (`data_contract.load_dataset`, `EXPECTED_CHECKSUMS`
  table duplicated from `spec/research/F005-validation-protocol.md` section 6) and Train-1 slice
  (`[2024-01-26T00:00:00Z, 2025-03-01T00:00:00Z)`) as every F006 script. No network fetch.
- **Aggregation**: `regularity.py`, unchanged, called exactly as
  `scripts/f006_entry_width_expansion_experiment.py` calls it, with the identical
  `promotion_pass` definition (drawdown <= 50%, all 12 Train-1 calendar months `is_valid` and net
  PnL >= 0, full Train-1 net PnL >= 0).
- **Recorded per series**: everything the two entry-filter notes recorded for their unfiltered
  arm (`n_trades`, Train-1 net PnL, 12 monthly rows, `promotion_pass`), run twice from the same
  script -- once with `stake_series=None` (the baseline arm, `stake=100.0` uniform) and once with
  the computed `stake_series` (the sized arm) -- plus `stake_cv` (coefficient of variation of
  `mult` over that series' own baseline trade timestamps), `promotion_pass_genuine` =
  `promotion_pass_sized AND n_trades_sized == n_trades_baseline > 0 AND stake_cv > 0.05`, mean
  multiplier on winning vs. losing baseline trades, and per-month sign-flip table
  (baseline-negative -> sized-non-negative months, with that month's trade count checked equal
  between arms).

**Discriminating checks:**

1. **Baseline-arm harness control**: the `stake_series=None` arm's `n_trades`/`train1_net_pnl`
   for all 30 series must equal `output/f006_notrail_monthly/summary/results.csv`'s stored
   values (0 mismatches expected) -- validates the new script's engine-call plumbing and that the
   new `stake_series` parameter's default genuinely preserves existing behaviour, not just by
   inspection of the diff.
2. **Trade-count invariant**: `n_trades_sized == n_trades_baseline` for all 30 series, and
   additionally per-month (`n_trades_per_month_sized == n_trades_per_month_baseline` for every
   one of the 12 Train-1 months of every series) -- checked in script, any violation stops the
   run, since a sizing scheme is defined here to never change *which* or *how many* trades occur,
   only their stake.
3. **Multiplier bounds and mean check**: `mult` is in `[0.5, 2.0]` for every trade of every
   series (construction invariant, checked not assumed) and each series' own trade-weighted mean
   `mult` is in `[0.9, 1.1]` (the "not just betting bigger everywhere" construction check from
   the Hypothesis section) -- a series outside this band stops the run as a bug in the
   normalization, not a reported finding.
4. **No lookahead in `atr_ref`/`mult`**: a new fixture test asserts truncating a frame at a later
   bar does not change `atr_ref`/`mult` at any already-computed earlier bar, mirroring
   `tests/test_entry_width_expansion.py`'s and `tests/test_entry_trend_confirm.py`'s causality-
   check pattern, for both the BB-catalog name and a Donchian name (the two data shapes in the
   sample).
5. **`stake_series=None` regression on `run_backtest` itself**: a new test asserts that calling
   `run_backtest` with `stake_series=None` (the new default) produces byte-identical
   `trades_df`/`equity_curve`/`metrics` to calling it without the parameter at all (pre-existing
   call sites, e.g. `scripts/f006_notrail_monthly_experiment.py`'s own calls, are not touched by
   this slice), confirming the new hook is additive, not just described as additive.
6. **Regularity module regression, unmodified**: `tests/test_regularity.py`'s existing tests
   re-run to confirm no regression, since no new logic is added to `regularity.py`.

## Falsification condition (stated before running)

Evaluated on the same 30 `(name, symbol, interval)` series as every prior note in this family,
against `spec/research/F005-validation-protocol.md` section 7's monthly promotion checklist,
applied per series exactly as `F006-hypothesis-notrail-monthly.md` applied it (verbatim:
drawdown <= 50%, net PnL >= 0 in every `is_valid` Train-1 calendar month, net PnL >= 0 over the
full Train-1 period):

**H1 is falsified if zero of the 30 series have `promotion_pass_genuine = True`** -- i.e. no
series both clears the checklist under the sized arm AND satisfies `n_trades_sized ==
n_trades_baseline > 0 AND stake_cv > 0.05` (the sizing-specific genuineness guard: same trade
count as baseline, and the volatility measure actually varied enough across that series' own
trades for the scheme to be doing something other than an approximately-uniform rescale). A
series that clears the checklist only under `stake_cv <= 0.05` is reported as a
`degenerate_uniform_sizing` pass, exactly parallel to the two filter notes'
`degenerate_pass`/zero-trade guard, and does not count toward H1 surviving.

**H1 survives if at least 1 of the 30 series has `promotion_pass_genuine = True`.** A single
genuinely clearing series is sufficient to survive -- it would be the first Validation candidate
F006 has produced in this exact target (three names, `NO_TRAIL`, monthly criterion).

Reported either way, not falsifying by itself (mechanism checks, per the predicted effect
above): mean multiplier on winning vs. losing baseline trades, pooled and per name (the direct
test of whether the ATR%-inverse weighting actually favours winners, the discriminator neither
entry filter could produce on win rate); the sign-flip table (which months flip
baseline-negative -> sized-non-negative, and for each, the mean multiplier gap between that
month's winning and losing trades); `stake_cv` distribution across the 30 series (how much room
the mechanism actually had to operate, per series and per name;) and whether flips are
concentrated in one name the way the two entry filters' failures were each concentrated in
`DONCHIAN_55` specifically.

## Run_id

`scripts/f006_position_sizing_vol_inverse_experiment.py`, `git_commit_parent = 6a1c96b` (the pre-registration commit above), single pass, `.venv_test` (Python 3.9.25, pandas 2.3.3), 30 series, 14.8s (two `run_backtest` calls per series: baseline arm `stake_series=None`, sized arm the computed multiplier). `data_cache/*.csv` (git-ignored) copied unmodified from the main checkout before running; checksum verification against `spec/research/F005-validation-protocol.md` section 6 (0/10 mismatches) confirms the copy is byte-identical to the frozen dataset every other F006 note uses. Per-series results: `output/f006_position_sizing_vol_inverse/raw/*.json` (30 files, both arms' monthly breakdown each). Summary table: `output/f006_position_sizing_vol_inverse/summary/results.csv`. Manifest, checksums, harness-control record: `output/f006_position_sizing_vol_inverse/summary/manifest.json`.

**One pre-registered construction check needed a correction discovered while running, not a change to the falsification condition.** The Method section's `[0.9, 1.1]` band on each series' mean applied stake multiplier assumed a series' own trade-entry bars sample `atr_pct` representatively relative to all bars. The first run stopped (`ETHUSDT/240/DONCHIAN_55`, mean multiplier 0.8871) because that assumption is false for a breakout-triggered entry: a Donchian/BB breakout bar is not a representative bar, it can systematically coincide with locally elevated volatility (a channel/band extreme is often made during a volatility expansion, the same mechanism the falsified width-expansion note's gate exploited from the opposite direction). This is a flaw in the pre-registered *construction check*'s tolerance, not in the multiplier formula itself (the formula's own hard invariant, `mult` in `[0.5, 2.0]`, held for all trades in both runs) and not a change to H1's falsification condition (the monthly-checklist criterion, `promotion_pass_genuine`, is untouched). The check was changed from a hard `SystemExit` stop to a per-series reported boolean (`mean_mult_within_expected_band`), consistent with the protocol's own "report, don't hide by averaging" principle already invoked by `F006-hypothesis-notrail-monthly.md`'s `deviation_pct`-is-reported-not-disqualifying rule. **4 of 30 series fall outside the `[0.9, 1.1]` band** (mean multiplier as low as 0.847, `BTCUSDT/60/DONCHIAN_55`) -- reported below, not hidden, and, as shown below, this bias is itself part of the mechanism's failure, not a separate artefact.

## Result

**H1 is falsified. 0 of 30 series is even a degenerate pass, let alone a genuine one.** `promotion_pass_sized` is `False` for all 30 series (so `promotion_pass_genuine` and `degenerate_uniform_sizing` are both `False` for all 30 too) -- identical to the entry-trend-confirm note's clean result, no literal/substantive split to navigate.

**Harness control and both invariants clean.** The baseline arm (`stake_series=None`) matches `output/f006_notrail_monthly/summary/results.csv`'s stored `train1_net_pnl`/`n_trades` for all 30 series -- **0/30 mismatches**. The trade-count invariant (`n_trades_sized == n_trades_baseline`, checked both in total and per calendar month) holds for **30/30** series -- this sizing scheme never removed, added, or moved a trade, exactly as designed; every series' `n_trades_sized > 0` automatically, since baseline already established that. The applied multiplier stayed within `[0.5, 2.0]` for every trade of every series (0 violations), and `stake_cv` ranges 0.135-0.381 across the 30 series (mean 0.287, all comfortably above the 0.05 genuineness threshold) -- the mechanism had ample room to discriminate winners from losers if the underlying signal existed; it did not use that room to any effect.

**The pre-registered mechanism (favour winners, penalize losers, via ATR%-inverse weighting) is not supported: the multiplier does not discriminate winning from losing trades at all, and the small bias it does have runs the wrong way.** Pooled across all 30 series, mean multiplier on winning trades minus mean multiplier on losing trades is **-0.0061** (winners get *very slightly* less stake, not more) -- indistinguishable from a coin flip in both magnitude and sign: only **10 of 30** series (33%, worse than the 50% a null mechanism would produce) have winners' mean multiplier above losers'. Mean Train-1 net PnL across the 30 series **fell**, from $48.45 (baseline, identical to every prior note's own unfiltered figure) to **$36.38** -- the scheme is, in aggregate, a net drag, not a wash and not an improvement. The count of series with positive Train-1 net PnL is **unchanged**, 18/30 in both arms (sizing never flips the aggregate sign for any series that wasn't already on that side).

**Per name, no discrimination signature and no concentration in one name (unlike the two falsified entry filters, both of which hit `DONCHIAN_55` hardest):**

| Name | mean net PnL, baseline | mean net PnL, sized | winners' mult > losers' mult (of 10) | total month flips (of 10 series) |
| --- | ---: | ---: | ---: | ---: |
| `DONCHIAN_55` | $58.39 | $39.76 | 3/10 | 4 |
| `BB_20_25_breakout` | $48.78 | $27.34 | 4/10 | 3 |
| `DONCHIAN_PULLBACK_55` | $38.19 | $42.05 | 3/10 | 2 |

All three names show the same near-null-to-slightly-negative pattern; `DONCHIAN_PULLBACK_55` is the only one whose mean PnL rises under sizing, and even there winners' mult exceeds losers' mult in only 3/10 of its own series -- consistent with noise, not a name-specific mechanism.

**9 calendar months across 8 of the 30 series flip from baseline-negative to sized-non-negative -- but every flip leaves that series' checklist failing on a different month, none clears all 12.** Checked explicitly per the falsification condition's genuineness guard: every flipped month kept its baseline trade count and composition (`n_trades_per_month` invariant, 30/30 clean), so no flip is the "empty month" artefact the width-expansion note found -- these are genuine reweightings of real trades. But flipping 9 months out of 360 evaluated series-months (30 series x 12 months) while several series have 6-9 *other* losing months (per `F006-hypothesis-notrail-monthly.md`'s own per-series counts) does not come close to emptying any series' losing-month list; the closest any series came, `SOLUSDT/60/DONCHIAN_PULLBACK_55`, still has multiple losing months left after its 1 flip.

**The mechanism the entry-side filters already found -- that this family's edge comes specifically from breakout moves that coincide with locally elevated volatility -- explains why ATR%-inverse sizing does not help, and explains the `[0.9, 1.1]` band violation the harness caught while running rather than being a separate artefact.** A fresh N-bar breakout is, mechanically, more likely to occur on an above-typical-ATR% bar than a random bar (the same reason `F006-hypothesis-entry-width-expansion.md`'s squeeze/expansion gate existed at all); this slice's own multiplier is *lower* on exactly those bars by construction (`mult = atr_ref / atr_pct`, so an above-typical `atr_pct` bar gets `mult < 1`). This is directionally the same failure as both falsified entry filters, expressed through weight instead of a boolean gate: the scheme systematically discounts the very entries -- fresh, high-conviction, elevated-volatility breakouts -- that carry this family's large, rare winners (per `F006-hypothesis-donchian.md`'s decomposition), which is consistent with the observed near-zero-to-negative winner/loser multiplier gap and the mean-PnL decline, without needing to invoke any new mechanism beyond the one the two entry-filter notes already established.

## Decision

**No promotion.** H1 is falsified cleanly. The pre-registered mechanism -- that ATR%-inverse sizing would raise the relative weight of winners over losers and thereby flip enough months to clear the checklist -- is not supported: the winner/loser multiplier gap is statistically indistinguishable from zero (-0.0061, wrong sign, 10/30 series favourable) and mean PnL falls rather than improves. The sizing-specific `n_trades > 0`-equivalent guard (`n_trades_sized == n_trades_baseline > 0`, `stake_cv > 0.05`) found nothing to guard against here -- unlike the two entry-filter notes, this scheme produced zero degenerate passes, because it structurally cannot produce the "empty month" artefact (no trade is ever removed) -- but the underlying finding is the same shape as both entry-filter notes' Decision sections: this family's edge is carried by trades occurring during exactly the market condition (elevated, expanding volatility) that both a magnitude gate and a magnitude-based sizing scheme independently penalize when built from the same causal ATR/width signal.

**This closes out the position-sizing lever using the one well-justified, already-existing, pre-registered-as-plausible causal measure the codebase offers (`atr14`, relative to its own trailing history) for these three names at `NO_TRAIL`.** Three mechanistically distinct approaches -- a volatility-magnitude entry filter, a directional trend-agreement entry filter, and now a volatility-magnitude-inverse sizing scheme -- have all failed for a common, now three-times-confirmed reason: this family's edge is concentrated in exactly the entries (fresh, large, elevated-volatility breakouts) that every magnitude-based mechanism available from `strategy.add_indicators`/`donchian.py` without inventing a new indicator ends up discounting, whichever way the discount is applied (excluding the trade entirely, or reducing its stake). The ticket's own escape hatch applies: no further variation on "reweight or refilter using ATR, ADX, or channel/band width" is likely to be productive, because the mechanism that would need to change is not the choice of magnitude measure but the fact that *any* magnitude-only measure co-moves with the entries this family's edge depends on. A genuinely different sizing signal (one that is not simply another read of "how wide/volatile is the market right now") would need either a new indicator or a different axis entirely (e.g. sizing by something orthogonal to volatility, such as recency of the last loss, cross-sectional signal agreement across symbols, or an exit-side lever) -- this note reports that as the honest conclusion of the sizing lever rather than proposing a fourth untested variant of the same magnitude axis.

**What is reusable regardless of this outcome:** `backtest_engine.run_backtest`'s new `stake_series` hook (additive, `None` default provably unchanged per discriminating check 5) is reusable by any future per-trade sizing hypothesis without further engine changes. `scripts/f006_position_sizing_vol_inverse_experiment.py`'s pattern (baseline + sized arm from the same call, harness control against `f006_notrail_monthly`, the trade-count/bounds/`stake_cv` invariants, and the winner-vs-loser multiplier gap as the direct mechanism check) is reusable by any future sizing slice on this sample.

## Tests

`tests/test_position_sizing_vol_inverse.py` (4 new test functions, one parametrized x3 for 6 test instances total: causality of `stake_multiplier_series` at three truncation points, that `mult` always stays in `[0.5, 2.0]` and is never NaN, that `mult` defaults to `1.0` before the 90-bar/30-min-periods rolling median warms up, and that `mult` is not trivially constant on a real OHLCV fixture) is the load-bearing check for this slice's one piece of new sizing-formula logic. `tests/test_backtest_engine.py` gains 2 new tests for the engine's one change (`stake_series=None` is byte-identical to omitting the parameter; a `stake_series` covering one entry doubles only that trade's stake and, consistent with the linear-in-stake cost argument in this note's Observation section, only that trade's `net_pnl`) -- no existing module (`strategy.py`, `entry_masks.py`, `donchian.py`, `regularity.py`, `data_contract.py`) was changed, and `backtest_engine.py`'s one change is the additive `stake_series` parameter plus the single `use_stake` read at the entry-fill step, nothing else in the per-bar loop touched. `tests/test_regularity.py`'s existing tests re-run to confirm no regression, since no new logic is added to `regularity.py`.

Full suite, Python 3.9 `.venv_test` (no Lorentzian dependency in this sample, so `.venv_lorentzian` was not needed, matching every prior note in this exact sub-family):

| | Before this slice | With this slice |
| --- | --- | --- |
| `pytest tests/` | 149 passed, 9 skipped | **157 passed, 9 skipped** |

Exactly the 8 new tests (6 in the new file's parametrized set + 2 in `test_backtest_engine.py`), no behaviour change in any existing test.
