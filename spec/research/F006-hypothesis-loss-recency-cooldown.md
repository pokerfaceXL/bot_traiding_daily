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

`scripts/f006_loss_recency_cooldown_experiment.py`, `git_commit_parent = e0c3ff1` (the
pre-registration commit above), single pass, `.venv_test` (Python 3.9.25, pandas 2.2.3, rebuilt
in this worktree from the cached offline wheelhouse at `/tmp/mine-strategy-wheels` plus
`/tmp/pipdl` for `pyyaml`, since this worktree's `.venv_test` did not pre-exist; no network
access), 30 series, 18.1s. This worktree's `data_cache/*.csv` (git-ignored) were also missing and
were copied unmodified from the main checkout's `data_cache/` before running; the harness control
below (0/30 mismatches against `output/f006_notrail_monthly/summary/results.csv`) confirms the
copy reproduces that prior note's numbers exactly, which would not happen if the checksum-verified
load were pulling different bytes. Per-series results and monthly tables:
`output/f006_loss_recency_cooldown/raw/*.json` (30 files, baseline + gated monthly breakdown
each). Summary table: `output/f006_loss_recency_cooldown/summary/results.csv`. Manifest,
checksums and the harness-control/subset-invariant record:
`output/f006_loss_recency_cooldown/summary/manifest.json`.

**One correction to the Method section discovered while writing the script, not a change to the
falsification condition.** The Method section's engine-parameter list did not explicitly restate
that the existing one-shot entry mask (`entry_masks.one_shot_entry_mask`) must still be applied
-- it is implicit in "identical to `F006-hypothesis-notrail-monthly.md`'s cell", since that note's
own baseline already uses the one-shot mask as part of the `NO_TRAIL` cell definition, but the
first run of this note's script omitted `entry_regime_mask` entirely and produced a baseline that
did not match `output/f006_notrail_monthly/summary/results.csv` at all (persistent-state
re-entries inflated trade counts 2-4x for the Donchian names specifically). Adding
`entry_regime_mask=entry_masks.one_shot_entry_mask(entry_masks.strategy_signal_series(...))` to
both the baseline and gated calls (identical mask object passed to both, so the loss-recency gate
is tested strictly on top of the one-shot mask, not as a replacement for it) reproduced the prior
note's baseline exactly -- the harness control below is 0/30 mismatches after this fix. No change
to the pre-registered `LOSS_COOLDOWN=50` value, the sample, or the falsification condition.

## Result

**H1 is falsified. 0 of 30 series is even a degenerate pass, let alone a genuine one --
`promotion_pass_gated` is `False` for all 30 series.** The harness control against
`output/f006_notrail_monthly/summary/results.csv` (baseline arm, `loss_cooldown_candles=0`) is
**0/30 mismatches** on both `n_trades` and `train1_net_pnl` (tolerance $0.001), confirming this
script's engine-call plumbing before trusting its `loss_cooldown_candles=50` numbers. The subset
invariant (`n_trades_gated <= n_trades_baseline`) holds for all 30 series (0 violations) -- the
gate only ever removed entries, exactly as designed, and every series still traded a comfortably
nonzero number of times under the gate (`n_trades_gated` ranges 11-90, no series anywhere near
zero), so `degenerate_pass` is trivially `False` for all 30 -- unlike the width-expansion note,
there is no zero-trade artefact to disambiguate here either.

**Unlike every other lever tried in this sub-family, this one does not merely fail to help --
it makes the checklist's own load-bearing metric measurably worse.** Trade count fell 31.9%
(1,695 baseline -> 1,155 gated), a smaller cut than three of the four prior mechanisms (width
52%, trend 48%, cross-symbol 43.0%) but comparable in kind. Pooled trade-weighted win rate is
flat-to-slightly-down (25.07% -> 24.76%, -0.31 pp) -- not the wrong-signed collapse the trend gate
produced (-3.16 pp), but not the modest gain the cross-symbol gate produced either (+1.84 pp);
it sits closest to the position-sizing note's near-null result (-0.0061 winner/loser gap), i.e.
this mechanism does not discriminate winners from losers any better than chance. **Mean negative
months per series rose from 6.47 to 7.43** -- the checklist's own binding constraint moved in the
wrong direction, the only lever in this entire five-mechanism sub-family (width, trend, sizing,
cross-symbol at two thresholds, and now loss-recency) to do so; every prior mechanism was at worst
neutral on this measure (cross-symbol's 30-series arm: 6.47 -> 6.63, itself already flagged as
"the opposite of what a genuinely edge-improving filter should do"; this note's own -0.96 move is
roughly the same size in the same wrong direction, on a smaller trade-count cut). Mean Train-1 net
PnL per series fell 41.9%, from $48.45 to $28.15 -- the steepest proportional mean-PnL decline of
any lever tried against this target (position sizing: -24.9%; the pooled cross-symbol gate at
`MIN_AGREE=2` was the only prior lever where mean PnL *rose*). The count of series with positive
Train-1 net PnL fell from 18/30 to 15/30, the lowest of any arm reported anywhere in this
sub-family (every prior filtered/sized arm reported 12-20/30 positive, all otherwise >=18).

