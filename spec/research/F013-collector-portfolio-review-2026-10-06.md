# F013 — Collector portfolio review (2026-10-06)

> One-shot PO portfolio review of active collectors after **F012 CLOSED: NO CANDIDATE**
> and **F013 identification brief: NO CANDIDATE**. Docs only. No strategy, backtest,
> new collector, or alpha family. Services were **not** stopped in this review.
>
> Measured on limen at ~2026-10-06 19:35 UTC (21:35 Europe/Warsaw). Tip baseline `a6e38ef`.
> Primary cost remains owner-tier **≈ 9.9 bp RT**. Free PIT data remains a condition.

## Context

| Item | Status |
| --- | --- |
| F011 Forced-Flow Lab | **ARCHIVED** (T4 all-negative). Paid historical liq **NO-GO**. Unresolved only: `H-PRECASCADE-LIQ-01` |
| F012 structural-edge | **CLOSED, NO CANDIDATE** (C01/C02 mechanism-ID FAIL; C03/R2-A PIT-data FAIL, mechanism untested) |
| F013 identification brief | **NO CANDIDATE** (forced quantity has no free PIT history) |
| Board disposition | **structural-edge = PARKED — evidence constrained** (this note) |

Scope guards (binding): do not resume F011 cascades; do not reopen catalog mean-reversion,
funding-carry, or spread-capture; do not open a new structural-edge family or candidate list;
do not treat a larger sample as repair of a killed mechanism; do not change historical thresholds.

## Decision table

| collector | open hypothesis / closed gate | future data fixes blocker? | start / continuity / quality / PIT | N + earliest reassess | cost / risk / monitoring | **recommendation** |
| --- | --- | --- | --- | --- | --- | --- |
| `f011-liq-collector` | `H-PRECASCADE-LIQ-01`: crowding-only features → cascade labeled from **real liq volume** (removes circular OI label). Paid data only if free test clears PR-AUC ≥2× **and** monetisation vs ~9.9 bp RT (historical 34 bp band was stress/reference) | **Yes** — blocker is insufficient live episodes, not a killed identification | Start 2026-10-05T19:26:50Z; running ~24h; 1 WS drop/reconnect (~1.5s gap @ 06:14Z); BTC ≈547 / ETH ≈212 flattened events; heartbeat fresh; schema `recv_ts` + exchange `T` = PIT OK | **N = 50** independent liq-defined cascade episodes **per symbol**; earliest concrete date **2026-10-20** Europe/Warsaw (conservative; heuristic bursts ~5–9/day suggest possibly earlier — re-measure formally before reopen) | ~11 MB RAM; public WS; `Restart=always`; monitor `heartbeat.json` age <3 min + `collector.log` | **REVIEW_AT_N** |
| `f012-deribit-book.timer` | Collect-forward for options-constraint (C04 max-pain, C05 dealer charm/gamma). **C04 REJECTED** (919 expiries). **C05 REJECTED** until signed dealer exposure exists — public book summary cannot supply sign | **No** — unsigned OI snapshots only enlarge sample for rejected/blocked mechanisms | Timer since 2026-10-06T14:52Z; 5 hourly snaps in `deribit_option_book_2026-10-06.jsonl.gz` (~1720 rows/snap); heartbeat ok; 2 GB + 5 GB free-space caps | No open N. No reopen without a new PO-approved mechanism that needs unsigned book surface **and** a free PIT path for the missing input | Hourly oneshot; Nice=10; low CPU; disk-capped | **SUNSET** |
| `f012-farside-etf.timer` | C01 ETF NAV-window × prior-day public flow. **C01 = mechanism-identification FAIL** (Gate A large-day lift 1.38 < 1.5; B/C not reached) | **No** — larger sample does not repair a killed identification (PO rule). F012/F013 closed | Daily 21:30 UTC; last fetch 2026-10-06T14:52Z; BTC 702 / ETH 564 rows; full-history CSV rewrite; same-day cells often "-" until publish (known PIT lag) | No open N. Reopen only if PO amends C01 criteria **as a new pre-registration** (prior open question; not granted) | Tiny CSV; 64 MB cap; scrape risk if Farside HTML changes | **SUNSET** |

## Per-collector detail

### 1. `f011-liq-collector` — REVIEW_AT_N

