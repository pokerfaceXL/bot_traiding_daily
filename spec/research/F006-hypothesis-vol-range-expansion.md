# F006 — Relative-volume surge + range-expansion breakout (new OHLCV signal family)

> Sections "Observation" through "Method" (including falsification) were written and committed
> BEFORE any new signal module / experiment script was written and before any backtest was run,
> per the same pre-registration discipline as every prior F006 hypothesis note. "Run_id",
> "Result", "Decision" and "Tests" are placeholders filled in after the run.
>
> TRAIN-1 ONLY, same window as every F006 slice: `[2024-03-01T00:00:00Z, 2025-03-01T00:00:00Z)`
> plus the protocol's 35-day warm-up buffer from `2024-01-26T00:00:00Z`. Validation 1-4 and the
> Holdout window are not loaded, not sliced and not looked at.

## Observation

After twelve F006 hypotheses the 85-name `STRATEGY_CATALOG` is exhausted on both mechanism axes
under `NO_TRAIL`: momentum/breakout (0/80 series clear the monthly criterion; best = 2 losing
months on `DONCHIAN_55`/DOGEUSDT/1h) and mean-reversion (all 5 catalog counter-trend names
aggregate-negative — Decision in
`spec/research/F006-hypothesis-mean-reversion-notrail.md`). Portfolio diversification of the
best momentum series does not reduce losing months below the best constituent
(`spec/research/F006-portfolio-diversification-exploration.md`). Lorentzian Classification was
already wired as a causal catalog entry and falsified as a lead at library defaults; its Decision
(`spec/research/F006-lorentzian-causality.md`) explicitly forbids a parameter-tuning rescue and
points at a different generator family next — that path was taken (Donchian) and later exhausted
with the rest of the catalog. `spec/build.md` NOW states the next step needs a **new signal
source outside `add_indicators` / the current catalog families**, or an owner tolerance decision.
Owner chose: propose and launch one new signal source.

Existing volume use in the catalog is **not** that source: `sig_bb_breakout_vol` and
`sig_ema_vol` only *gate* an already-defined BB-breakout or EMA-cross with `vol_ratio > 1.2`.
They do not define entry from participation + expansion themselves. Donchian enters on an N-bar
high/low breach; BB on close vs std bands. None of those is "volume climax + range expansion
as the primary trigger."

Funding-rate / open-interest: no project-local series found under the data cache / loaders —
skipped (would require new external data acquisition, out of scope for a few-hour slice).

## Hypothesis

**H1 (new generator, aggregate).** An additive OHLCV-only signal family — relative-volume surge
AND bar-range expansion vs ATR AND close location in the bar for direction — produces at least
one catalog name whose **mean net PnL across the 10 `(symbol, interval)` series is > 0** at
`NO_TRAIL` (`activate_pct=10.0`, `max_sl_pct=0.03`, one-shot entry mask, `cd=0`, `leverage=1`),
same pooling bar as `spec/research/F006-catalog-notrail-sweep.md`.

Concrete generator (implement as a new additive module, Donchian/Lorentzian pattern — do **not**
stuff this into `add_indicators` as a quiet extension of `vol_ratio`; register new
`STRATEGY_CATALOG` names via `catalog_entries()`):

- `rvol = volume / SMA(volume, VOL_MA)` with `VOL_MA ∈ {20}` (may reuse a locally computed SMA;
  must not require BB/EMA/Donchian state).
- `range_atr = (high - low) / ATR(ATR_P)` with `ATR_P ∈ {14}` (ATR computed inside the module or
  from an existing column if already present after `add_indicators` — either is fine; the
  *signal definition* must not depend on BB bands, Donchian channels, or EMA crosses).
- `close_loc = (close - low) / (high - low)` (0 if range=0).
- Long (+1) when `rvol > RVOL_THR` AND `range_atr > RANGE_THR` AND `close_loc >= CLOSE_HI`.
- Short (−1) when `rvol > RVOL_THR` AND `range_atr > RANGE_THR` AND `close_loc <= CLOSE_LO`.
- Else 0. Persistent-state signal (family one-shot mask applied by the experiment harness, as
  elsewhere).

