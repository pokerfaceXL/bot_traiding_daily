# F012-R2A · Leveraged-ETF daily reset (BITX, BITU, SBIT): identification falsification

> Owner-approved identification test (PO session `f006-chatgpt-po`, 2026-10-06). Not a strategy search.
> Pre-registration: `spec/features/active/F012-r2a-letf-reset-identification/prereg.md` (commit `686f6ee`),
> frozen before any AUM history download or outcome scoring. Train-1 only (2024-03-01 → 2025-02-28).
> Validation and holdout were not touched. Collectors were not touched. Nothing was bought, and no human was asked for data.

## Verdict: **FAIL**, killed at Gate 0 (Data)

**BITX point-in-time AUM covers 29 of 250 Train-1 sessions (11.6%). The bar is 90%.**
No free source publishes a daily BITX AUM (NAV × shares outstanding) history. The only free PIT
evidence is Wayback captures of the issuer page, which give 9 distinct as-of values across the
whole year. Per the absolute kill rule (round-2 §5, prereg §7), gates 1–5 were **not reached**.
**No outcome was scored**: no 15:00–16:00 return, placebo, slope or net figure exists for this study.
This is a FAIL, not a CONDITIONAL. The pre-registered Gate 0 is a kill gate, the owner rule forbids a
proxy rescue, and BITX is not an optional fund. It was the largest fund in F for most of Train-1
(about $1.2–3.8 bn, against BITU's median of about $0.38 bn).

STOP. PASS/CONDITIONAL would not have authorized implementation either. Following round-2 §5, the
default after an R2-A KILL is **NO CANDIDATE** for F012 round 2 until a new owner brief. R2-B and R2-C
are not started automatically.

---

## 1. Mechanism and frozen equations (from prereg §2)

A daily-reset fund with target L, AUM A at the prior close, and underlying return r must trade
**ΔE = L(L−1)·A·r** into the close to restore L× exposure.

- Long funds (BITX, BITU; L = +2): `F_long = Σ 2·A_{i,t−1}·r_t`. The trade has the same sign as r.
- Inverse fund (SBIT; L = −2): `F_inv = 6·A_{SBIT,t−1}·r_t`. This also has the same sign as r.
- `F = F_long + F_inv`. The signal r runs from the prior session's official close to 15:00 ET (Coinbase 5m).
  The outcome is Bybit BTCUSDT from 15:00 to 16:00 ET. The placebo is weekends and NYSE holidays.

Because sign(F) = sign(r) on every day, identification depends on the placebo, on dose-response in
|F| (which comes from AUM variation), and on the adjacent hours. Dose-response needs **daily AUM for
the dominant fund**, and that is exactly what is missing.

## 2. Leverage targets (verified on issuer pages, 2026-10-06)

| Fund | L | Evidence |
| --- | --- | --- |
| BITX | +2 | volatilityshares.com/bitx: "2x Bitcoin ETF" (archived Train-1 title "2x Bitcoin Strategy ETF") |
| BITU | +2 | proshares.com: "daily investment results … two times (2x) the daily performance of the Bloomberg Bitcoin Index" |
| SBIT | −2 | proshares.com: "daily investment results … −2x the daily performance of its underlying benchmark" |

## 3. Point-in-time source audit (`output/f012_r2a_letf_reset/pit_timeline.csv`)

| Fund | Source | Daily history? | PIT evidence | Status |
| --- | --- | --- | --- | --- |
| BITX | Volatility Shares fund page | **No.** Current snapshot only ("Net Assets as of D", NAV, Shares Outstanding) | Wayback capture time | PIT-by-capture, **sparse** |
| BITX | Volatility Shares premium/discount PDF | No (premium/discount chart only, 2025-01 → now) | n/a | unusable |
| BITX | Volatility Shares holdings XLS | No (current holdings; no date or shares field) | 3 captures | unusable |
| BITU, SBIT | ProShares history CSV (`accounts.profunds.com/etfdata/ByFund/{T}-historical_nav.csv`) | **Yes.** Date, NAV, shares (000), AUM; 230 Train-1 rows from launch 2024-04-01 (229 usable sessions) | Downloaded today. The file itself has no Wayback capture, and archived fund pages render NAV/shares by JS (not comparable) | **UNVERIFIED-LABELED** (as-of rule: row D = D close, public by D 20:00 ET) |
| all | SEC EDGAR N-PORT | **Monthly** | EDGAR acceptance time | never daily AUM (prereg §5.3) |

The BITX Wayback detail (`bitx_wayback_captures.csv`): the CDX lists 17 Train-1 captures. Wayback's
`id_` redirects serve **10 distinct snapshots**, with 9 distinct as-of dates: 2024-05-02, 05-03,
05-17, 05-20, 06-14, 09-05, 12-03, 2025-01-17, 01-28. Every served capture shows an as-of date before
its capture date, so all are PIT-valid. One defect was caught and fixed during the probe: several CDX
timestamps redirect to a *later* snapshot. For example, CDX `20240812` serves the 2024-09-06 page,
which shows as-of 09-05. Using the requested timestamp instead of the served one would have created
look-ahead. The lab records the served timestamp (`fetch.wayback_raw`).
Sanity check: captured BITX NAV vs Yahoo close on the as-of date differs by −0.30% to +0.34%
(`bitx_nav_vs_yahoo.csv`). The captures are genuine, just rare.

## 4. Gate 0 result (`gate0_coverage.json`, `aum_pit_panel.csv`, `price_coverage.csv`)

| Check | Value | Bar | Result |
| --- | --- | --- | --- |
| BITX PIT AUM (as-of ≤ t−1, public by 15:00 ET t, carry ≤ 3 sessions) | **29 / 250 = 11.6%** (8 fresh, 21 stale ≤ 3) | ≥ 90% | **KILL** |
| Longest BITX gap | 59 consecutive sessions | (none) | (none) |
| BITU PIT AUM, live sessions | 229 / 229 (21 pre-launch sessions structurally absent) | (none) | labelled UNVERIFIED |
| SBIT PIT AUM, live sessions | 229 / 229 (21 pre-launch absent) | (none) | labelled UNVERIFIED |
| 5m price coverage, US days (Coinbase signal + Bybit outcome bars) | 247 / 247 = 100% | ≥ 95% | pass |
| 5m price coverage, placebo days | 115 / 115 = 100% | (none) | (none) |
| NYSE calendar vs BITX Yahoo sessions | 250 = 250, no mismatch | (none) | pass |

Missing BITX days were **not** turned into zero signal (prereg §5). They are MISSING. Leaving BITX
out of F was not an allowed rescue: the prereg requires BITX, and BITX is the dominant fund.

## 5. Gates 1–5, first stage, long vs inverse, cost: **NOT REACHED**

| Gate | Status |
| --- | --- |
| 0 Data | **KILL** (BITX PIT AUM 11.6% < 90%) |
| 1 Size | not reached |
| 2 Episodes | not reached (an eligible-day count would be ≤ 29 with BITX, far below 150) |
| 3 Identification (US − placebo, slope, adjacent hours) | not reached, not computed |
| 4 Cost (large-flow net after 9.92 bp RT) | not reached, not computed |
| 5 Concentration | not reached |

- **First-stage metrics:** none were computed, by design (stop at the first KILL). No outcome return
  series was built.
- **Long vs inverse:** data status only. The long leg is broken (BITX missing on 221/250 sessions).
  The inverse leg (SBIT) has a full but unverified issuer history. No signed results exist for either leg.
- **Cost:** primary 9.92 bp RT (maker 5.12, stress 50/75/100) was never applied, because there is no
  outcome. 34 bp was not used.

## 6. What would be needed (no purchase proposed)

Exactly one field is missing: **daily BITX shares outstanding (or net assets) for Train-1 with a
credible as-of timestamp.** The issuer does not publish a free history. Free archives give 9 points
per year. N-PORT is monthly. Any reconstruction, such as interpolating shares between captures or N-PORT
months, or inferring creations from volume, would be a PROXY, and the prereg forbids a proxy from
passing Gate 0. This note does not recommend buying data; the owner rule rules it out.

## 7. Caveats

- ProShares BITU/SBIT history is free and complete but downloaded after the fact. Its PIT status is
  `UNVERIFIED-LABELED`. Even if BITX had passed, the best verdict would have been CONDITIONAL (prereg §9).
- The BITX page shows AUM as of the prior close, and its update time within the day is unknown. Only
  the capture time proves publication, which is conservative.
- The ETH replication (prereg §10) did not run, because BTC did not reach Gate 3.
- The price caches are complete (Coinbase 108,264 bars; Bybit 108,288 bars), so Gate 0 price coverage
  is not the issue. Binance perp volume (needed only for Gate 1) was not fetched because Gate 1 was not reached.

## 8. Reproduce

```
python3 -m letf_reset_lab.run          # fetches into data_cache/f012_r2a/ (git-ignored), writes output/f012_r2a_letf_reset/
python3 -m pytest -q tests/test_letf_reset_lab.py
```
Inputs are hashed in `output/f012_r2a_letf_reset/inputs_sha256.json`. Issuer pages and Wayback can
change. The hashes pin the snapshot used on 2026-10-06.
