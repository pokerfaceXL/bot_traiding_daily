# F011 · Live liquidation collector (Bybit allLiquidation, non-trading)

## Outcome

A small, robust process that subscribes to Bybit public WebSocket
`wss://stream.bybit.com/v5/public/linear` topics `allLiquidation.BTCUSDT` and
`allLiquidation.ETHUSDT` and persists every raw event, so we build our own liquidation
history starting now (Bybit serves no liquidation history). Owner-approved 2026-10-05.

## Scope

- `forced_flow_lab/liq_collector.py`: connect, subscribe, ping every 20s, auto-reconnect with
  backoff, write each raw message (plus local receive timestamp) as one JSON line to
  `data_cache/liquidations/bybit/<SYMBOL>/<YYYY-MM-DD>.jsonl` (UTC day rotation, append,
  flush per line). Log connects/disconnects/gaps to `data_cache/liquidations/bybit/collector.log`.
- Heartbeat file updated every minute (last message time per symbol) so a monitor can detect
  a dead collector.
- A systemd **user** unit file `deploy/f011-liq-collector.service` (Restart=always) and a
  short `forced_flow_lab/LIQ_COLLECTOR.md` with start/stop/status commands. Do not enable or
  start it yourself; the coordinator deploys it.
- A unit test for message parsing/rotation using a recorded sample message (no network in tests).
- Ensure `data_cache/liquidations/` is git-ignored (raw data never committed).

## Out of scope

Any feature, label, signal or backtest. Other venues (can be added later). Live bot changes.

## Acceptance

Run the collector for ~2 minutes in the job and show that files were written (liquidations may
be sparse; subscription success messages count as proof of connectivity). pytest green.
