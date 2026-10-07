# F013 · Delisting Informational Alpha — informational underreaction after public delisting announcements

> **OWNER MANDATE (written), 2026-10-07 Europe/Warsaw.** New track F013. Informational
> **underreaction** after a public delisting announcement — **not** forced-flow, **not** C02 revival.
> Proceed under the written owner mandate only; do not contact the ChatGPT PO session
> (`f006-chatgpt-po`), Slack, or email.
> The F013 number is now owned by this track. The earlier F013 structural-edge brief
> (`spec/research/F013-structural-edge-identification-brief.md`) stays a historical NO CANDIDATE.
> Supersedes the parked note `spec/research/F012-delisting-informational-alpha-parked.md`.

## Question
After a venue publicly announces a token's perp/spot delisting, does the token keep falling after the
first publicly observable time P, net of realistic costs, outside the contaminated discovery sample?
The C02 incidental naive short (+938 / +508 bp, Train-1) is **hypothesis-generating only**. Goal:
**destroy** it. Strategy work starts only if it survives every attack and the frozen OOS validation.

## SSOT
- Pre-registration (frozen before any F013 scoring): `spec/research/F013-delisting-informational-alpha-prereg.md`
  — copy in `prereg.md` (this folder). Signal, latency, universe, horizons, costs, gates A–Q, validation
  window, decision rules.
- Discovery = C02 Train-1 events (CONTAMINATED). Validation = announcements [2025-03-01, 2026-03-01)
  UTC, untouched. Sealed holdout [2026-03-01, 2026-09-01).

## Deliverables (first job)
- Feature folder (this `ticket.md` + `prereg.md`), research prereg note, board/journal update, parked
  note marked superseded.
- **Gate A** timestamp audit: `delisting_lab/f013_raw.py` (raw re-fetch, public endpoints, cache
  `data_cache/f013/raw/`), `delisting_lab/f013_timestamp_audit.py`;
  outputs `output/f013_delisting_info/gate_a_timestamp_audit.{csv,md}`; tests
  `tests/test_f013_timestamp_audit.py` (no network).
- `output/f013_delisting_info/STATUS.md`. Next gate = B.

## Constraints
- No ML, optimizer, feature search, exit optimization. Equal-notional sizing for validation.
- Cost: owner ≈ 9.9 bp RT is context; decision ladder 34/50/75/100/150/200 bp RT (prereg §4).
- Reuse `delisting_lab/` and `output/f012_c02_delisting/` read-only; never mutate C02 decision artifacts.
- Do not reopen F011 / C01 / C02 forced-unwind / C03 / F012 R2-B/C without genuinely new data.
- `f011-liq-collector` keeps running unchanged; F012 timers stay SUNSET. No systemd/collector edits.
- No live bot, no orders, no `git reset --hard`.

## Verdict
Exactly one of **PASS | CONDITIONAL | FAIL**, per prereg §10. FAIL → archive. PASS → STOP before any
live bot or optimization (owner decision). CONDITIONAL → condition observable at P + independent validation.
