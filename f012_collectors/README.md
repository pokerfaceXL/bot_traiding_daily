# F012 collectors (free prospective, non-trading)

Two optional collectors that store **raw / slim observations** useful whether or not
F012 is accepted. They never place orders and **must not** touch
`f011-liq-collector`.

| Unit | Script | Data | Cap |
| --- | --- | --- | --- |
| `f012-deribit-book.timer` | `deribit_book_summary.py` | Slim Deribit BTC/ETH option book summaries → `data_cache/f012/deribit_book/` | **2 GB** dir + refuse if free &lt; 5 GB |
| `f012-farside-etf.timer` | `farside_etf_flows.py` | Farside BTC/ETH ETF daily flow CSVs → `data_cache/f012/etf_flows/` | 64 MB dir + free &lt; 5 GB floor |

## Install (systemd user, same pattern as F011)

```bash
REPO=~/bot_traiding_daily/bot_traiding_daily
mkdir -p ~/f012-collectors ~/.config/systemd/user
cp $REPO/f012_collectors/deribit_book_summary.py \
   $REPO/f012_collectors/farside_etf_flows.py \
   $REPO/f012_collectors/disk_guard.py \
   $REPO/f012_collectors/__init__.py \
   ~/f012-collectors/
# Make imports work when ExecStart runs from ~/f012-collectors
touch ~/f012-collectors/f012_collectors_path.pth  # unused; PYTHONPATH set in unit
cp $REPO/deploy/f012-deribit-book.service $REPO/deploy/f012-deribit-book.timer \
   $REPO/deploy/f012-farside-etf.service $REPO/deploy/f012-farside-etf.timer \
   ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now f012-deribit-book.timer f012-farside-etf.timer
loginctl enable-linger "$USER"
```

The service files set `PYTHONPATH=%h/bot_traiding_daily/bot_traiding_daily` so
`import f012_collectors...` resolves from the repo (not the copied stubs). Copied
scripts are only a fallback; **ExecStart calls the repo paths**.

## Stop

```bash
systemctl --user stop f012-deribit-book.timer f012-farside-etf.timer
systemctl --user disable f012-deribit-book.timer f012-farside-etf.timer
# one-shot services if running:
systemctl --user stop f012-deribit-book.service f012-farside-etf.service
```

## Manual smoke

```bash
cd ~/bot_traiding_daily/bot_traiding_daily
python3 -m f012_collectors.deribit_book_summary --out-dir /tmp/f012-deribit-smoke
python3 -m f012_collectors.farside_etf_flows --out-dir /tmp/f012-etf-smoke
python3 -m pytest -q f012_collectors
```

## Schema notes

- Deribit: one gzipped JSONL file per UTC day; each line is one instrument slim row
  with `run_ts` / `run_ts_ms` (collector clock, UTC).
- Farside: full history CSV replaced each run; `last_fetch.json` stores fetch time and
  row counts (HTML body not retained).
