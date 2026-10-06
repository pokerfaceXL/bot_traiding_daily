# F012-R2A: pre-registration (frozen before any AUM history download or outcome scoring)

Written 2026-10-06. Before this file was frozen, the only data touched was the round-2 availability
probe (Yahoo daily bar *counts* for BITX/BITU/SBIT/ETHU, `2ae9c99` §4). No AUM, NAV, share count,
or 5m price was downloaded. No outcome was computed.

Everything below is frozen. Tickers, windows, thresholds, models and gates are **not** changed after
results. There is no symbol shuffle and no post-hoc expansion.

---

## 1. Universe and leverage targets

| Fund | Issuer | Target L | L(L−1) | Role |
| --- | --- | --- | --- | --- |
| BITX | Volatility Shares (2x Bitcoin Strategy ETF) | +2 | +2 | long, in F |
| BITU | ProShares (Ultra Bitcoin ETF) | +2 | +2 | long, in F |
| SBIT | ProShares (UltraShort Bitcoin ETF) | −2 | +6 | inverse, in F |
| ETHU, ETHT | Volatility Shares / ProShares 2× ether | +2 | +2 | **ETH replication only, never a gate** (§10) |

Each L is recorded from the issuer's prospectus or fund page, with the source URL kept in
`output/f012_r2a_letf_reset/pit_timeline.csv`. If a prospectus states a different L, that fund is
logged as a data defect and the frozen L above is **not** changed.

## 2. Predicted reset flow (point-in-time equations)

Notation: `A_{i,t−1}` = fund i's AUM (NAV per share × shares outstanding) as of the US session t−1
close. `r_t` = BTC return over the signal window (§3).

After a day with return r, the fund's exposure is `L·A(1+r)` and its NAV is `A(1+L·r)`. Getting back
to target exposure `L·A(1+L·r)` needs a trade of **ΔE = L(L−1)·A·r**. This is exact, before fees and
same-day creations and redemptions, which are unknown at 15:00 and are ignored.

- **Long funds (L = +2):** `F_long,t = Σ_{i∈{BITX,BITU}} 2 · A_{i,t−1} · r_t` (same sign as r)
- **Inverse fund (L = −2):** `F_inv,t = Σ_{i∈{SBIT}} (−2)(−3) · A_{i,t−1} · r_t = 6 · A_{SBIT,t−1} · r_t` (also same sign as r)
- **Aggregate:** `F_t = F_long,t + F_inv,t = Σ_i L_i(L_i−1) · A_{i,t−1} · r_t`, in **USD of BTC exposure** (buy if > 0).

Because L(L−1) > 0 for every fund and A > 0, **sign(F_t) = sign(r_t)** on every day. AUM sets only the
magnitude. Identification therefore rests on (i) the weekend/holiday placebo, (ii) dose-response in |F|
with AUM variation, and (iii) adjacent hours (§6).

## 3. Clock, cutoff and windows (America/New_York, DST-aware; all prices are 5m bar **opens**)

- **Information cutoff:** 15:00:00 ET on US trading day t. Every input must be known by then.
- **Signal return r_t:** Coinbase BTC-USD `open(15:00 ET, t) / open(C_{t−1}) − 1`. Here C_{t−1} is the
  official close time of the previous NYSE session: 16:00 ET, or 13:00 ET on an early-close day.
  Monday uses Friday's close, and the day after a holiday uses the last session's close. This is the
  same span the funds' daily return covers, up to 15:00.
  Bybit BTCUSDT is a cross-check only: the signs must agree on ≥ 95% of days, reported.
- **AUM cutoff:** `A_{i,t−1}` must be a value whose as-of date is ≤ t−1, published by the issuer after
  the t−1 close and therefore before 15:00 ET on t. The latest such value is used.
- **Outcome (trade) window:** Bybit BTCUSDT linear perp, entry at the open of the 15:00 ET 5m bar and exit
  at the open of the 16:00 ET 5m bar. `ret_t = exit/entry − 1`, in bp. One trade per eligible US
  trading day. There are no official-close or NAV fills.
- **Signed return:** `y_t = sign(F_t) · ret_t` (bp). A day with F_t = 0 exactly gives y = 0 and is counted.
- **Adjacent-hour controls:**
  - 16:00→17:00 ET: same sign(F_t) (known at 15:00), outcome Bybit open(16:00)→open(17:00).
  - 14:00→15:00 ET: signal recomputed without look-ahead as r ending at 14:00
    (`open(14:00)/open(C_{t−1}) − 1`, same AUM), outcome Bybit open(14:00)→open(15:00). Using the
    15:00 signal here would put the outcome inside the signal window (a tautology), so it is not done.

## 4. Calendar and day classes

- **US trading days:** NYSE full sessions in 2024-03-01 → 2025-02-28. Holidays are hard-coded and
  cross-checked against BITX Yahoo trading dates (expected 250 sessions): 2024-03-29, 05-27, 06-19,
  07-04, 09-02, 11-28, 12-25, 2025-01-01, 01-09 (national day of mourning), 01-20, 02-17.
