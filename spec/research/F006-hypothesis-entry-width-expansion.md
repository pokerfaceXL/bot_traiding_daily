# F006 — Hypothesis: does an entry-side volatility-expansion gate clear the monthly
# criterion for the three NO_TRAIL aggregate-positive names? Train 1 only

> Sections "Observation" through "Falsification condition" (including the sample and the exact
> predicted effect) are written and committed to this file BEFORE
> `scripts/f006_entry_width_expansion_experiment.py` is written and before any backtest is run,
> per the same discipline as every prior F006 hypothesis note. "Run_id", "Result", "Decision"
> and "Tests" are filled in after the run.
>
> TRAIN-1 ONLY, same window as every F006 slice: `[2024-03-01T00:00:00Z, 2025-03-01T00:00:00Z)`
> plus the protocol's 35-day warm-up buffer from `2024-01-26T00:00:00Z`. Validation 1-4 and the
> Holdout window are not loaded, not sliced and not looked at by any script in this slice.

## Observation

The exit-geometry axis for the three `NO_TRAIL`-aggregate-positive names — `DONCHIAN_55`,
`BB_20_25_breakout`, `DONCHIAN_PULLBACK_55` — is exhausted. `F006-hypothesis-trailing-boundary.md`
established `NO_TRAIL` (`activate_pct=10.0`, trail never arms, `max_sl_pct=0.03`) as the best
exit-geometry cell tested (pooled breakeven win% 30.14, the only cell with positive pooled gross
per-trade expectancy) and named these three names as the only ones with positive aggregate
Train-1 net PnL at that cell. `F006-hypothesis-stop-width-notrail.md` then swept `max_sl_pct` at
`NO_TRAIL` and found the effect is a wash past 0.08 in aggregate, with `DONCHIAN_PULLBACK_55`
actually *worsening* monotonically as the stop widens (its best width in that sweep is the
default, 0.03) — so there is no single wider `max_sl_pct` that helps all three names, and the
ticket for this slice pins the default (0.03) unless a specific per-name reason from that note
says otherwise; here it does not, uniformly. `F006-hypothesis-notrail-monthly.md` then built the
Train-1 monthly PnL series for all 30 `(name, symbol, interval)` series at exactly this cell and
found **0/30 clear** `spec/research/F005-validation-protocol.md` section 7's monthly promotion
checklist (zero tolerance for a losing month) — every series has 2-9 losing months out of 12,
spread across the year rather than concentrated, a pattern that note attributed to a structural
mechanism: low win rate (14-32% pooled per name, per `F006-hypothesis-trailing-boundary.md`'s and
`F006-hypothesis-donchian.md`'s decomposition tables) carried by a few large winners. That note's
Decision section named the next step explicitly: *"a change to the entry/exit mechanism that
raises the win rate or otherwise smooths the monthly PnL distribution ... not a further search
within the exit-geometry axis."*

`F006-hypothesis-entry-regime-filter.md` tested a generic ADX14 entry-quality gate on the whole
old 10-strategy catalog and found only a small ($17.68, ~5% of the deficit), mechanistically weak
improvement — win rate stayed flat while net PnL improved, meaning the gain was fewer trades /
less cost drag, not better selection. That measurement is not reusable evidence here for two
independent reasons the ticket names: it ran at the old `activate_pct=0.03`/`trail_pct=0.02`
exit-geometry corner (since shown to be the *worst* tested, on two axes), before `NO_TRAIL`
existed as a concept; and it was not targeted at these three names specifically — ADX measures
directional trend strength, a property unrelated to how Donchian/Bollinger channel signals are
actually defined.

**A better-justified entry filter already exists in the codebase, unused on these three names.**
`strategy.py`'s `sig_bb_breakout_squeeze` (catalog entries `BB_20_2_SQ`/`BB_20_25_SQ`) gates a BB
breakout on `width > width.rolling(30).mean()` — the band must already be *expanding*, not
contracting, at the breakout bar — with the docstring's own justification: *"prawdziwy breakout z
konsolidacji"* (a genuine breakout out of consolidation, as opposed to a channel edge crossed
inside an already-choppy, non-expanding range that is more likely to whipsaw back through the
5%-away initial stop). This is a **volatility-regime** gate, not a trend-strength gate like ADX —
mechanistically distinct from the already-falsified `F006-hypothesis-entry-regime-filter.md` — and
it is defined in terms of exactly the quantity (channel/band width) that both `BB_20_25_breakout`
and the Donchian family are built from, so it generalizes to all three target names without
inventing a new indicator. It has never been run on `DONCHIAN_55`/`DONCHIAN_PULLBACK_55` (which
have no `_width` column at all — `donchian.py` never computed one), never been run at `NO_TRAIL`,
and never been measured against the monthly criterion.

