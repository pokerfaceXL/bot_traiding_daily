# Outcome — F012 structural edge: **CLOSED, NO CANDIDATE**

> Closed 2026-10-06 on the ChatGPT PO decision (session `f006-chatgpt-po`) after R2-A died at Gate 0.
> Research only. F012 shipped no strategy, backtest-for-trading, live change or data purchase.
> The research notes under `spec/research/F012-*.md` stay unchanged as historical records.
> Collectors (`f011-liq-collector`, `f012-deribit-book.timer`, `f012-farside-etf.timer`) were not touched.

F012 asked who **must** trade, why, when, and whether we can see the cause before the flow is priced.
Four mechanisms reached a pre-registered test on Train-1 (2024-03-01 → 2025-02-28). Validation and holdout
were never opened. All four failed, **but they failed for two different reasons, and they must not be merged.**

## Two kinds of FAIL

| Kind | Meaning | What it does **not** say |
| --- | --- | --- |
| **Mechanism identification FAIL** | The data existed and was PIT-usable. The pre-registered identification gate ran and rejected the forced-flow explanation | — |
| **PIT data FAIL** | Gate 0 killed the test, because free point-in-time data for a required input is missing. **No identification gate ran, and no outcome was scored** | It says nothing about whether the mechanism exists. The mechanism is **untested**, not refuted |

## Per-candidate verdicts

| ID | Mechanism | Verdict | Kind | Gates actually run | Note / archive commit |
| --- | --- | --- | --- | --- | --- |
| C01 | Spot-ETF NAV window (15:00–16:00 ET) × prior-day public flow | **FAIL** | **Mechanism identification** | Gate A ran on fold F3 (n 84): large-day lift **1.38 < 1.5**. Gates B and C **not reached** | `spec/research/F012-c01-etf-identification.md` · `3764020` |
| C02 | Exchange delisting forced unwind | **FAIL** | **Mechanism identification** | Full event study (80/82 events, 44 day-batch clusters). Perp − spot ≈ 0, OI decay does not predict drift, no deadline-window drift, spot-only delistings fall as hard. Informational/stigma drift, **not forced flow** | `spec/research/F012-c02-delisting-falsification.md` · `4fc012d` (owner-tier cost restamp `f6812c5`) |
| C03 | Token unlock / vesting cliff | **FAIL** | **PIT data** | Gate 0 KILL: pre-event archive verified **3/30 = 10% < 80%** of the free schedule. **DO NOT BUY.** The hindsight tables in the note are an upper-bound diagnostic. They are not an identification verdict | `spec/research/F012-c03-unlock-identification.md` · `3eb051d` |
| R2-A | US leveraged-ETF daily reset (BITX/BITU/SBIT), 15:00–16:00 ET | **FAIL** | **PIT data** | Gate 0 KILL: BITX PIT AUM **29/250 = 11.6% < 90%**. Gates **1–5 NOT REACHED / not tested**. **No outcome was scored**: there is no return, placebo, slope or net figure | `spec/research/F012-r2a-letf-reset-identification.md` · `5205c63` |

Do not cite R2-A as evidence against leveraged-ETF reset pressure, or C03 as evidence against unlock
supply. Both are open questions that free PIT data cannot answer today. C01 and C02 are real
identification rejections on their pre-registered criteria.

Also out of scope and unchanged: the delisting informational/event-alpha channel stays **PARKED**
(`spec/research/F012-delisting-informational-alpha-parked.md`). Round-1 rejects C04–C16 and
round-2 R2-B…R2-E were never tested. R2-B and R2-C were **not** started after the R2-A kill
(round-2 §5).

## Cost and data discipline used throughout

Primary hurdle: owner-tier **≈ 9.92 bp RT** taker, maker bound ≈ 5.12 bp; stress 50/75/100 bp
(`spec/research/F012-owner-cost-hurdle.md`). The 34 bp figure is obsolete. Only C02 reached a cost
table, and it failed on identification, not on cost. Train-1 only, with pre-registration committed
before any outcome.

## What the program taught (input to the next brief)

1. Forecasting a flow from its own lagged prints is not compulsion (C01).
2. If the trigger is also news, spot and perp move together and the forced part cannot be isolated (C02).
3. In crypto, the binding obstacle for direct-mandate mechanisms is usually the **forced quantity**
   (AUM, outstanding, collateral) at daily PIT resolution, not the trigger (C03, R2-A).
   An identification brief must audit free PIT data first.

## Ticket locations (moved from `spec/features/active/`)

`F012-c01-etf-identification/`, `F012-c02-delisting-falsification/`, `F012-c03-unlock-identification/`,
`F012-r2a-letf-reset-identification/` now sit under this folder. Their contents are unchanged, so
paths quoted inside older notes, `etf_lab/gates.py` and `letf_reset_lab/run.py` still name the old
`active/` location.

## Next

F012 is closed. The successor direction is an identification-only brief:
`spec/research/F013-structural-edge-identification-brief.md`. It starts nothing. Any further test
needs a separate PO decision.
