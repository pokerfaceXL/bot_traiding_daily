# F013 — Delisting Informational Alpha: discovery gates B–Q — decision

> 2026-10-07 Europe/Warsaw. Prereg SSOT `spec/research/F013-delisting-informational-alpha-prereg.md`
> (frozen in `0d77ea4`, no amendments). Discovery = C02 Train-1 announcements [2024-03-01, 2025-03-01)
> UTC, **contaminated**. Validation [2025-03-01, 2026-03-01) and sealed holdout **not opened**.

## Decision: **FAIL**

Gate D (cost ladder, **KILL**) fails on the discovery set: the net@34 day-batch cluster CI lower bound
is −197 bp. The C02 incidental short did not survive the first cost attack. Per prereg §6/§10 the run
stopped at the first KILL FAIL: Gates E–N, P, Q were **not run**, and Gate O (validation) is **not
scored**. F013 is archived. No relabeled retry.

## What was tested

- Sample (frozen funnel): 163 catalog rows → Gate A usable 151 → 89 tradeable same-venue USDT-perp events.
  Of these, 76 are in the primary universe (61 perp-only, 15 spot+perp; index 2 and migration 11 are
  excluded). 74 have perp data: Bybit ZKUSDT (pre-market contract) and MONUSDT have no archive. All 74
  have sufficient notice. 73 are eligible (Gate C). The Gate K liquidity exclusion (pre-P 24 h
  turnover < 500 k USDT or > 20 % zero-volume bars) removes 18. **Scored: 55 events, 32 day-batch
  clusters** (Binance 26 / Bybit 29).
- Trade: short at the open of the first 1m bar ≥ P + 5 min. Exit at the open of the first 1m bar ≥
  min(entry + 72 h, eff − 1 h). Equal notional. Funding received by the short over (entry, exit].
- Inference: day-batch cluster bootstrap, 10 000 draws, seed 13, percentile 95 % CI.
- Data: fetched fresh into `data_cache/f013/` (git-ignored). Sources: Binance fapi REST 1m with a
  vision daily-klines fallback, Bybit v5 REST 1m (it still serves delisted symbols), Binance vision
  aggTrades and Bybit trade archive for ticks (archives deleted after slicing), venue funding APIs, and
  spot REST/vision. Total cache ≈ 16 MB.
- Cross-check: event gross returns match C02's independently computed `short_bar5m_+72h` (e.g. VGX
  −7395 vs −7421 bp, AMB +6007 vs +6189 bp, REEF +4739 vs +4740 bp). The FAIL is not a data artefact.

## Gate table

| Gate | Kind | Status | Key numbers |
|---|---|---|---|
| A Timestamp integrity | KILL | PASS (prior job) | 151/163 usable; 12 Bybit F3 dropped |
| B Latency decay | ROUTE | PASS | net@34: P+10s 720, P+30s 625, P+60s 598, P+1m 508, **P+5m 528**, P+15m 513 bp. Every CI includes 0. Not a speed race. |
| C Short eligibility | KILL | PASS | 73/74 = 98.6 % (≥ 70 %). FBUSDT had no trade in the entry minute. Binance "no new positions" starts ≈ eff − 30 min, which is after entry. |
| **D Cost ladder** | **KILL** | **FAIL** | net@34 mean **528.5**, median 359.9, CI **[−197.1, 1182.8]**. Mean net@75 = 487.5 (> 0), but the CI lower bound must be > 0. Breakeven 562.5 bp RT. |
| E Funding carry | KILL | NOT RUN | stopped after D |
| F Fixed horizons | ROUTE | NOT RUN | stopped after D |
| G Market-adjusted | KILL | NOT RUN | stopped after D |
| H Spot/perp co-move | ROUTE | NOT RUN | stopped after D |
| I Clustering | KILL | NOT RUN | stopped after D (D already uses the day-batch CI) |
| J Tails | KILL | NOT RUN | stopped after D |
| K Liquidity | KILL | NOT RUN (exclusion rule applied to the sample) | 18 excluded, 55 kept |
| L Notice length | ROUTE | NOT RUN | stopped after D |
| M Delisting type | ROUTE | NOT RUN | stopped after D |
| N Novelty | ROUTE | NOT RUN | stopped after D |
| O Validation | KILL | NOT SCORED | validation sealed (prereg §7) |
| P Placebos | KILL | NOT RUN | stopped after D |
| Q Pre-trend | KILL | NOT RUN | stopped after D |

Cost ladder (scored n = 55, 32 clusters, mean / CI in bp):
9.9 (context) 552.6 [−173.0, 1206.9] · **34 528.5 [−197.1, 1182.8]** · 50 512.5 [−213.1, 1166.8] ·
75 487.5 [−238.1, 1141.8] · 100 462.5 [−263.1, 1116.8] · 150 412.5 [−313.1, 1066.8] ·
200 362.5 [−363.1, 1016.8]. Even the owner-tier 9.9 bp rung has a CI that crosses 0.

## Robustness / context (not decision-bearing)

- **Gate A PASS-only** (WARN events dropped): n = 40, 26 clusters, net@34 mean 692.3, CI [−2.0, 1354.7].
  The sign holds, and the CI still crosses 0.
- **Before the Gate K exclusion** (eligible sample): n = 73, 37 clusters, net@34 mean 492.4, CI
  [−143.8, 1090.6]. So the FAIL does not depend on reading Gate K as a sample filter.
- Shape: the mean is large, but the distribution is two-sided and very fat-tailed. On the loss side,
  VGX −7447, GFT −4874 (−2019 bp funding), STMX −4494, XEM −3413 and LOOM −3056 bp. On the win side,
  AMB +6158/+4928, REEF +4803 and 1000IQ50 +4339 bp. The worst day-batch cluster (Bybit B022) loses
  10 503 bp. With 32 clusters the effect cannot be told apart from zero.

## Interpretation

On the contaminated set the post-P short has a positive point estimate (~+5 %/event net of 34 bp).
At this sample size it cannot be distinguished from a heavy-tailed coin flip. The C02 +938/+508 bp
figures did not survive cluster-honest inference at the P + 5 min clock. The prereg forbids redefining
the sample, exit, or rung after scoring, and forbids opening validation after a discovery KILL. So
nothing further is learnt here about H1. Archived as FAIL with evidence.

## Artefacts

- Outputs `output/f013_delisting_info/`: `event_table.csv` (per event), `gate_b_latency_decay.{csv,md}`,
  `gate_c_short_eligibility.{csv,md}`, `gate_d_cost_ladder.{csv,md}`, `robustness_gate_a_pass_only.csv`,
  `summary.json`, `decision.md`, `STATUS.md`.
- Code `delisting_lab/f013_{sample,data,core,events,gates,placebo,run}.py`; tests `tests/test_f013_gates.py`
  (no network). Gate P/E–Q code exists but did not run (stop rule).
- Reproduce: `python3 -m delisting_lab.f013_data && python3 -m delisting_lab.f013_run`.