## Hypothesis

**H1.** Gating new entries of `DONCHIAN_55`, `BB_20_25_breakout` and `DONCHIAN_PULLBACK_55` on
their own channel/band width being above its trailing 30-bar mean at the moment of entry — applied
via `backtest_engine.run_backtest`'s `entry_regime_mask` hook, on top of the existing one-shot
mask, at `NO_TRAIL` (`activate_pct=10.0`, `max_sl_pct=0.03`) — causes **at least 1 of the 30**
`(name, symbol, interval)` series to clear `spec/research/F005-validation-protocol.md` section 7's
monthly promotion checklist (identical three criteria to
`F006-hypothesis-notrail-monthly.md`: full-run max drawdown ≤ 50%, net PnL ≥ 0 in every
`is_valid` Train-1 calendar month, net PnL ≥ 0 over the full Train-1 period) — where that note
found 0/30 without the filter.

**Mechanism, stated before running.** Under `NO_TRAIL`, a losing trade is bounded only by
`max_sl_pct=0.03` (no trail cuts it short), and `F006-hypothesis-donchian.md`'s decomposition
showed the breakeven-win-rate gap for these names is 20-27 percentage points, driven by avg loser
being roughly 1.7-2.3x avg winner in magnitude for the raw-breakout variants (better, ~1.8x, for
`DONCHIAN_PULLBACK_55`). A breakout or pullback-trigger bar occurring while the channel/band is
**not** expanding (still narrow relative to its own recent history) is, by construction, more
likely a range-bound false break that reverses quickly into the 3% stop than a genuine trend
initiation — the width-expansion condition should disproportionately remove exactly these
low-conviction entries, raising pooled win rate and, because losing months are driven by strings
of small losses accumulating between rare large winners (the "spread thin" pattern the monthly
note described), reducing the number of losing months per series even where it does not flip the
full-period sign.

**Predicted effect**, reported regardless of whether H1 survives: pooled win rate across the 30
filtered series is higher than the 30 unfiltered series (`F006-hypothesis-notrail-monthly.md`'s
own runs, re-derivable from `output/f006_notrail_monthly/summary/results.csv`); mean number of
losing months per series (out of 12) is lower; and n_trades falls (the gate is strictly a subset
of the existing one-shot mask, so `n_trades_filtered <= n_trades_unfiltered` for every one of the
30 series, checked as a harness invariant below, not just predicted).

## Sources

This repo's own prior findings only, plus the pre-existing, unmodified `strategy.py` function this
slice reuses the *mechanism* of (not the catalog entry itself — see Method):
`F006-hypothesis-notrail-monthly.md` (the 0/30 baseline, the monthly checklist definition, the
mechanism this slice targets), `F006-hypothesis-stop-width-notrail.md` (why `max_sl_pct=0.03` is
kept uniform across all three names in this slice), `F006-hypothesis-trailing-boundary.md` (the
`NO_TRAIL` cell definition and the three names), `F006-hypothesis-donchian.md` (the win/loss
decomposition that motivates the mechanism, and the causal `donchian_channel` this slice reuses
unmodified), `F006-hypothesis-entry-regime-filter.md` (the already-falsified ADX gate, cited to
establish this is a different mechanism, and the `entry_regime_mask` engine hook it added),
`spec/research/F005-validation-protocol.md` section 7 (the monthly promotion criterion, verbatim).

