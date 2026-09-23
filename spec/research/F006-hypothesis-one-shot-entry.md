# F006 — Hypothesis: one-shot flip entry (one entry per directional call), Train 1 only

> Sections "Observation" … "Falsification condition" were written and committed to this file
> BEFORE the experiment script was run, per the same discipline as
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

A signal name's raw per-bar signal column — what `strategy.STRATEGY_CATALOG[name](df)` returns
inside `backtest_engine.run_backtest` — is a **persistent state, not an edge**. `EMA_8_21` is +1
on every bar the fast EMA stays above the slow one, and it only changes value on the bar the
underlying condition flips. `spec/research/F006-lorentzian-causality.md` measured the consequence:
at 4h the causal Lorentzian classifier changes directional state **58-76 times** over Train 1
while the engine executes **270-313 trades** — 4 to 5 executed trades per directional call. Step 4
of the engine loop re-queues an entry on the very next bar after any exit, because the state is
still non-zero and `pos == 0`.

`spec/research/F006-hypothesis-cooldown.md` attacked this with the engine's existing
`cooldown_candles` gate and found the largest single-knob effect measured on this catalog so far
(mean net PnL -$363.67 → -$215.40 from cooldown 0 → 50, 40.8% of the deficit, max DD 72.95% →
43.49%, survival 29/120 → 98/120) — but with **flat per-trade expectancy** (-$1.260 → -$1.266 at
4h, where 63.7% of the gain is). Its conclusion: cooldown averages fewer bad trades, it does not
fix selection. Its own "next slice" section names the lever this note tests, and names why it is
different in kind:

* `cooldown_until` is set **only** on an `initial_sl` exit (`backtest_engine.py` step 2), so
  trailing-stop, signal-reversal and end-of-data exits start no cooldown at all;
* a *fixed* window of N bars is both too strong and too weak — it blocks a genuinely new call that
  happens to arrive 10 bars after a stop-out, and it permits a re-entry into the same **stale**
  call once N bars have elapsed.

Define a **call** as one maximal contiguous run of the same nonzero signal value. Then "at most one
entry per call" is exactly the rule that removes re-entry into an unchanged directional call,
regardless of how the previous position exited and regardless of elapsed bars.

## Hypothesis

Gating new entries so that only the **first bar of each call** is eligible — computed directly from
the strategy's own signal series before the backtest runs, passed as the existing
`entry_regime_mask` parameter, with `cooldown_candles=0` — recovers **more** of the Train-1 deficit
than `cooldown_candles=50` did, because it removes every wasteful re-entry into a stale call
regardless of exit reason or elapsed bars, while never delaying a genuinely new call the way a
fixed 50-bar cooldown can.

**Predicted effect**: mean net PnL with the one-shot mask at `cooldown_candles=0` is better than
the recorded cooldown=50 number (-$215.40), trades-per-call falls to ≤1 by construction, and — the
part that actually matters — mean net PnL **per trade** improves rather than staying flat, since
the trades being removed are, on the hypothesis, systematically worse than the first entry into a
call. One-shot and cooldown=50 together should add little over one-shot alone, since a call's first
entry is rarely the one a cooldown would have blocked.

## Sources

This repo's own prior findings only, no external source:
`spec/research/F006-hypothesis-cooldown.md` (the cooldown=0 baseline -$363.67 and the cooldown=50
bar -$215.40 this hypothesis must beat, the per-trade-expectancy caveat, and the engine detail that
cooldown fires only after `initial_sl`), `spec/research/F006-lorentzian-causality.md` (the 4-5
trades-per-directional-call measurement, the `startLongTrade`/`startShortTrade` flip semantics this
mask reproduces, the causal Lorentzian adapter and its Python 3.11 venv recipe),
`spec/research/F006-hypothesis-stop-width.md` and
`spec/research/F006-hypothesis-entry-regime-filter.md` (the 10-strategy sample, the Train-1-only
methodology, the checksum table and the `entry_regime_mask` parameter itself),
`spec/research/F005-validation-protocol.md` (frozen windows section 3.2, basket/cost defaults
section 6), `spec/build.md` (leverage=1 as the F006 research placeholder).

## Falsification condition (stated before running)

This hypothesis is **falsified** if mean net PnL with the one-shot mask at `cooldown_candles=0`
does not improve on the recorded cooldown=0 baseline (-$363.67 across the 12-signal × 5-symbol ×
2-interval Train-1 sample) **by at least as much as `cooldown_candles=50` already achieved**
(-$215.40, i.e. a $148.27 improvement) — **or** if it does improve net PnL but only by trading even
less, with no accompanying improvement in win rate or per-trade expectancy. The second clause is
the caveat every prior F006 note applied to itself: a reduction in trade count is not evidence of
better selection unless expectancy per trade also improves.

A secondary check, reported either way but not by itself falsifying: whether one-shot and
cooldown=50 **compound** (the `one_shot × cd=50` cell beating both single-lever cells by a margin)
or whether one subsumes the other.
