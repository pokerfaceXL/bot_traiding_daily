# F006 — Lorentzian Classification: causality audit + first Train-1 comparison

> Sections "Observation" … "Causality audit" were written BEFORE the adapter was written and
> before any backtest was run, per the same "hypothesis before running" discipline as
> `spec/research/F006-hypothesis-stop-width.md` and `spec/research/F006-hypothesis-entry-regime-filter.md`.
> The audit is based on reading the actual installed source of `advanced-ta==0.1.8`, not on a
> paraphrase of its documentation. "Method", "Run_id", "Result" and "Decision" were filled in
> after the run.
>
> TRAIN-1 ONLY. Per `spec/research/F005-validation-protocol.md` section 7.3, F006 selects on
> train+validation and never opens holdout; this slice restricts itself further, to Train 1
> (`[2024-03-01T00:00:00Z, 2025-03-01T00:00:00Z)`) plus the protocol's own 35-day warm-up buffer
> from `2024-01-26T00:00:00Z`. Validation 1-4 and the Holdout window (2026-03-01 onward) are not
> loaded, not sliced and not looked at by any script in this slice.

## Observation

Two independent single-dimension tuning hypotheses on the existing 79-strategy catalog have now
been falsified on Train 1: stop width (`spec/research/F006-hypothesis-stop-width.md`, 0/400
positive runs) and an ADX14 entry regime filter
(`spec/research/F006-hypothesis-entry-regime-filter.md`, 0/500 positive runs). Combined with
`spec/research/F005-baseline.md` (0/24885 valid months meet the goal) and
`spec/research/F005-leverage-sensitivity.md` (no leverage/cooldown value rescues the catalog),
and with `spec/research/F006-pipeline-positive-control.md` confirming the engine itself computes
a correct positive result on favourable data, the evidence points at the *signal generator*, not
at sizing, exits or filters. `spec/build.md` names the next candidate explicitly: "Priorytet:
Lorentzian Classification z advanced-ta (0.1.8) — odtworzyć wariant referencyjny z dokumentacji,
dodać adapter do wspólnego silnika… Przed rankingiem zbadać przyczynowość".

## Hypothesis

A genuinely different signal generator — the Lorentzian-distance kNN classifier of
`advanced-ta==0.1.8`, at its library defaults, wired as an entry signal into the existing
`backtest_engine.run_backtest` SL/trailing/cost logic — produces Train-1 results that are
*directionally different* from the existing catalog: not necessarily profitable in this first
untuned slice, but different enough (in net PnL, win rate, trade count or drawdown) to justify a
follow-up parameter-tuning slice on Train. **Prerequisite hypothesis, tested first**: the
library's classification can be computed causally, i.e. the value at bar `i` can be made a
function of data up to and including bar `i` only.

## Sources

- PyPI project page and files: <https://pypi.org/project/advanced-ta/> — version **0.1.8**,
  checked **2026-09-23**. Installed artefacts verified by SHA-256 against the hashes PyPI
  publishes: wheel `advanced_ta-0.1.8-py3-none-any.whl` =
  `e4f8a04d1b9b500c32fb70a55959af40b9cfa155e5d992bc4882e157d8d71312`, sdist
  `advanced_ta-0.1.8.tar.gz` =
  `c29194cae57de69baa340381bd73377a2c942b0f43c7895b550bdb0384a3647e`.
- Package source read directly (this is what the audit below is based on):
  `advanced_ta/LorentzianClassification/Classifier.py`, `…/MLExtensions.py`,
  `…/KernelFunctions.py`, `…/Types.py`, `advanced_ta/Utils.py`. Upstream repository per the
  package metadata: <https://bitbucket.org/lokiarya/advanced-ta> (checked 2026-09-23).
- Original Pine Script indicator the package ports, referenced by the package README:
  <https://www.tradingview.com/script/WhBzgfDu-Machine-Learning-Lorentzian-Classification/>
  (@jdehorty, checked 2026-09-23).