## Sample (identical set of series to `F006-hypothesis-notrail-monthly.md`, not re-derived)

30 series: `DONCHIAN_55`, `BB_20_25_breakout`, `DONCHIAN_PULLBACK_55` ×
`SOLUSDT`/`ETHUSDT`/`BTCUSDT`/`XRPUSDT`/`DOGEUSDT` × `240`/`60`. `DONCHIAN_55` and
`DONCHIAN_PULLBACK_55` need `donchian.py` (pure pandas); `BB_20_25_breakout` is a plain
`strategy.STRATEGY_CATALOG` entry with an existing `bb_20_2.5_width` column from
`strategy.add_indicators`. No Lorentzian dependency — single pass on `.venv_test` (Python 3.9)
covers all 30 series.

## Method

**Engine parameters: identical to `F006-hypothesis-notrail-monthly.md`'s cell, unchanged.**
`activate_pct=10.0` (NO_TRAIL), `trail_pct=0.04` (moot, `None`), `max_sl_pct=0.03`,
`atr_multiplier=1.5`, `cooldown_candles=0`, `leverage=1.0`, `commission_rate_bps=10.0`,
`half_spread_bps=5.0`, `slippage_bps=2.0`, `initial_equity=500.0`, `stake=100.0`, `now` pinned to
`2025-03-01T00:00:00Z`. **No change to `backtest_engine.py`, `strategy.py`, `entry_masks.py`,
`donchian.py`, `regularity.py`.**

**Width-expansion gate, computed in the new script, not by editing `strategy.py`.** The gate
reuses `sig_bb_breakout_squeeze`'s exact condition (`width > width.rolling(30).mean()`, 30-bar
lookback, no new free parameter) but is built as a *standalone entry mask*, combined with the
existing one-shot mask via `entry_regime_mask`, rather than baked into a new catalog signal
function — this keeps each of the three names' own directional-call structure (and hence which
bars are call-starts) exactly as `F006-hypothesis-notrail-monthly.md` measured it, so the *only*
thing this slice changes is which call-start bars are allowed to open a position, isolating the
filter's effect from any change to signal generation itself:

* `BB_20_25_breakout`: width = `strategy.add_indicators(df)["bb_20_2.5_width"]` (existing column,
  unmodified formula: `(2 * 2.5 * rolling_std_20) / rolling_mean_20`).
* `DONCHIAN_55`, `DONCHIAN_PULLBACK_55`: width = `(upper - lower) / mid` from
  `donchian.donchian_channel(df, 55)` (unmodified function; both names share the same n=55
  channel, so the same width series is reused for both — for the pullback variant the gate is
  evaluated at whatever bar the pullback's own one-shot entry mask fires, i.e. the midline
  re-cross/trigger bar, not the original breakout bar; this is well-defined and introduces no
  lookahead since `donchian_channel` already excludes the current bar by construction).

`entry_regime_mask = one_shot_entry_mask(signal) & (width > width.rolling(30).mean())`, reindexed
by `run_backtest` onto its own post-filter/post-indicator frame (existing engine behaviour,
unchanged). A call whose start bar fails the width condition is never entered at all — the mask
does not re-arm later in that same call, matching the one-shot semantics the rest of F006 uses.

- **Script**: `scripts/f006_entry_width_expansion_experiment.py`. Single pass, `.venv_test` only.
- **Data**: identical checksum-verified load (`data_contract.load_dataset`, `EXPECTED_CHECKSUMS`
  table duplicated from `spec/research/F005-validation-protocol.md` section 6) and Train-1 slice
  (`[2024-01-26T00:00:00Z, 2025-03-01T00:00:00Z)`) as every F006 script. No network fetch.
- **Aggregation**: `regularity.py`, unchanged, called exactly as
  `scripts/f006_notrail_monthly_experiment.py` calls it, with the identical `promotion_pass`
  definition (drawdown ≤ 50%, all 12 Train-1 calendar months `is_valid` and net PnL ≥ 0, full
  Train-1 net PnL ≥ 0).
