# F013 — Delisting Informational Alpha: pre-registration (SSOT freeze)

> **Frozen 2026-10-07 Europe/Warsaw**, before any F013 return was computed and before the
> Gate A audit was run. Owner mandate (written, 2026-10-07): new track F013 — informational
> **underreaction** after a public delisting announcement. Not forced-flow, not C02 revival.
> Feature folder: `spec/features/active/F013-delisting-informational-alpha/` (`ticket.md`,
> `prereg.md` = verbatim copy of this file; on any divergence **this file wins**).
>
> Amendments are allowed only as a new dated section appended below §12, committed **before**
> the data they affect is scored, and they can never touch §7 (validation window) or §10
> (decision rules) after Gate O scoring started.

## 0. Thesis and what would destroy it

- **H1 (informational underreaction).** After a venue publicly announces the delisting of a
  token's USDT linear perp (alone or together with its spot pairs), the token keeps falling
  *after* the public observability time P. The market underreacts to the news. Perp and spot
  should move **together** (information hits the token, not just the deadline contract).
- **Not tested here:** forced unwind / deadline flow (C02, FAIL-archived), basis, OI decay.
  A result that only exists as perp − spot divergence is out of scope and counts against H1.
- **Origin.** The C02 incidental naive short (+938 / +508 bp, Train-1) is hypothesis-
  generating only. The C02 Train-1 events are the **contaminated discovery set**. The goal of
  the discovery phase is to **destroy** that result (Gates B–Q). Only a survivor is scored once
  on the frozen, untouched validation window (Gate O).

## 1. Universe and event definition

- Venues: **Binance** (CMS catalog 161 "Delisting") and **Bybit** (announcements type
  `delistings`). USDT-margined linear perpetuals only.
- An **event** = one (announcing venue, perp symbol) pair where the article either delists that
  USDT perp (`perp_delist`) or delists the token's spot pairs while the same-venue USDT perp is
  live at P (`token_delist` with `same_venue_perp_live_at_announcement`).
- Traded instrument: the **same-venue USDT linear perp**, short only.
- Excluded from the **primary** sample (reported separately in Gate M): composite index perps
  (`INDEX_BASES`: BTCDOM, FOOTBALL, BLUEBIRD, DEFI), ticker migrations / mergers / rebrands
  (`MIGRATION_BASES`), Coin-M, leveraged tokens, pair-only or margin/earn product removals,
  postponement / revision articles as standalone events.
- Event catalog code: `delisting_lab/catalog.py` (unchanged C02 parser rules). Validation-window
  catalog must be built with the same code, with no parser change made after looking at
  validation prices.

## 2. Timestamps (Gate A clock)

- **P = `first_publicly_observable_ts`** — primary clock. No entry, signal, or feature may use
  data at or after P except the entry itself at P + latency.
  - Binance: CMS `releaseDate` (cross-checked against detail `publishDate`).
  - Bybit: `max(dateTimestamp, publishTime)` when |publishTime − dateTimestamp| ≤ 6 h, else
    `dateTimestamp` (C02 rule), re-verified against the article page `date`.
- **S = `announcement_ts`** — secondary, audit only. Never a trading clock.
- `effective_ts` = delisting/settlement time parsed from the article body, cross-checked with
  instrument delivery time; postponements update `effective_ts` (announced value kept).

## 3. Signal, entry, exit, sizing

- **Signal:** event passes Gates A and C → short the perp. No other condition in the primary
  spec. No ML, no optimizer, no feature search, no parameter grid.
- **Primary entry:** open of the first 1-minute perp bar starting at or after **P + 5 min**.
  (Shorter latencies are Gate B diagnostics; the primary is deliberately not a speed race.)
- **Primary exit:** open of the first 1-minute bar at or after
  `min(entry + 72 h, effective_ts − 1 h)`. Events with `effective_ts − 1 h − entry < 1 h` are
  excluded from the primary sample (insufficient notice) and reported.
- **Return:** short gross bp = `−(exit/entry − 1) × 10⁴`. Funding: short receives positive
  funding prints with funding time in (entry, exit]; net = gross + funding − cost.
- **Sizing:** equal notional per event. No pyramiding, no leverage tuning, no compounding.
- **Primary statistic:** mean net bp per event; uncertainty = **day-batch cluster bootstrap**
  (resample `day_batch_cluster_id`, 10 000 draws, seed 13, percentile 95 % CI).