- Frozen windows/basket/costs: `spec/research/F005-validation-protocol.md` (sections 3.2 and 6).
- Comparison sample and run discipline: `spec/research/F006-hypothesis-stop-width.md`,
  `scripts/f006_stop_width_experiment.py`.

## Falsification condition (stated before running)

Two separate conditions, checked in order:

1. **Causality.** If the classification at bar `i` cannot be made a function of data up to bar
   `i` only — i.e. if the leakage identified by the audit cannot be removed by changing *how the
   library is called* and would instead require patching the library's internals or changing its
   documented algorithm — then the hypothesis is abandoned at this step and no comparison run is
   reported as a strategy result. A concrete, mechanical check decides this: **the signal at bar
   `i` must be bit-identical whether it is computed on a series ending at bar `i` or on the same
   series extended by 50 further bars.** A signal that changes when future bars are appended is
   disqualified.
2. **Interest.** If the causal signal passes (1), the comparison run is falsifying for the
   *follow-up tuning slice* if `LORENTZIAN_default` on Train 1 is not even directionally
   interesting next to the same 10-strategy sample: i.e. if it is not better than that sample on
   net PnL, and not better on win rate, and not better on drawdown/survival — in that case there
   is nothing to tune towards and the next slice is another generator family, not Lorentzian
   parameter tuning.

Note what is *not* a falsification here: "not profitable on Train 1 at library defaults". This
is the first slice of an open-ended hypothesis, with zero parameter tuning by construction; a
negative-but-clearly-different result is a legitimate reason to tune next.

## Causality audit (written before the adapter, from the installed 0.1.8 source)

### A. What the library actually computes, bar by bar

`LorentzianClassification.__init__(data, features, settings, filterSettings)` copies the frame
and immediately calls `__classify()`; there is no `fit`/`predict` split and no incremental/online
API. Everything is computed once, in batch, over whatever frame is passed in. Defaults, from
`Types.py` and `Classifier.__init__`:

- **Features (5)**: `RSI(14,2)`, `WT(10,11)`, `CCI(20,2)`, `ADX(20,2)`, `RSI(9,2)` — the exact
  default list in `Classifier.__init__`, matching the Pine original's defaults.
- **Settings**: `source=close`, `neighborsCount=8`, `maxBarsBack=2000`, `useDynamicExits=False`,
  `useEmaFilter=False`, `useSmaFilter=False`.
- **FilterSettings** (defaults applied when `filterSettings is None`): `useVolatilityFilter=True`,
  `useRegimeFilter=True`, `useAdxFilter=False`, `regimeThreshold=-0.1`, `adxThreshold=20`, plus a
  default `KernelFilter(useKernelSmoothing=False, lookbackWindow=8, relativeWeight=8.0,
  regressionLevel=25, crossoverLag=2)`.

**Labels.** `y_train_array = np.where(src.shift(4) < src.shift(0), SHORT, np.where(src.shift(4) >
src.shift(0), LONG, NEUTRAL))`. At index `i` this compares `src[i-4]` with `src[i]` — both at or
before bar `i`, so the label array is causal. (It is worth recording that the label at index `i`
describes the *already realised* 4-bar move ending at `i`, inverted — a rise over the last 4 bars
labels index `i` SHORT. The Pine original does exactly the same thing, so this port is faithful;
it simply means "next bar classification" is a marketing description of a contrarian
nearest-neighbour vote over past 4-bar moves, not a forward-looking label.)

**Neighbour search.** `maxBarsBackIndex = len(df) - maxBarsBack` when `len(df) >= maxBarsBack`,
else `0`. The generator yields `0` for every `bar_index < maxBarsBackIndex`, then for
`bar_index` in `[maxBarsBackIndex, len(src))` scans a precomputed distance row:

```python
self.dists  # row for bar_index: log(1 + |feature[bar_index] - feature[:size]|) summed over features
            # with size = len(src) - maxBarsBackIndex = min(len(src), maxBarsBack)
span = min(self.settings.maxBarsBack, bar_index + 1)
for i, d in enumerate(dists[bar_index - maxBarsBackIndex][:span]):
    if d >= lastDistance and i % 4:
        lastDistance = d; distances.append(d); predictions.append(round(y_train_array[i]))
        if len(predictions) > neighborsCount:
            lastDistance = distances[round(neighborsCount*3/4)]; distances.pop(0); predictions.pop(0)
yield sum(predictions)
```

Three properties of this loop matter for causality:

1. The candidate ("training") set is `feature[:size]` — the **first** `min(len, maxBarsBack)` bars
   of the passed frame in *absolute* index terms, not a trailing window relative to `bar_index`.
   This is a real deviation from the Pine original, where `featureSeries[i]` means "`i` bars back
   from the current bar" and the training set therefore slides with the current bar. In the
   Python port the training set is a fixed prefix of whatever frame you hand it.
2. `[:span]` with `span = min(maxBarsBack, bar_index + 1)` truncates the candidate list at
   absolute index `bar_index`, so **no bar after `bar_index` ever enters the neighbour scan**.
   Together with the causal label array, the *index set* used at bar `i` is causal.
