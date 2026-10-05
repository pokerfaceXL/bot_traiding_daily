# Retained OI evidence and collector recovery

Review source: `.limen/jobs/2026-10-05-f011-plan-c-review-d541f1e0/result` in the coordinator checkout. Both active F011 data-coverage and liq-collector tickets govern this slice.

The prepared worktree did not contain required base `3101d78`. Merge `aec6631` brings that candidate into this branch; ancestry now passes. No ticket, board, live trading code, deployed service, or `/home/limen/f011-liq-collector` edits.

## Seams and evidence

- `scripts/f011_data_coverage.py`: `bybit_spot_check` now retains each response and puts its relative path beside the derived count. `--refresh-oi-spots` updates only the four 15min probes and their table entries in an existing report; it preserves other measurements and records a separate refresh timestamp/request count. Re-run with `python3 scripts/f011_data_coverage.py --refresh-oi-spots`.
- Four real API responses fetched on 2026-10-05, 96 rows each, under `output/f011_forced_flow/coverage/raw/bybit/oi_15min_*_spot.json`; about 48 KiB allocated total. No bulk downloads. Report/JSON regenerated. Other historical measurements were reused, not independently re-fetched in this repair.
- Optional full-pull recommendation generation no longer indexes absent `train1_full_pull`; it calls full-window coverage unverified rather than claiming a download happened.
- `forced_flow_lab/liq_collector.py`: subscription NACK is persisted, then triggers reconnect/backoff/resubscription; pongs cannot mask it. Outer retry loop checks duration; backoff and connection timeout are bounded by remaining duration. `LIQ_COLLECTOR.md` now identifies Buy as a liquidated long, Sell as a liquidated short, with the official documentation link.

## Discriminating checks

- Original reviewer simulation reproduced NACK + pongs staying unsubscribed for 85 seconds, and `--duration=2` retrying through 31.4 seconds. Original recommendation raised `KeyError('train1_full_pull')` without full pulls. All four required spot responses were absent.
- Added offline tests in `forced_flow_lab/test_liq_collector_recovery.py` and `tests/test_f011_data_coverage.py`. Scoped run before capture: 13 passed, 1 failed on missing `raw_file`. After real capture: 14 passed. Tests check exact retained JSON, report equality, each count's source, NACK persistence/resubscription, pings/final heartbeat, immediate failures, connection timeout, zero duration, and clipped exponential backoff.
- Full pytest after code commit `b21a2f5`: first run had 2 failures, 518 passed, 8 skipped; both failures were absent local BTC/ETH Train-1 hourly OHLCV CSVs. Copied those two existing CSVs from the coordinator checkout into this worktree (about 1.2 MiB, git-ignored; no downloads or symlinks). Re-run: **520 passed, 8 skipped in 17.85s**. Cache checksum validation ran as part of the formerly failing causality tests.
- `git diff --cached --check` passed before the code commit. Logs and reviewer-readable report/JSON/raw copies are exported to `/tmp/f011-plan-c-fix-evidence/` outside this worktree. The refresh command originally printed the preserved original run's 3137-request/683.5s metadata; that console message was corrected before the code commit. Refresh metadata and report correctly record the four new requests.

## Boundaries for the next worker

No live collector smoke run or deployed-service restart was performed; this repair tests collector recovery offline. Deployment of the repaired collector remains the coordinator's decision. Board drift noted by review remains for the coordinator; `spec/build.md` must not be edited by this job. The full network coverage probe was not rerun.
