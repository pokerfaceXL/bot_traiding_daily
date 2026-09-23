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

## Method

Same continuous-run methodology, fixed parameter block, data slice and checksum discipline as
`scripts/f006_cooldown_experiment.py` (itself `scripts/f006_stop_width_experiment.py` at its
`max_sl_pct=0.03` row). **No engine change was needed or made**, which was the first thing checked:
`entry_regime_mask` gates exactly step 4 of the loop ("queue an entry for the next bar's open"), so
setting it True on a call's first bar and False everywhere else expresses "at most one entry per
call" directly — the mask is static, the engine is untouched, and a bar that is ineligible stays
ineligible no matter how the previous position exited.

- **Mask construction**: new module `entry_masks.py`, `one_shot_entry_mask(signal)`. A bar is
  eligible iff `signal != 0` and `signal != signal.shift(1)` (with "before the series starts"
  treated as flat). `strategy_signal_series` reproduces the engine's own pipeline —
  `data_contract.filter_closed_candles(interval, now)` → `strategy.add_indicators` →
  `STRATEGY_CATALOG[name]` — so the mask index matches the frame `run_backtest` builds and the
  engine's `reindex(...).fillna(False)` is a no-op rather than a silent block.
- **Script**: `scripts/f006_one_shot_experiment.py`.
- **Grid**: mask ∈ {one-shot, none} × `cooldown_candles` ∈ {0, 50} × 12 signal names × 5 symbols ×
  2 intervals = **480 runs**. The unmasked control runs in the same process over the same frames,
  so nothing in the comparison depends on the other notes' stored numbers. The 12 names are the
  10-strategy sample of `spec/research/F006-hypothesis-stop-width.md` plus `LORENTZIAN_default` and
  `LORENTZIAN_raw`.
- **Fixed**: `leverage=1`, `max_sl_pct=0.03`, `atr_multiplier=1.5`, `activate_pct=0.03`,
  `trail_pct=0.02`, `initial_equity=500`, `stake=100`, `commission_rate_bps=10`,
  `half_spread_bps=5`, `slippage_bps=2`, `now` pinned to `2025-03-01T00:00:00Z`.
- **Data**: `data_contract.load_dataset("data_cache", …, "2024-01-26T00:00:00Z",
  "2026-09-01T00:00:00Z")`, all ten checksums verified in-script against
  `spec/research/F005-validation-protocol.md` section 6, then sliced to
  `[2024-01-26T00:00:00Z, 2025-03-01T00:00:00Z)` — warm-up + Train 1 only — before `run_backtest`
  sees it. No network fetch. Regularity deliberately not computed (Train-only exploration).
- **Recorded per run**: net PnL, win rate, n_trades, max_drawdown_pct, `survived = final_equity ≥
  $100`, plus `gross_pnl`, `total_costs`, `n_initial_sl_exits` and **`n_calls`** (the number of
  directional calls in that series) — `n_calls` is what makes "trades per call" measurable instead
  of inferred.
- **Two passes, one schema**: `--catalog` (400 runs) on Python 3.9 `.venv_test`, `--lorentzian`
  (80 runs) on a standalone Python 3.11 `.venv_lorentzian` rebuilt by the recipe in
  `spec/research/F006-lorentzian-causality.md`, then `--merge`.

**Discriminating checks, run before and alongside the grid:**

1. **Mask construction, unit-tested against a fixture with a known run structure**
   (`tests/test_entry_masks.py`, 11 tests). Signal `[0,1,1,1,0,1,1,-1,-1,0,-1]` must produce mask
   `[F,T,F,F,F,T,F,T,F,F,T]`: the two boundary cases that are easy to get wrong are pinned
   separately — a return to the **same** direction after a flat gap is a **new** call (idx 5), and
   a direct `+1 → -1` flip with no flat bar between is a new call (idx 7). NaN is flat, as it is in
   the engine. **Sabotage-and-restore**: shifting the mask by one bar fails 7 of 11 tests, and
   treating the flat-gap return as a continuation (forward-filled direction state) fails 4 of 11,
   including the two named boundary tests. Both were then restored.
2. **End-to-end in the engine, not just in the mask**: a test runs `EMA_8_21` (a persistent
   always-in-market state, the exact shape this hypothesis is about) through `run_backtest` with
   and without the mask and asserts every trade's *queue* bar is an eligible bar and no two trades
   share a call id.
3. **On the real grid**: `n_trades ≤ n_calls` holds for **240/240** masked runs and is violated by
   **78/240** unmasked runs — the rule is doing on real data what the fixture says it does.