**The best-performing single series on the checklist's own criterion got WORSE, not better, under
the gate.** Baseline's own closest approach (`F006-hypothesis-notrail-monthly.md`'s own
headline figure), `DOGEUSDT/60/DONCHIAN_55` with only 2 negative months, rises to **4** negative
months under `loss_cooldown_candles=50` (net PnL also falls, $197.91 -> $168.82). The minimum
negative-month count anywhere in the 30-series gated arm is **4** (three series tie at 4:
`ETHUSDT/240/DONCHIAN_55`, `DOGEUSDT/60/DONCHIAN_55`, and a fourth pair at 5) -- strictly worse
than the baseline's own best (2) and worse than the cross-symbol-refined note's own best-ever
finding in this whole sub-family (2, at `MIN_AGREE=4` on a thin 2-5-trade sample). This sub-family
has now measured five mechanisms and the minimum achievable negative-month count on a
normally-trading (non-thin) sample has never gone below 2 (`F006-hypothesis-notrail-monthly.md`'s
own unfiltered baseline), and this note's own gate moves every series it touches away from, not
toward, that floor.

**Per-name breakdown: all three names get worse on mean PnL, none improves on mean negative
months.**

| Name | mean PnL, baseline -> gated | mean neg. months, baseline -> gated | trade-wtd win%, baseline -> gated | trades baseline -> gated |
| --- | ---: | ---: | ---: | ---: |
| `BB_20_25_breakout` | $48.78 -> $37.68 (-22.7%) | 5.8 -> 8.0 | 25.66% -> 25.05% | 869 -> 539 |
| `DONCHIAN_55` | $58.39 -> $38.43 (-34.2%) | 6.5 -> 6.7 | 27.31% -> 29.70% (+2.39 pp) | 476 -> 330 |
| `DONCHIAN_PULLBACK_55` | $38.19 -> $8.33 (-78.2%) | 7.1 -> 7.6 | 20.57% -> 18.53% (-2.04 pp) | 350 -> 286 |

`DONCHIAN_55` is the only name where win rate improves (+2.39 pp, in the predicted direction, the
direct analogue of what the cross-symbol note found for this same name under a different
mechanism), but even there mean negative months still rises slightly (6.5 -> 6.7) and mean PnL
still falls (-34.2%) -- the trades removed are not disproportionately losers by enough margin to
offset the trade-count reduction's effect on monthly variance. `BB_20_25_breakout`'s negative-month
count rises the most of the three (+2.2), and `DONCHIAN_PULLBACK_55` -- already this sub-family's
most fragile name per the cross-symbol note's own finding -- has both its win rate and its mean PnL
collapse hardest of the three (-78.2%, the single worst per-name mean-PnL outcome measured anywhere
in this whole sub-family to date).

