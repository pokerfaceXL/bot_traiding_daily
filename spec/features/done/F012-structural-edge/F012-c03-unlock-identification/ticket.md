# F012-C03 · Token unlock cliff — IDENTIFICATION / DATA-FEASIBILITY ONLY

> **OWNER-APPROVED** identification + data feasibility ONLY. No purchase. No strategy
> backtest. No optimize. No auto-start of the next F012 candidate.
> C01 FAIL (Gate A, lift 1.38 < 1.5) archived at `3764020`; do not relax it or reopen B/C.
> C02 FAIL archived at `4fc012d`; the parked delisting note stays untouched.
> Collectors keep running unchanged: `f011-liq-collector`, `f012-deribit-book.timer`,
> `f012-farside-etf.timer`.
> Disk floor 10–20 GB free. Never `git reset --hard`. Merge only after `limen spawn --review` PASS.

Prior: `spec/research/F012-structural-edge-candidates.md` §C03 (calendar A-class; paid /
pre-priced risk). Train-1 only: **2024-03-01 → 2025-03-01 UTC**.

## Core thesis (narrow; NOT "unlock → short")
KNOWN CLIFF → tokens transferable → sellable inventory → some moves to exchanges →
market absorbs → possible impact. Which links are observable point-in-time (PIT) before impact?

## Gates (owner brief; sequential where dependent; ALL outcomes reported)
0. Data feasibility, free first: events, unique tokens, recipient %, on-chain %, PIT reliability;
   ONE free schedule source frozen in `prereg.md` before download; automatic kill if no free PIT
   history without TOS-violating UI scrapes or paid APIs.
1. Supply shock: % circulating, USD/ADV, depth where obtainable — distributions first.
2. Recipient type: team / VC / ecosystem / other / UNKNOWN (first-class).
3. Pre-unlock pricing: abnormal returns −30d…+30d vs BTC and matched controls; when?
4. On-chain realization: scheduled vs realized sellable flow; coverage.
5. Signal classes A / B / C.
6. First falsification: LARGE vs SMALL vs matched non-event; continuous before thresholds.
7. Interaction: LARGE × LOW ABSORPTION × HIGH-SELL recipient (pre-registered).
8. Earliest realistic entry per family A / B / C / D.
Cross-cutting: short availability, survivorship, independence/clustering, success bar,
BUY / DO NOT BUY with exact missing fields.

## Costs (owner binding)
Primary owner tier ≈ 9.9 bp RT (taker 4.4/side + ~0.56 measured basket half-spread+impact);
stress 34 / 50 / 75 / 100 bp. No leverage rescue.

## Deliverables
- `prereg.md` (this dir) — frozen before unlock download/scoring.
- `spec/research/F012-c03-unlock-identification.md` — Gates 0–8, short availability,
  BUY / DO NOT BUY, overall PASS | CONDITIONAL | FAIL, causal sentence, caveats.
- `output/f012_c03_unlock/` compact tables; code `unlock_lab/`.
- One Decision entry in `spec/RESEARCH_JOURNAL.md`.

## Outcome
Exactly one of PASS | CONDITIONAL | FAIL. Commit and STOP for review.
