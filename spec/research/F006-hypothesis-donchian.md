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

*(filled in after the run)*

## Run_id

*(filled in after the run)*

## Result

*(filled in after the run)*

## Decision

*(filled in after the run)*
