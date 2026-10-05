# F011 · Free high-resolution data coverage (T0 recon, non-trading)

## Outcome

An evidence-based coverage report answering: what free historical data at 5m (or finer)
resolution can we actually obtain for BTCUSDT + ETHUSDT perps over Train-1
(2024-01-26T00Z .. 2025-02-28T23Z), from Bybit and Binance? Owner decision 2026-10-05:
use the maximum free resolution first; **no paid vendor**; the hourly OI frame is only a
coarse baseline, never a go/no-go verdict on forced-flow. This report decides which source(s)
the 5m frame (next ticket) is built from.

## Scope — verify empirically, do not trust docs or assume retention

For each source, record: earliest timestamp actually returned/listed, whether Train-1 is fully
covered, missing periods (gaps), resolution, fields, and approximate full-window size on disk.

1. Bybit `/v5/market/open-interest` intervalTime=5min (and 15min) — paginate backwards with
   startTime/endTime/cursor; find the true earliest reachable bar for both symbols.
2. Bybit `/v5/market/account-ratio` period=5min — same pagination test.
3. Bybit public trade archive (`https://public.bybit.com/trading/<SYMBOL>/`) — confirm daily
   files exist for every Train-1 day, fields (timestamp, side=taker side, size, price),
   per-day compressed size (sample a few days; HEAD/listing only for the rest). Download at
   most 2 sample days per symbol to verify schema and that 5m taker_buy/taker_sell/OFI/CVD/
   trade_count can be reconstructed.
4. Binance `https://data.binance.vision/` futures/um daily: `metrics` (5m sum_open_interest,
   long/short ratios, taker long/short vol ratio), `klines` 5m (taker_buy_base_volume,
   trade count), `aggTrades`. Same checks: coverage, gaps (list missing days), size.
5. Funding (both venues) — confirm already-cached funding covers Train-1 for both symbols.
6. Cross-check on 2 overlap days: Bybit 5m OI vs Binance 5m OI direction agreement, and
   reconstructed Bybit taker flow vs Binance kline taker volume (sanity only, not a test).

## Out of scope

- Any feature engineering beyond the sample reconstruction, any label, signal, backtest.
- Downloading full archives (that is the next ticket, after this report).
- Paid vendors; liquidation history (live collector is a separate ticket).

## Deliverables

- `scripts/f011_data_coverage.py` (re-runnable probe).
- `output/f011_forced_flow/coverage/report.md` + `coverage.json` with a table per
  source × symbol: earliest, Train-1 covered (y/n), gaps, resolution, fields, est. size,
  plus a one-paragraph recommendation of the highest common resolution and source(s).
- No changes to live bot, strategy.py or catalog. `python3 -m pytest -q` stays green.

## Acceptance

Every number in the report comes from an actual API response or listing captured by the
script (store raw probe responses under `output/f011_forced_flow/coverage/raw/`, small).
