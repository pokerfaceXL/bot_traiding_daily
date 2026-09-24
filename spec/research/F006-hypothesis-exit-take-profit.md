# F006 — Hypothesis: does an exit-side take-profit (the last untried lever) clear the
# monthly checklist for the three NO_TRAIL lead names? Train 1 only

> Sections "Observation" through "Falsification condition" (including the sample, the exact
> engine change, and the exact take-profit multiple) are written and committed to this file
> BEFORE `backtest_engine.py` is touched, before `scripts/f006_exit_take_profit_experiment.py`
> is written and before any backtest is run, per the same discipline as every prior F006
> hypothesis note. "Run_id", "Result", "Decision" and "Tests" are filled in after the run.
>
> TRAIN-1 ONLY, same window as every F006 slice: `[2024-03-01T00:00:00Z, 2025-03-01T00:00:00Z)`
> plus the protocol's 35-day warm-up buffer from `2024-01-26T00:00:00Z`. Validation 1-4 and the
> Holdout window are not loaded, not sliced and not looked at by any script in this slice.

## Observation

Five independent, mechanistically distinct levers have now been tried against the same target
(`DONCHIAN_55`, `BB_20_25_breakout`, `DONCHIAN_PULLBACK_55` at `NO_TRAIL` — `activate_pct=10.0`,
`max_sl_pct=0.03`, one-shot mask, `cooldown_candles=0`) and `spec/research/F005-validation-
protocol.md` section 7's monthly promotion checklist (full-run max drawdown ≤ 50%, net PnL ≥ 0
in every `is_valid` Train-1 calendar month, net PnL ≥ 0 over the full Train-1 period) has stayed
at 0/30 (or 0/80 on the cross-symbol note's narrower 20-series refinement) throughout: a
volatility-magnitude entry filter (`F006-hypothesis-entry-width-expansion.md`), an own-symbol
trend-agreement entry filter (`F006-hypothesis-entry-trend-confirm.md`), an ATR%-inverse
position-sizing scheme (`F006-hypothesis-position-sizing-vol-inverse.md`), a cross-sectional
signal-agreement gate (`F006-hypothesis-entry-cross-symbol-agreement.md`, refined in
`F006-hypothesis-entry-cross-symbol-refined.md`), and a loss-recency re-entry cooldown
(`F006-hypothesis-loss-recency-cooldown.md`). Every note attributes the 0/30 result to the same
mechanism, most explicitly stated in `F006-hypothesis-notrail-monthly.md`'s Result section: a low
win rate (14-30% per the trailing-boundary note's pooled figures) carried by occasional large
winners produces losing months "spread thin" across the year, not concentrated in one bad
stretch — with an average winner roughly 2.3x the average loser at `NO_TRAIL`
(`F006-hypothesis-trailing-boundary.md`'s pooled table: avg winner $4.773, avg loser -$2.060,
R:R 2.318), a calendar month simply needs to miss one of those rare large winners to go negative,
and at these win rates a run of several such months in any 12-month window is close to
guaranteed.

`F006-hypothesis-trailing-boundary.md`'s own Decision section named the one remaining lever this
whole entry/sizing search has never touched, explicitly out of scope there because it needs an
engine change: *"a fixed take-profit at a multiple of the initial stop distance."* Its Method
section states the exact reason it could not be tested without a code change: *"The engine
supports `take_profit=None` only through `execution.resolve_stop_take_within_bar`'s existing
parameter, which `run_backtest` never populates."* Confirmed directly by reading both modules
before writing this note: `execution.resolve_stop_take_within_bar(direction, bar, stop_loss,
take_profit)` already accepts and correctly resolves a `take_profit` level — with the same
conservative, documented Bar-Magnifier rule as the stop-loss side (`resolve_level_fill`: gap-aware
fill, and when both SL and TP fall inside the same bar's `[low, high]`, SL always wins,
`resolve_stop_take_within_bar`'s own docstring) — but `backtest_engine.run_backtest`'s step 2 calls
it as `execution.resolve_stop_take_within_bar(pos, bar, stop_loss=active_sl, take_profit=None)`,
a hard-coded `None` with no parameter to override it. This is a pure plumbing gap, not a missing
feature in `execution.py`.

Five mechanistically distinct entry/sizing levers have now failed identically. The mechanism
every note names is the same: a few large, unevenly-timed winners are what makes the full-period
PnL positive at all, and every filter/sizing/cooldown lever tried so far can only remove or
resize trades — none of them can change how large a winner is allowed to get. A take-profit is
the first lever in this whole sub-family that acts on that exact axis: it directly caps the size
of a winner, which is the one variable every prior note has held fixed.

## Hypothesis

**H1.** Adding a take-profit at `TP_MULTIPLE = 2.0` times the initial stop distance
(`max_sl_pct * entry_price`, the same `dist` `backtest_engine._calc_initial_sl` already computes)
for `DONCHIAN_55`, `BB_20_25_breakout` and `DONCHIAN_PULLBACK_55` at `NO_TRAIL`
(`activate_pct=10.0`, so trailing never arms and, after this slice's engine change, the
take-profit and the initial stop are the only two levels that can end a trade before
`signal_reverse`/`end_of_data`) causes **at least 1 of the 30** `(name, symbol, interval)` series
to **genuinely** clear the monthly promotion checklist, where the checklist has been 0/30 (or
0/80 on the narrower subsample) in every prior note that measured it.

**The mechanism is stated explicitly before running, per the ticket's requirement, and is
two-sided by construction — this note does not assume which side wins.** Capping every winner at
2x the initial risk converts what is currently a low win rate carried by a few large winners into
a (mechanically, necessarily) higher win rate carried by many more, uniformly smaller winners —
any trade that would have run past `2x` risk under `NO_TRAIL` now exits at exactly `+2x` instead
of whatever larger multiple it would otherwise have reached. This **could help**: if the win rate
rises enough that more calendar months contain at least one net-positive month, and the size of
the now-uniform winner is still large enough relative to the average loser to keep months
individually positive more often, monthly cleanliness could improve even as aggregate PnL falls.
It **could hurt**: the fat-tail winners this note's own Observation section identifies as the
reason full-period PnL is positive at all (`DONCHIAN_PULLBACK_55`/DOGEUSDT/4h's own single
+$279.63 Train-1 run at `NO_TRAIL`, `F006-hypothesis-trailing-boundary.md`'s Result section) would
be capped at a small fraction of their actual size, and if those specific trades are what carries
the months that are currently positive, capping them could turn currently-positive months
negative and make the monthly record *worse*, exactly as `F006-hypothesis-loss-recency-cooldown.md`
found for a different, orthogonal reason (removing exactly the trades that were each month's only
saving win). **This note reports which of the two actually happens; it does not assume either.**

**`TP_MULTIPLE = 2.0`, fixed before running, not swept — the ticket's "ONE concrete hypothesis,"**
same discipline as the loss-recency note's single, pre-justified `LOSS_COOLDOWN=50` value rather
than a grid search. `2.0` is not an arbitrary round number: it is the value closest to this exact
target's own already-measured pooled reward/risk ratio at `NO_TRAIL` — 2.318, from
`F006-hypothesis-trailing-boundary.md`'s pooled `NO_TRAIL` row (avg winner $4.773 / avg loser
-$2.060) — rounded down (conservatively, so the cap binds on the true fat tail rather than
sitting entirely above where most winners already land) to the nearest half-integer multiple.
Reusing this repository's own already-established empirical reward/risk ratio for this exact
target, rather than an untested round number, is the same justification pattern the loss-recency
note used for `LOSS_COOLDOWN=50`. A `TP_MULTIPLE` sweep, if this note's single value shows a real
but insufficient effect in either direction, is named as the natural next step in the Decision
section rather than run here.

## Engine change (additive, `take_profit_multiple: Optional[float] = None`, default preserves
## prior behaviour exactly)

`backtest_engine.run_backtest` gains one new optional parameter, `take_profit_multiple:
Optional[float] = None`, parallel in spirit to the existing `stake_series`/`loss_cooldown_candles`
hooks and defaulting to `None` (off), which preserves every existing call site's behaviour
exactly (verified as a regression test below — this is the load-bearing property, proven, not
just described as additive). Implementation, additive only, no other line of the existing
per-bar loop touched:

* At entry fill (loop step 1, immediately after `initial_sl = _calc_initial_sl(pos, entry_price,
  max_sl_pct)` is computed), one new loop-local variable is set: `take_profit_price =
  (entry_price + take_profit_multiple * abs(entry_price - initial_sl)) if (take_profit_multiple
  is not None and pos == 1) else (entry_price - take_profit_multiple * abs(entry_price -
  initial_sl)) if (take_profit_multiple is not None and pos == -1) else None`. Using
  `abs(entry_price - initial_sl)` (rather than recomputing `entry_price * max_sl_pct` a second
  time) ties the take-profit distance to the *actual* initial stop distance already computed for
  this trade, not a second, independently-computed copy of the same formula — the two can never
  silently drift apart.
* Loop step 2's existing call, `execution.resolve_stop_take_within_bar(pos, bar,
  stop_loss=active_sl, take_profit=None)`, becomes `execution.resolve_stop_take_within_bar(pos,
  bar, stop_loss=active_sl, take_profit=take_profit_price)` — the one-line plumbing change the
  trailing-boundary note's Method section identified as the entire gap. No change to
  `execution.py` — `resolve_stop_take_within_bar` and `resolve_level_fill` already implement the
  full take-profit resolution, gap-handling and SL-wins-on-ambiguity rule; this slice only
  supplies the previously-hard-coded `None` argument.
* The existing `if trigger.kind == TriggerKind.STOP_LOSS:` branch gains a parallel `elif
  trigger.kind == TriggerKind.TAKE_PROFIT:` branch, identical in every respect (close the
  position via `portfolio.close_position`, call `_record_close`, reset `pos`/`trail_active`/
  `active_position_id`) except `exit_reason = "take_profit"` instead of the
  `"trailing_sl"`/`"initial_sl"` disambiguation, and it does **not** set `cooldown_until` (that
  gate is scoped to `initial_sl` exits specifically, per its own docstring, unchanged) but DOES
  participate in the existing `loss_cooldown_candles` check exactly like every other exit path
  (a `take_profit` exit is by construction `net_pnl` ambiguous-but-usually-positive before costs,
  so the existing `if loss_cooldown_candles > 0 and closed_trade.net_pnl < 0:` check, unmodified,
  is the correct and sufficient handling — no new branch needed there).
* Default `take_profit_multiple=None` means `take_profit_price` is always `None`, so
  `resolve_stop_take_within_bar` receives the same `take_profit=None` every existing call site
  already passed implicitly — the new `elif TAKE_PROFIT` branch is dead code whenever the
  parameter is not passed, verified as discriminating check 1 below.

## Sources

This repo's own prior findings and pre-existing, unmodified code only: `F006-hypothesis-
trailing-boundary.md` (the `NO_TRAIL` cell definition, the three names, the pooled reward/risk
ratio 2.318 this note's `TP_MULTIPLE` is derived from, and the Decision section naming this exact
lever and the exact plumbing gap), `F006-hypothesis-notrail-monthly.md` (the 0/30 baseline, the
monthly checklist definition, the spread-thin mechanism), `F006-hypothesis-loss-recency-
cooldown.md` (the most recent falsified lever against this target, its `n_trades_sized > 0`
genuineness-guard pattern reused verbatim below, its own precedent for the "could help or hurt,
report which" framing this note's Hypothesis section follows, its additive-engine-parameter
pattern this note's engine change follows), `F006-hypothesis-position-sizing-vol-inverse.md` (the
`stake_series` additive-hook precedent), `F006-hypothesis-donchian.md` (the win/loss decomposition
motivating why capping winners is a two-sided bet), `spec/research/F005-validation-protocol.md`
section 7 (the monthly promotion criterion, verbatim), `backtest_engine.py` and `execution.py`
(read in full before this note was written — the existing per-bar loop, the existing
`take_profit` parameter already implemented in `execution.resolve_stop_take_within_bar` and
`resolve_level_fill`, and the exact one-line gap in `run_backtest`'s step 2 that this slice
closes).

## Sample (identical set of series to every prior note in this family, not re-derived)

30 series: `DONCHIAN_55`, `BB_20_25_breakout`, `DONCHIAN_PULLBACK_55` × `SOLUSDT`/`ETHUSDT`/
`BTCUSDT`/`XRPUSDT`/`DOGEUSDT` × `240`/`60`. `DONCHIAN_55` and `DONCHIAN_PULLBACK_55` need
`donchian.py` (pure pandas); `BB_20_25_breakout` is a plain `strategy.STRATEGY_CATALOG` entry.
No Lorentzian dependency — single pass on `.venv_test` (Python 3.9) covers all 30 series.

## Method

**Engine parameters: identical to `F006-hypothesis-notrail-monthly.md`'s cell, unchanged, plus
the one new parameter above.** `activate_pct=10.0` (NO_TRAIL), `trail_pct=0.04` (moot, `None`),
`max_sl_pct=0.03`, `atr_multiplier=1.5`, `cooldown_candles=0`, `loss_cooldown_candles=0` (this
note's lever is tested in isolation from the already-falsified loss-recency lever — combining the
two would confound which mechanism produced any effect), `leverage=1.0`,
`commission_rate_bps=10.0`, `half_spread_bps=5.0`, `slippage_bps=2.0`, `initial_equity=500.0`,
`stake=100.0`, one-shot `entry_regime_mask=None` (this lever needs no mask), `now` pinned to
`2025-03-01T00:00:00Z`. Two arms per series: baseline (`take_profit_multiple=None`, must
reproduce `output/f006_notrail_monthly/summary/results.csv` exactly) and gated
(`take_profit_multiple=2.0`). No change to `strategy.py`, `entry_masks.py`, `donchian.py`,
`regularity.py`, `data_contract.py`.

**Aggregation: `regularity.py`, unchanged, reused exactly as `F006-hypothesis-notrail-monthly.md`
built it.** For each series and each arm: `days, months = regularity.compute_regularity(result.
equity_curve)`, filtered to the 12 `train_1` calendar months, `promotion_pass` computed per the
identical three-criterion checklist as that note.

- **Script**: `scripts/f006_exit_take_profit_experiment.py`. Single pass, `.venv_test` only, no
  `--merge` step needed (no Lorentzian dependency in this sample).
- **Data**: identical checksum-verified load (`data_contract.load_dataset`, the `EXPECTED_
  CHECKSUMS` table duplicated from `spec/research/F005-validation-protocol.md` section 6) and
  Train-1 slice (`[2024-01-26T00:00:00Z, 2025-03-01T00:00:00Z)`) as every F006 script. No
  network fetch.
- **Recorded per series per arm**: `symbol`, `interval`, `strategy`, full-run `max_drawdown_pct`,
  `final_equity`, `n_trades`, Train-1 total net PnL, 12 monthly rows, `promotion_pass: bool`,
  `promotion_pass_genuine: bool` (`promotion_pass AND n_trades > 0`, the ticket's explicit
  precondition), `degenerate_pass: bool` (`promotion_pass AND n_trades == 0`), plus the win/loss
  decomposition columns `F006-hypothesis-donchian.md` introduced (win rate, avg winner, avg
  loser, exit-reason mix including the new `take_profit` reason) so the two-sided mechanism in
  the Hypothesis section is measured directly, not inferred from PnL alone.

**Discriminating checks:**

1. **`take_profit_multiple=None` regression on `run_backtest` itself** (`tests/
   test_backtest_engine.py`): calling `run_backtest` with `take_profit_multiple=None` (the new
   default) produces byte-identical `trades`/`equity_curve`/`metrics` to calling it without the
   parameter at all, mirroring the `stake_series=None` and `loss_cooldown_candles=0` regression
   tests the two prior additive-hook notes required.
2. **Hand-built fixture: the take-profit fires at exactly the predicted price and bar, caps a
   winner that would otherwise have run further, and a trade that never reaches the TP level is
   unaffected.** A synthetic frame where a long position's `high` crosses the predicted
   `take_profit_price` on a specific bar (with `initial_sl` and `signal_reverse` both clearly out
   of range on that bar) asserts `exit_reason == "take_profit"`, `exit_price ==
   pytest.approx(take_profit_price)`, and (by comparing against a `take_profit_multiple=None` run
   on the identical frame where the position is instead closed later, at a higher price, by
   `signal_reverse`) that the gated run's `net_pnl` is strictly smaller than the ungated run's —
   the direct proof that capping actually caps.
3. **Gap-and-ambiguity correctness is execution.py's, not re-implemented**: a second fixture
   scenario where both `stop_loss` and `take_profit` fall inside the same bar's `[low, high]`
   asserts the resulting `exit_reason` is `"initial_sl"`, not `"take_profit"` — confirming
   `backtest_engine.py`'s new `elif TAKE_PROFIT` branch correctly defers to `execution.py`'s
   existing SL-wins-on-ambiguity rule rather than accidentally short-circuiting it.
4. **Harness-control**: the `take_profit_multiple=None` arm's 30 rows must match `output/
   f006_notrail_monthly/summary/results.csv`'s stored `train1_net_pnl`/`n_trades` for all 30
   series exactly (0 mismatches expected).
5. **Subset/superset is not assumed either way**: unlike `loss_cooldown_candles` (which can only
   remove trades) or `stake_series` (which never changes trade count), a take-profit can in
   principle *increase* trade count relative to baseline (an early exit frees the position for
   the persistent signal to re-enter sooner, inside the same directional call, before the
   one-shot mask would otherwise have suppressed a would-be re-entry) — this is reported per
   series (`n_trades_gated` vs `n_trades_baseline`, both directions), not assumed monotone in
   either direction the way the two prior additive-hook notes could assume.
6. **Genuineness guard enforced in code**: `promotion_pass_genuine` is a computed column exactly
   as the loss-recency note defined it; any series with `promotion_pass=True` and `n_trades==0`
   is flagged `degenerate_pass=True` and does not count toward H1 surviving.

## Falsification condition (stated before running)

Evaluated on the same 30 `(name, symbol, interval)` series as every prior note in this family,
against `spec/research/F005-validation-protocol.md` section 7's monthly promotion checklist,
applied per series exactly as `F006-hypothesis-notrail-monthly.md` applied it.

**H1 is falsified if zero of the 30 series have `promotion_pass_genuine = True`** under
`take_profit_multiple=2.0` — i.e. no series both clears the checklist AND has `n_trades > 0`
(the ticket's explicit precondition, checked before counting any series, exactly the same guard
every prior note in this sub-family has used).

**H1 survives if at least 1 of the 30 series has `promotion_pass_genuine = True`.** A single
genuinely clearing series is sufficient, and — per the ticket's explicit instruction — is
flagged prominently as this project's first real Validation candidate if it occurs. A series
that clears the checklist but trades only a handful of times over the full Train-1 year is
reported prominently as a thin-sample near-miss (the cross-symbol-refined note's own standard)
and is explicitly NOT treated as a genuine Validation candidate.

**Mandatory reporting regardless of H1's outcome, per the ticket's explicit mechanism
requirement**: which of the two predicted directions actually occurred (win rate up/down, mean
negative months per series up/down, mean Train-1 net PnL per series up/down, all baseline vs.
gated), and the exit-reason mix (what fraction of trades now exit via `take_profit` vs.
`initial_sl`/`signal_reverse`/`end_of_data`) — this is the direct evidence for which side of the
two-sided mechanism won, not inferred from the checklist pass/fail count alone.

**If H1 is falsified, this note states plainly, per the ticket's explicit instruction, that the
whole simple entry/exit/sizing axis is now exhausted for these three names at `NO_TRAIL`** — six
independent mechanisms (2 entry filters, 1 sizing scheme, cross-symbol agreement at 2
name-subsets, loss-recency cooldown, and now a take-profit) all falsified against the same
target and the same criterion — and that the next step is either a materially different signal
source or accepting the limit and returning to a broader basket/catalog search, not a further
lever on this exact axis.

## Run_id

`scripts/f006_exit_take_profit_experiment.py`, single pass, `.venv_test`. To be filled in after
running.

## Result

To be filled in after running.

## Decision

To be filled in after running.

## Tests

To be filled in after running.