## 4. Costs (Gate D)

- Ladder: **34 / 50 / 75 / 100 / 150 / 200 bp RT**, every rung reported, no rung dropped.
- Owner-tier ≈ **9.9 bp RT** is reported as context only; it can never decide PASS.
- **Decision rung = 34 bp RT** (illiquid delisting names: owner-tier taker is not a credible
  fill for the event set). Stress rung = 75 bp.

## 5. Data and sample windows

- Prices: perp 1m klines (Binance vision `futures/um`, Bybit v5 kline); ticks (Binance vision
  aggTrades, Bybit public trade archive) only for Gate B sub-minute latencies; spot 1m (Binance
  spot vision, Bybit spot archive); BTCUSDT perp 1h for beta; funding history (venue APIs).
- Reuse `delisting_lab/` code and C02 caches only read-only. C02 decision artifacts in
  `output/f012_c02_delisting/` are never modified. F013 outputs: `output/f013_delisting_info/`.
- **Discovery (contaminated):** C02 Train-1, announcements in [2024-03-01, 2025-03-01) UTC.
- **Validation (true OOS, frozen now, untouched):** announcements in
  **[2025-03-01, 2026-03-01) UTC**, both venues, same universe rules.
- **Sealed holdout:** announcements in **[2026-03-01, 2026-09-01) UTC** — not opened by this
  prereg under any outcome; reserved for a CONDITIONAL re-test or a later owner decision.
- Nobody has scored delisting returns after 2025-03-01 in this repository. The F013 brief probe
  (2026-10-06) only listed Bybit announcement metadata.

## 6. Gates A–Q (frozen)

Each gate is tagged **KILL** (FAIL ⇒ track FAIL) or **ROUTE** (can only move the result to
CONDITIONAL or flag thesis mismatch as stated). "net@34" = mean net bp at 34 bp RT incl. funding.
"CI" = day-batch cluster bootstrap 95 % CI. "n_min" = 8 events per reported split; a split
below n_min is reported as "insufficient", never used to pass or fail.

### Gate A — Timestamp integrity (KILL) — *scored in this job, discovery set*

Per event, re-fetch raw fields (Binance detail `publishDate` + body; Bybit page `date`, body,
API `dateTimestamp`/`publishTime` where still served) and classify:

- **FAIL** if any: F1 P missing or P < S; F2 re-fetched raw anchor differs from the catalog
  anchor by > 60 s (Binance `publishDate` vs `releaseDate`; Bybit page `date` vs
  `dateTimestamp`); F3 Bybit `publishTime` later than `dateTimestamp` by > 6 h **and** before
  `effective_ts` while P < publishTime (true first push ambiguous ⇒ look-ahead risk);
  F4 `effective_ts` missing or ≤ P.
- **WARN** if any (and no FAIL): W1 body re-parse of effective time missing or differs from
  catalog announced effective by > 60 s; W2 instrument delivery vs `effective_ts` > 1 min;
  W3 effective postponed; W4 Bybit publishTime > 6 h earlier than dateTimestamp, or later but
  at/after `effective_ts` (post-event edit); W5 P − S > 15 min; W6 raw source unavailable;
  W8 an explicit body datetime earlier than S − 1 h.
- **PASS** otherwise.
- FAIL events are dropped from every later gate (no re-timing). WARN events stay in the
  primary sample; every KILL gate is also re-run on PASS-only as a robustness split, which
  must keep the sign of net@34.
- **Gate A aggregate PASS** iff ≥ 85 % of events are PASS|WARN **and** no venue has > 25 %
  FAIL. Otherwise Gate A FAIL ⇒ track FAIL (timestamps cannot support an event study).
- Report: per-event CSV, P − S distribution, share of events where S + {10 s, 30 s, 60 s,
  5 min, 15 min} < P (look-ahead if S were used), ts_flag rates, A vs B choice.
- The same audit is re-run on the validation catalog before Gate O scoring.

### Gate B — Latency decay (ROUTE)

Entries at P + 10 s, 30 s, 60 s (tick data; first trade at/after the time) and P + 1 min, 5 min,
15 min (1m bar open). Same exit rule. Report per-latency n with data support (events lacking
ticks are listed, not imputed). **Pass** iff net@34 > 0 at both P + 5 min (primary) and
P + 15 min. If net@34 > 0 only at ≤ 60 s ⇒ thesis mismatch (speed race, not underreaction) ⇒
**FAIL**.