4. **Control rows reproduce the prior experiments exactly**: all **240** unmasked rows matched
   their stored counterparts on net_pnl, win_rate, n_trades, max_drawdown_pct and final_equity —
   100 catalog + 20 Lorentzian `cd=0` rows against `output/f006_stop_width/summary/results.csv` and
   `output/f006_lorentzian/summary/results.csv`, and 100 + 20 `cd=50` rows against
   `output/f006_cooldown/summary/results.csv`. **0 mismatches.**

## Run_id

`scripts/f006_one_shot_experiment.py`, `git_commit_parent =
b89d6455c3bb62814b580ec933a30853013b1c14`, `n_runs = 480`. Catalog pass: `run_timestamp_utc =
2026-09-23T09:20:14Z`, Python 3.9.25, 400 runs, `elapsed_seconds = 146.2`. Lorentzian pass:
`run_timestamp_utc = 2026-09-23T09:28:57Z`, Python 3.11.16 + advanced-ta 0.1.8, 80 runs,
`elapsed_seconds = 43.8`. pandas 2.3.3 in both. Full parameters, checksums, cross-checks and
aggregate tables: `output/f006_one_shot/summary/manifest.json`. Per-run results, 480 rows:
`output/f006_one_shot/summary/results.csv` (per-pass: `results_catalog.csv`,
`results_lorentzian.csv`).

## Result

**Aggregate means, 120 (symbol, interval, signal) series per cell:**

| Cell | Mean net PnL | Δ vs control | Mean net PnL **per trade** | Mean win rate | Mean n_trades | Trades per call | Mean max DD | Survived | Positive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| control, `cd=0` | -$363.67 | — | -$1.078 | 28.75% | 372.6 | 1.217 | 72.95% | 29/120 | 0/120 |
| control, `cd=50` (the bar) | **-$215.40** | +$148.27 | -$1.010 | 29.37% | 279.0 | 0.608 | 43.49% | 98/120 | 0/120 |
| **one-shot, `cd=0`** | **-$265.61** | **+$98.06** | **-$0.985** | **31.18%** | 324.4 | 0.764 | 53.64% | 89/120 | 0/120 |
| one-shot, `cd=50` | **-$171.79** | +$191.88 | -$0.958 | 31.32% | 241.2 | 0.466 | 34.93% | 110/120 | 0/120 |

The control rows reproduce `spec/research/F006-hypothesis-cooldown.md` to the cent (-$363.67 and
-$215.40), so the comparison is exact rather than approximate.

**Against the falsification condition, honestly: the stated condition IS met, and the hypothesis is
falsified on its primary criterion.** One-shot at `cooldown_candles=0` improves the baseline by
**$98.06** — a real improvement, but **less than the $148.27** that a plain `cooldown_candles=50`
already achieved. The prediction that removing *every* stale re-entry would beat a fixed 50-bar
delay is wrong: at 4h, 50 bars is over 8 days, long enough to suppress not just the stale re-entry
but most of the *next* call too, so cooldown simply cuts more trades (279.0 vs 324.4) than the
one-shot rule does.

**The second clause of the falsification condition, however, is *not* met — and this is the part
that differs from every prior F006 note.** The improvement is not "trading less with nothing else
changing":

| | control `cd=0` → `cd=50` | control `cd=0` → one-shot `cd=0` |
| --- | ---: | ---: |
| Δ net PnL | +$148.27 | +$98.06 |
| Δ n_trades | -93.6 (-25%) | **-48.2 (-13%)** |
| Δ win rate | +0.62 pp | **+2.43 pp** |
| Δ net PnL per trade | +$0.068 (+6.3%) | **+$0.093 (+8.6%)** |
| Δ per-trade, **4h only** | **-$0.006 (flat)** | **+$0.066 (+5.2%)** |
| of Δ that is saved costs / gross PnL | $29.97 / $118.31 | $15.45 / $82.61 |

One-shot buys **two thirds of cooldown's PnL gain with half the trade reduction**, and it is the
first lever in F006 to move per-trade expectancy at 4h at all — the slice where
`spec/research/F006-hypothesis-cooldown.md` found expectancy dead flat (-$1.260 → -$1.266) while
producing 63.7% of its gain. Under one-shot, 4h expectancy moves to -$1.194 and 4h win rate from
25.57% to 29.33%. Mean cost per trade is $0.32 in all four cells, so this is not the
smaller-notional-near-the-floor confound.

