Add that source to the harness, else the test is invalid.

# F006 — H-NONCANDLE-SLEEVE-01 (pre-registered, INVALID)

> Pre-registered **before** any run. Trader kierunku approved one direction:
> one hypothesis, one change, Train-1 only, its own book on ONE source the
> catalog candles do not have (order flow, open interest, liquidations, or
> cross-asset context), whichever is already in the harness.
>
> **Status: INVALID. Do not run. Do not spawn.** None of those four series
> exists as a loadable input. This card does not invent a second family,
> does not name a download, and does not substitute a candle proxy.

experiment_id: H-NONCANDLE-SLEEVE-01
date: 2026-10-04
base_strategy: flat cash 0
number_of_trials: 1
status: INVALID until one named non-candle source is already loadable

## Source search (2026-10-04 ~00:27 Europe/Warsaw)

Searched the repo (Python and research notes, excluding virtualenvs) and
`data_cache/`. Nothing the catalog candle backtest does not already use
qualifies.

Quoted loaders and files:

- `scripts/f006_family_runner.py` `load_train1` (the Train-1 loader) calls
  `data_contract.load_dataset("data_cache", symbol, interval, WARMUP_START, TRAIN1_END)`.
- `data_cache/BTCUSDT_60_20240126T000000Z_20250301T000000Z.csv` columns are
  only `timestamp, open, high, low, close, volume`. The other four symbols
  in the frozen basket are the same shape. That is the catalog candle book.
- `data_cache/funding/<SYM>_funding_20240126T000000Z_20250301T000000Z.csv`
  columns are `timestamp, funding_rate`, loaded by
  `scripts/f006_funding_carry.py` `load_funding`. Funding is not order flow,
  open interest, liquidations, or cross-asset context. `H-FUNDING-CARRY-01`
  already consumed it and is **FALSIFIED (a)+(b)**, mean M -318.858103,
  Decision `03d49bd`. Do not reuse it as this sleeve.
- `data_cache/f005_liquidity_snapshot.json` is one Bybit linear ticker
  snapshot (`generated_at` 2026-09-22, `turnover24h`). Not a Train-1 series.
- `liq_range_eqh.py` (module docstring): "Every decision at bar i uses OHLCV
  through i". That is a candle proxy for a range sweep, not exchange
  liquidation prints. Do not run it.
- `btc_filter.py` `btc_er_permission` reads `btc_df["close"]` only. Cross-asset
  context built from catalog candles the backtest already has. Not this card.
  `cross_sectional_rs.py` ranks those same candles. Family XS_RS stays closed.
- No project module loads open interest, liquidation prints, aggTrades, or a
  book. No such file is in `data_cache/`.

There is no series for the harness to pass in. This card does not name a
URL and does not name a file that is not on disk. Until one of those four
sources is added as a real cached series the harness can pass in, every
backtest of this id is INVALID.

## Shared losing months

Verified against `output/f006_shared_losing_months/summary.json`
`cooccurrence.ge_5_of_5.months`, which is the same list as
`ge_4_of_5.months`:

`2024-03, 2024-04, 2024-05, 2024-08, 2024-09, 2024-12`

That matches the owner list. Do not use `ge_3_of_5` (that set adds
`2025-01`). The note
`spec/research/F006-hypothesis-catalog5-shared-losing-months.md` states the
same six months as 5/5 names all losing.

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
A position book whose only new input is one series the catalog candles do
not contain: order flow, open interest, liquidations, or cross-asset context
that is not those candles. That series is not in the harness and not in the
data cache. Without it there is no mechanism, only a candle proxy, and a
candle proxy is out of scope.

Why this family is different:
It is not an EMA, BB, or Donchian entry filter, not catalog mean-reversion,
not spread capture, not funding carry, not a reopen of XS_RS, ORB, or swarm,
and not a portfolio of catalog names. The difference is the input series.
Until that series is loadable the difference is not real, so this card stays
INVALID and is not a second invented family.

What evidence would reject it:
(a) Train-1 mean after costs <= 0, against flat cash 0.
(b) the sleeve is not positive after costs inside the six shared losing
months listed above.
A run that does not actually consume the non-candle source is INVALID, not
a pass and not a falsification of (a) or (b).

What is the maximum initial research budget:
number_of_trials = 1. One change versus flat cash. Train-1 only. Five
symbols, one interval, no grid. This commit spends zero trials. Do not spend
the trial on a candle proxy, on funding, or on a download with no file
already in the cache.
```

## Frozen rule

No rule is frozen, because freezing one would fake the source. When a named
file of exactly one of the four kinds is later in the harness, the single
change versus flat cash is: one position rule that reads that file and no
candle feature the catalog book does not already use. That rule is not
written here.

- Symbols, if a later valid run is ever licensed: SOLUSDT, ETHUSDT, BTCUSDT,
  XRPUSDT, DOGEUSDT.
- Interval: 60 only. Do not also run 240.
- Window: warmup from WARMUP_START 2024-01-26T00:00:00Z, score only Train-1
  months 2024-03 through 2025-02, slice end TRAIN1_END 2025-03-01T00:00:00Z.
  Do not load validation or holdout bars.
- Costs, unchanged: commission_rate_bps=10, half_spread_bps=5,
  slippage_bps=2, leverage=1, stake=100, initial_equity=500. Do not retune.
- Baseline: flat cash 0. The same script with an empty entry mask must show
  0 trades, total_costs 0, Train-1 net 0. Do not copy a catalog name mean
  (+91, +72, or any other). The harness has no separate control series for
  a source that is not loaded.

## Invalid unless the non-candle source is consumed

Before any score, the run must show that entries change when that cached
series is shuffled or zeroed and the candles are held fixed, and that a run
with the series omitted refuses to score. If the series is absent, empty,
or unused, write Result INVALID and stop. Do not label (a) or (b). Do not
report that run as evidence. A candle-only proxy (CVD from close-open,
volume median, EQH/EQL, BTC efficiency ratio, cross-sectional rank) is
INVALID on this card.

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
- INVALID if the run does not actually consume the non-candle source.
  INVALID is not (a) and not (b).
- `number_of_trials = 1`. One change only. No second rule, no threshold
  grid, no second source.

Both (a) and (b) may fire. Label them literally. No other letters.

## decision_if_fail

Close this sleeve's first mechanism. Do not unfreeze catalog names. Do not
open catalog portfolio. No retune, no second source, no symbol drop, no
second interval. Do not reopen funding-carry, spread capture, catalog
mean-reversion, XS_RS, ORB, or swarm. Section 8 stays blocked. INVALID
(source missing or unused) does not fire this sentence and does not close
a mechanism that was never run.

## decision_if_pass

Not reachable while this card is INVALID. A later valid pass (mean > 0 and
(b) not fired, source actually consumed) still does not promote, does not
unfreeze a catalog name, and does not open a catalog portfolio. Leave
Decision blank. Worker does not open Val-1 or holdout.

## Out of scope

EMA/BB/Donchian entry filters, catalog mean-reversion, spread capture,
funding carry, closed families XS_RS / ORB / swarm, a portfolio of catalog
names, holdout, validation, editing `strategy.py` on disk, `.pi/config.json`,
and `spec/features/active/F006-catalog5-unfreeze-correction/`. Do not
`git reset --hard`.

## Result

Not run. No source file. Result = INVALID. No spawn.