- **Recorded per series**: everything `F006-hypothesis-notrail-monthly.md` recorded (`n_trades`,
  Train-1 net PnL, 12 monthly rows, `promotion_pass`), plus `n_trades_unfiltered` (re-run with an
  always-True width gate in the same process, i.e. the plain one-shot mask alone) and
  `n_calls_gated_out` (count of call-start bars where the width condition was False), so the
  filter's selectivity is visible directly rather than only inferable from the trade-count delta.

**Discriminating checks:**

1. **Subset invariant**: `n_trades_filtered <= n_trades_unfiltered` for all 30 series (the width
   gate can only remove entries the one-shot mask already allowed, never add one) — checked in
   script, any violation stops the run.
2. **Harness control against the unfiltered baseline**: the `n_trades_unfiltered` /
   `train1_net_pnl_unfiltered` column, produced by re-running this script's own pipeline with the
   gate forced to all-True, must match `output/f006_notrail_monthly/summary/results.csv`'s stored
   `train1_net_pnl`/`n_trades` for all 30 series (0 mismatches expected) — this both validates the
   new script's engine-call plumbing against the already-verified prior note and confirms the gate
   is additive (not silently changing anything when it imposes no restriction).
3. **No lookahead in the width gate**: `donchian_channel` already asserted causal by
   `tests/test_donchian.py`; `bb_..._width` is a rolling-window function of past bars only
   (`strategy.add_indicators`, unmodified). A new fixture test asserts truncating a 100-bar frame
   at bar i+10 does not change the width-gate boolean at bar i, for both the BB and Donchian width
   series, mirroring `tests/test_donchian.py`'s existing causality-check pattern.
4. **Regularity module regression, unmodified**: `tests/test_regularity.py`'s existing 8 tests
   re-run to confirm no regression, since no new logic is added to `regularity.py`.

## Falsification condition (stated before running)

Evaluated on the same 30 `(name, symbol, interval)` series as `F006-hypothesis-notrail-monthly.md`,
against `spec/research/F005-validation-protocol.md` section 7's monthly promotion checklist,
applied per series exactly as that note applied it (verbatim: drawdown ≤ 50%, net PnL ≥ 0 in
every `is_valid` Train-1 calendar month, net PnL ≥ 0 over the full Train-1 period):

**H1 is falsified if zero of the 30 series clear the checklist under the width-expansion
gate** — i.e. the same 0/30 outcome as the unfiltered baseline, meaning the entry filter did not
change the monthly-promotion picture at all.

**H1 survives if at least 1 of the 30 series clears the checklist.** A single clearing series is
sufficient to survive (this mirrors the "≥1" bar `F006-hypothesis-notrail-monthly.md`'s own H1
used) — it would be the first Validation candidate F006 has produced.

Reported either way, not falsifying by itself (mechanism checks, per the predicted effect above):
pooled win rate with vs. without the gate; mean number of losing months per series with vs.
without the gate (does the filter reduce the "spread thin" pattern even for series that still
fail the zero-tolerance checklist); n_trades reduction and `n_calls_gated_out` per name (is the
gate removing a similar fraction of calls from all three names or concentrated in one); and, for
any series that still fails, how many losing months it has left compared to its unfiltered count
(to distinguish "close but not zero" from "no better than baseline" among the failures).

## Run_id

`scripts/f006_entry_width_expansion_experiment.py`, `git_commit_parent = 05b5288` (the
pre-registration commit above), single pass, `.venv_test` (Python 3.9.25, pandas 2.3.3),
30 series, 25.2s. Per-series results and monthly tables: `output/f006_entry_width_expansion/raw/*.json`
(30 files, each carrying both the filtered and unfiltered monthly breakdown). Summary table:
`output/f006_entry_width_expansion/summary/results.csv`. Manifest, checksums, harness-control
and subset-invariant records: `output/f006_entry_width_expansion/summary/manifest.json`.

## Result

