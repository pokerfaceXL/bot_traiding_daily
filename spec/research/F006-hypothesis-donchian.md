# F006 — Hypothesis: Donchian channel breakout & pullback-after-breakout, Train 1 only

> Sections "Observation" … "Signal definitions (design decisions, fixed before running)" were
> written and committed to this file BEFORE `donchian.py` existed and before any backtest was run,
> per the same discipline as `spec/research/F006-hypothesis-one-shot-entry.md`,
> `spec/research/F006-hypothesis-cooldown.md`, `spec/research/F006-hypothesis-stop-width.md`,
> `spec/research/F006-hypothesis-entry-regime-filter.md` and
> `spec/research/F006-lorentzian-causality.md`. "Method", "Run_id", "Result" and "Decision" were
> filled in after the run.
>
> TRAIN-1 ONLY. Per `spec/research/F005-validation-protocol.md` section 7.3, F006 selects on
> train+validation and never opens holdout; this slice restricts itself further, to Train 1
> (`[2024-03-01T00:00:00Z, 2025-03-01T00:00:00Z)`) plus the protocol's 35-day warm-up buffer from
> `2024-01-26T00:00:00Z`. Validation 1-4 and the Holdout window are not loaded, not sliced and not
> looked at by any script in this slice.

## Observation

Six F006 slices have now measured the same invariant on the same Train-1 sample, and none of them
has produced a single profitable run or a single positive per-trade expectancy:

| Slice | Lever | Kind of lever | Result on per-trade expectancy |
| --- | --- | --- | --- |
| `F006-hypothesis-stop-width` | `max_sl_pct` 0.01 → 0.05 | position sizing / exit | negative at every width |
| `F006-hypothesis-entry-regime-filter` | ADX ≥ threshold entry gate | *when* to enter | negative at every threshold |
| `F006-lorentzian-causality` | a different generator (kNN classifier) | *what* generates the call | negative, worse than EMA |
| `F006-hypothesis-cooldown` | `cooldown_candles` 0 → 50 | *when* to re-enter | -$1.078 → -$1.010, flat at 4h |
| `F006-hypothesis-one-shot-entry` | one entry per directional call | *when* to re-enter | -$1.078 → **-$0.985** (best so far) |

