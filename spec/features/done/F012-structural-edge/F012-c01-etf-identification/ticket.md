# F012-C01 · ETF NAV-window × prior flow — IDENTIFICATION GATE only

> **OWNER-APPROVED** identification gate ONLY — NOT a trading strategy yet.
> Sequential gates **A → B → C**. FAIL at any gate → STOP (no rescue).
> Do NOT run C02 optimization. Do NOT auto-start C03. Do NOT purchase data.
> Keep collectors unchanged: `f011-liq-collector`, `f012-deribit-book.timer`, `f012-farside-etf.timer`.
> C02 FAIL archived at `4fc012d` — leave archived. Delisting informational alpha is PARKED
> in `spec/research/F012-delisting-informational-alpha-parked.md` (not this ticket).

Prior: `d44de5a` / `spec/research/F012-structural-edge-candidates.md`; Farside collector
`f012-farside-etf.timer` already collecting under `data_cache/f012/etf_flows/`.
Train-1 only: **2024-03-01 → 2025-03-01 UTC**. Validation/holdout untouched.

## Core question

Can we know **BEFORE** the relevant ETF execution/NAV window something that predicts
**mechanically necessary** ETF-related BTC buying/selling?

NOT: published ETF flow → future BTC return (may be post-flow).

Need: `observable_at_T → expected create/redeem at T+Δ → AP/MM hedge → BTC flow → tradeable impact`.

If the first arrow fails point-in-time (PIT) → **Gate A FAIL** before strategy development.

## Outcome

One decision: **PASS | CONDITIONAL | FAIL**, with GATE A/B/C status, mechanism + PIT docs,
Gate analyses under `output/f012_c01_etf/`, journal Decision. Stop for owner approval before
any optimization. Commit + push after review PASS.

## Scope (follow owner brief exactly)

### 1. Mechanism reconstruction (Train-1 US spot BTC ETFs)
Create/redeem model by date; APs; MMs; cash vs in-kind; cutoffs; NAV time; when BTC
acquire/dispose/hedge likely (before/during/after NAV window); public info at each stage.
Preserve **effective dates** of procedure changes. ETFs are not identical — document
per-issuer differences material to timing. In-kind creations approved **2025-07-29** (SEC)
is post–Train-1 for the kill window but record as regime note for persistence.

### 2. PIT information timeline
For each candidate input: KNOWN BEFORE / DURING / AFTER FLOW.
Record `source_timestamp`, `publication_timestamp`, `earliest_live_availability_timestamp`.
**No revised EOD as intraday predictors.**

### 3. Gate A — Predictability first
`Observable_t → ETF_Flow_t` **before** testing BTC returns.
Baselines: unconditional/persistence; previous-day flow; short rolling flow;
premium/discount if PIT valid; prior ETF volume/activity.
OOS metrics: sign, magnitude corr, MAE, directional accuracy, rank corr, incremental R²,
lift for **extreme-flow days**.
**Must predict LARGE flow days before the execution window.** Else reject (Gate A FAIL → stop).

### 4. No circularity
No same-day BTC move as predictor if it may already reflect ETF execution.
Same-day predictors need timestamp **demonstrably earlier** than hypothesized flow window.

### 5. Economic magnitude
Predicted BTC demand vs spot volume, US-session volume, depth/liquidity.
Statistically predictable ≠ large enough.

### 6. Gate B — NAV-window event study (ONLY if Gate A survives)
High predicted-flow → abnormal BTC around **mechanics-justified** windows (narrow intraday).
Returns, AR, volume, RV, basis, venue diffs, MFE/MAE, pre/during/post.
Strongest evidence: predicted sign → same-sign abnormal move **concentrated in expected
window**, weak/absent in placebos.
Windows from mechanics first — **no threshold-mine**.

### 7. Placebos
Wrong TOD windows; time-scrambled predictions; next-day vs same-day; non-ETF days;
low predicted-flow days.

### 8. Reverse causality
BTC move → ETF demand/flow vs ETF flow → BTC. Lead/lag with PIT timestamps.