- **Early-close sessions** (13:00 ET close: 2024-07-03, 2024-11-29, 2024-12-24): the reset trades before
  13:00, so the 15:00–16:00 window is not the reset window. These days are **excluded** and counted
  separately as `early_close`. They are neither US-eligible nor placebo.
- **Placebo days:** every Saturday, Sunday and full NYSE holiday in Train-1, when BTC trades but no fund
  resets. Placebo signal: `r_p,d = open(15:00 ET, d)/open(16:00 ET, d−1) − 1` (Coinbase), where d−1 is
  the previous calendar day. A Saturday's window starts Friday 16:00 and a Sunday's starts Saturday
  16:00. Placebo signed return `y_p,d = sign(r_p,d) · ret_d`, on the same Bybit 15:00→16:00 clock and with
  the same sign rule. The placebo adjacent hours use the same construction as §3.

## 5. Data sources, PIT rules, missing vs zero

**Price sources (free):** Coinbase Exchange public candles API (BTC-USD 5m); Bybit v5 public kline API
(BTCUSDT linear 5m, volume + turnover); Binance `data.binance.vision` USD-M futures monthly 5m klines
(BTCUSDT, quote volume). Raw files are cached git-ignored under `data_cache/f012_r2a/` and sha256 is
recorded.

**AUM source hierarchy (free only, first that works):**
1. Issuer daily history files from the fund pages (Volatility Shares for BITX; ProShares for BITU/SBIT)
   with date, NAV and shares outstanding (or net assets). As-of rule: the row dated D is the D close,
   published that evening, and used from D+1. **This history is downloaded today, after the fact.** It
   is labelled `issuer-history as-of rule` and must be verified (below).
2. Wayback Machine captures of the issuer fund pages inside Train-1. These are PIT by capture time.
   They are used for verification. If source 1 does not exist, they are a sparse primary with
   carry-forward ≤ 3 sessions.
3. SEC EDGAR N-PORT is **monthly**. It is never used as daily AUM. At most it is a labelled cross-check.
   No paid source. No proxy (for example Yahoo volume, end-of-period AUM, or N-PORT interpolation) is used
   as AUM without a `PROXY` label, and a proxy cannot pass Gate 0.

**PIT verification of source 1:** compare history values to every parseable Wayback capture of the
issuer pages that falls in Train-1 (NAV or shares for the date displayed on the capture). Match =
within 1% on NAV and shares (or net assets).
- `VERIFIED`: ≥ 10 matched comparisons and ≥ 90% agree.
- `UNVERIFIED-LABELED`: fewer than 10 comparable captures. Scoring continues, but the best verdict is
  **CONDITIONAL** (§9).
- `CONTRADICTED`: ≥ 10 comparisons and < 90% agree. This is a **Gate 0 KILL**.

**Leave-out and missing rules (frozen):**
- Before its first NAV row (BITU/SBIT launched 2024-04-02), a fund is **structurally absent**:
  contribution 0, which is a true zero and not missing. Its first eligible day is the session after its
  first NAV row.
- After launch, a missing `A_{i,t−1}` is carried forward from the latest earlier as-of value for at
  most 3 sessions (flagged `stale`). Beyond that the **day is MISSING**: excluded and counted, never
  treated as zero signal.
- BITX missing on a day (after the 3-session carry) → the day is MISSING.
- A missing required 5m bar (exact bar open; no interpolation) for the signal or the outcome → the day
  is MISSING (counted by reason). Missing adjacent-hour bars drop the day only from that adjacent-hour
  control.
- A day whose |r| is computed but whose F is uncertain for any of the reasons above is never scored as
  zero.

## 6. Primary specification and statistics

- **Eligible US days:** US trading days, not early-close, not MISSING.
- **Large-flow subset (PIT):** day t is large if |F_t| ≥ the 67th percentile of |F| over **prior** eligible
  US days (expanding window, `numpy.quantile` linear, prior days only). **Warm-up = the first 40
  eligible US days**, which are never large but stay in all-day tests.
- **Bootstrap:** weekly block bootstrap. Blocks are calendar weeks (Mon–Sun, ET dates), so US days and
  placebo days of the same week resample together. B = 10,000, seed 20261006. One-sided p for "stat > 0"
  = share of replicates with `(stat* − stat̂) ≥ stat̂` (null-centred). The 95% CI is percentile.
- **Gate-3a statistic:** `D = mean(y_t | eligible US) − mean(y_p,d | placebo)`.
- **Gate-3b regression:** `y_t = a + b·|F_t| + e` on eligible US days (|F| in $100M). Slope b > 0 is the
  dose-response "signed return on predicted flow". p from the weekly block bootstrap (HAC t reported).
- **Gate-3c:** D computed the same way for 14:00–15:00 and 16:00–17:00 (§3). The 15:00–16:00 D must be
  **strictly larger** than both point estimates.