### Gate C — Short eligibility (KILL)

An event is eligible iff the perp has ≥ 1 trade in [entry, entry + 1 min] and the article does
not restrict opening new positions (reduce-only / "not able to open new positions") at or
before entry. Ineligible events are dropped and listed. **Fail** if < 70 % of Gate-A-usable
primary events are eligible.

### Gate D — Cost ladder (KILL)

Report net mean, median, CI at 9.9 (context) and 34/50/75/100/150/200 bp. **Pass** iff
net@34 CI lower bound > 0 **and** mean net > 0 at 75 bp. Breakeven cost reported.

### Gate E — Funding carry (KILL)

Report gross, funding, net. **Pass** iff net@34 **excluding** funding is still > 0 and funding
contributes < 50 % of net@34. (The short must not be a funding trade.)

### Gate F — Fixed-horizon drift (ROUTE)

Fixed exits entry + 1 h, 4 h, 12 h, 24 h, 72 h, and `effective_ts − 1 h`; each horizon only on
events whose exit precedes `effective_ts − 1 h` (except the eff−1h exit itself). No exit
optimization; the primary exit (§3) is not re-chosen. **Pass** iff net@34 > 0 at ≥ 3 of the 5
fixed horizons. Otherwise ⇒ **FAIL** (drift not robust to the horizon).

### Gate G — Market-adjusted (KILL)

β from OLS of the perp's 1h log returns on BTCUSDT perp 1h log returns over
[P − 20 d, P − 24 h] (≥ 200 hourly obs, else β = 1). Abnormal short return =
`−(r_perp − β·r_BTC)` over the primary window. **Pass** iff abnormal net@34 CI lower > 0.

### Gate H — Spot/perp co-move (ROUTE, thesis check)

For events with same-token spot 1m data (same venue, else the other venue): spot short return
over the identical window. Report spot, perp, perp − spot with CI. Co-movement supports H1.
**Thesis mismatch ⇒ FAIL** iff perp − spot CI lower > 0 **and** spot short mean ≤ 0 (the
effect would be contract-specific deadline flow, already archived as C02).

### Gate I — Clustering (KILL)

Report n events, n `announcement_cluster_id`, n `day_batch_cluster_id`, and token-level clusters
(same base on both venues within 30 d merged). **Pass** iff ≥ 25 day-batch clusters in the
scored sample **and** net@34 CI lower > 0 under **both** day-batch and token-cluster bootstrap.
Event-level (iid) CIs are reported for comparison only.

### Gate J — Tails (KILL)

Report mean, median, 10 % trimmed mean, 5/95 winsorized mean, contribution share of top-1/3/5
events, mean ex-top-1/3/5 (all net@34). **Pass** iff median net@34 > 0 **and** winsorized
mean > 0 **and** ex-top-3 mean > 0. Ex-top-5 ≤ 0 is reported as a warning.

### Gate K — Liquidity (KILL)

Pre-registered exclusion (before scoring): drop events whose perp quote turnover over
[P − 24 h, P) is < 500 000 USDT or with > 20 % zero-volume 1m bars in that window.
Report included/excluded n. Split the included events at the median of pre-P 24 h turnover.
**Pass** iff the more liquid half has net@34 > 0 (the edge must not live only in illiquids).

### Gate L — Notice length (ROUTE)

Bins of `effective_ts − P`: (0, 24 h], (24 h, 72 h], (72 h, 168 h], > 168 h. No other bins.
**Pass** iff net@34 > 0 in ≥ 2 populated bins (n ≥ n_min). Effect confined to one bin ⇒
**CONDITIONAL** route (§10).

### Gate M — Delisting type (ROUTE)

Splits: perp-only (spot not delisted in the article), spot + perp (token delisting), migration
(excluded from primary), index (excluded from primary). **Pass** iff net@34 > 0 in both primary
types with n ≥ n_min (a type below n_min is a stated limitation). Effect only in one primary
type ⇒ CONDITIONAL route. Effect present only via migration/index ⇒ **FAIL**.

### Gate N — Announcement novelty (ROUTE)