### 9. Costs (Gate C)
- **Primary owner bar:** taker 4.4 + measured ~0.56 ≈ 4.96 bps/side → **~9.9 bp RT**.
- Also report **gross**.
- Also report vs **34 bp** (historical harness / Gate C brief reference).
- Maker bound ~5.1 for context.
- **No leverage rescue** of 10–20 bp edges.
Gate C PASS only if OOS effect exceeds owner **~9.9** (primary) after realistic latency;
also show vs 34. FAIL if neither meaningful.

### 10. Chronology & inference
Chronological train/val/test **within Train-1** (or documented chronological folds).
Multiple-testing correction. Report n, mean, median, CI, effect size; by year; by ETF;
leave-out top 1/3/5 flow days.

### 11. Sequential gates (binding)
| Gate | Question | On FAIL |
| --- | --- | --- |
| **A Predictability** | Can PIT observables predict ETF flow (esp. large days) before the window? | STOP |
| **B Causal timing** | Does predicted flow map to abnormal BTC **in** the justified NAV/hedge window (not placebos)? | STOP |
| **C Tradeability** | OOS effect > owner ~9.9 bp RT primary (also report vs 34) after realistic latency? | STOP |

Only **A+B+C** → PASS or CONDITIONAL, then **STOP for approval** before optimization.
Do not auto-start C03.

### 12. Data
Free data first. Farside BTC/ETH already cached. Use existing Bybit/Binance Train-1
frames (`output/f011_forced_flow/frame_5m/`, `data_cache/` klines) for intraday BTC.
If paid data needed: exact dataset, vendor, coverage, price if findable, which gate
blocked, why no free proxy. **Do not purchase.**

### 13. Structural brief alignment
Brief kill sketch (`F012-structural-edge-candidates.md` §C01): prior-day Farside Total →
next session 15:00–16:00 ET hold; controls adjacent hours / zero-flow / scramble.
Owner expansion above **supersedes** that sketch where stricter (Gate A first; 9.9 primary).
Satisfy both: run mechanics-first windows; if Gate A passes, the brief’s one-hour window
is a primary hypothesized window unless mechanism docs justify a different narrow window.

## Deliverables

1. This ticket under `spec/features/active/F012-c01-etf-identification/`.
2. Mechanism doc + PIT timeline (under ticket dir and/or `output/f012_c01_etf/` + research note).
3. Gate A/B/C analysis code + compact tables under `output/f012_c01_etf/`.
4. Research note `spec/research/F012-c01-etf-identification.md` with GATE A/B/C + overall
   PASS|CONDITIONAL|FAIL.
5. `spec/RESEARCH_JOURNAL.md` Decision entry with GATE A/B/C.
6. Confirm parked note exists (do not expand it).
7. Commit + push after review PASS (FF preferred). Leave host dirt alone.

## Out of scope

- Trading-strategy optimization / threshold mining / leverage rescue.
- C02 reopen or mixing delisting informational alpha into this study.
- Auto C03.
- Purchasing data; touching live collectors; validation/holdout; `git reset --hard`.

## Acceptance

- Mechanism + PIT timeline docs exist with effective dates.
- Gate A run and scored; if FAIL, B/C marked not reached and study stops.
- If A passes: Gate B with placebos + reverse-causality; if B passes: Gate C with
  owner ~9.9 primary and 34 secondary.
- Exactly one overall PASS|CONDITIONAL|FAIL in journal + research note.
- Paid-data blockers listed if any (no purchase).
- Collectors still running unchanged; C02 artifacts untouched; no C03 ticket.
- `python3 -m pytest -q` green (add unit tests for PIT/causality parsers as needed).
- Disk floor 10–20 GB free respected.

## Notes for implementer

- PATH=`/home/limen/.npm-global/bin:$PATH`. No `rg` on host — use `grep`.
- Prefer `limen` worktree; do not use spark. Codex needs re-login — use Claude.
- Farside same-day Total often blank until publish — lag to next session; document
  `earliest_live_availability_timestamp` (brief used ~20:00 UTC conservative stamp —
  verify/adjust with evidence).
- BTC primary; ETH replication optional/pre-registered secondary if free and cheap.
- Disk-safe: reuse caches; batch any downloads; delete raw after aggregate.
