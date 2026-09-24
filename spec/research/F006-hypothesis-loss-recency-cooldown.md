# F006 -- Hypothesis: does a loss-conditioned re-entry cooldown (gate on recency
# of the SAME series' last losing trade, not a blanket post-exit delay) clear the
# monthly criterion for the three NO_TRAIL lead names? Train 1 only

> Sections "Observation" through "Falsification condition" (including the sample, the exact
> gate formula, the exact `loss_cooldown_candles` value, and the exact predicted effect) are
> written and committed to this file BEFORE `scripts/f006_loss_recency_cooldown_experiment.py`
> is written, before `backtest_engine.py`'s one additive change is made, and before any backtest
> is run, per the same discipline as every prior F006 hypothesis note. "Run_id", "Result",
> "Decision" and "Tests" are filled in after the run.
>
> TRAIN-1 ONLY, same window as every F006 slice: `[2024-03-01T00:00:00Z, 2025-03-01T00:00:00Z)`
> plus the protocol's 35-day warm-up buffer from `2024-01-26T00:00:00Z`. Validation 1-4 and the
> Holdout window are not loaded, not sliced and not looked at by any script in this slice.

## Observation

Four mechanistically distinct levers have now been tried against this exact target (`DONCHIAN_55`,
`BB_20_25_breakout`, `DONCHIAN_PULLBACK_55` at `NO_TRAIL`, `spec/research/F005-validation-
protocol.md` section 7's monthly promotion checklist, established as 0/30 by
`F006-hypothesis-notrail-monthly.md`): a volatility-magnitude entry filter
(`F006-hypothesis-entry-width-expansion.md`), an own-symbol trend-agreement entry filter
(`F006-hypothesis-entry-trend-confirm.md`), an ATR%-inverse position-sizing scheme
(`F006-hypothesis-position-sizing-vol-inverse.md`), and a cross-sectional signal-agreement gate
(`F006-hypothesis-entry-cross-symbol-agreement.md`, refined in
`F006-hypothesis-entry-cross-symbol-refined.md`). All four are falsified against the checklist
(0/30, 0/30, 0/30, 0/30+0/80). The cross-symbol note's refinement produced this sub-family's
closest approach to date -- three cells with only 2 negative months out of 12, all on 2-5 total
trades -- but explicitly flagged those as thin-sample near-misses, not robust selections, and its
Decision section named the two remaining untried, volatility-orthogonal levers verbatim:
*"recency of the last loss"* and *"an exit-side lever."* This note takes the first.

**Distinct from the existing `cooldown_candles` engine parameter, on two separate axes, stated
explicitly per the ticket's requirement.** `F006-hypothesis-cooldown.md` already tested
`cooldown_candles` at `leverage=1` on a *different* catalog (10 pre-`NO_TRAIL` strategies + 2
Lorentzian entries, not `DONCHIAN_55`/`BB_20_25_breakout`/`DONCHIAN_PULLBACK_55` at `NO_TRAIL`)
and found a real but non-mechanistic effect (mean net PnL improved monotonically 0->50, but
per-trade expectancy at 4h -- where the effect was largest -- was flat, meaning cooldown was
removing *average* trades of a negative-expectancy process, not genuinely bad ones; that note's
own Decision section: "not the fix -- it is a mitigation"). `cooldown_candles` is unconditional
on win/loss (`backtest_engine.py`'s existing per-bar loop sets `cooldown_until` after **every**
`exit_reason == "initial_sl"` exit, win or loss -- though in practice an `initial_sl` exit is a
loss by construction of the SL formula, so this is a narrower distinction than the second one
below) and, more importantly, **it only ever fires on `initial_sl` exits** -- the module
docstring for that note states directly: "a large part of each strategy's trade flow is
untouched by it," since `trailing_sl`, `signal_reverse` and `end_of_data` exits never set
`cooldown_until` at all. This note's lever is **conditioned specifically on whether the closed
trade's realized `net_pnl` was negative**, evaluated for **every** exit reason (`initial_sl`,
`trailing_sl`, `signal_reverse`, `end_of_data`) -- a `trailing_sl` exit that locks in a small net
loss after costs, or a `signal_reverse` exit that closes at a loss, both start this note's
cooldown; neither starts `cooldown_candles`'s. This is the ticket's own required distinction
("condition specifically on loss vs win, not blanket cooldown") made concrete in the engine, not
only in prose.