First venue vs follower (`follower_event`: same base announced on the other venue in the prior
30 d). H1 predicts first ≥ follower. **Route:** if first-venue net@34 ≤ 0 while followers carry
the effect ⇒ CONDITIONAL (condition = follower status, observable at P).

### Gate O — True out-of-sample validation (KILL) — *the only decision-bearing score*

Scored **once**, only if discovery Gates A–N, P, Q did not FAIL. Window §5 [2025-03-01,
2026-03-01). Equal notional, primary spec §3 unchanged, Gate A re-run on validation first,
Gate K exclusion rule unchanged. **Pass** iff on validation: n ≥ 40 primary events, ≥ 25
day-batch clusters, net@34 CI lower > 0, mean net > 0 at 75 bp, and Gates E, G, I, J, K pass on
validation. Fewer than 40 events ⇒ FAIL (insufficient), with owner option to extend forward
data under this unchanged prereg.

### Gate P — Placebos (KILL)

(1) **Time-scrambled:** per event, 200 pseudo-P times drawn uniformly from [P − 90 d, P − 10 d],
excluding ±10 d around any delisting announcement of the same base on either venue; same entry/
exit/cost rules; seed 13. Empirical one-sided p = share of placebo sample means ≥ actual mean.
(2) **Matched controls:** for each event, 3 same-venue USDT perps not delisted within ±90 d,
nearest on (pre-P 30 d return rank, pre-P 24 h turnover rank), live and trading at P; control
short return over the identical window. **Pass** iff p < 0.05 **and** event − control mean > 0
with cluster CI lower > 0.

### Gate Q — Pre-trend (KILL)

Report short returns over [P − 72 h, P − 5 min] and [P − 24 h, P − 5 min], and [P − 1 h, P).
**Pass** iff the post-P effect persists among events whose [P − 24 h, P − 5 min] return is in the
upper half (least pre-event decline): net@34 > 0 there. Mean [P − 1 h, P) drop worse than
−200 bp is flagged as a possible leak (reported, and re-checked against Gate A FAILs).

## 7. Discovery vs validation discipline

- Discovery (Train-1) runs the **attack** gates A–N, P, Q on the frozen primary spec. They exist
  to falsify. Any KILL FAIL or thesis-mismatch FAIL on discovery ⇒ track FAIL; validation is
  then **not opened**.
- No change of the primary spec, horizons, cost rung, exclusions, or bins after discovery
  scoring. Discovery ROUTE outcomes are recorded before validation is opened.
- Validation is opened once (Gate O). The sealed holdout is never opened by this prereg.

## 8. What is explicitly not done

No ML, optimizer, feature search, exit optimization, leverage tuning, or position-size tuning.
No live bot, no orders, no exchange keys. No contact with Slack/email/ChatGPT PO session. No
reopening F011 / C01 / C02 forced-unwind / C03 / F012 R2-B/C. Collectors and systemd untouched.

## 9. Execution order

1. **Gate A** on discovery (this job) → STOP.
2. Gates B–N, P, Q on discovery (next job; Gate B first).
3. Validation catalog build + Gate A on validation.
4. Gate O once.
5. Decision §10, then STOP.

## 10. Decision rules (frozen)

- **FAIL** — any KILL gate fails (discovery or validation), Gate A aggregate FAIL, a
  thesis-mismatch FAIL (B, H, M), Gate F FAIL, or Gate O insufficient. ⇒ archive F013 with the
  evidence; no relabeled retry.
- **CONDITIONAL** — all KILL gates pass on discovery, but a ROUTE gate (L, M, N) shows the
  effect only inside a subset defined by a condition **observable at or before P**. ⇒ the
  condition is written as a new dated amendment **before** any further scoring; it then needs
  independent validation on data not used for the condition (validation window if not yet
  opened; otherwise the sealed holdout or forward data, owner decision). CONDITIONAL is never a
  PASS.
- **PASS** — discovery passes every KILL gate and no ROUTE gate routes away, **and** Gate O
  passes. ⇒ **STOP**. No live bot, no optimization, no sizing work. Owner decision only.

## 11. Outputs

`output/f013_delisting_info/`: `gate_a_timestamp_audit.{csv,md}`, later `gate_<x>_*.{csv,md}`,
`STATUS.md`. Code: `delisting_lab/f013_*.py`. Tests: `tests/test_f013_*.py` (no network).

## 12. Amendments

(none)