**Harness control and subset invariant both clean.** The gate-forced-all-True rerun (this
script's own "unfiltered" arm) matches `output/f006_notrail_monthly/summary/results.csv`'s
stored `train1_net_pnl`/`n_trades` for all 30 series -- **0/30 mismatches** -- so this new
script's engine-call plumbing reproduces the already-verified prior note exactly. The subset
invariant (`n_trades_filtered <= n_trades_unfiltered`) holds for **30/30** series -- the gate
never adds an entry, only removes one.

**H1 technically survives, by exactly one series, and that series is degenerate.** The
falsification condition as pre-registered ("falsified if zero of the 30 series clear the
checklist") is not met: **1/30** filtered series clears the monthly promotion checklist --
`DONCHIAN_55`/DOGEUSDT/4h. But `n_calls_gated_out = 18 = n_calls` for that series: the width
gate rejected **every single one** of its 18 directional calls in Train 1, so it produced
**zero trades**, **$0.00** net PnL, **0%** drawdown, and trivially "zero losing months" because
every month has no trade and therefore no PnL to be negative. Hand-verified (not just read off
the summary row) against the raw width/gate values at all 18 of that series' call-start bars: the
gate's `width > width.rolling(30).mean()` condition is `False` at every one, by margins ranging
from -0.023 to -0.19 width-units -- not a rounding-boundary artefact, a genuine, if narrow,
miss on every occasion. This is not a promotion candidate in any substantive sense -- an
empty strategy trivially satisfies a zero-tolerance "no losing month" rule -- and the
pre-registered falsification condition did not anticipate this degenerate case (it should have
required `n_trades > 0` as an implicit precondition for "clears the checklist"; that gap is
recorded here rather than silently patched after the fact). Read literally, per the condition
as written before the run, **H1 survives**; read for substance, **it does not** -- no series with
any trading activity clears the checklist.

**The pre-registered mechanism (better selection -> higher win rate, fewer losing months) is not
supported.** Trade-count fell by more than half across the sample -- 1,695 unfiltered trades to
812 filtered (-52.1%), matching the scale of selectivity the Donchian and BB families showed in
prior notes -- but the trade-weighted pooled win rate barely moved: **25.07% unfiltered ->
25.49% filtered, +0.42 pp**, an order of magnitude smaller than the swings
`F006-hypothesis-stop-width-notrail.md` called "real" (win rate moved 3-5 pp there for a
comparable-sized trade-count change). Mean net PnL across the 30 series **fell**, from $48.45 to
$15.21, and the count of series with positive Train-1 net PnL fell from 18/30 to 17/30 -- the
filter is, in aggregate, removing more good trades than bad ones, the opposite of the predicted
effect.

**Mean losing months per series moved in different directions for different names, and even where
it improved the improvement does not survive scrutiny.**

| Name | mean net PnL, unfiltered | mean net PnL, filtered | mean neg months, unfiltered | mean neg months, filtered | positive series (of 10) |
| --- | ---: | ---: | ---: | ---: | --- |
| `BB_20_25_breakout` | $48.78 | $48.59 | 5.8 | **6.5 (worse)** | 7 -> 9 |
| `DONCHIAN_55` | $58.39 | **$0.06** | 6.5 | 5.2 | 7 -> 4 |
| `DONCHIAN_PULLBACK_55` | $38.19 | **-$3.01** | 7.1 | 5.6 | 4 -> 4 |

`BB_20_25_breakout` is the one name whose net PnL survives the filter roughly intact (and whose
positive-series count genuinely rises, 7 -> 9) -- but its own mean losing-months count gets
*worse*, not better (5.8 -> 6.5), the opposite of the predicted direction. Both Donchian names
show an apparent losing-months improvement, but it is not the win-rate-driven smoothing the
hypothesis predicted: their mean net PnL collapses toward zero or negative in the same breath
(`DONCHIAN_55`'s mean falls from $58.39 to $0.06, essentially the filter erasing the name's own
edge, and `DONCHIAN_PULLBACK_55`'s flips from positive to negative), which is exactly the
mechanical artefact the falsification-condition gap above hints at: cutting trades in half turns
some previously-negative months into **flat $0.00 months** (no trade that month, not a winning
one), which counts as "non-negative" under the checklist's literal wording without representing
any actual improvement in trade quality. The DOGEUSDT/4h `DONCHIAN_55` series is the extreme,
degenerate end of exactly this artefact, not an isolated glitch.

**No name shows the hypothesis's predicted signature (win rate up, PnL preserved or improved,
losing months down) simultaneously.** `BB_20_25_breakout` keeps its PnL but not its monthly
profile; the two Donchian names improve their monthly profile but at the cost of the PnL (and,
for `DONCHIAN_55`, the win rate too -- not shown per-name above but visible in
`output/f006_entry_width_expansion/summary/results.csv`) that made them promotion leads in the
first place.

## Decision

**No promotion.** Read for substance rather than by the falsification condition's literal
wording, **H1 is not supported**: the one series that technically clears the monthly checklist
does so by trading zero times, which is not a candidate in any sense the protocol's promotion
gate was designed to certify, and no series with actual trading activity clears it. The
pre-registered mechanism -- that a width-expansion gate would raise win rate and thereby smooth
the monthly PnL distribution -- is contradicted by the pooled numbers: win rate moved 0.42 pp
against a 52% trade-count cut, an order of magnitude too small to be the reason any month's sign
changed, and the apparent losing-months improvement for the two Donchian names is explained
more parsimoniously by trades disappearing (turning negative months into empty, flat-zero months)
than by better entry selection -- the same "starving, not selecting" failure mode
`F006-hypothesis-entry-regime-filter.md` already found for the generic ADX gate on the old
catalog, now reproduced with a mechanistically distinct, volatility-based gate on the three
specific NO_TRAIL-positive names it was targeted at.

**This closes out the width-expansion approach for these three names.** The BB-derived
squeeze/expansion mechanism, reused here exactly as `strategy.py`'s own `sig_bb_breakout_squeeze`
defines it, does not generalize into an entry-quality filter that raises win rate for either the
BB or the Donchian family at `NO_TRAIL`. Combined with
`F006-hypothesis-entry-regime-filter.md` (ADX gate, old exit geometry, whole catalog) and this
slice (width gate, `NO_TRAIL`, the three lead names), two mechanistically distinct entry filters
have now both failed to raise win rate for the reason the monthly criterion actually needs --
real trade-quality improvement, not fewer trades. A future entry-side hypothesis for these three
names should look for a filter that changes *which* calls are entered without simply shrinking
the sample (e.g. a directional/multi-timeframe confirmation rather than a magnitude-of-volatility
threshold), and should build in the `n_trades > 0` guard this slice's falsification condition
should have had from the start, so a future run cannot again "pass" by trading nothing.

**What is reusable regardless of this outcome:** `scripts/f006_entry_width_expansion_experiment.py`'s
pattern of scoring both a filtered and an unfiltered (gate=all-True) arm from the same call to the
engine, and diffing the unfiltered arm against a prior note's stored rows as the harness control,
is cheap and reusable by any future entry-filter slice on this sample. `tests/test_entry_width_expansion.py`'s
causality checks on `width_series`/`width_gate` are the load-bearing correctness check for this
script's one piece of new logic and pass cleanly; no engine, strategy, or Donchian module change
was needed.

## Tests

`tests/test_entry_width_expansion.py` (7 new tests: causality of the width gate for both
`DONCHIAN_55` and `BB_20_25_breakout`, at three truncation points each, plus a warm-up-window
check) is the load-bearing check for this slice's one piece of new logic (`width_series`/
`width_gate` in the new script) -- no existing module (`backtest_engine.py`, `strategy.py`,
`donchian.py`, `entry_masks.py`, `regularity.py`) was changed. `tests/test_regularity.py`'s
existing 8 tests re-run to confirm no regression: 8/8 passed, unchanged.

Full suite, Python 3.9 `.venv_test` (no Lorentzian dependency in this sample, so
`.venv_lorentzian` was not needed, per `F006-hypothesis-notrail-monthly.md`'s precedent):

| | Before this slice | With this slice |
| --- | --- | --- |
| `pytest tests/` | 136 passed, 9 skipped | **143 passed, 9 skipped** |

Exactly the 7 new tests, no behaviour change in any existing test.
