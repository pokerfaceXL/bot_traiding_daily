# F013 Delisting Informational Alpha — STATUS

**2026-10-07 Europe/Warsaw · Gate A PASS · next gate = B (latency decay, discovery set)**

## Shipped
- Prereg (gates A–Q, decision rules, validation window), frozen before any scoring:
  `spec/research/F013-delisting-informational-alpha-prereg.md` (SSOT) +
  `spec/features/active/F013-delisting-informational-alpha/{ticket,prereg}.md`.
- Gate A code: `delisting_lab/f013_raw.py` (raw re-fetch, public endpoints → `data_cache/f013/raw/`,
  git-ignored), `delisting_lab/f013_timestamp_audit.py`; tests `tests/test_f013_timestamp_audit.py`.
- Gate A outputs: `gate_a_timestamp_audit.csv` (per event), `gate_a_timestamp_audit.md` (report).
- Board/journal updated; parked note `spec/research/F012-delisting-informational-alpha-parked.md`
  marked superseded.

## Gate A summary (C02 Train-1 discovery catalog, contaminated)
- 163 events (58 Binance / 105 Bybit; 86 articles): **PASS 92 / WARN 59 / FAIL 12**.
- Usable 92.6 % (bar ≥ 85 %); worst-venue FAIL 11.4 % Bybit (bar ≤ 25 %) ⇒ **PASS**.
- All 12 FAILs are Bybit F3 (publishTime 19–78 h after dateTimestamp, before delisting ⇒ first push
  ambiguous). Dropped from every later gate, not re-timed.
- Raw anchors re-verified for 163/163: Binance |publishDate − releaseDate| ≤ 9.5 s (publishDate earlier
  ⇒ P conservative); Bybit page `date` = `dateTimestamp` exactly; Bybit API `publishTime` unchanged vs the
  C02 cache.
- WARN reasons: W5 P − S > 15 min (34), W4 Bybit post-event edit (16) / early push (5), W2 instrument
  delivery mismatch (3), W3 postponed (1).
- Observability lag P − S: Binance 0 s for all (single CMS clock — a residual risk the free data cannot
  remove); Bybit median 151 s, p90 10 554 s, max 21 403 s.
- Look-ahead exposure if S were the clock: S + 10 s < P for 42.9 % of events; S + 15 min < P for 20.9 %.
  ⇒ **B = first_publicly_observable_ts is primary**; A = announcement_ts audit-only.
- ts_flag rate 33/163 (20.2 %), all Bybit.
- Side finding: the Bybit announcements API now serves delistings back to 2022-08 (482 items), so the
  validation-window Bybit catalog is buildable from the API.

## Not done (by design)
No price read, no alpha scored, gates B–Q not run, validation window not touched.

## Next
Gate B (entries P + 10 s/30 s/60 s from ticks, P + 1/5/15 min from 1m bars) on Gate-A-usable discovery
events, then C–N, P, Q. Any KILL ⇒ FAIL and validation stays closed.
