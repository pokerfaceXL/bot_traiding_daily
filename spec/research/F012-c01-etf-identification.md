# F012-C01 — ETF NAV-window × prior flow: identification gate

**Decision: FAIL** · GATE A = **FAIL** (criterion (c)) · GATE B = NOT REACHED · GATE C = NOT REACHED

Ticket `spec/features/active/F012-c01-etf-identification/ticket.md`; criteria pre-registered in
`prereg.md` (committed `0dbfdd2` before any result); mechanism + PIT in `mechanism_pit.md`
and `output/f012_c01_etf/pit_timeline.csv`. Train-1 only (250 US trading days,
2024-03-01 → 2025-02-28). Validation/holdout untouched. Free data only: Farside snapshot,
Coinbase BTC-USD 5m, Yahoo daily ETF bars, F011 Bybit/Binance 5m frame. No paid data needed
to reach this decision.

## Mechanism in one paragraph
In Train-1, creations were cash-only. For IBIT the AP's cash order for trade date T is due by
18:00 ET on **T-1**; the issuer's counterparty buys/sells BTC on T against the 16:00 ET
benchmark (BRRNY window 15:00–16:00 ET). The flow for T is published (Farside) only late T to
the morning of T+1. So the public can't see the T order before the window. All it can use
before the window is row T-1 and older, plus market data up to the prior close. Gate A asks
whether that is enough to forecast T's flow, especially the large days.

## Gate A — Observable → ETF_Flow (scored on untouched fold F3 = 2024-10-28 → 2025-02-28)

Primary model chosen on F2 by MAE: **M3** (OLS on y_{T-1}, 5-day mean, IBIT/GBTC lags, prior
BTC day return, prior ETF $-volume z, prior premium proxy). F3 has n = 84.

| Criterion (pre-registered) | Value | Bar | Result |
| --- | --- | --- | --- |
| (a) OOS R² vs expanding mean | 0.426 | > 0 | pass |
| (a) Spearman ρ(pred, y) | 0.657 (Holm p 1e-11) | > 0, p < .05 | pass |
| (b) Sign accuracy on large-flow days (n = 44) | 0.886 (Holm p 7e-8) | ≥ 0.60, sig. | pass |
| (b) vs. benchmark M0 on same days | 0.886 vs 0.750 | ≥ M0 | pass |
| (c) Lift P(large \| pred large)/P(large) | **1.38** (0.724 / 0.524) | ≥ 1.5 | **FAIL** |

Per the binding rule, Gate A FAILs and the study stops: **B and C were not run.**

How to read it (context only; it changes nothing):
- The flow series is very persistent (prior-day Total alone: ρ 0.53 on F3). Signs are easy
  to predict. Days when the size jumps are not. In F3 the size regime changed: median |flow|
  was $367M vs $117–140M in F1/F2. The PIT 80th-percentile "large" threshold, built on the
  calmer history, flagged 52% of F3 days, which caps any lift at 1.91. The model's top
  predictions were large only 72% of the time.
- On other scopes the lift clears 1.5: F2∪F3 1.76, walk-forward 1.70 (n = 190), M1 on F2∪F3
  1.63. The flagged pre-open model M3o (adds the overnight BTC return; not eligible as
  primary) reaches 1.51 on F3. These were **not** used to override the verdict. Changing
  criterion (c) after the fact would be a pre-registration amendment, which is the owner's call.
- Sign predictability mostly reflects trend persistence. M0, which only knows "inflows are
  the norm", already gets 75% of large-day signs on F3. So the prior that a public flow
  signal still has an unpriced directional component (SSRN 7545019) is weak.
- Robustness (`gate_a_robustness.csv`): leaving out the top 1/3/5 |flow| days gives ρ
  0.63/0.62/0.61. By period: 2024 0.64, 2025 0.59. By issuer (own lag): IBIT ρ 0.61, FBTC
  0.31, GBTC 0.12, ARKB 0.30, BITB 0.19. Persistence is essentially an IBIT effect.

## Economic magnitude (context, `economic_magnitude_daily.csv`)
Median |actual flow| is **1.8×** Coinbase BTC-USD $-volume in 15:00–16:00 ET. Median |predicted
flow| is 1.3×. Against Coinbase + Bybit + Binance perp window volume, the share is ~12%
(median). The flows are large enough to matter. The failure is about identification, not
size.

## Gates B and C
NOT REACHED. The 15:00–16:00 ET BRRNY window (brief §C01) is documented as the
mechanics-justified primary window. Placebos, reverse causality and costs (9.9 bp primary,
34 bp secondary, no leverage) are specified in `prereg.md` but were not computed.

## Paid-data blockers
None for this decision. Not available free and not used: historical Farside publication
vintages (only a current snapshot exists; the live collector began 2026-10-06), the official
daily premium/discount history (a proxy was used), and issuer intraday execution prints. None
of these would change Gate A's criterion (c).

## Artifacts
`output/f012_c01_etf/`: `gate_a_scores.csv` (all models × F2/F3/F2∪F3/walk-forward),
`gate_a_robustness.csv`, `economic_magnitude_daily.csv`, `daily_pit_frame.csv`,
`pit_timeline.csv`, `summary.json`, `inputs/farside_BTC_flows_snapshot.csv` (sha256 in
summary). Code: `etf_lab/` (`python3 -m etf_lab.run_study`). Tests: `tests/test_f012_c01_etf.py`.

## Owner question (open)
Should criterion (c) be amended, for example to lift against a fixed-dollar "large" threshold
or measured walk-forward, as a new pre-registration before any Gate B? Under the current
rule, C01 is FAIL. Nothing in this study may be optimized, and C03 is not started.
