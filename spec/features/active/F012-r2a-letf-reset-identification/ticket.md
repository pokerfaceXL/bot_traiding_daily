# F012-R2A · Leveraged-ETF daily reset (BITX, BITU, SBIT): IDENTIFICATION FALSIFICATION only

> **OWNER-APPROVED** by the ChatGPT Product Owner (session `f006-chatgpt-po`), 2026-10-06.
> This is an identification falsification, not a strategy search. No sizing, portfolio, or live work.
> No data purchase. No human ask. A PASS does **not** authorize implementation. It needs a new PO decision.
> Collectors stay untouched: `f011-liq-collector`, `f012-deribit-book.timer`, `f012-farside-etf.timer`.
> C01 (`3764020`), C02 (`4fc012d`) and C03 (`3eb051d`) stay archived as FAIL and are not reopened.

Prior: `2ae9c99` / `spec/research/F012-round2-candidate-selection.md` (R2-A chosen; absolute kill gates in §5).
Cost: `spec/research/F012-owner-cost-hurdle.md`. Primary **9.92 bp RT** taker, maker bound 5.12 bp,
stress 50/75/100 bp. 34 bp is a historical label only.
Train-1 only: US trading days **2024-03-01 → 2025-02-28**. Validation and holdout stay untouched.

## Question
Does the mechanical daily exposure reset of 2× / −2× BTC ETFs (ΔExposure = L(L−1)·AUM·r) create
signed, predictable pressure in Bybit BTCUSDT during 15:00–16:00 ET on US trading days? To count, the
pressure must be absent on weekends and US holidays, scale with PIT predicted $ flow, beat both adjacent
hours, and survive 9.92 bp RT.

## Deliverables
- `prereg.md` (this folder). Equations, cutoffs, windows, gates, warm-up, leave-out and missing-data
  rules. **Committed before any AUM history download or outcome scoring.**
- `letf_reset_lab/`. Fetchers, calendar, frame, gates, tests. One command reproduces everything:
  `python3 -m letf_reset_lab.run`.
- `output/f012_r2a_letf_reset/`. CSVs, `summary.json`, sha256 of every input.
- `spec/research/F012-r2a-letf-reset-identification.md`. Standalone report with the final verdict.
- One Decision entry in `spec/RESEARCH_JOURNAL.md`. A one-bullet NOW swap in `spec/build.md`, kept at about 184 lines.

## Verdict
Exactly one of **PASS | CONDITIONAL | FAIL**, mapped in `prereg.md` §9. Gates run 0 → 5 and stop at the first KILL.
STOP after the verdict. Do not merge, do not implement, do not start R2-B or R2-C.
