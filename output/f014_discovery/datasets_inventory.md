# F014 datasets inventory (Train-1 files only)

data_root: `/home/limen/bot_traiding_daily/bot_traiding_daily/data_cache`
window loaded: [2024-01-26 00:00:00+00:00, 2025-03-01 00:00:00+00:00) — validation/holdout files never read

| file | present | rows | first | last |
| --- | --- | --- | --- | --- |
| BTCUSDT/ohlcv | True | 9600 | 2024-01-26 00:00:00+00:00 | 2025-02-28 23:00:00+00:00 |
| BTCUSDT/funding | True | 1200 | 2024-01-26 00:00:00+00:00 | 2025-02-28 16:00:00+00:00 |
| BTCUSDT/oi_1h | True | 9600 | 2024-01-26 00:00:00+00:00 | 2025-02-28 23:00:00+00:00 |
| BTCUSDT/account_ratio_5m | True | 115200 | 2024-01-26 00:00:00+00:00 | 2025-02-28 23:55:00+00:00 |
| ETHUSDT/ohlcv | True | 9600 | 2024-01-26 00:00:00+00:00 | 2025-02-28 23:00:00+00:00 |
| ETHUSDT/funding | True | 1200 | 2024-01-26 00:00:00+00:00 | 2025-02-28 16:00:00+00:00 |
| ETHUSDT/oi_1h | True | 9600 | 2024-01-26 00:00:00+00:00 | 2025-02-28 23:00:00+00:00 |
| ETHUSDT/account_ratio_5m | True | 115200 | 2024-01-26 00:00:00+00:00 | 2025-02-28 23:55:00+00:00 |
| SOLUSDT/ohlcv | True | 9600 | 2024-01-26 00:00:00+00:00 | 2025-02-28 23:00:00+00:00 |
| SOLUSDT/funding | True | 1200 | 2024-01-26 00:00:00+00:00 | 2025-02-28 16:00:00+00:00 |
| SOLUSDT/oi_1h | True | 9600 | 2024-01-26 00:00:00+00:00 | 2025-02-28 23:00:00+00:00 |
| SOLUSDT/account_ratio_5m | False |  |  |  |

## Gaps / constraints

- SOLUSDT/account_ratio_5m: missing (SOLUSDT_account_ratio_5min_20240126T000000Z_20250301T000000Z.csv)
- liquidations/bybit: live only from ~2026-10-05 -> not usable for Train-1 discovery (collector untouched)
- 5m OHLCV: only 2-day samples -> primary bar is 1h
- account_ratio_5m and open_interest_5m: BTC/ETH only (no SOL) -> Family C has no bonus asset
- f012 deribit/etf: preserved read-only, not used
- funding / OI: Train-1 only -> Family B and H-TIME-FUNDING-HOUR cannot be re-scored on validation without a new discovery-window-safe fetch (not done here)
