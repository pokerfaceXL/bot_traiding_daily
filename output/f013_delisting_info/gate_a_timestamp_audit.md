# F013 Gate A — timestamp integrity audit

Sample: C02 Train-1 discovery catalog (`output/f012_c02_delisting/event_catalog.csv`, CONTAMINATED discovery set). No prices read; no alpha scored. Rules frozen in `spec/features/active/F013-delisting-informational-alpha/prereg.md` §Gate A.

## Verdict: **Gate A PASS** — usable 92.6% ≥ 85%, worst-venue FAIL 11.4% ≤ 25% (n=163)

Primary timestamp **P = first_publicly_observable_ts** (choice B). Secondary S = announcement_ts (choice A) is audit-only. FAIL events are excluded from every later gate; WARN events stay in the primary sample and are re-run as a PASS-only robustness split.

## Status by venue (events)

| exchange | FAIL | PASS | WARN | All |
|---|---|---|---|---|
| binance | 0 | 54 | 4 | 58 |
| bybit | 12 | 38 | 55 | 105 |
| All | 12 | 92 | 59 | 163 |

Articles: 86 (15 Binance, 71 Bybit).

## Reason counts (events; one event may carry several)

| reason | events |
|---|---|
| W5_observability_lag_gt_15m | 34 |
| W4_publishTime_post_event_edit | 16 |
| F3_ambiguous_late_push | 12 |
| W4_publishTime_early_push | 5 |
| W2_instrument_delivery_mismatch | 3 |
| W3_effective_revised | 1 |

## Raw-source re-verification

- **binance**: raw anchor re-fetched for 58/58 events; |anchor − catalog| ≤ 60 s for 58; max |diff| 9.5 s.
- **bybit**: raw anchor re-fetched for 105/105 events; |anchor − catalog| ≤ 60 s for 105; max |diff| 0.0 s.
- Bybit API list (re-fetched today) serves 105/105 catalog events; dateTimestamp equal to catalog for 105; publishTime equal to the C02-cached value for 105. publishTime is still not a proven first-push clock: gaps of days/months exist (W4/F3).
- Binance `publishDate − releaseDate`: min -9.5 s, max 0.0 s (negative = publishDate earlier, so P = releaseDate is the later, conservative clock).
- Binance: the catalog anchor is CMS `releaseDate`; detail `publishDate` is the re-fetch. Both are Binance CMS clocks — no third-party observability clock exists in the free data. Residual risk: an article staged before `releaseDate` cannot be detected here.

## Body-parsed effective times

- Consistency check, not an independent parser: re-fetched bodies run through the same C02 parser. It proves the body text did not change and the catalog matches today's source.
- Re-parsed from re-fetched bodies: 163/163; match catalog announced effective_ts (±60 s): 163; mismatch: 0; unparsed: 0.
- Instrument delivery cross-check |Δ| > 1 min: 3 of 75 with a reported delivery time.
- Postponed (effective_revised): 1.
- Notice length from P (h): n=163 min 21.4 p25 120.0 p50 167.9 p75 192.0 p90 332.0 max 1350.0.

## Observability lag P − S (seconds)

- binance: n=58 min 0.0 p25 0.0 p50 0.0 p75 0.0 p90 0.0 max 0.0; P ≠ S for 0/58.
- bybit: n=105 min 0.0 p25 0.0 p50 151.0 p75 1476.0 p90 10554.0 max 21403.0; P ≠ S for 71/105.
- all: n=163 min 0.0 p25 0.0 p50 0.0 p75 364.5 p90 4773.6 max 21403.0; P ≠ S for 71/163.

Look-ahead exposure if entries were timed from S instead of P (share of events where S + latency is still before P):

| latency | events where S+latency < P | share |
|---|---|---|
| 10s | 70 | 42.9% |
| 30s | 70 | 42.9% |
| 60s | 66 | 40.5% |
| 300s | 42 | 25.8% |
| 900s | 34 | 20.9% |

## ts_flag rates (C02 catalog)

- events with a ts_flag: 33/163 (20.2%); Bybit 33/105; Binance 0/58.
- Bybit publishTime classes (events): within_gap 72, post_event_edit 16, ambiguous_late_push 12, early_push 5.

## A vs B primary timestamp choice

- **B (first_publicly_observable_ts) is primary — frozen.** It is ≥ A for every event by construction and audited above; entries are only legal at P + latency.
- A (announcement_ts) is retained for audit only. Using A as the clock would place entries before public observability for the share shown in the look-ahead table; it is forbidden as a trading clock.
- F3 (ambiguous late push) events are dropped instead of re-timing them to publishTime: re-timing would be a post-hoc choice, and the drop is the conservative frozen rule.

## FAIL events (excluded downstream)

| event_id | gate_a_reasons | catalog_ts_flag |
|---|---|---|
| BYBIT-202403190836-STRAXUSDT | F3_ambiguous_late_push | publishTime_gap_19.4h_ignored |
| BYBIT-202408080559-DEFYUSDT | F3_ambiguous_late_push | publishTime_gap_26.0h_ignored |
| BYBIT-202408080559-HONUSDT | F3_ambiguous_late_push | publishTime_gap_26.0h_ignored |
| BYBIT-202408080559-KUNCIUSDT | F3_ambiguous_late_push | publishTime_gap_26.0h_ignored |
| BYBIT-202409180800-LFWUSDT | F3_ambiguous_late_push | publishTime_gap_28.2h_ignored |
| BYBIT-202411290804-AZYUSDT | F3_ambiguous_late_push | publishTime_gap_78.3h_ignored |
| BYBIT-202411290804-HEROUSDT | F3_ambiguous_late_push | publishTime_gap_78.3h_ignored |
| BYBIT-202411290804-LENDSUSDT | F3_ambiguous_late_push | publishTime_gap_78.3h_ignored |
| BYBIT-202411290804-RUBYUSDT | F3_ambiguous_late_push | publishTime_gap_78.3h_ignored |
| BYBIT-202501201243-BTGUSDT | F3_ambiguous_late_push | publishTime_gap_45.3h_ignored |
| BYBIT-202501201243-DPXUSDT | F3_ambiguous_late_push | publishTime_gap_45.3h_ignored |
| BYBIT-202501201243-DZOOUSDT | F3_ambiguous_late_push | publishTime_gap_45.3h_ignored |

## Reproduce

`python3 -m delisting_lab.f013_timestamp_audit --refetch` (network, public endpoints, cache `data_cache/f013/raw/`), then without `--refetch` offline.