1. **Hypothesis.** `H-PRECASCADE-LIQ-01` (recorded in `spec/research/F011-forced-flow-lab.md` §9b): using only *pre-stress* crowding variables (`oi_zscore`, `funding_zscore`, L/S, OI build-up — **no** STRESS flag, **no** OI-collapse inputs), predict a cascade defined independently from **real liquidation volume**.
2. **Does more data fix the blocker?** Yes. The forced-flow *strategy* is archived; this single gate remains open because the live free collector has not yet accumulated enough independent liq-defined episodes. Extra days enable the gate; they are not "more sample for a killed mechanism."
3. **Data state.** Continuous systemd user service; reconnect logic healthy; one short gap documented; event files append-only JSONL; control frames logged; heartbeat rewritten ~60s. Quality adequate for episode counting once a formal cascade definition is applied at review time.
4. **N and date.** Reassess when **both** symbols have ≥50 independent liquidation-defined cascade episodes (formal definition to be fixed in the reopen pre-registration, not here). Earliest calendar checkpoint: **2026-10-20 Europe/Warsaw**. May be earlier if formal counts hit N sooner; may be later if formal episodes are rarer than the heuristic bursts.
5. **Ops.** Keep enabled. Monitor: `systemctl --user status f011-liq-collector`; `data_cache/liquidations/bybit/heartbeat.json` freshness; weekly `wc -l` on symbol JSONL. Failure mode: WS ban/idle — Restart=always covers process death; long silence on *both* symbols + stale heartbeat warrants human/PO alert (no alert wired yet — checklist only).
6. **Reopen trigger / owners.**
   - **Trigger:** formal episode count ≥50/symbol from collector data **and** PO decision to run the free `H-PRECASCADE-LIQ-01` test (still no paid data until that test clears both PR-AUC and monetisation hurdles).
   - **Control owner (decision):** ChatGPT PO.
   - **Measurement owner:** Limen coordinator.
   - **N / date:** N=50/symbol; date gate 2026-10-20 Europe/Warsaw (whichever comes second unless N arrives first and PO advances).

### 2. `f012-deribit-book.timer` — SUNSET

1. **Hypothesis / gate.** No open identification gate. C04/C05 were rejected at candidate selection; F013 did not revive an options-constraint candidate with free signed exposure.
2. **Does more data fix the blocker?** No. Missing dealer sign (C05) and empirical max-pain failure (C04) are not cured by more unsigned hourly OI surfaces.
3. **Data state.** Healthy prospective store; PIT via `run_ts` / `run_ts_ms` on each slim row; continuity = 5/5 expected hours since install.
4. **N / date.** None — sunset, not review-at-N.
5. **Ops until sunset executed.** Timer still running (this review does not stop it). Low risk; disk guard present.
6. **Safe sunset procedure (DO NOT EXECUTE in this ticket — wait for next PO decision):**
   ```bash
   systemctl --user stop f012-deribit-book.timer f012-deribit-book.service
   systemctl --user disable f012-deribit-book.timer
   # PRESERVE data — do not delete:
   #   data_cache/f012/deribit_book/
   # optional: copy to offline archive, keep gitignore as-is
   ```
   After stop: confirm `systemctl --user is-active f012-deribit-book.timer` → inactive; leave JSONL.gz + heartbeat on disk.

### 3. `f012-farside-etf.timer` — SUNSET

1. **Hypothesis / gate.** C01 identification FAIL on pre-registered Gate A. Forecasting flow from lagged public prints is not compulsion.
2. **Does more data fix the blocker?** No. PO rule: do not treat larger sample as repair of a wrong mechanism. Threshold 1.5 stays.
3. **Data state.** Full history re-scraped daily; PIT of *fetch* is `last_fetch.json` / `run_ts`; historical cell edits on Farside side are a known external risk (same as C01). Quality fine for archival.
4. **N / date.** None — sunset.
5. **Ops until sunset.** One daily scrape; negligible cost.
6. **Safe sunset procedure (DO NOT EXECUTE now):**
   ```bash
   systemctl --user stop f012-farside-etf.timer f012-farside-etf.service
   systemctl --user disable f012-farside-etf.timer
   # PRESERVE:
   #   data_cache/f012/etf_flows/farside_BTC_flows.csv
   #   data_cache/f012/etf_flows/farside_ETH_flows.csv
   #   data_cache/f012/etf_flows/last_fetch.json
   #   data_cache/f012/etf_flows/heartbeat.json
   ```

## STOP

- This review **documents** recommendations only.
- **Do not** execute SUNSET stop/disable without a subsequent PO decision.
- **Do not** reopen `H-PRECASCADE-LIQ-01` before N/date gate + PO trigger.
- All three collectors remain **running** as of note time.
- structural-edge remains **PARKED — evidence constrained**; no new family.

## References

- `spec/research/F011-forced-flow-lab.md` §9b
- `spec/features/done/F012-structural-edge/outcome.md`
- `spec/research/F013-structural-edge-identification-brief.md`
- `spec/research/F012-structural-edge-candidates.md` (C04/C05 rejects; collect-forward rationale)
- `spec/research/F012-c01-etf-identification.md`
- `f012_collectors/README.md`, `forced_flow_lab/LIQ_COLLECTOR.md`
