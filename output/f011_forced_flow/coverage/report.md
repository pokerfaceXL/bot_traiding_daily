# F011 · Free high-resolution data coverage (Train-1 recon)

Generated 2026-10-05T18:06:14Z by `scripts/f011_data_coverage.py` on host `lorenzian-free` (all probes run from this host). HTTP requests: 3137.

Train-1 = 2024-01-26T00:00Z .. 2025-02-28T23:00Z → 5m grid [2024-01-26, 2025-03-01) = 400 days × 288 = 115200 bars per symbol. Every number below is taken from responses/listings captured in this run (`coverage.json`, `raw/`).

## Coverage table

| source | symbol | earliest (empirical) | Train-1 covered | gaps in Train-1 | resolution | fields | approx. Train-1 size |
|---|---|---|---|---|---|---|---|
| Bybit REST oi_5min | BTCUSDT | 2020-08-04T07:50:00Z | y | 0 missing bars in 0 runs (of 115200) | 5min | openInterest (contracts=base), timestamp | 6.9 MB CSV (115,200 rows, 576 requests) |
| Bybit REST oi_5min | ETHUSDT | 2020-10-21T08:55:00Z | y | 0 missing bars in 0 runs (of 115200) | 5min | openInterest (contracts=base), timestamp | 7.0 MB CSV (115,200 rows, 576 requests) |
| Bybit REST oi_15min | BTCUSDT | 2020-08-04T08:00:00Z | y (spot) | spot: 2024-01-26 96/96, 2025-02-28 96/96 | 15min | openInterest, timestamp | ~38,400 rows (est.) |
| Bybit REST oi_15min | ETHUSDT | 2020-10-21T09:00:00Z | y (spot) | spot: 2024-01-26 96/96, 2025-02-28 96/96 | 15min | openInterest, timestamp | ~38,400 rows (est.) |
| Bybit REST account_ratio_5min | BTCUSDT | 2020-08-04T07:50:00Z | y | 0 missing bars in 0 runs (of 115200) | 5min | buyRatio, sellRatio (share of accounts long/short), timestamp | 6.5 MB CSV (115,200 rows, 231 requests) |
| Bybit REST account_ratio_5min | ETHUSDT | 2020-10-21T09:25:00Z | y | 0 missing bars in 0 runs (of 115200) | 5min | buyRatio, sellRatio (share of accounts long/short), timestamp | 6.5 MB CSV (115,200 rows, 231 requests) |
| Bybit trade archive (public.bybit.com/trading) | BTCUSDT | 2020-03-25 | y | 0 missing days | tick (every trade; 5m rebuilt) | timestamp(s), side(taker), size, price, tickDirection, trdMatchID, grossValue, homeNotional, foreignNotional | 25.34 GB gz (median 56.1 MB/day) |
| Bybit trade archive (public.bybit.com/trading) | ETHUSDT | 2020-10-21 | y | 0 missing days | tick (every trade; 5m rebuilt) | timestamp(s), side(taker), size, price, tickDirection, trdMatchID, grossValue, homeNotional, foreignNotional | 17.62 GB gz (median 36.3 MB/day) |
| Binance vision metrics | BTCUSDT | 2020-09-01 | y | 0 missing files | 5m | sum_open_interest(+value), top-trader & global long/short ratios, taker long/short vol ratio | 4.5 MB zip (400 files) |
| Binance vision metrics | ETHUSDT | 2021-12-01 | y | 0 missing files | 5m | sum_open_interest(+value), top-trader & global long/short ratios, taker long/short vol ratio | 4.7 MB zip (400 files) |
| Binance vision klines_5m | BTCUSDT | 2019-12-31 | y | 0 missing files | 5m | OHLCV, quote_volume, count, taker_buy_volume, taker_buy_quote_volume | 5.6 MB zip (400 files) |
| Binance vision klines_5m | ETHUSDT | 2019-12-31 | y | 0 missing files | 5m | OHLCV, quote_volume, count, taker_buy_volume, taker_buy_quote_volume | 5.7 MB zip (400 files) |
| Binance vision aggTrades | BTCUSDT | 2019-12-31 | y | 0 missing files | tick (aggregated trades) | agg_trade_id, price, quantity, first/last_trade_id, transact_time, is_buyer_maker | 7.63 GB zip (400 files) |
| Binance vision aggTrades | ETHUSDT | 2019-12-31 | y | 0 missing files | tick (aggregated trades) | agg_trade_id, price, quantity, first/last_trade_id, transact_time, is_buyer_maker | 7.82 GB zip (400 files) |
| Binance vision fundingRate_monthly | BTCUSDT | 2020-01 | y | 0 missing files | 8h | calc_time, funding_interval_hours, last_funding_rate | 12 KB zip (14 files) |
| Binance vision fundingRate_monthly | ETHUSDT | 2020-01 | y | 0 missing files | 8h | calc_time, funding_interval_hours, last_funding_rate | 12 KB zip (14 files) |
| cached Bybit funding (data_cache/funding) | BTCUSDT | 2024-01-26 00:00:00+00:00 | y | 0 missing 8h slots | 8h | timestamp, funding_rate | 1200 rows |
| cached Bybit funding (data_cache/funding) | ETHUSDT | 2024-01-26 00:00:00+00:00 | y | 0 missing 8h slots | 8h | timestamp, funding_rate | 1200 rows |