Five of the six tune **when the existing catalog's signals are entered, re-entered or exited**. The
one that changed the generator (Lorentzian at library defaults) is still a *momentum-state*
generator: like `EMA_8_21`, `MACD_12_26_hist` and `ADX14_DI_20`, it emits a persistent directional
state derived from smoothed price, and it landed in the same place (-$384.99 mean net PnL,
`spec/research/F006-hypothesis-one-shot-entry.md`'s per-strategy table).

The one-shot note's own decision section draws the conclusion this slice implements: *"the
per-trade-expectancy invariant is a statement about the **signals**, not about the engine wrapped
around them, and no further reshaping of *when* these particular signals are entered is worth Train
budget. Any such new generator should be evaluated with one-shot entry on from the start, since it
is now known to be both cheap and expectancy-improving."*

`spec/build.md`'s F006 section names the next family explicitly: *"Równolegle: rodziny EMA/RSI/MACD/
ADX, BB breakout/squeeze, RSI/BB mean reversion, potem **Donchian/pullback**/filtr reżimu"*. Donchian
is genuinely different from everything in the catalog in one specific way: **it is a function of
realised extremes, not of an average.** Every existing trend entry in `STRATEGY_CATALOG` fires on a
relationship between two smoothed series (EMA vs EMA, MACD line vs its signal, price vs a Bollinger
band built from a rolling *mean* and *std*). A Donchian channel has no smoothing at all — the upper
band is literally the highest high of the last N bars — so the signal changes state only when price
makes a genuinely new N-bar extreme. That is the property `BB_20_25_breakout` (the catalog's least
bad name, -$168.62 unmasked / -$143.32 one-shot) approximates and Donchian states exactly.

## Hypothesis

A Donchian breakout — enter on a new N-bar extreme, hold until the opposite N-bar extreme — is a
*different kind* of signal from the catalog's smoothed-state family, and its Train-1 per-trade
expectancy, measured with the one-shot entry mask on, is **positive**, or at minimum materially
less negative than the catalog's own one-shot-masked mean of **-$0.985** per trade.

Two sub-claims, tested by the four variants:

1. **N = 20 vs N = 55** (the classic Turtle-system pair: the original Dennis/Eckhardt rules used a
   20-day entry channel with a 55-day channel as the slower, "never miss a big trend" alternative;
   they are cited here because they are the historically-specified pair, not because a grid search
   picked them). If the family has any edge on this basket, the slower channel should show fewer,
   better trades — the 55-bar channel demands a much rarer extreme.
2. **Raw breakout vs pullback-after-breakout.** The breakout bar is the worst possible fill in a
   mean-reverting market: it is by construction an N-bar extreme, so a buyer at that price is buying
   the highest price of the window. Waiting for a retracement to the channel midline and entering
   only when price turns back up through it trades away some of the move for a materially better
   entry price. If the catalog's negative expectancy is *entry-price* driven (paying the extreme),
   the pullback variants beat the breakout variants; if it is *direction* driven (the calls are
   simply wrong), they do not, and all four sit at the same negative number.

**Predicted effect** if the hypothesis holds: at least one variant has positive mean net PnL per
trade on Train 1 under the one-shot mask, `DONCHIAN_PULLBACK_*` beats `DONCHIAN_*` at the same N,
and `*_55` trades far less often than `*_20` with better expectancy per trade.

## Sources

This repo's own prior findings plus one historical citation for the parameter choice:

* `spec/research/F006-hypothesis-one-shot-entry.md` — the one-shot mask semantics this slice runs
  with from the start, the **-$0.985** per-trade bar the falsification condition uses, the -$265.61
  masked / -$363.67 unmasked mean net PnL, and the decision paragraph that commissions this slice.
* `spec/research/F006-hypothesis-cooldown.md`, `spec/research/F006-hypothesis-stop-width.md`,
  `spec/research/F006-hypothesis-entry-regime-filter.md` — the Train-1-only methodology, the fixed
  parameter block (`leverage=1`, `max_sl_pct=0.03`, …), the `EXPECTED_CHECKSUMS` discipline.
* `spec/research/F006-lorentzian-causality.md` — the additive-module + `catalog_entries()` pattern
  reused here, and the truncation-style causality test this slice's fixture test copies.
* `spec/research/F005-validation-protocol.md` — frozen windows (section 3.2), basket and cost
  defaults (section 6), the ten dataset checksums.
* `spec/build.md` — the F006 family list that names Donchian/pullback, and `leverage=1` as the F006
  research placeholder.
* Turtle-system parameter pair (20/55): R. Dennis / W. Eckhardt's original mechanical rules, as
  published in the "Original Turtle Trading Rules" document — System 1 enters on a 20-day breakout,
  System 2 on a 55-day breakout. Cited only to justify *which two N*, nothing else is taken from it
  (no ATR-unit position sizing, no 10/20-day exit channel, no pyramiding).

## Signal definitions (design decisions, fixed before running)

Notation, for a lookback N at bar i, all of it **excluding the current bar** — the channel at bar i
is built from bars `[i-N, i-1]`, i.e. `high.rolling(N).max().shift(1)` and
`low.rolling(N).min().shift(1)`. Nothing in the definition reads bar i's own high/low or any later
bar, so the value at bar i is a function of bars `0..i` only:

```
upper[i] = max(high[i-N .. i-1])
lower[i] = min(low [i-N .. i-1])
mid[i]   = (upper[i] + lower[i]) / 2
```

During the first N bars `upper`/`lower`/`mid` are NaN and every signal below is 0.

### `DONCHIAN_20`, `DONCHIAN_55` — raw breakout (persistent state)

```
dir[i] = +1                if close[i] >  upper[i]
       = -1                if close[i] <  lower[i]
       = dir[i-1]          otherwise          (carry the previous nonzero state; 0 before the
                                               first breakout)
```

Strict inequalities. The carry-forward is the same convention as every existing catalog trend entry
(`sig_ema_cross` and friends hold their state until the opposite condition fires), which is what
makes the one-shot mask meaningful: one contiguous run of `dir` = one directional call.

> **Correction to this pre-registered paragraph, made while implementing it** (left visible rather
> than edited away): the paragraph originally said that a bar satisfying *both* conditions resolves
> short "by evaluation order — an arbitrary tie-break". That was wrong. `upper[i] >= lower[i]`
> always (the max of a window's highs cannot be below the min of its lows), and the rule compares a
> single scalar `close[i]` against both bands, so `close > upper AND close < lower` is
> **unreachable**. There is no tie to break and the evaluation order is irrelevant. The test
> `test_upper_is_never_below_lower_so_the_two_breakout_conditions_cannot_both_fire` asserts both
> halves of this on the real 600-bar fixture at N=20 and N=55.

### `DONCHIAN_PULLBACK_20`, `DONCHIAN_PULLBACK_55` — pullback-after-breakout

This is the real design decision of this slice, so the whole state machine is written out. `dir` is
exactly the series above. The pullback signal `p` is produced by one left-to-right pass with two
state variables — `armed` (the direction of a breakout call that has not yet been entered, or 0)
and `touched` (whether that armed call has reached the midline yet):

1. **Arm.** On the bar `b` where `dir` *changes* to a nonzero `d` (the first bar of a new
   directional run — exactly the bars `entry_masks.one_shot_entry_mask` marks True on `dir`), set
   `armed = d`, `touched = False`, and set `p[b] = 0`. The previous call's position, if any, is
   closed here: a fresh opposite breakout invalidates the old direction immediately even though the
   new one has not yet earned an entry. **Emitting 0 rather than `-d` is the point of the variant** —
   the breakout bar itself is never an entry.
2. **Touch.** While `armed = +1` and not yet `touched`: the first bar `i > b` with
   `close[i] <= mid[i]` sets `touched = True` (price has pulled back to the midline). Mirrored for
   `armed = -1`: `close[i] >= mid[i]`. `p[i]` is unchanged (still 0) on the touch bar — the touch
   arms the trigger, it does not pull it.
3. **Trigger.** Once `touched`, the first bar `j > i` with `close[j] > mid[j]` (for `armed = +1`;
   `close[j] < mid[j]` for `armed = -1`) sets `p[j] = +1` (resp. `-1`), and `armed` is cleared. The
   entry is the *re-cross* of the midline in the breakout's direction, as specified.
4. **Hold.** After a trigger, `p` carries that value forward on every subsequent bar (same
   persistent-state convention as every other catalog entry) until step 1 fires again — i.e. until
   the **opposite** N-bar extreme is breached. `p` does not exit when price crosses back under the
   midline; only an opposite breakout ends the call.

Two failure modes, both decided here rather than in code comments:

* **A pullback that never completes.** There is **no bar limit** on how long an armed call waits.
  The call stays armed until the opposite breakout (step 1) cancels it, at which point it is
  discarded having never produced a signal, and the opposite direction is armed in its place. The
  alternative — a fixed "wait at most K bars" cap — is rejected deliberately: it introduces a third
  free parameter into a family being tested for the first time, and the breakout regime itself is
  already a natural, parameter-free deadline. Consequence, accepted: a breakout that runs away
  without ever retracing to its midline is **never traded at all** by this variant. That is the
  cost of the "higher-conviction entry" claim and the most likely way the variant loses to the raw
  breakout.
* **A pullback that overshoots through the opposite channel edge.** No special case is needed:
  `close` falling below `lower` *is* the condition for `dir` to flip to -1, so an overshoot through
  the far edge is exactly step 1 firing in the opposite direction. The armed long is cancelled
  unentered and a short is armed. The rule is therefore "an overshoot is a cancellation, never a
  fill" — the variant never buys a failed breakout on the way down.

Both failure modes are asserted on hand-built fixtures in `tests/test_donchian.py`; they are the
two cases where an implementation is most likely to silently do something else (enter late at a bad
price, or enter in the wrong direction).

### Interaction with the one-shot mask

The mask is built from **each variant's own signal**, via `entry_masks.one_shot_entry_mask`
(unchanged, reused, not reimplemented), so for the pullback variants a "call" is a run of `p`, not
of `dir` — the canceled-unentered calls simply never appear. For the raw breakout variants a call
is a run of `dir`. In both cases the mask means the same thing it did in the prior note: at most one
executed entry per directional call.

## Falsification condition (stated before running)

This hypothesis is **falsified** if, on the Train-1 sample (4 variants × 5 symbols × 2 intervals,
one-shot mask on, `cooldown_candles=0`):

* **(a)** *none* of the 4 Donchian variants shows positive mean per-trade expectancy
  (net PnL / n_trades, averaged over its 10 series, the same quantity the one-shot note reported),
  **OR**
* **(b)** mean per-trade expectancy is **not** less negative than the existing catalog's own
  one-shot-masked mean of **-$0.985** per trade (`spec/research/F006-hypothesis-one-shot-entry.md`,
  one-shot `cd=0` cell) for **at least 2 of the 4** variants.

Surviving therefore requires both: at least one variant genuinely profitable per trade, and at
least half the family beating the incumbent catalog. Either clause alone falsifies.

Reported either way, not by itself falsifying: the unmasked (control) numbers for the same 40
configurations, so the one-shot mask's effect on this new family is measurable in the same
before/after format as the prior note, and the per-N and breakout-vs-pullback comparisons of the
two sub-claims.

## Method

Same continuous-run methodology, fixed parameter block, data slice and checksum discipline as
`scripts/f006_one_shot_experiment.py` (itself `scripts/f006_cooldown_experiment.py`, itself
`scripts/f006_stop_width_experiment.py` at its `max_sl_pct=0.03` row). **No engine change**, and no
existing line of `strategy.py` changed: `donchian.py` is a new module registered by two lines
appended to the bottom of `strategy.py`, exactly the `lorentzian.py` pattern.

- **Signals**: `donchian.py`, four new catalog entries. `donchian_channel` is
  `high.rolling(N).max().shift(1)` / `low.rolling(N).min().shift(1)`, so the current bar is excluded
  from its own channel. `sig_donchian_breakout` is the persistent state; `sig_donchian_pullback` is
  the ARM/TOUCH/TRIGGER/HOLD machine written out above. Pure OHLC, no `add_indicators` columns, no
  third-party dependency — so unlike the Lorentzian and one-shot experiments this runs in **one
  pass on one interpreter**, with no `.venv_lorentzian` rebuild needed.
- **Script**: `scripts/f006_donchian_experiment.py`.
- **Grid**: 4 variants × 5 symbols × 2 intervals × mask ∈ {one-shot, none} = **80 runs**, all at
  `cooldown_candles=0`. The unmasked arm runs in the same process over the same frames.
- **Harness control, 40 further runs reported separately**: `EMA_8_21` (the catalog's canonical
  persistent state) and `BB_20_25_breakout` (its least-bad name, and the nearest incumbent in kind
  to a Donchian breakout) re-run here under both mask modes. The falsification condition compares
  against a number stored in another note, produced by another script; these 40 rows are what make
  that comparison legitimate instead of assumed.
- **Masks**: built by `entry_masks.one_shot_entry_mask` over
  `entry_masks.strategy_signal_series(...)` — the merged helper, reused unmodified, so a "call" here
  means exactly what it meant in the one-shot note.
- **Fixed**: `leverage=1`, `max_sl_pct=0.03`, `atr_multiplier=1.5`, `activate_pct=0.03`,
  `trail_pct=0.02`, `initial_equity=500`, `stake=100`, `commission_rate_bps=10`,
  `half_spread_bps=5`, `slippage_bps=2`, `now` pinned to `2025-03-01T00:00:00Z`.
- **Data**: `data_contract.load_dataset("data_cache", …, "2024-01-26T00:00:00Z",
  "2026-09-01T00:00:00Z")`, all ten checksums verified in-script against
  `spec/research/F005-validation-protocol.md` section 6, then sliced to
  `[2024-01-26T00:00:00Z, 2025-03-01T00:00:00Z)` — warm-up + Train 1 only — before `run_backtest`
  sees it. No network fetch.
- **Recorded per run**: net PnL, win rate, n_trades, max_drawdown_pct, `survived`, `n_calls`,
  `gross_pnl`, `total_costs`, exit-reason counts, mean bars held, and the sum/count of winning and
  losing trades — the last of these so that a negative expectancy can be *decomposed* (too few
  winners vs winners too small) rather than merely restated.

**Discriminating checks, run before and alongside the grid:**

1. **The signal fires on the bar the rule says, and only there** (`tests/test_donchian.py`, 17
   tests). Hand-built n=3 OHLC fixtures with the full expected array per bar: the breakout state
   changes at exactly bars 4 and 9, the pullback enters at exactly bars 7 and 12 and is flat on
   both breakout bars. **Sabotage-and-restore on four mutations**: dropping `.shift(1)` from the
   channel fails 8 of 17; entering at the ARM bar instead of the midline re-cross fails 4; letting
   an armed call survive the opposite breakout fails 2; allowing TOUCH and TRIGGER on the same bar
   (`elif` → `if`) fails 4. All four restored.
2. **No lookahead**, the check `tests/test_lorentzian.py` applies to the Lorentzian adapter:
   truncating the 600-bar fixture at bar i+20 moves **0** values at bar i, for both variants × both
   Turtle lookbacks × three cut points.
3. **Both pre-registered failure modes are asserted, not assumed**: a breakout that never retraces
   produces **no** entry for the rest of the series, and an overshoot through the far channel edge
   cancels the call — tested both after a touch and before any touch, with a following bounce back
   through the midline that a still-armed long would wrongly fill.
4. **Additive-only at value level, not name level**: all **79** pre-existing catalog entries hash
   bit-identically to the commit before `donchian.py` was wired in
   (`tests/fixtures/catalog_fingerprints_pre_donchian.json`); the catalog is 79 + 2 Lorentzian + 4
   Donchian = **85**.
5. **The harness reproduces the note it is being compared against**: all **40** harness-control rows
   match `output/f006_one_shot/summary/results.csv` on net_pnl, win_rate, n_trades,
   max_drawdown_pct, final_equity **and** n_calls. **0 mismatches.**
6. **On the real grid**: `n_trades ≤ n_calls` holds for **40/40** masked Donchian runs and is
   violated by **40/40** unmasked ones — the highest re-entry rate measured anywhere in F006.

## Run_id

`scripts/f006_donchian_experiment.py`, `git_commit_parent =
b7441d931b1416629e608a5b92cd81fcc721d1b7`, `run_timestamp_utc = 2026-09-23T12:13:59Z`, Python 3.9.25,
pandas 2.3.3, `n_runs = 120` (80 grid + 40 harness control), `elapsed_seconds = 51.1`. Full
parameters, checksums, cross-checks and aggregate tables:
`output/f006_donchian/summary/manifest.json`. Per-run results, 120 rows:
`output/f006_donchian/summary/results.csv`. The run is deterministic — it was executed twice (once
before the win/loss decomposition columns were added) and every shared figure is identical.

## Result

**Falsified, on both clauses, without ambiguity.** 0 of 80 runs is profitable. 0 of 80 has positive
per-trade expectancy. No variant beats the catalog's own one-shot-masked -$0.985 per trade.

| Variant (one-shot, cd=0) | Mean net PnL **per trade** | Positive? | Beats the -$0.985 bar? |
| --- | ---: | :-: | :-: |
| `DONCHIAN_20` | -$1.010 | no | no |
| `DONCHIAN_55` | -$1.119 | no | no |
| `DONCHIAN_PULLBACK_20` | -$1.261 | no | no |
| `DONCHIAN_PULLBACK_55` | -$1.068 | no | no |

Clause (a) — no variant positive — is met. Clause (b) — fewer than 2 of 4 beat the bar — is met with
**0 of 4**. Per series rather than per variant, 15 of the 40 masked runs beat the -$0.985 bar (3 to
4 of 10 for each variant), so this is a property of the family, not one bad symbol.

**Aggregate means, 40 (symbol, interval, variant) series per cell, against the prior note's
120-series catalog cells:**

| Cell | Mean net PnL | Mean net PnL **per trade** | Mean win rate | Mean n_trades | Trades per call | Mean max DD | Survived | Positive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| catalog control, `cd=0` (prior note) | -$363.67 | -$1.078 | 28.75% | 372.6 | 1.217 | 72.95% | 29/120 | 0/120 |
| catalog one-shot, `cd=0` (prior note) | -$265.61 | **-$0.985** | 31.18% | 324.4 | 0.764 | 53.64% | 89/120 | 0/120 |
| **Donchian control, `cd=0`** | -$363.25 | -$1.265 | 32.06% | 291.7 | **7.04** | 73.00% | 12/40 | 0/40 |
| **Donchian one-shot, `cd=0`** | **-$75.79** | -$1.115 | 36.76% | **75.0** | 1.00 | **15.86%** | **40/40** | 0/40 |

**The one-shot mask has by far its largest effect here — and it is almost entirely a trade-count
effect.** Net PnL improves by **$287.46**, 79% of the deficit, against $98.06 (27%) for the
catalog; but trades fall by **74%** against the catalog's 13%, and per-trade expectancy moves only
-$1.265 → -$1.115 (11.9%), ending up **worse** than the catalog's masked -$0.985. This is exactly
the caveat `spec/research/F006-hypothesis-cooldown.md` applied to itself and
`spec/research/F006-hypothesis-one-shot-entry.md` escaped: fewer trades, not better ones.

The reason the mask matters so much here is measurable rather than speculative. Donchian calls are
the **longest-lived signals in the repo**: `DONCHIAN_55` makes 20.0 directional calls over 2,400
4h Train-1 bars (one call per ~120 bars, ~20 days), and the unmasked engine turns each into **14.1**
executed trades. Unmasked trades-per-call by variant and interval:

| Variant | 4h | 1h |
| --- | ---: | ---: |
| `DONCHIAN_20` | 6.24 | 1.68 |
| `DONCHIAN_55` | **14.14** | 4.49 |
| `DONCHIAN_PULLBACK_20` | 6.88 | 2.14 |
| `DONCHIAN_PULLBACK_55` | **15.68** | 5.07 |

For comparison the catalog's mean is 1.217 and the worst case the Lorentzian note found was 4.46.

**The two sub-claims both fail, and one fails in the informative direction.**

| | `DONCHIAN_20` | `DONCHIAN_55` | `DONCHIAN_PULLBACK_20` | `DONCHIAN_PULLBACK_55` |
| --- | ---: | ---: | ---: | ---: |
| Mean net PnL (one-shot) | -$126.06 | -$48.26 | -$95.77 | **-$33.07** |
| Per-trade (mean of ratios) | **-$1.010** | -$1.119 | -$1.261 | -$1.068 |
| Per-trade (pooled) | -$0.984 | -$1.014 | -$1.102 | **-$0.889** |
| Pooled win rate | 37.00% | 39.08% | 37.63% | **44.09%** |
| Mean n_trades | 128.1 | 47.6 | 86.9 | **37.2** |
| Mean max DD | 26.00% | 10.25% | 19.82% | **7.35%** |

* **N=55 vs N=20**: the slower channel does trade far less (47.6 vs 128.1) and loses far less in
  total, but it is **not better per trade** — `DONCHIAN_55` is *worse* than `DONCHIAN_20` on both
  the mean-of-ratios (-$1.119 vs -$1.010) and the pooled (-$1.014 vs -$0.984) measure. The
  prediction "rarer extreme ⇒ better trade" is wrong.
* **Pullback vs breakout**: at N=20 the pullback is clearly **worse** per trade (-$1.261 vs
  -$1.010); at N=55 it is modestly better (-$1.068 vs -$1.119, pooled -$0.889 vs -$1.014). What the
  pullback filter reliably does is raise the win rate (+0.6 to +5.0 pp) while cutting trades by
  ~25% — it does *not* reliably improve expectancy. **So the negative expectancy is not explained by
  paying the extreme on the breakout bar**, which was the sharper of the two sub-claims.

**The decomposition, which is the part of this run worth keeping.** Recording winners and losers
separately turns "negative expectancy" into a statement about geometry (all figures pooled over
every trade in the one-shot cell):

| Name (one-shot, cd=0) | Win rate | Avg win | Avg loss | Reward/risk | Win rate needed to break even | **Gap** |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `DONCHIAN_20` | 37.00% | $1.459 | -$2.419 | 0.603 | 62.38% | 25.4 pp |
| `DONCHIAN_55` | 39.08% | $1.483 | -$2.615 | 0.567 | 63.81% | 24.7 pp |
| `DONCHIAN_PULLBACK_20` | 37.63% | $1.407 | -$2.616 | 0.538 | 65.03% | 27.4 pp |
| `DONCHIAN_PULLBACK_55` | 44.09% | $1.554 | -$2.815 | 0.552 | 64.44% | 20.4 pp |
| `BB_20_25_breakout` (control) | 36.19% | $1.411 | -$2.416 | 0.584 | 63.13% | 26.9 pp |
| `EMA_8_21` (control) | 29.54% | $1.368 | -$1.697 | 0.806 | 55.36% | 25.8 pp |
| **all Donchian, 4h** | 32.82% | $1.050 | -$2.419 | **0.434** | **69.74%** | **36.9 pp** |
| **all Donchian, 1h** | 39.75% | $1.545 | -$2.588 | 0.597 | 62.63% | 22.9 pp |

Every name, old and new, is **20 to 27 percentage points short of its own breakeven win rate**, and
the reason is the same everywhere: **the average winner is roughly 0.55-0.60 of the average loser.**
At 4h it is 0.43, which is why 4h expectancy (-$1.281 pooled) is so much worse than 1h (-$0.946)
despite 4h having the better drawdown profile.

This is not a cost effect. Cost per trade is **$0.320** in every cell of this run (identical to all
four cells of the one-shot note), and **pooled gross PnL per trade is -$0.691** — with zero
commission, zero spread and zero slippage the family still loses $0.69 per trade. Costs are 32% of
the loss; removing them entirely would not make any variant positive.

Nor is it the signal changing its mind. Exit-reason mix over all masked Donchian trades: **39.2%
`initial_sl`, 47.0% `trailing_sl`, 13.7% `signal_reverse`**, mean holding time **13.8 bars**. 86%
of trades are closed by the engine's stop machinery. At 4h under the mask, `DONCHIAN_55` holds a
position for a mean of 5.0 bars inside a directional call that lasts ~120 bars — the one-shot rule
converts a slow regime signal into a single short-horizon bet on the bars immediately after the
breakout, and it is that bet, not the regime call, that these numbers measure.

**The one genuinely new high-water mark, stated with its sample size.** `DONCHIAN_PULLBACK_55` is
the best-behaved name ever measured in F006 by risk: mean net PnL -$33.07, mean max drawdown 7.35%,
**40/40 Donchian runs survived** (against 89/120 for the catalog's best single-lever cell), and the
single best run in the grid is `DONCHIAN_PULLBACK_55`/BTCUSDT/4h at **-$9.40** with a 50.0% win
rate — better than the previous F006 best single run of -$33.01. It is also **12 trades over a
year**. At $0.32 of cost per trade that run's entire loss is $3.84 of costs plus $5.56 of gross; it
is not evidence of anything, and it is recorded here so that it is not later mistaken for a find.

## Decision

**The invariant holds. A genuinely different generator — unsmoothed, extreme-based, with a
higher-conviction entry variant, run with the best entry rule F006 has found — lands in the same
place as everything before it: negative per-trade expectancy on every variant, every symbol, every
interval, 0 profitable runs out of 80.** Six hypotheses and two alternative generators have now
been tested on Train 1 and none has produced a single positive-expectancy configuration.

Saying it plainly, as the ticket asks: **catalog expansion is exhausted as a route to edge, and
this note is the evidence for stopping it.** The Donchian family was the strongest remaining
candidate on the `spec/build.md` list precisely because it is *not* another smoothed-state
variation, and it changed nothing that matters. Adding RSI/BB mean-reversion names, or more
Donchian lookbacks, or a fifth EMA pair, would sample the same measured invariant again at the cost
of another Train-1 slice. **Recommendation: do not spend the next slice on another signal family.**

Widening the symbol basket is also not the answer, and this run says so with data rather than
assertion: the invariant reproduces across 5 symbols × 2 intervals × 6 names here, with per-series
expectancy negative in 40 of 40 masked runs. A basket that included more symbols would need every
one of them to behave unlike all five current ones.

**What this run actually found, and what F006 should test next.** The decomposition above is the
first F006 measurement that explains *why* expectancy is negative rather than restating that it is:
the average winner is 0.55-0.60 of the average loser, so **every name needs a ~63% win rate to break
even and none of them gets past 44%.** That ratio is not a property of any signal. It is set by the
exit geometry, and the exit geometry is the one degree of freedom F006 has **never** varied:
`activate_pct=0.03` / `trail_pct=0.02` are hard-coded identically in
`scripts/f006_stop_width_experiment.py`, `f006_regime_filter_experiment.py`,
`f006_cooldown_experiment.py`, `f006_lorentzian_experiment.py`, `f006_one_shot_experiment.py` and
this one. The stop-width slice swept `max_sl_pct` — the **loss** side — and found nothing; the
**win** side has never been touched. A trade must gain 3% before the trail even activates, then
gives back 2% of its best price; that is a mechanism that systematically produces small winners
next to full-width -3% losers, and it is consistent with the measured $1.46 vs -$2.55.

So the next slice should be: **sweep `activate_pct` × `trail_pct` (including "no trailing stop at
all", and a fixed take-profit at a multiple of the initial stop distance) on a small name sample
with the one-shot mask on, and read reward/risk and breakeven-win-rate gap, not net PnL, as the
outcome.** It is falsifiable in the same shape as this note: if the reward/risk ratio stays near
0.6 across the whole sweep, then the ratio is a property of this basket's price action rather than
of the exit rules, and that — not another generator — is the finding that should force F006 to
revisit its assumptions (leverage=1 with a $100 stake, 4h/1h bars, these five symbols, this
cost model) from the top.

**What is reusable regardless of that outcome:**

* `donchian.py` and its four catalog entries are merged, tested (17 tests, 4 sabotages), causal by
  construction and free of any third-party dependency — available to any later slice at no cost.
* `scripts/f006_donchian_experiment.py`'s **harness control** pattern: re-running two incumbent
  names inside the new experiment and diffing them against the prior note's stored rows (40/40
  exact) is cheap and makes cross-note comparisons legitimate rather than assumed. Every future
  F006 script should do this.
* The win/loss decomposition columns (`sum_wins`/`n_wins`/`sum_losses`/`n_losses`, exit-reason mix,
  mean bars held) cost nothing to record and are what turned this run from "another negative
  result" into a specific, testable next hypothesis. Prior F006 scripts did not record them.

**Falsification verdict, restated for the record**: hypothesis **falsified**. Clause (a) met (no
variant positive), clause (b) met (0 of 4 beat -$0.985). Both sub-claims rejected: the 55-bar
channel is not better per trade than the 20-bar one, and the pullback entry does not beat the raw
breakout except marginally at N=55.

## Tests

`tests/test_donchian.py` (17 new tests) is described under "Method", check 1. Full suite on the
Python 3.9 `.venv_test` interpreter, before and after this slice:

| | Baseline (this slice's tests excluded) | With this slice |
| --- | --- | --- |
| `pytest tests/` | 95 passed, 5 skipped | **112 passed, 5 skipped** |

Exactly the 17 new tests, no behaviour change in any existing test. The baseline was re-measured in
this worktree before `donchian.py` was written, not copied from the prior note. The Python 3.11
`.venv_lorentzian` interpreter was not needed and not used: `donchian.py` has no advanced-ta
dependency.