**The mechanism check that cooldown failed, one-shot passes.** The hypothesis says the gain should
track the *re-entry rate* — trades per call in the unmasked control — and not merely trade volume.
Across the 120 series, Spearman correlation between unmasked trades-per-call and the one-shot gain
is **0.893** (Pearson 0.852); for cooldown=50 it is 0.755 (Pearson 0.615). Split on the same
quantity:

| Series group | n | control `cd=0` | control `cd=50` | one-shot `cd=0` | one-shot beats `cd=50` |
| --- | ---: | ---: | ---: | ---: | ---: |
| trades/call > 1.5 (re-entry chains) | 31 | -$392.55 | -$129.53 | -$167.43 | 11/31 |
| trades/call ≤ 1.0 (flickering signal) | 57 | -$375.42 | -$299.71 | -$351.70 | — |

**Where the mechanism exists, the fix works; where it does not, the mask is nearly a no-op.** The
sharpest single case is the one that motivated the whole line of work — `LORENTZIAN_default` at 4h,
the series where `spec/research/F006-lorentzian-causality.md` measured 4-5 trades per directional
call:

| `LORENTZIAN_default`, 4h | n_calls | n_trades | Net PnL | Win rate |
| --- | ---: | ---: | ---: | ---: |
| control `cd=0` | 66.0 | 294.4 (4.46/call) | -$382.08 | 27.23% |
| control `cd=50` | 66.0 | 81.2 | -$107.69 | 28.91% |
| **one-shot `cd=0`** | 66.0 | **66.0 (exactly 1/call)** | **-$79.22** | **33.04%** |
| one-shot `cd=50` | 66.0 | 39.0 | -$47.56 | 31.63% |

The counterpart at the other end: at 1h the signals *flicker* — 934 calls per series on average
against 455 executed trades (0.49 trades per call) — so there is no stale-re-entry to remove, and
the mask does almost nothing (-$375.64 → -$336.02). It even *increases* 1h trade count (455.5 →
472.0): skipping a mid-call re-entry leaves the engine flat and therefore eligible when the next
call's first bar arrives, where the unmasked run was still holding a position. `STOCH14_cross` is
the degenerate case (3966 calls per 1h series, 0.19 trades/call): net PnL changes by **$0.01**.

**Per-strategy net PnL, mean over 10 series:**

| Strategy | control `cd=0` | control `cd=50` | one-shot `cd=0` | one-shot `cd=50` | Δ one-shot | Δ `cd=50` | one-shot beats `cd=50`? |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | :-: |
| `LORENTZIAN_default` | -$384.99 | -$202.29 | **-$162.64** | -$105.28 | +$222.35 | +$182.70 | **yes** |
| `EMA_8_21` | -$399.02 | -$246.22 | **-$223.82** | -$147.50 | +$175.20 | +$152.80 | **yes** |
| `TS_13_34_200_14` | -$365.91 | -$163.85 | -$221.98 | -$112.42 | +$143.93 | +$202.06 | no |
| `EMA_13_34_RSI14_55` | -$379.46 | -$190.60 | -$259.95 | -$136.32 | +$119.51 | +$188.86 | no |
| `RSI14_7030` | -$362.75 | -$117.83 | -$250.18 | -$111.50 | +$112.57 | +$244.92 | no |
| `LORENTZIAN_raw` | -$401.03 | -$267.90 | -$310.78 | -$232.48 | +$90.25 | +$133.13 | no |
| `MACD_12_26_hist` | -$401.56 | -$267.71 | -$319.12 | -$212.74 | +$82.44 | +$133.85 | no |
| `MACD_RSI14_50` | -$393.22 | -$245.49 | -$311.18 | -$192.35 | +$82.04 | +$147.73 | no |
| `ADX14_DI_20` | -$400.65 | -$271.36 | -$326.26 | -$241.02 | +$74.39 | +$129.29 | no |
| `BB_20_2_RSI14` | -$306.23 | -$169.38 | -$257.43 | -$152.11 | +$48.80 | +$136.85 | no |
| `BB_20_25_breakout` | -$168.62 | -$106.11 | -$143.32 | -$95.05 | +$25.30 | +$62.51 | no |
| `STOCH14_cross` | -$400.64 | -$336.01 | -$400.63 | -$322.77 | +$0.01 | +$64.63 | no |

