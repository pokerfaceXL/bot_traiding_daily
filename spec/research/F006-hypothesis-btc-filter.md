# F006 — BTC structure as a permission filter for alt breakouts (H-BTC-FILTER-01)

> Sections through **Method** were written before any BTC-filter signal module, experiment
> script, or Train-1 backtest. Train-1 only: `[2024-03-01T00:00:00Z,
> 2025-03-01T00:00:00Z)`, with the frozen warm-up from `2024-01-26T00:00:00Z`.
> Validation and holdout bars are neither loaded nor inspected.

## Observation

The catalog's no-trail momentum signals have positive aggregate pockets but lose in
correlated months. Same-symbol EMA confirmation and cross-symbol direction agreement
were already tested as entry filters; neither establishes whether a broad-market
structure regime can make an alt's own breakout selective without predicting that
alt's return from BTC's lagged return.

This is deliberately **not BTC_LEAD**. BTC is never traded, ranked, or used as a
lag-return forecast for an alt. At each alt decision bar it supplies only a
contemporaneous, causal permission bit: bullish, bearish, or neutral. This is also
not `XS_RS`: no top-1 selection or portfolio rotation is performed.

## Hypothesis

**H1.** Requiring an alt's causal prior-channel breakout direction to agree with a
causal BTC directional-efficiency structure bit produces at least one positive-mean
candidate under the frozen no-trail Train-1 harness. The frozen runner's ten-row mean
includes two forced-flat BTC diagnostic rows, so its sign is the same as the summed
eight eligible-alt rows; BTC never contributes a trigger or trade.

### Frozen construction

- **Trade universe:** ETHUSDT, SOLUSDT, XRPUSDT, and DOGEUSDT only. BTCUSDT is a
  permission-data input only; it must produce no candidate trigger or trade.
- **BTC permission bit:** at aligned bar `i`, using only BTC closes at or before `i`,
  `ER20(i) = (close[i] - close[i-20]) / sum(abs(diff(close[i-20:i+1])))`.
  Permission is `+1` when `ER20 >= 0.30`, `-1` when `ER20 <= -0.30`, and `0`
  otherwise (including warm-up, zero denominator, missing or unaligned BTC bar).
  It is pass-through: a matching alt direction is retained; neutral or opposing BTC
  makes the alt signal flat. The current closed BTC bar is allowed because the engine
  fills only at the next bar's open.
- **Alt trigger:** at bar `i`, long if `close[i] > max(high[i-N:i])`, short if
  `close[i] < min(low[i-N:i])`, otherwise flat. Current-bar high/low are excluded
  from the prior channel. The resulting matching-direction trigger is persistent
  only while the BTC permission remains matching; the shared one-shot mask turns each
  new permitted run into one next-bar-open entry.
- **Pre-registered catalog names (all candidates; no more than five):**

| Name | Alt prior-channel N | BTC ER window / threshold |
| --- | ---: | --- |
| `BTC_FILTER_ER20_DONCHIAN_5` | 5 | 20 / ±0.30 |
| `BTC_FILTER_ER20_DONCHIAN_10` | 10 | 20 / ±0.30 |
| `BTC_FILTER_ER20_DONCHIAN_20` | 20 | 20 / ±0.30 |

The frozen shared runner still requires all five datasets and always aggregates ten
rows. Its two BTC candidate rows are intentionally forced-flat diagnostics, so they
can neither add a BTC trade nor create a BTC promotion claim; their only mechanical
effect is the fixed denominator in the runner's H1 mean. Alt-only sums and H2 rows
are reported separately in the experiment Result.

**H2, conditional on H1.** For each H1-passing candidate, at least one eligible alt
series clears the frozen monthly promotion checklist (12 valid Train-1 months, every
valid month non-negative, full Train-1 PnL non-negative, DD ≤50%, and trades >0).

## Falsification

H1 is falsified if no frozen candidate has positive mean net PnL in the fixed
10-row runner aggregate (with BTC's two rows forced flat). H2 is not applicable if
H1 fails; otherwise it is falsified if no H1-passing candidate has a passing
eligible-alt series.

Do not add ER windows, thresholds, alternate BTC structures, alt lookbacks, BTC
lags, BTC trades, or a portfolio/top-rank rule after seeing Train-1. Do not reopen
closed `BTC_LEAD`: permission filtering is not lag-return prediction. A negative
result closes this exact filter construction; it does not justify tuning it on
validation or holdout.

## Method

1. Add an offline additive signal module and unit tests for causal ER permission,
   matching-direction gating, neutral flatness, unaligned BTC flatness, and future
   perturbation invariance. Do not wire `strategy.py` or live code.
2. Add one thin experiment script that registers the frozen runtime-only entries and
   calls `f006_family_runner.run_family(...)` once. It may supply BTC context only
   from bounded Train-1 data; it must not copy the harness loop.
3. Use the shared runner's DONCHIAN_55 control and write raw rows, summary, manifest,
   and the refreshed cross-family digest under `output/f006_btc_filter/`.

## Run_id

`f006_btc_filter`, commit `2a5a8c6`, bounded Train-1 cache checksums recorded in
`output/f006_btc_filter/summary/manifest.json`; executed 2026-09-29.

## Result

The 10-row shared-runner H1 aggregate passed for all frozen names: N=5 `+$594.01`
(`+$59.40` mean), N=10 `+$734.03` (`+$73.40`), and N=20 `+$857.06` (`+$85.71`).
BTC's six candidate rows (three names × two intervals) were all flat: zero calls,
zero trades, and `$0.00` PnL. Across the eight actual alt rows, the corresponding
means were `+$74.25`, `+$91.75`, and `+$107.13`.

H2 is falsified: no eligible-alt series passed the 12-month checklist. The closest
monthly count was four negative months (SOL/60/N=20, ETH/60/N=10, and DOGE/60/N=10
or N=20), despite all candidate DD values remaining below 50%. The unconditional
DONCHIAN_55 control compared 10 rows with zero mismatches; no run had a trailing exit
or one-shot violation.

## Decision

The frozen BTC ER20 permission filter clears aggregate H1 but fails monthly H2. Do
not promote it or retune its ER threshold, window, or channel lookback on validation
or holdout. It remains a distinct permission-filter result, not evidence for or a
reopening of BTC_LEAD.

## Tests

`/usr/bin/python3 scripts/f006_btc_filter_experiment.py` completed: control 10/10
rows matched, H1 passed for all three names, H2 falsified. `/usr/bin/python3
scripts/f006_cross_family_digest.py` refreshed both digest files. `/usr/bin/python3
-m pytest tests/test_btc_filter.py tests/test_signal_family_contract.py -q` passed
55 tests.
