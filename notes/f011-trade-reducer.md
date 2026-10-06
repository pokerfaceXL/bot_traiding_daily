# Disk-safe Bybit 5m trade reducer — continuation handoff

Status 2026-10-06: the full Train-1 reduction and both 5m feature frames are
built and committed. See "Full-range run and frame build (PROVEN)" below. The
reducer safety contract and integration conventions in this file are unchanged.
Ticket: `spec/features/active/F011-forced-flow-frame-5m/ticket.md`.
Free-source authority: `output/f011_forced_flow/coverage/report.md`.

## Entry point and safety contract

```sh
# Both symbols, all 400 days; end is exclusive. Resume uses the same command/cache.
python3 -m forced_flow_lab.reduce_trades_5m
# Small real-network check, not the full Train-1 acceptance run:
python3 -m forced_flow_lab.reduce_trades_5m --start 2024-06-12 --end 2024-06-13
```

`forced_flow_lab/reduce_trades_5m.py` writes per-symbol/day CSVs and SHA256
manifests to `data_cache/bybit_trades_5m/` (now git-ignored). No new dependencies.
A nonblocking Linux flock serializes both symbols and recovery in that cache.
Use one shared cache path for all reducer invocations; locks do not coordinate
different cache directories or unrelated processes writing to the same disk.

Only `.raw-day.csv.gz` holds a compressed raw day. Download writes are 1 MiB
chunks; gzip/CSV reduction retains 288 accumulators, never the whole trade table.
Each day and each write checks free space: 10 GiB minimum plus 16 MiB headroom
plus pending payload size. A failed guard exits 2, removes the current raw/partial
files, and preserves earlier verified outputs. No lowering-the-guard CLI option.
Checks cannot reserve space against unrelated disk consumers; the manifests and
stdout record sampled free-space minima, not continuous filesystem monitoring.

The output is atomically replaced, raw removed, then the manifest published as
the completion marker. Resume skips only matching schema version, symbol, day,
row count and SHA256. Missing/corrupt outputs are rebuilt. A killed process's raw
and owned partial files are removed under the cache lock before another download.
Abrupt SIGKILL can leave that single raw day until the next invocation. HTTP or
corrupt-gzip failures stop rather than advancing to another day; rerun to retry.

## Frame integration contract

- `timestamp` is UTC bar open; `available_at` is its close. Flow in `[t,t+5m)` is
  unavailable until `t+5m`; do not join it as information known at open `t`.
- Taker `Buy`/`Sell` sizes are base-asset volume. `ofi=(B-S)/(B+S)`;
  `delta_cvd=B-S`. `cvd_day` resets at midnight. The frame must cumsum
  `delta_cvd` across the full ordered range, not concatenate daily CVD levels.
- All 288 buckets are output. Empty buckets have zero volume/count/OFI and are
  explicitly listed in manifests; inspect those lists, not just row counts.
- Exact decimal seconds determine bucket membership. The coverage sample code
  rounds seconds to milliseconds first, which can move a trade to the next bar.
  Do not copy that rounding into the frame or an expected-output oracle.

## Checks and evidence

External reviewer bundle:
`/home/limen/f011-artifacts/2026-10-05-f011-forced-flow-frame-5m-ab57d483/`.
It contains test logs, real sample CSVs/manifests, per-day/resume JSONL, and an
independent streaming Decimal oracle (`verify_sample.py`, no raw disk writes).

- Initial `python -m pytest ...` could not run: this host has no `python` command.
  `python3 -m pytest -q forced_flow_lab/test_reduce_trades_5m.py` passed first
  15 tests, then 16, and finally **17 passed** after all safety/boundary cases.
- Tests inject low space before a day and between chunks, proving no second chunk
  is written and raw is deleted. Other tests cover preserved prior days, checksum
  skip/rebuild, cache exclusion lock, interrupted manifest, network/truncated gzip
  cleanup, stale raw recovery, invalid trades, sub-float timestamp precision and
  future-trade perturbation leaving the earlier closed bar unchanged.
- Real 2024-06-12 downloads: BTC 1,764,280 trades, ETH 907,225 trades, each 288
  bars, zero empty buckets. Rerun reports `verified-skip` for both. Raw and partial
  files are absent. Minimum observed free space was 33,649,487,872 bytes (BTC)
  and 33,681,457,152 bytes (ETH), both above the guard. Exact observations are in
  `sample-run.jsonl` and manifests.
- The initial equality check against coverage reconstruction **failed** for BTC
  trade counts. An independent Decimal pass through the original archive matched
  the new reducer (max volume difference < 5.1e-9) and explained the discrepancy:
  Sell 0.003 BTC at `1718202599.9997` belongs before 14:30 UTC, but the old probe
  rounds it into 14:30. The oracle also reproduces all old rounded counts/volumes.
  ETH has no such moved trade on this sample day. Coverage files were not edited.