## Bybit 5m OI consistency

- oi_5min/BTCUSDT: openInterest / singleOpenInterest in [2.0, 2.0] over all 115,200 rows; 5m bars at HH:00 vs cached 1h OI (`data_cache/open_interest/BTCUSDT_oi_1h_20240126T000000Z_20250301T000000Z.csv`): 9600 hours matched, exact-equal fraction 1.0, max |rel diff| 0.0.
- oi_5min/ETHUSDT: openInterest / singleOpenInterest in [2.0, 2.0] over all 115,200 rows; 5m bars at HH:00 vs cached 1h OI (`data_cache/open_interest/ETHUSDT_oi_1h_20240126T000000Z_20250301T000000Z.csv`): 9600 hours matched, exact-equal fraction 1.0, max |rel diff| 0.0.

## Sample-day checks

- Bybit trades BTCUSDT 2024-06-12: header `timestamp,symbol,side,size,price,tickDirection,trdMatchID,grossValue,homeNotional,foreignNotional`; 1,764,280 trades, timestamp unit `s`, sides {'Buy': 894447, 'Sell': 869833}, 288 5m buckets rebuilt (taker_buy_vol, taker_sell_vol, OFI, CVD, trade_count) → `raw/bybit_archive/BTCUSDT_2024-06-12_5m_reconstruction.csv`.
- Bybit trades BTCUSDT 2024-10-01: header `timestamp,symbol,side,size,price,tickDirection,trdMatchID,grossValue,homeNotional,foreignNotional`; 2,916,579 trades, timestamp unit `s`, sides {'Sell': 1468945, 'Buy': 1447634}, 288 5m buckets rebuilt (taker_buy_vol, taker_sell_vol, OFI, CVD, trade_count) → `raw/bybit_archive/BTCUSDT_2024-10-01_5m_reconstruction.csv`.
- Bybit trades ETHUSDT 2024-06-12: header `timestamp,symbol,side,size,price,tickDirection,trdMatchID,grossValue,homeNotional,foreignNotional`; 907,225 trades, timestamp unit `s`, sides {'Buy': 461617, 'Sell': 445608}, 288 5m buckets rebuilt (taker_buy_vol, taker_sell_vol, OFI, CVD, trade_count) → `raw/bybit_archive/ETHUSDT_2024-06-12_5m_reconstruction.csv`.
- Bybit trades ETHUSDT 2024-10-01: header `timestamp,symbol,side,size,price,tickDirection,trdMatchID,grossValue,homeNotional,foreignNotional`; 1,687,211 trades, timestamp unit `s`, sides {'Sell': 849765, 'Buy': 837446}, 288 5m buckets rebuilt (taker_buy_vol, taker_sell_vol, OFI, CVD, trade_count) → `raw/bybit_archive/ETHUSDT_2024-10-01_5m_reconstruction.csv`.
- Binance BTCUSDT 2024-06-12: metrics 288 rows (step 300.0s), columns `create_time, symbol, sum_open_interest, sum_open_interest_value, count_toptrader_long_short_ratio, sum_toptrader_long_short_ratio, count_long_short_ratio, sum_taker_long_short_vol_ratio`; klines 5m 288 rows, columns `open_time, open, high, low, close, volume, close_time, quote_volume, count, taker_buy_volume, taker_buy_quote_volume, ignore`.
- Binance BTCUSDT 2024-10-01: metrics 288 rows (step 300.0s), columns `create_time, symbol, sum_open_interest, sum_open_interest_value, count_toptrader_long_short_ratio, sum_toptrader_long_short_ratio, count_long_short_ratio, sum_taker_long_short_vol_ratio`; klines 5m 288 rows, columns `open_time, open, high, low, close, volume, close_time, quote_volume, count, taker_buy_volume, taker_buy_quote_volume, ignore`.
- Binance ETHUSDT 2024-06-12: metrics 288 rows (step 300.0s), columns `create_time, symbol, sum_open_interest, sum_open_interest_value, count_toptrader_long_short_ratio, sum_toptrader_long_short_ratio, count_long_short_ratio, sum_taker_long_short_vol_ratio`; klines 5m 288 rows, columns `open_time, open, high, low, close, volume, close_time, quote_volume, count, taker_buy_volume, taker_buy_quote_volume, ignore`.
- Binance ETHUSDT 2024-10-01: metrics 288 rows (step 300.0s), columns `create_time, symbol, sum_open_interest, sum_open_interest_value, count_toptrader_long_short_ratio, sum_toptrader_long_short_ratio, count_long_short_ratio, sum_taker_long_short_vol_ratio`; klines 5m 288 rows, columns `open_time, open, high, low, close, volume, close_time, quote_volume, count, taker_buy_volume, taker_buy_quote_volume, ignore`.
- Binance aggTrades BTCUSDT (range-read, not downloaded): `agg_trade_id,price,quantity,first_trade_id,last_trade_id,transact_time,is_buyer_maker`, e.g. `2208923165,67320.6,0.149,5079880580,5079880587,1718150400086,true`.
- Binance aggTrades ETHUSDT (range-read, not downloaded): `agg_trade_id,price,quantity,first_trade_id,last_trade_id,transact_time,is_buyer_maker`, e.g. `1666770892,3498.17,0.143,4105091376,4105091376,1718150400032,false`.

