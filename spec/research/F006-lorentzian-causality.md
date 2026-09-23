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

## Method

_(filled in after the run — see below)_

## Run_id

_(filled in after the run — see below)_

## Result

_(filled in after the run — see below)_

## Decision

_(filled in after the run — see below)_