The full native lane ran once after candidate commit `72a84b8`:
`python3 -m pytest -q` → **537 passed, 8 skipped in 17.84s**. Before this run,
the two existing BTC/ETH hourly OHLCV CSV prerequisites were copied from the
coordinator checkout into this worktree (git-ignored, no symlinks/downloads).
`git diff --cached --check` also passed before the candidate commit. The full
Train-1 reducer run, complete 5m frame acceptance, and frame-specific 5m OI
reconciliation have **not** run.

## Full-range run and frame build (PROVEN)

Reduction (`python3 -m forced_flow_lab.reduce_trades_5m`, one shared cache) ran to
completion on 2026-10-06 for all 400 days × 2 symbols: 798 `written` + 2
`verified-skip` (the pre-existing 2024-06-12 samples). All 800 day CSVs exist and
checksum-verify; zero days carried empty 5m buckets; BTC reduced 675,698,155
trades. Global minimum observed free space across the run was 33,270,108,160 bytes
(30.99 GiB) — never near the 10 GiB guard. After the run `.raw-day.csv.gz` and all
`*.part` files were absent. Per-day evidence (status, free-byte minima, trade
counts): `/home/limen/f011-artifacts/frame-5m-continuation/reduction.jsonl`.

Inputs: `python3 -m forced_flow_lab.fetch_inputs_5m --reuse-cache <checkout>/data_cache`
fetched Bybit 5m OHLCV (REST kline, grid-exact) and the Binance `bn_` daily ZIPs
(metrics + 5m klines), held in memory; it only reuses/copies the already-verified
coverage inputs (5m OI, 5m account ratio, cached 8h funding, cached 1h OI) and the
hourly `_60_` OHLCV data-contract cache. It never reads `data_cache/liquidations`
nor the Bybit tick archive (that is the reducer's job alone).

Frame: `python3 -m forced_flow_lab.build_frame_5m` wrote
`output/f011_forced_flow/frame_5m/<SYMBOL>.csv.gz` + manifest (committed). Both
symbols: 115,200 rows, 56 columns, warm-up 2,016 bars (= max rolling window =
7 days of 5m OI/funding z-score). Zero post-warm-up nulls/infinities in the Bybit
core columns; liquidation columns are float64 all-null (deliberate, no free
Train-1 history); only the `bn_` metrics layer carries ~127–144 listed nulls where
Binance dropped 5m metric bars (klines and all Bybit core series are complete).
Hourly OI reconciliation: 9,600 hours matched, max |diff| 0.0, using the
`openInterest` (two-sided) convention that equals the cached 1h OI exactly;
`singleOpenInterest` (2x smaller) is not used. CVD is `cumsum(delta_cvd)` from a
zero baseline at Train-1 start, never reset at midnight. Funding is the latest
settlement ≤ bar open, strictly <8 h old, flagged (`funding_filled`, 114,000 bars)
with `funding_age_minutes`.

Checks run (not merely present): `python3 -m pytest -q` → **547 passed, 8
skipped** (the pre-existing 8 skips; the 1h `test_causality` now passes because the
hourly `_60_` caches are present). Focused: `test_frame_5m.py` **10 passed**,
`test_reduce_trades_5m.py` **17 passed**. The strongest frame check is
`test_compute_frame_is_prefix_causal`: recomputing on truncated input prefixes
leaves every earlier row byte-identical, proving no feature reads future bars. An
independent reconciliation unit test (`reconcile_hourly_oi`) covers both the exact
match and the mismatch/missing-hour failure paths. A rebuild with the final code
reproduced `frame_sha256` 27a31d89… (BTC) / 1b5c76848… (ETH).

## Remaining slice

The T1b frame is complete; the next tickets are F011-forced-flow-states and
-event-study, which consume these frames. Before any downstream join, honor the
row-availability rule: a row timestamped `t` is only known at `available_at`=t+5m
(state snapshots at t, completed candle/flow over [t,t+5m)). Liquidation columns
stay null for Train-1; the live collector's data (from 2026-10-05) is outside this
window and is a separate future layer. The `bn_` columns are cross-venue
robustness only — never substitute them for Bybit OI.

To reproduce from an empty cache: run the reducer (≈25 GB transient, one raw day
at a time), then `fetch_inputs_5m --reuse-cache` (or let it fetch Bybit 5m OHLCV
and hourly `_60_` from REST if no reuse cache), then `build_frame_5m`. The
`data_cache/{bybit_trades_5m,frame_5m_inputs,open_interest_5m,account_ratio_5m}`
trees are all git-ignored and re-fetchable.

No collector service, `data_cache/liquidations`, strategy, live bot or catalog
changes were made. No labels, event study, signals or backtests. No ticket/board
edits.
