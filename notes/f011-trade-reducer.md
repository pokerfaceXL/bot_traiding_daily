# Disk-safe Bybit 5m trade reducer — continuation handoff

The first F011 T1b slice implements the streaming trade reducer only. The complete
5m feature frame and the full 800-symbol-day Train-1 reduction are not delivered.
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

## Remaining slice

Run the remaining 798 symbol-days using the guarded reducer, then build the
causal 5m frame from verified Plan-C inputs. No background full-range process was
left running. Reduced sample days are retained both here and in the external
bundle; copy CSV + matching manifest together to reuse them in another cache.

The frame builder still needs Bybit 5m OI/account ratio/OHLCV, cached funding,
separate `bn_` metrics/klines, frozen rolling choices, typed-null liquidations,
full-range CVD, 115,200 rows/symbol, OI full-hour reconciliation and frame
causality tests. Prefer `openInterest` if reconciling unchanged cached hourly OI;
the coverage report proves it matches exactly, while `singleOpenInterest` is 2x
smaller. The frame builder must document whichever convention it chooses.

No collector service, `data_cache/liquidations`, strategy, live bot or catalog
changes. No labels, event study, signals or backtests. No ticket/board edits.
