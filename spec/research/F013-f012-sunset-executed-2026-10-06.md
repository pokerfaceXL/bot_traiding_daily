# F013 — F012 collectors SUNSET executed (2026-10-06)

> Operational proof for ChatGPT PO-approved safe-stop of both F012 collectors.
> Docs-only commit; systemd state change is operational (no code). No data deleted.
> Human / Slack / email: **not contacted**.

## Authority

- PO decision note: `spec/research/F013-collector-portfolio-review-2026-10-06.md`
- PO approval (verbatim capture on box): ChatGPT PO approved SUNSET of both F012 timers; `f011-liq-collector` stays **REVIEW_AT_N**
- Host: `limen@100.98.80.81` (`lorenzian-free`), user systemd
- Repo tip before docs: `580c21d`

## Commands executed (no secrets)

```bash
# Before capture ~2026-10-06T20:28:00Z / 22:28 Europe/Warsaw
systemctl --user stop f012-deribit-book.timer f012-deribit-book.service
systemctl --user disable f012-deribit-book.timer
systemctl --user stop f012-farside-etf.timer f012-farside-etf.service
systemctl --user disable f012-farside-etf.timer
# After capture ~2026-10-06T20:28:08Z / 22:28 Europe/Warsaw
```

Disable removed:

- `~/.config/systemd/user/timers.target.wants/f012-deribit-book.timer`
- `~/.config/systemd/user/timers.target.wants/f012-farside-etf.timer`

## State before → after

| unit | before enabled/active | after enabled/active |
| --- | --- | --- |
| `f012-deribit-book.timer` | enabled / active (waiting) | **disabled / inactive (dead)** |
| `f012-deribit-book.service` | disabled / inactive | disabled / inactive |
| `f012-farside-etf.timer` | enabled / active (waiting) | **disabled / inactive (dead)** |
| `f012-farside-etf.service` | disabled / inactive | disabled / inactive |
| `f011-liq-collector.service` | enabled / active (running) MainPID=2460311 | **unchanged** enabled / active (running) MainPID=2460311 |

`systemctl --user list-timers --all` after: **0 timers listed**.

## Data preserved (not deleted)

| path | exists after | notes |
| --- | --- | --- |
| `data_cache/f012/deribit_book/` | **yes** | `deribit_option_book_2026-10-06.jsonl.gz` + `heartbeat.json` (mtime 19:56 UTC) |
| `data_cache/f012/etf_flows/` | **yes** | BTC/ETH CSVs + heartbeat + last_fetch (mtime 14:52 UTC) |

## Verifications

| check | result |
| --- | --- |
| both f012 timers disabled | PASS (`is-enabled=disabled`) |
| both f012 timers inactive | PASS (`is-active=inactive`) |
| both f012 oneshot services inactive | PASS |
| data dirs still exist | PASS |
| `f011-liq-collector` still active | PASS (same MainPID 2460311; not stopped/restarted/modified) |
| no f012 units loaded/active | PASS (`list-units f012*` → 0) |

## f011 REVIEW_AT_N policy (confirmed, unchanged)

- **N = 50** independent, liq-defined cascade episodes **per symbol**
- Earliest checkpoint: **2026-10-20** Europe/Warsaw
- Measurement owner: **Limen coordinator**
- Decision owner: **ChatGPT PO**
- Not a license to reopen F011 tests now

## STOP

No F011 test, no new alpha family, no backtest, no candidate selection, no new collector.