## Cross-check (sanity only)

| symbol | day | OI Δ direction agreement 5m lag0 / best lag | OI Δ agree 15m / 1h | OI Δ corr 5m / 15m / 1h | taker-buy corr | taker-sell corr | OFI corr | OFI sign agree | trade-count corr | Bybit/Binance volume |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSDT | 2024-06-12 | 0.5645 / 0.5734 (lag 1) | 0.6 / 0.7826 | 0.1248 / 0.376 / 0.4846 | 0.9887 | 0.9862 | 0.6941 | 0.7674 | 0.9925 | 0.4523 |
| BTCUSDT | 2024-10-01 | 0.5226 / 0.5909 (lag 1) | 0.5368 / 0.5217 | -0.255 / -0.126 / -0.098 | 0.9647 | 0.9727 | 0.697 | 0.7535 | 0.9804 | 0.5869 |
| ETHUSDT | 2024-06-12 | 0.5958 / 0.5979 (lag 1) | 0.6526 / 0.5652 | 0.0723 / 0.2028 / -0.0867 | 0.9793 | 0.9594 | 0.6159 | 0.7569 | 0.9846 | 0.3094 |
| ETHUSDT | 2024-10-01 | 0.561 / 0.5804 (lag 1) | 0.5895 / 0.6087 | 0.1559 / 0.2909 / -0.1384 | 0.9408 | 0.959 | 0.5887 | 0.7326 | 0.9827 | 0.4064 |

