# F006 — H-NONCANDLE-SLEEVE-01 (pre-registered; OI source frozen)

> Pre-registered **before** any result. Trader kierunku named one source:
> Bybit linear open interest. This card freezes exactly one position rule
> that reads that series. It is not a catalog name, not funding-carry, not
> a candle proxy, and not a second invented family.

experiment_id: H-NONCANDLE-SLEEVE-01
date: 2026-10-04
base_strategy: flat cash 0
number_of_trials: 1
status: frozen rule; OI cache coverage passed; await T0 Result

## Source (named by Trader kierunku)

Bybit v5 `/v5/market/open-interest`, `category=linear`, `intervalTime=1h`.
Same five Train-1 symbols: BTCUSDT, ETHUSDT, SOLUSDT, XRPUSDT, DOGEUSDT.
Window from repo constants `WARMUP_START` = `2024-01-26T00:00:00Z` through
`TRAIN1_END` = `2025-03-01T00:00:00Z` (`scripts/f006_family_runner.py`).

Cached under `data_cache/open_interest/` (not the candle cache, not
`data_cache/funding/`):

- `BTCUSDT_oi_1h_20240126T000000Z_20250301T000000Z.csv`
- `ETHUSDT_oi_1h_20240126T000000Z_20250301T000000Z.csv`
- `SOLUSDT_oi_1h_20240126T000000Z_20250301T000000Z.csv`
- `XRPUSDT_oi_1h_20240126T000000Z_20250301T000000Z.csv`
- `DOGEUSDT_oi_1h_20240126T000000Z_20250301T000000Z.csv`
- `manifest.json` (checksums)

Coverage gate (2026-10-04 ~00:32 Europe/Warsaw): every symbol has 9600
hourly rows spanning `2024-01-26T00:00:00+00:00` through
`2025-02-28T23:00:00+00:00` (WARMUP_START inclusive through the last hour
before TRAIN1_END), gaps=0, dups=0, monotonic. Columns:
`timestamp, open_interest`. Do not download liquidations, order flow, or
trades. Do not build a candle proxy.

Funding (`data_cache/funding/`) is a closed family (**FALSIFIED (a)+(b)**,
Decision `03d49bd`, mean M -318.858103). Do not reuse it as this sleeve.

## Shared losing months

Verified against `output/f006_shared_losing_months/summary.json`
`cooccurrence.ge_5_of_5.months`, which is the same list as
`ge_4_of_5.months`:

`2024-03, 2024-04, 2024-05, 2024-08, 2024-09, 2024-12`

That matches the owner list. Do not use `ge_3_of_5` (that set adds
`2025-01`).

```text
Why existing family is insufficient:
Catalog5 is FREEZE (EMA_50_200, BB_20_25_EMA200, EMA3_21_50_200,
EMA3_13_50_200, BB_20_2_EMA200) and DONCHIAN_55_NO_TRAIL stays FREEZE.
Entry axes on those names are falsified on each name's own trades. The
shared-losing-months artifact blocks an in-family portfolio: the six months
above are one basket regime, so section 8 stays blocked while a new sleeve's
losses still move with those months. Spread capture is closed (DOGEUSDT
inside spread 1.076716 bps < 17). Funding-carry is FALSIFIED (a)+(b),
Decision 03d49bd, mean M -318.858103. Further candle filters on catalog
names do not add a book the candles do not already have.

What mechanism is missing:
A position book whose only new input is open interest — a series the
catalog candles do not contain.

Why this family is different:
It is not an EMA, BB, or Donchian entry filter, not catalog mean-reversion,
not spread capture, not funding carry, not a reopen of XS_RS, ORB, or swarm,
and not a portfolio of catalog names. The difference is the OI input series.

What evidence would reject it:
(a) Train-1 mean after costs <= 0, against flat cash 0.
(b) the sleeve is not positive after costs inside the six shared losing
months listed above.
A run that does not actually consume the cached OI series is INVALID, not
a pass and not a falsification of (a) or (b).

What is the maximum initial research budget:
number_of_trials = 1. One change versus flat cash. Train-1 only. Five
symbols, one interval, no threshold, no grid.
```

## Frozen rule (one change versus flat; written before any result)