**Distinguishing genuine selection from starving the sample, per the ticket's explicit
requirement: there is no ambiguity to resolve, because the mechanism did not select against losers
at any margin large enough to matter, and it demonstrably starved the sample of exactly the kind of
monthly diversification the checklist needs.** A 31.9% trade-count cut with an essentially flat
pooled win rate (-0.31 pp) and a *worse* monthly-negative-count outcome is the least favourable
combination of the five mechanisms this sub-family has now tried: the width and trend gates at
least held win rate roughly flat or the mean-PnL floor intact on a comparable or larger trade cut;
this gate's trade-count reduction comes disproportionately from bars that would otherwise have
formed part of a calendar month's *only* winning trade, which is the exact failure mode `F006-
hypothesis-donchian.md`'s original decomposition (rare, large, unevenly-timed winners) predicts for
any mechanism that removes trades without being able to tell, in advance, whether the removed
trade would have been this month's one saving win. A post-loss pause has no way to distinguish "a
regime this series should sit out" from "the very next signal after a stop-out is this month's only
large winner" -- and on this sample, evidently, it removes the latter often enough to make the
monthly record worse in aggregate, not better.

## Decision

**No promotion. Falsified, and more cleanly negative than any of the four prior mechanisms tried
against this exact target.** H1 is falsified: 0 of 30 series has `promotion_pass_genuine = True`,
and there is no degenerate-pass or literal/substantive ambiguity to navigate -- every series traded
a comfortably nonzero number of times, and the checklist's own binding metric (mean negative months
per series) moved in the wrong direction, the first and only time that has happened anywhere in
this five-mechanism sub-family.

**This closes out the loss-recency lever for this exact target (three names, `NO_TRAIL`, monthly
criterion) at the one well-justified value tested (`LOSS_COOLDOWN=50`), per the ticket's own
instruction to pre-register ONE concrete hypothesis rather than force a sweep.** A `LOSS_COOLDOWN`
sweep (smaller values, e.g. 5/10/20, mirroring `F006-hypothesis-cooldown.md`'s own grid) is a
plausible next step this note does not itself take -- unlike the `cooldown_candles` blanket lever,
which showed a real, monotone, still-improving effect all the way to its own upper bound of 50
(making 50 the obviously best-justified single value to test first there), this note's own single
data point at 50 already moves the checklist's binding metric in the *wrong* direction, which is a
weaker basis for assuming a smaller `LOSS_COOLDOWN` would do better rather than simply doing less
of the same harm (a smaller trade-count cut, closer to the unfiltered baseline, is the more likely
outcome of a smaller value here, not a reversal of sign) -- reported as an open, low-priority
question rather than a recommended follow-up, since nothing in this note's own data suggests the
mechanism would flip favourable at a different magnitude.

**No further volatility-orthogonal, single-series-history lever remains named by any prior note in
this sub-family.** Of the three levers `F006-hypothesis-position-sizing-vol-inverse.md`'s Decision
section named (recency of the last loss, cross-sectional agreement, exit-side), and the two
`F006-hypothesis-entry-cross-symbol-refined.md` reaffirmed as untried (recency of the last loss,
exit-side), this note closes out **recency of the last loss** with a clean, uniformly negative
result -- the second-most-uniform negative finding in this sub-family after the trend-confirm
gate's own -3.16 pp result, and arguably the most uniform on the checklist's own binding metric
specifically, since it is the only lever that made that metric worse rather than merely failing to
improve it. **The one lever this whole sub-family (five mechanisms across seven notes) has not yet
tried is the exit-side lever**, named identically by both prior Decision sections and not
addressed by this slice -- the natural next step for whichever future note the coordinator scopes.

**No series in this note's 30-series sample is a Validation candidate, genuine or otherwise, and
none comes close: the best negative-month count anywhere in the gated arm (4) is strictly worse
than the sub-family's already-established best on a non-thin sample (2, `F006-hypothesis-notrail-
monthly.md`'s own `DOGEUSDT/60/DONCHIAN_55`) and worse than the thin-sample near-misses
`F006-hypothesis-entry-cross-symbol-refined.md` explicitly flagged as not substantive (also 2).**
This is reported prominently and honestly, per the ticket's explicit instruction: this is a clean
negative result, not a partial or ambiguous one, and it should not be read as evidence that a
differently-tuned loss-recency lever would fare better without further data -- the one data point
gathered here points the wrong way on the metric that matters.

**What is reusable regardless of this outcome:** `backtest_engine.run_backtest`'s new
`loss_cooldown_candles` hook (additive, `0` default provably unchanged per the regression test
below, independently trackable alongside the existing `cooldown_candles`) is reusable by any future
loss-conditioned re-entry hypothesis, including a future note that combines it with
`cooldown_candles`, `entry_regime_mask`, or `stake_series` in the same run.
`scripts/f006_loss_recency_cooldown_experiment.py`'s pattern (one-shot mask precomputed exactly as
`f006_notrail_monthly_experiment.py` does it, baseline + gated arm from the same harness, harness
control against the stored `NO_TRAIL` baseline, subset invariant, and the per-name win-rate/mean-
PnL/mean-negative-months reporting table) is reusable by any future engine-level F006 slice on this
sample.

## Tests

`tests/test_backtest_engine.py` gains 3 new tests for the engine's one change: (1) a
`loss_cooldown_candles=0` regression test, mirroring the `stake_series=None` regression test the
position-sizing note's Method section required for its own new parameter, asserting byte-identical
`trades`/`equity_curve`/`metrics` with and without the parameter passed explicitly; (2) a
hand-designed 11-bar synthetic fixture (a monkeypatched `strategy.STRATEGY_CATALOG` entry with a
fixed signal series, not the real `ohlcv_sample.csv` fixture, since this scenario needs bar-by-bar
control no real data offers) asserting that gating a loss on `initial_sl` delays -- but does not
drop -- the next entry of a persistent signal (3 trades in both the `loss_cooldown_candles=0` and
`=3` arms, entry_time shifted from bar 3 to bar 7); (3) the ticket's own required discriminating
check, on the same fixture with one bar's close changed so the second trade closes at a LOSS via
`signal_reverse` (an exit reason `cooldown_candles` never gates at all) instead of a win --
confirming the third trade is suppressed only in the loss variant, not the win variant, i.e. the
gate is conditioned on realized `net_pnl` sign, not on exit-reason label, the ticket's own required
distinction from `cooldown_candles`. All 3 new tests are the load-bearing check for this slice's
one piece of new engine logic; no other module (`strategy.py`, `entry_masks.py`, `donchian.py`,
`regularity.py`, `data_contract.py`) was changed. `tests/test_regularity.py`'s existing tests
re-run to confirm no regression, since no new logic is added to `regularity.py`.

Full suite, Python 3.9 `.venv_test` (no Lorentzian dependency in this sample, so
`.venv_lorentzian` was not needed, matching every prior note in this exact sub-family):

| | Before this slice | With this slice |
| --- | --- | --- |
| `pytest tests/` | 162 passed, 9 skipped | **165 passed, 9 skipped** |

Exactly the 3 new tests, no behaviour change in any existing test.
