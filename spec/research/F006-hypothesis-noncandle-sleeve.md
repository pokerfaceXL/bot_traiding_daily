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

Run: `python3 scripts/f006_noncandle_oi_fade.py` (script commit
`7eb04c1`; artifacts `output/f006_noncandle_oi_fade/`). `number_of_trials = 1`,
60-minute Train-1 bars only (`f006_family_runner.load_train1`, checksums equal
the protocol section 6 values). OI read from
`data_cache/open_interest/<SYM>_oi_1h_...csv` with sha256 checked against
`manifest.json`. Costs are the existing harness costs (commission 10, half-spread 5,
slippage 2 bps, leverage 1, stake 100, equity 500, NO_TRAIL exit geometry
`max_sl_pct` 0.03). No funding, no threshold, no grid.

Timing as implemented. The signal on the bar opening at s is
`-sign(OI[s] - OI[s-1])`. The engine fills it at the open of t = s+1h, so the
position held over hour t uses exactly OI[t-1] and OI[t-2]. A same-sign signal
keeps the position. An opposite sign closes it at the bar-s close
(`signal_reverse`) and re-enters at the open of t. The 3% initial stop stays
active. With cooldown 0, the next signal re-enters after a stop. Independent
check against the trade files: in all 6,634 entries, the direction equals
`-sign(OI[t-1h] - OI[t-2h])` at `entry_time` (0 mismatches). The cache has no
OI ties and no gaps. The only flat hour is the first bar per symbol, before
any position exists. The script refuses to score if a flat hour falls inside a
hold, because the engine cannot go flat on signal 0.

Control (empty entry mask, same script): 0 trades, total_costs 0, net 0,
final equity 500 on 5/5. Baseline = 0.

OI consumption check (candles held fixed), run before scoring. Not INVALID:

| symbol | entries (real) | entries (OI shuffled, seed 20261004) | entries (OI zeroed) | OI omitted / empty |
|---|---|---|---|---|
| SOLUSDT | 1405 | 977, differ | 0 | refused / refused |
| ETHUSDT | 1423 | 1204, differ | 0 | refused / refused |
| BTCUSDT | 1120 | 1330, differ | 0 | refused / refused |
| XRPUSDT | 1505 | 1284, differ | 0 | refused / refused |
| DOGEUSDT | 1181 | 1128, differ | 0 | refused / refused |

Shuffling OI changes the signal on about 4,750-4,800 of 9,600 bars per
symbol. Zeroing OI changes 9,599 bars. Every symbol's entry list differs from
the real run's.

Train-1 score (net_pnl by Europe/Warsaw exit month, 2024-03 .. 2025-02):

| symbol | Train-1 trades | gross | total_costs | net | shared-month net | warm-up net |
|---|---|---|---|---|---|---|
| SOLUSDT | 996 | +30.1276 | 318.7824 | -288.6547 | -288.6547 | -112.7942 |
| ETHUSDT | 1006 | +41.6907 | 321.9519 | -280.2613 | -280.2613 | -120.4503 |
| BTCUSDT | 735 | -4.4415 | 235.2006 | -239.6421 | -239.6421 | -162.0094 |
| XRPUSDT | 1088 | +68.1212 | 348.1454 | -280.0242 | -280.0242 | -120.1495 |
| DOGEUSDT | 729 | -59.6260 | 233.2785 | -292.9045 | -292.9045 | -107.0979 |

**Mean net = -276.297349 <= 0. (a) FIRED.**

**(b):** sum of net_pnl over {2024-03, 2024-04, 2024-05, 2024-08, 2024-09,
2024-12} across the five symbols = **-1381.486747 <= 0. (b) FIRED.**

**FALSIFIED (a)+(b).**

Note: every book hits the engine margin floor early. Equity falls below the
100 stake (`InsufficientMarginError`, documented engine contract) on BTCUSDT
2024-04-29, DOGEUSDT 2024-05-01, SOLUSDT 2024-05-20, ETHUSDT 2024-05-24, and
XRPUSDT 2024-05-29. From then on, every entry is skipped (6,617-7,328 skips per
symbol), so June 2024 through February 2025 book 0. The Train-1 net is
therefore truncated, not a full-year figure. All Train-1 trades exit in
2024-03..05, which is why shared-month net equals net. The truncation cannot
flip either falsifier. Gross before costs is about +76 summed across the five
symbols over about 4,550 trades. That is about +0.017 per trade against about
0.32 of round-trip cost per trade, so more trading only adds cost. Frequent
flips (about one trade every two hours until the margin floor) are a property of the frozen rule, not a
retune target.

## Decision