3. `predictions` and `distances` are created **outside** the `for bar_index` loop and persist
   across bars (this mirrors Pine's `var` arrays, so again the port is faithful). The value
   yielded at bar `i` is therefore path-dependent on every iteration since the accumulation
   started, and the accumulation starts at `maxBarsBackIndex`, which is a function of
   `len(df)` — i.e. of how many bars come *after* bar `i` in the frame you pass.

**Filters.** `filter_volatility` (ATR(1) > ATR(10)), `regime_filter` (recursive KLMF, then
EMA(200) of the absolute curve slope), `filter_adx` (off by default) are all rolling/recursive
and use past data only. `KernelFunctions.rationalQuadratic` / `gaussian` sum `src.shift(i)` for
`i` in `0..regressionLevel+1` — past bars only, and the first `regressionLevel+1` values are
zeroed. `signal` is the filtered prediction sign, forward-filled from the previous bar when the
filters block it; `barsHeld`, the fractal filters, `isLastSignalBuy/Sell` and the strict exits
all use `shift(...)` (past-padded). None of these introduce future information.

**Dynamic exits.** `useDynamicExits=False` by default; the dynamic exit booleans
(`endLongTradeDynamic`/`endShortTradeDynamic`) are computed from kernel rate changes and
`barssince(...)`, and are only OR-ed into `endLongTrade`/`endShortTrade` when the setting is on.
Out of scope for this slice (see "Scope cut" below).

### B. Where the default usage pattern is NOT causal

Two independent defects, both in the *library's default batch usage*, neither requiring a change
to the algorithm to fix — only a change to how the classifier is called:

**L1 — lookahead normalisation of 2 of the 5 default features (genuine future-value leakage).**
`MLExtensions.normalize()` is

```python
scaler = MinMaxScaler(feature_range=(0, 1))
return range_min + (range_max - range_min) * scaler.fit_transform(src.reshape(-1,1))[:,0]
```

i.e. sklearn's `MinMaxScaler` is **fit on the entire array**, so every normalised value depends on
the global min and max of the whole frame — including bars after `i`. `n_cci` and `n_wt` both go
through `normalize()`, so the **WT and CCI features at bar `i` carry information from the future**
(if the all-time high of the series occurs after bar `i`, the scaling of bar `i`'s CCI/WT changes).
Since every Lorentzian distance sums over all five features, this contaminates every prediction.
`n_rsi` and `n_adx` use `rescale(..., 0, 100)` with fixed bounds and are unaffected.

**L2 — frame-length dependence of the ML window (repainting, not value leakage).**
`maxBarsBackIndex = len(df) - maxBarsBack` and the persistent `predictions`/`distances` state mean
the value yielded at bar `i` depends on where the accumulation began, which moves whenever bars
are appended after `i`. `Distances.size` (hence the candidate prefix) is likewise a function of
`len(df)`. No future *price* enters the arithmetic through L2, but the number written at bar `i`
in a batch run over `[start, T)` is not the number the same code would have produced live at bar
`i`, and it changes as `T` moves.

**Verdict: the library is NOT causal as used by default** (one `LorentzianClassification(df)` call
over the whole backtest frame, then reading the per-bar `signal`/`prediction` columns). Using it
that way would put a lookahead-normalised, `T`-dependent signal into the backtest. It *is*
causal at the level of the algorithm — the index set and the label array never reach past
`bar_index` — so the defect is in the calling pattern, which is fixable without touching the
library.

### C. Minimal causal reframing (this is what the adapter does)

Take the classification the library assigns to a bar **only when that bar is the most recent bar
of the frame handed to the library** — a bar-by-bar walk-forward:

```
for each bar i:
    window = df.iloc[i - W + 1 : i + 1]          # W bars ending exactly at bar i
    lc = LorentzianClassification(window, settings=Settings(source=window['close'], ...))
    signal[i] = lc.data['signal'].iloc[-1]       # keep only the last bar's value
```

Under this reframing both defects disappear by construction: the MinMaxScaler is fit on
`window`, whose maximum index is `i` (L1 gone); `maxBarsBackIndex`, the candidate prefix and the
accumulated state are all functions of `window` only, and `window` is the same set of bars no
matter how many bars follow `i` in the source frame (L2 gone). The mechanical check in the
falsification condition — signal at bar `i` unchanged when the source series is extended by 50
bars — is then satisfied by construction, and is asserted in
`tests/test_lorentzian.py` rather than assumed.

Cost: one classifier instantiation per bar, each O(W · min(W, maxBarsBack)) in a pure-Python
inner loop. The window length `W` is the one free choice the reframing forces, because the
library's training set is the *first* `min(W, maxBarsBack)` bars of the window (property A.1
above): with `W = maxBarsBack + 1` the training set is exactly the `maxBarsBack` bars
immediately preceding bar `i`, which is the closest causal analogue of the Pine original's
sliding window. The measured cost of that choice, and what was actually used, are recorded in
"Method" below — this is an implementation constraint of the reframing, not a tuning knob, and
it is reported honestly either way.

### D. Scope cut, stated explicitly

Per `spec/build.md`, the generator (raw kNN classification) and `useDynamicExits` (the library's
own kernel-based exit logic) are two separate concerns. **This slice wires up the generator
only**, as an entry signal into `backtest_engine.run_backtest`'s existing SL/trailing/cost logic.
`useDynamicExits` stays at its library default (`False`) and is *not* reproduced inside
`backtest_engine.py`; exits remain the engine's own `max_sl_pct`/trailing/signal-reversal rules,
exactly as for every existing catalog entry. Reproducing the library's dynamic exits would mean
changing `backtest_engine.py`'s exit logic, which this slice does not do.

### E. Empirical confirmation of the audit (run after the audit above was written)

`scripts/f006_lorentzian_causality_audit.py`, full numbers in
`output/f006_lorentzian/audit.json`, on real Train-1 data (SOLUSDT/240 and ETHUSDT/60,
checksum-verified).

**L1 is real, and data-dependent.** Extending a prefix by 50 bars changed *nothing* in the
library's `n_cci`/`n_wt` on either series — because those 50 bars set no new close extreme.
Extending the same prefix to the end of the Train-1 slice, which does set a new extreme,
moved almost every past feature value:

| Series | prefix → extension | `n_cci` (library) | `n_wt` (library) | `n_rsi` (library) | adapter's causal CCI/WT |
| --- | --- | ---: | ---: | ---: | ---: |
| SOLUSDT/240 | 1200 → +1200 bars | **98.25%** of past bars changed (max Δ 0.103) | **97.33%** | 0% | **0%** |
| ETHUSDT/60 | 2400 → +7200 bars | **99.17%** (max Δ 0.105) | **98.67%** | 0% | **0%** |

That asymmetry is itself worth recording: a 50-bar truncation test alone is *not* sufficient
evidence about L1 — it only bites once a later bar sets a new extreme, and then it moves
essentially the whole history at once. `n_rsi` (fixed 0..100 `rescale`) never moves, as the
source reading predicted.

**L2 is real at the 50-bar scale.** `LorentzianClassification(df[:N])` vs
`LorentzianClassification(df[:N+50])`, comparing the N shared bars:

| Series | `prediction` bars changed | `signal` bars changed | max abs diff |
| --- | ---: | ---: | ---: |
| SOLUSDT/240 (N=2350) | 51 / 2350 (2.17%) | 47 / 2350 (2.00%) | 8.0 (the full ±8 range) |
| ETHUSDT/60 (N=2400) | 54 / 2400 (2.25%) | 50 / 2400 (2.08%) | 8.0 |

Roughly 50 of those are exactly the bars that fall out of the shifted ML window
(`maxBarsBackIndex` moves by 50, so 50 bars that had a prediction are zeroed), plus a handful
that differ beyond the boundary. So the port's persistent neighbour state turns out to be
*mostly* start-independent after a short burn-in — the repaint is concentrated at the window
edge. That is a useful fact, not an excuse: the values a backtest would read at those bars are
still not what the same code produces live.

**The adapter passes the same check exactly.** 0 of 2350 and 0 of 2400 bars changed, in
`prediction`, `signal`, `raw_signal` and `filter_all`, when 50 future bars were appended.
Same result on the test fixture in `tests/test_lorentzian.py`.

**Fidelity of the reframing.** For 12 anchors spread over the second half of each series, the
adapter's value at bar `i` was compared against what advanced-ta itself assigns to bar `i` when
bar `i` is the last bar of the frame handed to it (the literal walk-forward):

| Series | `signal` agreement | `prediction` sign agreement | mean abs `prediction` diff (scale ±8) |
| --- | ---: | ---: | ---: |
| SOLUSDT/240 | **12/12 (100%)** | 10/12 (83.3%) | 3.17 |
| ETHUSDT/60 | **12/12 (100%)** | 11/12 (91.7%) | 1.67 |

The traded quantity — the filtered state signal — matched the library's own walk-forward value
at every sampled anchor. The raw vote magnitude differs at some anchors, which is the expected
price of pinning the accumulation anchor (the one deviation section C names).

**Cost of the literal alternative.** A per-bar library call costs 0.46-0.77 s, so literally
re-instantiating the classifier for every bar projects to 0.3-0.5 h for one 2400-bar series and
several hours for a 9600-bar one — ~7 h for the 10 series in this slice. The adapter computes a
whole 2400-bar series in 0.84-0.92 s. The reframing is not just cleaner, it is what makes the
comparison run affordable at all.

## Method

Same continuous-run methodology, fixed parameters and checksum discipline as
`scripts/f006_stop_width_experiment.py` at its `max_sl_pct=0.03` row, so every number below is
directly comparable with that experiment's table.

- **Script**: `scripts/f006_lorentzian_experiment.py`. **Audit script**:
  `scripts/f006_lorentzian_causality_audit.py`.
- **Sample**: `LORENTZIAN_default` and `LORENTZIAN_raw` against the same 10 strategies as
  `spec/research/F006-hypothesis-stop-width.md` (`EMA_8_21`, `EMA_13_34_RSI14_55`, `RSI14_7030`,
  `MACD_12_26_hist`, `MACD_RSI14_50`, `BB_20_25_breakout`, `BB_20_2_RSI14`, `ADX14_DI_20`,
  `STOCH14_cross`, `TS_13_34_200_14`), 5 symbols × 2 intervals = 120 runs.
- **Lorentzian parameters**: advanced-ta 0.1.8 library defaults only, nothing tuned — features
  RSI(14,2)/WT(10,11)/CCI(20,2)/ADX(20,2)/RSI(9,2), `neighborsCount=8`, `maxBarsBack=2000`,
  volatility + regime filters on, ADX filter off, `regimeThreshold=-0.1`, EMA/SMA filters off,
  `useDynamicExits=False`. `LORENTZIAN_default` is the filtered, forward-filled state signal;
  `LORENTZIAN_raw` is the bare `sign(prediction)` with no filters and no state carry-over.
- **Data**: `data_contract.load_dataset("data_cache", symbol, interval, "2024-01-26T00:00:00Z",
  "2026-09-01T00:00:00Z")`, checksums verified in-script against
  `spec/research/F005-validation-protocol.md` section 6, then sliced to
  `[2024-01-26T00:00:00Z, 2025-03-01T00:00:00Z)` — warm-up + Train 1 only — before
  `run_backtest` sees it. No network fetch, no Validation/Holdout bars in any run.
- **Warm-up note**: `maxBarsBack=2000` is longer than the protocol's 35-day warm-up buffer at
  4h (2000 bars = 333 days). No extra history was loaded to compensate, because the causal
  reframing does not need it: with the accumulation anchored at the frame's first bar, the
  candidate set is the first `min(len, 2000)` bars and the classifier produces a prediction from
  the first bars of the frame onward, exactly as advanced-ta does on any frame shorter than
  `maxBarsBack`. What this costs is that early Train-1 bars vote against a smaller pool of
  neighbours; what it buys is that the frozen protocol's data slice is used unchanged.
- **Fixed engine parameters** (identical to the stop-width experiment): `leverage=1`,
  `cooldown_candles=0`, `max_sl_pct=0.03`, `atr_multiplier=1.5`, `activate_pct=0.03`,
  `trail_pct=0.02`, `initial_equity=500`, `stake=100`, `commission_rate_bps=10`,
  `half_spread_bps=5`, `slippage_bps=2`, `now` pinned to `2025-03-01T00:00:00Z`.
- **Regularity deliberately not computed** — reserved for Validation/Holdout per the frozen
  protocol; this is Train-only exploration.
- **Cross-check built into the run**: the 10 existing strategies were re-run rather than quoted,
  and every row was compared against the stored
  `output/f006_stop_width/summary/results.csv` `max_sl_pct=0.03` numbers. **100/100 rows matched
  exactly, 0 mismatches** — the new catalog entries perturbed no existing strategy, and the
  pipeline reproduces the earlier experiment bit for bit.

## Run_id

`scripts/f006_lorentzian_experiment.py`, `run_timestamp_utc = 2026-09-23T08:14:15.298457+00:00`,
`git_commit_parent = ce585f52f5e5ab70c474361dfd0a6d4581d298c3`, `n_runs = 120`,
`elapsed_seconds = 50.5`, Python 3.11.16, advanced-ta 0.1.8. Full parameters, checksums, the
stop-width cross-check and the signal-shape diagnostics:
`output/f006_lorentzian/summary/manifest.json`. Per-run results (120 rows):
`output/f006_lorentzian/summary/results.csv`. Causality audit output:
`output/f006_lorentzian/audit.json`.

advanced-ta 0.1.8 declares `Requires-Python >=3.10,<4.0` and uses `match`/`case`, so it cannot be
imported by the project's Python 3.9 `.venv_test`; the runs above used a separate Python 3.11.16
venv with `numpy 1.26.4` (advanced-ta 0.1.8 still uses `np.NaN`, removed in numpy 2), `pandas
2.3.3`, `scikit-learn 1.9.1`, `ta 0.11.0`. Both interpreters were used for the test suite — see
"Tests" below.

## Result

**Causality: the signal can be made causal, and was.** Falsification condition 1 is not met —
the adapter's signal at bar `i` is bit-identical whether the series ends at bar `i` or continues
for another 50 bars (0 bars changed, both real series and the test fixture), while advanced-ta's
documented usage fails the same check (2.0-2.3% of bars move, up to the full ±8 range) and its
WT/CCI features move on 97-99% of past bars once a later bar sets a new extreme. The reframing
costs one measurable deviation: the adapter's traded signal matched the library's own
walk-forward value at 24/24 sampled anchors, and the sign of the raw vote at 21/24, while the
vote's magnitude differs more often (mean abs diff 1.67-3.17 on a ±8 scale).

**Comparison run: the untuned causal Lorentzian signal is worse than the existing catalog on
Train 1.** Means across the 10 (symbol, interval) series:

| Variant | Mean net PnL | Mean win rate | Mean n_trades | Mean max_drawdown_pct | Survived (≥$100) | Positive net PnL |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `LORENTZIAN_default` | **-$384.99** | 30.15% | 339.3 | 77.15% | 2/10 | 0/10 |
| `LORENTZIAN_raw` | -$401.03 | 25.53% | 453.8 | 80.29% | 0/10 | 0/10 |
| existing 10-strategy sample | -$357.81 | 28.94% | 367.8 | 71.80% | 27/100 | 0/100 |
| best of that sample (`BB_20_25_breakout`) | -$168.62 | 32.17% | — | — | — | 0/10 |

Per series, `LORENTZIAN_default` vs the 10-strategy sample's mean on the same series:

| Series | `LORENTZIAN_default` net PnL | win rate | n_trades | max DD | sample mean net PnL | sample best |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| BTCUSDT/240 | -$301.68 | 36.46% | 288 | 60.58% | -$295.20 | -$89.90 |
| BTCUSDT/60 | -$335.32 | 33.40% | 476 | 67.48% | -$313.44 | -$151.82 |
| SOLUSDT/60 | -$400.22 | 34.81% | 316 | 80.10% | -$385.35 | -$243.22 |
| XRPUSDT/60 | -$400.65 | 31.93% | 357 | 80.24% | -$393.24 | -$317.16 |
| DOGEUSDT/60 | -$400.92 | 30.45% | 312 | 80.18% | -$392.23 | -$314.02 |
| DOGEUSDT/240 | -$401.30 | 15.93% | 270 | 80.26% | -$362.96 | -$111.61 |
| SOLUSDT/240 | -$401.98 | 28.43% | 299 | 80.48% | -$356.93 | -$99.54 |
| ETHUSDT/240 | -$402.16 | 29.14% | 302 | 80.66% | -$347.00 | -$89.05 |
| ETHUSDT/60 | -$402.36 | 34.78% | 460 | 80.67% | -$375.23 | -$148.33 |
| XRPUSDT/240 | -$403.27 | 26.20% | 313 | 80.88% | -$356.47 | -$121.52 |

**`LORENTZIAN_default` is worse than the sample's mean on 10 of 10 series, and worse than the
sample's best on 10 of 10.** Eight of ten series end at the ~$100 bankruptcy floor
(`final_equity` $96.73-$99.78, max DD ~80%) — the same floor mechanism `F005-baseline.md`
described. The two exceptions are both BTCUSDT (final equity $198.32 at 4h, $164.68 at 1h),
which is also the sample's most survivable symbol, so that says more about BTCUSDT's Train-1
price path than about the classifier.

Against falsification condition 2, honestly: the run is *not* strictly falsifying, because mean
win rate is marginally higher than the sample's (30.15% vs 28.94%, +1.2pp). But that edge is
smaller than the spread inside the sample itself (`RSI14_7030` 35.18%, `STOCH14_cross` 20.35%),
and it comes with worse net PnL (-$385 vs -$358), worse drawdown (77.15% vs 71.80%) and worse
survival (20% vs 27%). Treating +1.2pp of win rate as "directionally interesting" while losing
on all three other axes would be reading noise as signal.

**The one clearly directional finding in this run is about trade frequency, not about the
classifier's direction.** From the signal-shape diagnostics in the manifest:

| Series | bars | filters let through | `signal` state flips | trades executed |
| --- | ---: | ---: | ---: | ---: |
| SOLUSDT/240 | 2400 | 17.0% | 70 | 299 |
| ETHUSDT/240 | 2400 | 15.4% | 76 | 302 |
| BTCUSDT/240 | 2400 | 16.4% | 58 | 288 |
| XRPUSDT/240 | 2400 | 16.8% | 62 | 313 |
| DOGEUSDT/240 | 2400 | 16.6% | 64 | 270 |
| SOLUSDT/60 | 9600 | 17.6% | 290 | 316 |
| BTCUSDT/60 | 9600 | 17.3% | 279 | 476 |

At 4h the classifier changes its mind 58-76 times over Train 1, but the engine executes 270-313
trades — **4 to 5 trades per directional call**. The engine treats a catalog entry as a
persistent state and re-enters as soon as the state is non-zero and no position is open, so a
3% stop plus a persistent state manufactures a long chain of re-entries into the same idea, each
paying full round-trip cost. `LORENTZIAN_raw` makes the same point from the other side: with the
filters and the state carry-over removed, flips rise to 264-1267 and net PnL drops to the floor
on all 10 series (-$401.03 mean). Filtering/holding helps; churn hurts.

**Tests.** `tests/test_lorentzian.py` adds 7 tests, of which the load-bearing one is the
truncation check above. On the project's Python 3.9 `.venv_test`: **84 passed, 5 skipped**
(baseline before this slice: 81 passed, 1 skipped — the 4 advanced-ta tests skip there because
the package needs ≥3.10). On the Python 3.11 venv where advanced-ta is installed: **87 passed,
2 skipped**. No existing test changed behaviour, and the 100-row cross-check against the
stop-width results is the stronger form of the same statement.

## Decision

**The adapter stays; the Lorentzian hypothesis does not get a parameter-tuning slice next.**

What was established: advanced-ta 0.1.8's Lorentzian Classification is usable in this pipeline
as a genuinely causal signal generator (`lorentzian.py`, two additive catalog entries, engine
untouched), and its leakage — which is real, measured, and would have silently inflated any
backtest that used the library as documented — is removed rather than tolerated. That part of
`spec/build.md`'s F006 priority is done and reusable.

What was not established: any reason to believe tuning this generator's own parameters
(`neighborsCount`, feature lengths, `maxBarsBack`) is the next best use of the research budget.
At library defaults it loses to the existing 10-strategy sample on 10/10 series, bottoms out at
the bankruptcy floor on 8/10, and its only advantage is +1.2pp of win rate — inside the sample's
own spread. Tuning a generator that is currently the worst option on every series would be
searching for a parameter set that rescues it, which is exactly the overfitting pattern
`spec/vision.md` warns about, on a Train window that has now falsified three hypotheses in a row.

**Next slice: entry frequency, not classifier parameters.** The measured 4-5 trades per
directional call at 4h is the largest single lever visible in this run, it is not
Lorentzian-specific, and it is testable on both the Lorentzian entries and the existing catalog
in one experiment: fire an entry only on a state *flip* (the library's own one-shot
`startLongTrade`/`startShortTrade` semantics, which this slice deliberately did not wire — see
"Scope cut") and/or set `cooldown_candles` so re-entry cannot immediately follow a stop-out, and
measure net PnL, trade count and drawdown on Train 1. Two prior F006 hypotheses failed on
exit-sizing and entry-filtering; this one targets the re-entry loop, which neither touched, and
`spec/research/F005-leverage-sensitivity.md`'s cooldown sweep only varied cooldown for
persistent-state signals rather than removing the re-entry behaviour itself. If that slice shows
nothing either, the honest next step is a different generator family (Donchian/pullback), not
more parameter search on any of these.

If the entry-frequency slice does restore a non-degenerate result for the Lorentzian entries
specifically, *then* the parameter-tuning slice becomes worth running, and the second concern
`spec/build.md` separates — `useDynamicExits`, i.e. the library's kernel-based exits, which would
require an exit hook in `backtest_engine.py` — becomes the natural follow-up after that.