**Mechanism, distinct from the four falsified magnitude/agreement levers.** None of the four
prior mechanisms used any information about this series' own **trade history** -- they all read
either the traded symbol's own current-bar magnitude (width, ATR%) or the rest of the basket's
current directional lean, never anything about how that specific series has performed recently.
`F006-hypothesis-donchian.md`'s own decomposition established this family's edge is a low win
rate carried by rare large winners; a natural, orthogonal hypothesis about *why* months are
uniformly spread-thin-negative rather than concentrated is that losing trades cluster in time
(a genuine losing streak, e.g. a choppy/ranging regime the breakout signal keeps false-firing
into) more than a Poisson-random scatter of independent losses would predict, and that pausing
re-entry for a fixed number of bars immediately after a loss lets that regime pass before the
same signal fires again into it -- unlike `cooldown_candles`, which pauses after every `initial_sl`
stop-out regardless of whether the broader pattern is "choppy losing streak" or "isolated stop-out
inside an otherwise clean run," and unlike all three magnitude/agreement gates, which read no
information about the series' own recent trade outcomes at all.

## Hypothesis

**H1.** Gating new entries of `DONCHIAN_55`, `BB_20_25_breakout` and `DONCHIAN_PULLBACK_55` so
that no new entry may open within `LOSS_COOLDOWN = 50` candles of that same series' own last
losing trade's close (`net_pnl < 0` at the close, any exit reason), applied at `NO_TRAIL`
(`activate_pct=10.0`, `max_sl_pct=0.03`), causes **at least 1 of the 30** `(name, symbol,
interval)` series to **genuinely** clear `spec/research/F005-validation-protocol.md` section 7's
monthly promotion checklist (identical three criteria to every prior note in this family:
full-run max drawdown <= 50%, net PnL >= 0 in every `is_valid` Train-1 calendar month, net PnL >=
0 over the full Train-1 period), where that checklist has been 0/30 (or 0/80 on the narrower
20-series refinement) in every prior note that measured it.

**"Genuinely clears" is a precondition of the falsification condition, not merely reported
alongside it -- the recurring guard this ticket explicitly names and requires not to regress:
`n_trades_sized > 0` for that series** (this lever, like `cooldown_candles`, can in principle
starve a series to zero trades if losses recur inside every re-opened cooldown window; unlike the
position-sizing note's scheme, it CAN remove trades, so this guard is a live risk here, not a
near-automatic invariant). A series that clears the checklist only by trading zero times is
reported as `degenerate_pass` (`n_trades_sized == 0`), exactly parallel to every prior filter
note's guard, and does **not** count toward H1 surviving.

**`LOSS_COOLDOWN = 50`, fixed before running, not swept -- the ticket's "ONE concrete
hypothesis," not a parameter search.** `50` is the single best-justified value already
established in this repository for "how many candles is enough to matter for a re-entry pause on
this exact basket": `F006-hypothesis-cooldown.md`'s own sweep (`{0, 5, 10, 20, 50}`) found the
effect on mean net PnL **monotonically increasing** all the way to its largest tested value with
no sign of saturating, and `50` was that sweep's own upper bound and its best-performing cell on
every reported measure (mean net PnL, max drawdown, survival rate) -- reusing it here is not an
arbitrary choice, it is the one magnitude this repository has already shown to matter most for a
re-entry-delay lever on a Train-1, `leverage=1` basket close to this one (a different catalog and
exit config, `NO_TRAIL` vs the trailing-active config that note used, but the same instrument
basket, `leverage=1`, and the same class of lever: a bar-count delay on re-entry). No sweep is run
in this note, consistent with the ticket's instruction and this sub-family's own precedent
(the original cross-symbol-agreement note tested one `MIN_AGREE` value before its own follow-up
swept it) -- a `LOSS_COOLDOWN` sweep, if this note's single value shows a real but insufficient
effect, is named as the natural next step in the Decision section rather than run here.