- **Tautology control (reported; PASS needs a positive point estimate):** the outcome window starts
  exactly at the end of the signal window, so there is no mechanical overlap. Generic momentum is
  controlled by (i) the placebo difference and (ii) the orthogonalised slope: regress |F_t| on |r_t|,
  take the residual (the AUM-driven part), and regress y_t on it. Reported with a bootstrap p.
- **Controls (reported, not gates):** unconditional BTC (mean raw ret_t, mean |ret_t| on US vs placebo);
  TOD (adjacent hours); vol (y on |F| + realised 5m vol over the signal window); daily return
  direction (signed mean on up-r vs down-r days, US and placebo).
- **Long vs inverse (reported, conflicts not hidden):** slopes of y on |F_long| and on |F_inv|
  separately; large-flow subsets built from F_long alone and from F_inv alone. Sign conflicts are stated
  in the report.

**Robustness checks (exactly two, frozen):**
- **RC1, period stability:** first half vs second half of Train-1 (split at 2024-09-01). Report D and the
  large-flow net mean per half. *Why:* AUM grew strongly and BITU/SBIT launched in April, so a one-period
  artefact must be ruled out.
- **RC2, venue:** same primary spec with the Coinbase BTC-USD outcome instead of Bybit. *Why:* the
  hedging pressure should appear in spot as well as in the perp. A Bybit-only effect would point to
  venue microstructure, not the reset.

## 7. Gates (absolute, from round-2 §5; run in order, stop at the first KILL)

| Gate | KILL if |
| --- | --- |
| 0 Data | BITX `A_{t−1}` (as-of ≤ t−1, free) is available for < 90% of Train-1 US sessions; **or** 5m price coverage (all signal + outcome bars present) < 95% of US sessions; **or** PIT verification is `CONTRADICTED`; **or** AUM is only available as an unlabeled or labelled proxy. Every fund in F needs AUM per §5 leave-out rules |
| 1 Size | median over large-flow days of `|F_t| / V_t` < **1%**, where V_t = Coinbase BTC-USD (Σ volume×close) + Bybit BTCUSDT turnover + Binance BTCUSDT perp quote volume, 15:00–16:00 ET bars. median|F| / median V is also reported |
| 2 Episodes | eligible US days < 150, **or** large-flow days < 40, **or** placebo days < 80 |
| 3 Identification | D not > 0 at one-sided p < 0.05; **or** slope b not > 0 at one-sided p < 0.05; **or** D(15–16) ≤ D(14–15) or ≤ D(16–17) |
| 4 Cost | large-flow net mean `mean(y_t) − 9.92` ≤ 0, **or** its bootstrap 95% CI lower bound ≤ 0 |
| 5 Concentration | dropping the 5 large-flow days with the largest |ret_t| makes the net mean ≤ 0 |

Maker 5.12 bp and stress 50/75/100 bp are reported only. If Gate 3 is reached, the report also shows
the top-5-day share of the gross signed sum and monthly means.

**Executability:** the signal is complete at 15:00:00 and entry is the 15:00 bar open, so there is zero
lag. Because a 0-lag fill is optimistic, a +5-minute delayed entry (open of the 15:05 bar) is reported.
If net after cost is ≤ 0 at the +5m entry while > 0 at 0 lag, the timing is not executable and PASS is
downgraded to FAIL ("no executable timestamp").

## 8. Minimum sessions and coverage (summary)
≥ 150 eligible US days, ≥ 40 large-flow, ≥ 80 placebo; ≥ 90% BITX AUM PIT coverage; ≥ 95% 5m coverage.

## 9. Verdict mapping (owner)
- **PASS:** Gates 0–5 all pass, **and** PIT status `VERIFIED`, **and** stable sign (RC1 D > 0 and
  large-flow net > 0 in both halves; RC2 D > 0), **and** orthogonalised slope > 0, **and** +5m entry net > 0.
- **CONDITIONAL:** the mechanism is identified (Gates 0–3 pass) **and exactly one** of these is
  unresolved: PIT status `UNVERIFIED-LABELED`, or one of the stability / executability / economics
  checks above. Never propose a purchase.
- **FAIL:** any gate KILL, or two or more PASS conditions fail, or the orthogonalised slope ≤ 0 (no
  first stage beyond momentum).
STOP after the verdict. PASS ≠ implementation.

## 10. ETH replication (one pass, not a gate)
Only if BTC reaches Gate 3. Same spec with ETHU (+2) and ETHT (+2), Coinbase ETH-USD signal, Bybit
ETHUSDT outcome, and the same placebo. Report D and slope b only. It cannot change the verdict.

## 11. Reproducibility
`python3 -m letf_reset_lab.run` fetches (idempotently cached), builds the frame, runs gates in order,
and writes `output/f012_r2a_letf_reset/`, including `summary.json` and `inputs_sha256.json`.
