# F011 · Bybit liquidation collector — operations

`forced_flow_lab/liq_collector.py` subscribes to the Bybit public linear WebSocket
(`wss://stream.bybit.com/v5/public/linear`, topics `allLiquidation.BTCUSDT`,
`allLiquidation.ETHUSDT`) and writes every raw message plus the local receive time. Bybit
serves **no** liquidation history, so this is our only liquidation history; keep it running.
Non-trading, public data, no API key. Dependency: `websocket-client` (`import websocket`).

## Output (git-ignored: `data_cache/liquidations/`)

```
data_cache/liquidations/bybit/
  BTCUSDT/2026-10-05.jsonl   # one line per WS message, UTC day of receive time, append, flush/line
  ETHUSDT/2026-10-05.jsonl
  _control/2026-10-05.jsonl  # subscribe acks and any unexpected non-topic frames
  collector.log              # start/stop, connects, disconnects, gap length, acks, errors (UTC)
  heartbeat.json             # rewritten every 60s: pid, connected, last frame/pong, per-symbol
                             # last_message_at, messages/events since start
```

Line format: `{"recv_ts_ms": <local epoch ms>, "recv_ts": "<ISO UTC>", "msg": <raw Bybit JSON>}`
(non-JSON frames are kept as `"raw_text"`). Bybit payload: `msg.data[]` items with
`T` (event ms), `s` (symbol), `S` (side of the *liquidated position's order*: `Buy` = a short
was liquidated, `Sell` = a long was liquidated — check Bybit docs before relying on it),
`v` (size, base), `p` (bankruptcy price). Symbol files appear only once a liquidation arrives;
quiet periods are normal. Liveness = `heartbeat.json.updated_at` fresh (< 2-3 min) and
`last_pong_at` fresh; per-symbol `last_message_at` may legitimately be old.

Behaviour: ping `{"op":"ping"}` every 20s; reconnect on any error or if no frame for 75s, with
exponential backoff 1s→60s (reset after a session healthy >60s); re-subscribes on every connect;
SIGTERM/SIGINT stop cleanly.

## Deployment (stable paths, outside any temporary worktree)

```bash
mkdir -p ~/f011-liq-collector ~/.config/systemd/user
cp forced_flow_lab/liq_collector.py ~/f011-liq-collector/
cp deploy/f011-liq-collector.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now f011-liq-collector
loginctl enable-linger "$USER"     # otherwise the user manager (and the collector) stops at logout
```

The unit runs `~/f011-liq-collector/liq_collector.py --out-dir
~/bot_traiding_daily/bot_traiding_daily/data_cache/liquidations/bybit`, `Restart=always`.

## Start / stop / status

```bash
systemctl --user status f011-liq-collector
systemctl --user restart f011-liq-collector
systemctl --user stop f011-liq-collector       # disable: systemctl --user disable --now ...
journalctl --user -u f011-liq-collector -n 50  # (if the user journal is available)
D=~/bot_traiding_daily/bot_traiding_daily/data_cache/liquidations/bybit
tail -n 20 $D/collector.log; cat $D/heartbeat.json
wc -l $D/*USDT/*.jsonl
```

Fallback without systemd user (no linger): run under a restart loop, e.g.
`setsid nohup bash -c 'while true; do python3 -u ~/f011-liq-collector/liq_collector.py --out-dir $D; sleep 10; done' >/dev/null 2>&1 &`
and stop it by killing the loop's process group (`kill -- -<PGID>`).

Smoke test (2 min, scratch dir): `python3 forced_flow_lab/liq_collector.py --out-dir /tmp/liq-smoke --duration 120`.
Offline tests: `python3 -m pytest -q forced_flow_lab/test_liq_collector.py`.