## Distinguishing genuine selection from starving the sample (the ticket's explicit requirement,
## carried forward unchanged from every prior note in this sub-family)

Reported for every series, not falsifying by itself but load-bearing for whether a checklist pass
(if any) is substantive: pooled and per-name win rate, baseline vs. loss-cooldown-gated; mean
negative months per series, baseline vs. gated; trade count, baseline vs. gated; and an explicit
`degenerate_pass` flag (`n_trades_sized == 0` while `promotion_pass_sized == True`) computed in
code for every series, not merely eyeballed -- exactly the same four reference points (win rate,
neg-months, trade count, degenerate-pass flag) every prior note in this sub-family has reported,
judged against this sub-family's own established reference points: width gate +0.42 pp/-52% trade
cut; trend gate -3.16 pp/-48%; position sizing -0.0061 winner/loser multiplier gap (near-null);
cross-symbol agreement (30-series) +1.84 pp/-43.0%, (20-series, `MIN_AGREE=2`) +2.82 pp/-41.4%.

## Sources

This repo's own prior findings and pre-existing, unmodified code only:
`F006-hypothesis-notrail-monthly.md` (the 0/30 baseline, the monthly checklist definition),
`F006-hypothesis-entry-cross-symbol-refined.md` (the Decision section naming this exact lever,
the three closest-approach thin-sample cells, the reference reporting points),
`F006-hypothesis-position-sizing-vol-inverse.md` (the Decision section independently naming this
same lever, the `stake_series` additive-hook precedent this note's own additive engine change
follows), `F006-hypothesis-cooldown.md` (the existing `cooldown_candles` mechanism, its own
`{0,5,10,20,50}` sweep and the `LOSS_COOLDOWN=50` justification above, its per-trade-expectancy
critique of *why* a naive cooldown does not restore edge -- context this note's own Result section
must engage with, not ignore), `F006-hypothesis-trailing-boundary.md` (the `NO_TRAIL` cell
definition and the three names), `F006-hypothesis-donchian.md` (the win/loss decomposition
motivating the mechanism), `spec/research/F005-validation-protocol.md` section 7 (the monthly
promotion criterion, verbatim), `backtest_engine.py` (the existing per-bar loop and
`cooldown_candles`/`entry_regime_mask`/`stake_series` hooks, read but only the new parameter
below is added), `entry_masks.py`/`donchian.py`/`strategy.py` (the three names' own signal
definitions, unmodified).

## Sample (identical set of series to every prior note in this family, not re-derived)

30 series: `DONCHIAN_55`, `BB_20_25_breakout`, `DONCHIAN_PULLBACK_55` x
`SOLUSDT`/`ETHUSDT`/`BTCUSDT`/`XRPUSDT`/`DOGEUSDT` x `240`/`60`. This is the full 30-series
sample, not the cross-symbol note's narrowed 20-series subsample -- this lever is mechanistically
unrelated to the `DONCHIAN_PULLBACK_55`-specific lag argument that motivated narrowing there (a
loss-recency gate reads that series' own trade history, not a same-bar cross-symbol read, so the
lagged-entry argument does not apply here), so there is no prior basis to exclude
`DONCHIAN_PULLBACK_55` before running. `DONCHIAN_55` and `DONCHIAN_PULLBACK_55` need `donchian.py`
(pure pandas); `BB_20_25_breakout` is a plain `strategy.STRATEGY_CATALOG` entry. No Lorentzian
dependency -- single pass on `.venv_test` (Python 3.9) covers all 30 series.

## Method

**Engine parameters: identical to `F006-hypothesis-notrail-monthly.md`'s cell, unchanged, plus
the one new parameter below.** `activate_pct=10.0` (NO_TRAIL), `trail_pct=0.04` (moot, `None`),
`max_sl_pct=0.03`, `atr_multiplier=1.5`, `cooldown_candles=0` (this note's lever is tested in
isolation from the existing blanket cooldown -- both are additive and could in principle be
combined in a future note, but combining them here would confound which mechanism produced any
effect), `leverage=1.0`, `commission_rate_bps=10.0`, `half_spread_bps=5.0`, `slippage_bps=2.0`,
`initial_equity=500.0`, `stake=100.0`, one-shot `entry_regime_mask=None` (this lever needs no
mask -- see below), `now` pinned to `2025-03-01T00:00:00Z`. **No change to `strategy.py`,
`entry_masks.py`, `donchian.py`, `regularity.py`, `data_contract.py`.**

