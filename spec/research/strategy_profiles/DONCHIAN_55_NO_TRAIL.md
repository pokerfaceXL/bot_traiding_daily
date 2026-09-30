# Strategy profile — DONCHIAN_55_NO_TRAIL

status: CONDITIONAL
profile_date: 2026-09-30
baseline_source: output/f006_signal_autopsy/control_on (main tip f925a47)
trade_table: output/f006_signal_autopsy/control_on/autopsy/*_DONCHIAN_55.csv
train1_entry_cohort: 2024-03-01 <= entry_time < 2025-03-01 UTC (train1_entry=True)

## Mechanism

Persistent Donchian N=55 breakout: long when close breaks prior 55-bar high, short on prior 55-bar low; hold until opposite extreme (signal_reverse) or initial stop. Exit geometry for this profile: **NO_TRAIL** (initial SL only, max_sl_pct=0.03, no trailing). One-shot entry mask as in shared F006 harness.

## Suspected edge source

Rare **channel runners** that reach the opposite Donchian extreme (`signal_reverse`). Aggregate edge is not a high win rate; it is a small number of large winners versus many capped ~−3.3 stop losses.

## Where it earns

- Exit reason `signal_reverse` (Train-1): n=168, WR≈70.8%, mean net ≈ +8.57, sum ≈ +1440.5
- Especially long direction (Train-1 longs net ≈ +595.7 vs shorts ≈ −25.5)
- Fat-tail months / symbols: 2024-11 alone ≈ +680.6 of ≈ +570.2 total Train-1 net; XRPUSDT and DOGEUSDT contribute most
- High relative ATR percentile bucket 75–100 has best mean, but this overlaps the same runner month

## Where it loses

- Exit reason `initial_sl` (Train-1): n=275 (61.5% of trades), WR=0%, mean ≈ −3.32, sum ≈ −913.0
- 7 of 12 Train-1 entry-months are net negative (spread across year, not one crash)
- Without 2024-11, pooled Train-1 net ≈ **−110** (series mean flips negative) — edge is economically fragile and concentrated
- Weak series: SOLUSDT/240, DOGEUSDT/240; ETHUSDT/60 slightly negative

## Win structure

- WR ≈ 27.5% (123 / 447)
- avg win ≈ +12.76, median win ≈ +5.85, max win ≈ +267.6
- Top 1 win ≈ 46.9% of total net; top 5 wins > 100% of total net
- Wins hold much longer (mean bars ≈ 178) with large MFE (mean ≈ 25.4%)

## Loss structure

- avg loss ≈ −3.09 (almost all full initial stops)
- Losses hold mean ≈ 29 bars; mean MFE ≈ 2.86% (67% of losses had MFE>1% before dying — not all are instant false breaks)
- Classic false-break proxy (`initial_sl` & MFE<1%): n=103 (23% of trades), ≈31.8% of loss count

## Core metrics (Train-1 entries)

| metric | value |
| --- | ---: |
| n_trades | 447 |
| net_pnl sum | +570.21 |
| mean net / trade | +1.276 |
| harness mean train1_net_pnl across 10 series | +58.387 |
| win rate | 27.52% |
| losing entry-months | 7 / 12 |
| costs sum | 143.97 |
| gross sum | 714.17 |

## Stability

- **Symbols:** uneven — XRP/DOGE carry; BTC near flat; SOL weak on 240
- **Intervals:** both 60 and 240 net positive in pool; 60 has far more trades (352 vs 95)
- **Periods:** unstable month-to-month; one month dominates
- **Concentration:** extreme (single-trade / single-month dependence)

## Tested modifications (family / same problem class)

| change | note | outcome vs this problem |
| --- | --- | --- |
| Trailing sweep / boundary | F006-hypothesis-trailing-* | NO_TRAIL best; keep |
| Stop width NO_TRAIL | F006-hypothesis-stop-width-notrail | modest net/trade gain; does not fix months |
| Entry width-expansion gate | F006-hypothesis-entry-width-expansion | starves trades; fails |
| Entry EMA50/200 trend confirm | F006-hypothesis-entry-trend-confirm | **destroys** DONCHIAN_55 (+58 → −3.6); removes fresh breakouts |
| Cross-symbol agreement | F006-hypothesis-entry-cross-symbol* | small WR help; no monthly clear |
| Loss-recency cooldown | F006-hypothesis-loss-recency-cooldown | worsens months |
| Take-profit | F006-hypothesis-exit-take-profit | WR up, **net negative** (cuts tails) |
| Vol-inverse sizing | F006-hypothesis-position-sizing-vol-inverse | falsified |
| Calm / low ATR-percentile keep | autopsy counterfactual | **destroys** edge (removes runners) |
| Catalog expansion / other families | many DNR | do not replace diagnosis of this baseline |

## Rejected hypotheses (do not retest without new info)

- “Quality = agree with slow EMA trend”
- “Quality = calm / low volatility at entry” (percentile≤0.5)
- “Raise WR with TP / trail”
- “Fix months with loss-recency cooldown”
- Random new independent strategies before finishing this profile’s open questions

## Unresolved questions

1. Can an **entry-time** feature separate `initial_sl` deaths from `signal_reverse` runners without removing Nov-type winners?
2. Absolute ATR% at entry is higher on `initial_sl` (≈1.63) than on `signal_reverse` (≈1.05) — is that a usable gate or another way to cut tails?
3. Is long-only a structural crypto asymmetry or Train-1 sampling artifact?
4. Given concentration, should status move to FREEZE if the next single-axis test fails?

## Allowed next experiments (budget: one primary change)

1. **H-DONCHIAN-ABS-ATR-ENTRY-GATE-01** (preferred): reject entry when ATR% exceeds a small pre-registered threshold grid — see companion hyp note.
2. If (1) falsified: optional long-only ablation as a *portfolio construction* question, not as “new strategy search”.
3. No new unrelated strategy family until this profile is FREEZE/FALSIFIED with documented insufficiency, or a clearly non-correlated mechanism is justified per COORDINATOR_RESEARCH_PROTOCOL §13.

## Status rationale

**CONDITIONAL** (protocol Level B): aggregate positive after costs, enough trades, risk-limit survivable on harness rows, explainable mechanism — but monthly regularity fails, edge is concentrated in few runners, and symbol/interval stability is uneven. Not FREEZE yet: one untested entry axis remains (absolute ATR% gate). Not CONTINUE as a generator of new families. Not REJECT: baseline still the research control (+58.387).