Pre-registered small name grid (keep ≤ ~6 names so 5×2×names stays in the usual ~60-run
budget; do not grid-search after seeing results):

| Name | RVOL_THR | RANGE_THR | CLOSE_HI / CLOSE_LO |
| --- | ---: | ---: | --- |
| `RVOL_RE_20_2_15_80` | 2.0 | 1.5 | 0.80 / 0.20 |
| `RVOL_RE_20_25_15_80` | 2.5 | 1.5 | 0.80 / 0.20 |
| `RVOL_RE_20_2_20_70` | 2.0 | 2.0 | 0.70 / 0.30 |
| `RVOL_RE_20_3_15_80` | 3.0 | 1.5 | 0.80 / 0.20 |
| `RVOL_RE_20_2_15_90` | 2.0 | 1.5 | 0.90 / 0.10 |

**Why mechanistically new:** entry is defined by a participation spike coincident with an
ATR-relative range expansion and directional close location — not a channel/band breach, not an
EMA/MACD/RSI cross, not "BB/EMA already fired and volume confirms." That is the diversification
mechanism `F006-portfolio-diversification-exploration.md` asked for and
`F006-hypothesis-mean-reversion-notrail.md` showed the catalog cannot supply.

**H2 (monthly, conditional on H1).** For any name that clears H1, at least one of its 10 series
clears `spec/research/F005-validation-protocol.md` section 7's zero-tolerance monthly checklist
on Train 1 (DD ≤ 50%, net PnL ≥ 0 in every valid month, all 12 months valid, full-window net
PnL ≥ 0, **`n_trades > 0`**), same wording as
`spec/research/F006-hypothesis-notrail-monthly-catalog5.md`.

## Falsification condition (stated before running)

**H1 falsified** if none of the pre-registered names has positive mean net PnL over its
10-series pool at `NO_TRAIL`.

**H2 falsified** if every H1-clearing name has zero series clearing all monthly criteria (with
`n_trades > 0`). If H1 fails, H2 is "not applicable — H1 failed", not silently passed/failed.

Do **not** invent extra thresholds after seeing results. Do **not** add BB/Donchian/EMA gates
"to help" mid-slice. A negative Result is valid and must be reported honestly; Decision should
then say this OHLCV order-flow-proxy family is closed at this geometry/basket (or name one
narrow, pre-justified follow-up only if the Result itself surfaces a clean, non-overfit lever).

## Sample

Up to 5 names × 5 symbols (`SOLUSDT`/`ETHUSDT`/`BTCUSDT`/`XRPUSDT`/`DOGEUSDT`) × 2 intervals
(`240`/`60`) = ≤50 series, Train-1 only. Plus one harness-control re-run of a known catalog
name already measured at `NO_TRAIL` (e.g. `DONCHIAN_55` or `BB_20_25_breakout` on one
symbol/interval) to prove the experiment script matches stored numbers before trusting new
names.

## Method

1. Implement additive module (suggested path: `vol_range_expansion.py`) exposing
   `catalog_entries()`; register via `STRATEGY_CATALOG.update(...)` at the bottom of
   `strategy.py` the same way `donchian.py` / `lorentzian.py` do. No live trading, no API keys.
2. Experiment script under `scripts/f006_vol_range_expansion_experiment.py` mirroring
   `scripts/f006_mean_reversion_notrail_experiment.py` / catalog-sweep harness (checksums,
   one-shot mask, `NO_TRAIL` geometry, output under `output/f006_vol_range_expansion/`).
3. Unit tests for the signal on a hand-built OHLCV fixture (surge+expansion long, surge+expansion
   short, surge-without-expansion stays flat, expansion-without-surge stays flat) and a
   regression that default catalog behaviour for untouched names is unchanged.
4. Fill Result / Decision / Run_id / Tests after the run; commit evidence.

## Run_id

_(placeholder)_

## Result

_(placeholder)_

## Decision

_(placeholder)_

## Tests

_(placeholder)_