**One small, additive engine change is required and is in scope for this slice, per the ticket's
own allowance ("if a new engine change is unavoidable, keep it additive with its own tests").**
This lever cannot be expressed through the existing `entry_regime_mask` hook: that hook requires
a static boolean series computed *before* `run_backtest` is called, but whether a given bar is
"within `LOSS_COOLDOWN` candles of the last loss" depends on which trades actually close as
losses *during* the run -- itself a function of which entries the gate has already allowed,
exactly the same inherent sequential-state argument that is why `cooldown_candles` is a
first-class engine parameter rather than a precomputed mask in the first place. Precomputing the
gate from a separate *unfiltered baseline* run's trade sequence (as the position-sizing note's
`stake_series` does for a continuous multiplier) would not be faithful here: once the gate starts
suppressing entries, the gated run's own loss sequence can differ from the baseline run's, and a
mask built from the wrong loss sequence would misdate the cooldown windows for exactly the
trades the gate is supposed to affect. The engine itself must therefore track, per bar, whether a
loss cooldown is currently active.

`backtest_engine.run_backtest` gains one new optional parameter, `loss_cooldown_candles: int = 0`,
parallel to the existing `cooldown_candles` int parameter and defaulting to `0` (off), which
preserves every existing call site's behaviour exactly (verified as a harness control below).
Implementation, additive only, no other line of the existing per-bar loop touched:

* A new loop-local variable `loss_cooldown_until = -1` (mirrors the existing `cooldown_until`,
  kept as a fully separate variable rather than merged into it, so `cooldown_candles` and
  `loss_cooldown_candles` can be set independently and their effects are never conflated).
* At every point in loop step 2 (stop-loss/trailing touch) and step 3 (signal reversal) where the
  existing code already calls `portfolio.close_position(...)` and `_record_close(...)`, exactly
  after the existing `if exit_reason == "initial_sl" and cooldown_candles > 0:` block (step 2
  only) or immediately after `_record_close` (step 3, which has no such block today), one new
  check is added: `if loss_cooldown_candles > 0 and closed_trade.net_pnl < 0: loss_cooldown_until
  = bar_count + loss_cooldown_candles`. This covers `initial_sl`, `trailing_sl` and
  `signal_reverse` exits (every exit that happens inside the per-bar loop); `end_of_data` (loop
  step 6, after the loop) closes a position that will never re-open in this backtest run anyway,
  so it needs no cooldown bookkeeping.