One-shot improves **102 of 120 series**. It is worse on 18 — every one of them a series with
unmasked trades/call < 1.0 (the retiming effect described above), and every one of them by a
trivial amount: the worst is -$2.32, the median -$0.89. It beats `cd=50` on only **31 of 120** and on
**2 of 12 names** — exactly the two names with the highest measured re-entry rate. Per-strategy
per-trade expectancy improves under one-shot for **12 of 12** names (+$0.017 to +$0.156), versus
cooldown's 12 of 12 at a smaller mean and a flat 4h.

**The two levers partly compound.** `one-shot × cd=50` is the best cell measured anywhere in F006:
-$171.79 mean, max DD 34.93%, 110/120 survived, and the best single run in the grid is
`EMA_8_21`/BTCUSDT/4h at **-$33.01** (the cooldown sweep's best was -$43.48). They are not additive
($191.88 against $148.27 + $98.06 = $246.33), as expected: both gates block overlapping sets of
re-entries.

**And the invariant holds.** **0 of 480 runs is profitable. 0 of 480 has positive per-trade
expectancy.** Five F006 hypotheses have now been tested on Train 1 — wider stops, an ADX entry
filter, a different generator, time-based cooldown, and now one-shot flip entry — and mean net PnL
per trade is negative for every signal name under every setting tried. One-shot moves expectancy
by 8.6%; closing the gap to zero would need roughly twelve times that.

## Decision

**The re-entry question is now settled, and the answer is "yes, re-entry into stale calls is real
and measurable, and removing it is still not an edge."**

What was established, and is reusable:

* One-shot-per-call is expressible with **no engine change** — `entry_regime_mask` is sufficient;
  `entry_masks.one_shot_entry_mask` + `tests/test_entry_masks.py` are 60 lines and now part of the
  repo, available to any future experiment that wants flip-only entry semantics.
* The wasteful-re-entry mechanism is **real and quantified**: trades-per-call is 1.22 on average,
  4.46 for `LORENTZIAN_default` at 4h, and removing the excess recovers $98.06 of a $363.67 deficit
  while improving per-trade expectancy by 8.6% and win rate by 2.43 pp. Unlike cooldown, the gain
  **tracks the re-entry rate** (Spearman 0.893) — this is the first F006 result whose stated
  mechanism survives its own secondary check.
* It is nonetheless **not the better lever by total PnL**: a fixed `cooldown_candles=50` recovers
  more ($148.27) by the cruder route of simply trading 25% less. One-shot is the better lever by
  *quality* per trade, and the two together (-$171.79) beat either alone.
* Practical measurement recommendation, extending the cooldown note's: Train experiments on this
  basket at 4h are best run with the one-shot mask **and** `cooldown_candles=50` — 110/120 survive,
  max DD 34.93%, so differences between signal generators stay visible instead of being censored at
  the ~$100 bankruptcy floor.

What was not established: any path to positive edge. This hypothesis was the sharpest remaining
test of the "the engine is wasting a good signal" theory, and it comes back with a clear verdict:
the engine *was* wasting trades, removing that waste helps a measurable amount, and the underlying
signals are still negative-expectancy after it is removed. The prediction made in the cooldown
note's own next-slice section — "the per-trade expectancy measured here predicts it will also fail
to produce positive edge" — is confirmed, with the refinement that expectancy did move (it just
moved ~8%, not ~1200%).

**Next slice: a different generator family, per the cooldown note's option (2) and
`spec/build.md`'s Donchian breakout / pullback.** Four levers around the entry loop (stop width,
ADX regime filter, cooldown, one-shot) and one alternative generator (Lorentzian, at defaults) have
now been tested; the per-trade-expectancy invariant is a statement about the **signals**, not about
the engine wrapped around them, and no further reshaping of *when* these particular signals are
entered is worth Train budget. Any such new generator should be evaluated with one-shot entry on
from the start, since it is now known to be both cheap and expectancy-improving.

## Tests

`tests/test_entry_masks.py` (11 new tests) is described under "Method". Full suite, both
interpreters, before and after this slice:

| Interpreter | Baseline (this slice's tests excluded) | With this slice |
| --- | --- | --- |
| Python 3.9 `.venv_test` | 84 passed, 5 skipped | **95 passed, 5 skipped** |
| Python 3.11 `.venv_lorentzian` | 87 passed, 2 skipped | **98 passed, 2 skipped** |

Exactly the 11 new tests, no behaviour change in any existing test. The baseline figures were
re-measured in this worktree (`pytest tests/ --ignore=tests/test_entry_masks.py`), not copied from
the prior note.