- Symbols: BTCUSDT, ETHUSDT, SOLUSDT, XRPUSDT, DOGEUSDT.
- Interval: 60 only. Do not also run 240.
- Window: warmup from WARMUP_START 2024-01-26T00:00:00Z, score only Train-1
  months 2024-03 through 2025-02, slice end TRAIN1_END 2025-03-01T00:00:00Z.
  Do not load validation or holdout bars.
- OI series: read `data_cache/open_interest/<SYM>_oi_1h_20240126T000000Z_20250301T000000Z.csv`
  (Bybit linear open interest, intervalTime 1h). Align to the hour bars.
  Do not substitute candles, volume, funding, or any candle-derived proxy.
- Position for hour t: the opposite sign of the prior hour's open-interest
  change. Let OI[t-1] and OI[t-2] be the cached open-interest values at the
  prior two hour timestamps.
  - sign = -1 if OI[t-1] > OI[t-2]
  - sign = +1 if OI[t-1] < OI[t-2]
  - flat (0) if OI[t-1] == OI[t-2], or if either OI value is missing
  Hold that signed position for hour t (enter/rebalance at the open of t
  under the existing harness conventions). One change. No threshold, no
  grid. `number_of_trials = 1`.
- Costs, unchanged: the existing harness cost model
  (commission_rate_bps=10, half_spread_bps=5, slippage_bps=2, leverage=1,
  stake=100, initial_equity=500). Do not retune.
- Baseline: flat cash 0. The same script with an empty entry mask must show
  0 trades, total_costs 0, Train-1 net 0. Do not copy a catalog name mean.

## Invalid unless the OI source is consumed

Before any score, the run must show that entries change when that cached
OI series is shuffled or zeroed and the candles are held fixed, and that a
run with the OI series omitted refuses to score. If the series is absent,
empty, or unused, write Result INVALID and stop. Do not label (a) or (b).
Do not report that run as evidence. A candle-only proxy (CVD from
close-open, volume median, EQH/EQL, BTC efficiency ratio, cross-sectional
rank) is INVALID on this card.

## Falsifiers

Score only Train-1, only after the invalidity check above passes. Per
symbol, net is sum of `net_pnl` after the harness costs. The reported mean
is the unweighted mean of that net across the five symbols.

- (a) Train-1 mean after costs <= 0. Baseline is flat cash 0.
- (b) the sleeve is not positive after costs inside the six shared losing
  months. Attribute each closed trade's `net_pnl` to the Europe/Warsaw
  calendar month of `exit_time` (`regularity.py` clock). Sum those nets
  across the five symbols over exactly
  {2024-03, 2024-04, 2024-05, 2024-08, 2024-09, 2024-12}.
  (b) fires if that sum is <= 0. A month with no trades contributes 0.
  Do not swap in `ge_3_of_5` or 2025-01.
- INVALID if the run does not actually consume the non-candle OI source.
  INVALID is not (a) and not (b).
- `number_of_trials = 1`. One change only. No second rule, no threshold
  grid, no second source.

Both (a) and (b) may fire. Label them literally. No other letters.

## decision_if_fail

Close this sleeve's first mechanism. Do not unfreeze catalog names. Do not
open a catalog portfolio. No retune, no second source, no symbol drop, no
second interval. Do not touch EMA/BB/Donchian filters, catalog
mean-reversion, spread capture, funding carry, XS_RS, ORB, or swarm.
Section 8 stays blocked. INVALID (source missing or unused) does not fire
this sentence and does not close a mechanism that was never run.

## decision_if_pass

A valid pass (mean > 0 and (b) not fired, OI source actually consumed)
still does not promote, does not unfreeze a catalog name, and does not
open a catalog portfolio. Leave Decision blank. Worker does not open Val-1
or holdout.

## Out of scope

EMA/BB/Donchian entry filters, catalog mean-reversion, spread capture,
funding carry, closed families XS_RS / ORB / swarm, a portfolio of catalog
names, holdout, validation, editing `strategy.py` on disk, `.pi/config.json`,
and `spec/features/active/F006-catalog5-unfreeze-correction/`. Do not
`git reset --hard`. Do not invent a new rule. The worker implements this
frozen rule only.

## Result

Not run yet. Frozen rule written before any result. OI cache coverage
passed. Await T0.