* Loop step 4's existing entry-queue condition, `if pos == 0 and signal != 0 and bar_count >
  cooldown_until and entry_allowed:`, gains one additional `and bar_count > loss_cooldown_until`
  clause. Both cooldowns must have expired for a new entry to queue -- with `cooldown_candles=0`
  (this note's fixed value) `cooldown_until` never advances past `-1`, so in this note's own runs
  the added clause is the only one that can ever gate an entry, and the two mechanisms remain
  independently combinable for any future note that wants both.
* Default `loss_cooldown_candles=0` means `loss_cooldown_until` never advances past its initial
  `-1`, so `bar_count > loss_cooldown_until` is `True` on bar 1 onward regardless -- every
  existing call site (which does not pass this new parameter) is provably unaffected, verified as
  discriminating check 5 below.

**Discriminating checks:**

1. **Baseline-arm harness control**: this script's own `loss_cooldown_candles=0` arm (the
   baseline) must reproduce `output/f006_notrail_monthly/summary/results.csv`'s stored
   `train1_net_pnl`/`n_trades` for all 30 series exactly (0 mismatches expected) -- validates the
   new script's engine-call plumbing and confirms the new parameter's default is inert.
2. **Subset invariant**: `n_trades_sized <= n_trades_baseline` for all 30 series (the loss
   cooldown can only remove entries the baseline already allowed, never add one) -- checked in
   script, any violation stops the run.
3. **No lookahead**: the cooldown state (`loss_cooldown_until`) is set only from a trade that has
   *already closed* by the current bar and consulted only for entries queued at bars *at or after*
   that close -- this is a direct, mechanical property of the per-bar loop's own sequencing
   (nothing computed for bar `i` ever reads `closed_trade`/`net_pnl` from a bar `> i`), verified by
   a new engine-level test asserting that truncating the input frame at any bar produces identical
   trades up to that truncation point with `loss_cooldown_candles > 0` set, mirroring
   `tests/test_backtest_engine.py`'s existing causality-adjacent tests.
4. **Genuineness guard enforced in code, not only in prose**: `promotion_pass_genuine` is a
   computed column (`promotion_pass_sized AND n_trades_sized > 0`); any series with
   `promotion_pass_sized=True` and `n_trades_sized=0` is flagged `degenerate_pass=True` separately,
   reported explicitly in the Result section regardless of whether any series passes.
5. **`loss_cooldown_candles=0` regression on `run_backtest` itself**: a new test asserts that
   calling `run_backtest` with `loss_cooldown_candles=0` (the new default) produces byte-identical
   `trades_df`/`equity_curve`/`metrics` to calling it without the parameter at all -- confirming
   the new hook is additive, not just described as additive, mirroring the `stake_series=None`
   regression test the position-sizing note's Method section required for its own new parameter.
6. **Loss-conditioning correctness, not merely reason-conditioning**: a new fixture test
   constructs a scenario where a `trailing_sl` exit closes at a net loss (small stop retracement
   after a marginal favourable move, arranged so trailing activates but the locked-in level is
   still below entry net of costs) and asserts `loss_cooldown_candles > 0` suppresses the very next
   bar's otherwise-would-fire re-entry, while an otherwise-identical scenario where the same exit
   reason closes at a net gain does NOT suppress the next entry -- the direct test that this lever
   discriminates on realized PnL sign, not on exit-reason label, the ticket's own required
   distinction from `cooldown_candles`.
7. **Regularity module regression, unmodified**: `tests/test_regularity.py`'s existing tests
   re-run to confirm no regression, since no new logic is added to `regularity.py`.

## Falsification condition (stated before running)

Evaluated on the same 30 `(name, symbol, interval)` series as every prior note in this family,
against `spec/research/F005-validation-protocol.md` section 7's monthly promotion checklist,
applied per series exactly as `F006-hypothesis-notrail-monthly.md` applied it:

**H1 is falsified if zero of the 30 series have `promotion_pass_genuine = True`** -- i.e. no
series both clears the checklist under `loss_cooldown_candles=50` AND has `n_trades_sized > 0`. A
series that clears the checklist only by trading zero times is `degenerate_pass=True` and does
**not** count toward H1 surviving.

**H1 survives if at least 1 of the 30 series has `promotion_pass_genuine = True`.** A single
genuinely clearing series is sufficient -- it would be the first Validation candidate this whole
F006 sub-family (three names, `NO_TRAIL`, monthly criterion) has produced on a non-thin sample,
and is flagged prominently as such, per the ticket's explicit instruction, if it occurs. A series
that clears the checklist but trades only 2-5 times over the full Train-1 year is reported
prominently as a thin-sample near-miss (exactly the standard the cross-symbol-refined note set)
and is explicitly NOT treated as a genuine Validation candidate, consistent with that note's own
precedent and this ticket's own framing ("samples too thin ... to count").

**Distinguishing genuine selection from starving the sample is mandatory reporting regardless of
H1's outcome**, per the ticket's explicit requirement: pooled and per-name win rate, mean
negative months per series, and trade count, baseline vs. `loss_cooldown_candles=50`, reported
and judged against this sub-family's own established reference points (see the section above).

## Run_id

(filled in after running)

## Result

(filled in after running)

## Decision

(filled in after running)

## Tests

(filled in after running)