## Funding

- Cached Bybit funding BTCUSDT: `data_cache/funding/BTCUSDT_funding_20240126T000000Z_20250301T000000Z.csv` 1200 rows 2024-01-26 00:00:00+00:00 .. 2025-02-28 16:00:00+00:00; missing 8h slots in Train-1: 0 / 1200.
- Cached Bybit funding ETHUSDT: `data_cache/funding/ETHUSDT_funding_20240126T000000Z_20250301T000000Z.csv` 1200 rows 2024-01-26 00:00:00+00:00 .. 2025-02-28 16:00:00+00:00; missing 8h slots in Train-1: 0 / 1200.
- Binance funding BTCUSDT (monthly fundingRate files, downloaded): 1200 rows in Train-1, missing 8h slots 0 / 1200; columns `calc_time, funding_interval_hours, last_funding_rate`.
- Binance funding ETHUSDT (monthly fundingRate files, downloaded): 1200 rows in Train-1, missing 8h slots 0 / 1200; columns `calc_time, funding_interval_hours, last_funding_rate`.

## Recommendation

**Highest common free resolution over Train-1 is 5m** (tick for flow). Build the 5m frame on **Bybit** (same venue as the bot): OI from `/v5/market/open-interest` 5min (covered; already pulled to `data_cache/open_interest_5m/`), long/short account ratio from `/v5/market/account-ratio` 5min (covered), and taker flow (taker_buy/sell, OFI, CVD, trade_count) rebuilt from the `public.bybit.com/trading` tick archive (covered; ~42.95 GB gz for both symbols). Use **Binance data.binance.vision** as the cross-venue / robustness layer: `metrics` 5m (covered; OI, top-trader and global L/S, taker L/S vol ratio) and `klines` 5m with taker_buy_volume + count (covered) — cheap (tens of MB); `aggTrades` (covered, ~15.45 GB) only if Binance tick flow is needed. Funding stays 8h (cached Bybit). Liquidations: no free history → live collector only. Caveat: cross-venue 5m OI-change direction agreement on the sample days is only 0.52-0.60 (1h: 0.52-0.78), so Bybit and Binance OI are distinct series (treat them as separate features, do not splice/substitute one for the other).

## Notes / caveats

- Taker-side semantics confirmed empirically: Bybit rebuilt 5m taker-buy vs Binance kline taker_buy_volume corr 0.941-0.989, taker-sell corr 0.959-0.986 on the sample days.
- Bybit OI conventions (from the pulled rows): openInterest/singleOpenInterest ratio range BTCUSDT: {'min': 2.0, 'max': 2.0}; ETHUSDT: {'min': 2.0, 'max': 2.0}; cached 1h OI vs 5m openInterest at HH:00 exact-equal fraction BTCUSDT: 1.0; ETHUSDT: 1.0. Pick one convention (singleOpenInterest = one-sided) and use it consistently.
- Bybit OI/account-ratio retention verified by a 1-day-window probe at every month start since 2018-01, day bisection, intra-day paging and an explicit empty-before check (see earliest_search).
- Bybit REST startTime/endTime are both inclusive; pulls use non-overlapping chunks [t, t+limit*step-1] (the full pulls report 0 duplicates and 0 off-grid rows).
- Bybit trade-archive `side` is the taker side (Buy = aggressive buy); Binance klines taker_buy_volume is the taker-buy base volume; Binance aggTrades is_buyer_maker=true means taker sell.
- Cross-check correlations are a sanity check of reconstruction/alignment only, not a test.
- Sample downloads and full pulls are in the main repo data dir (git-ignored), not committed.
