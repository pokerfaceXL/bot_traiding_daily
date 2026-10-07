# F014 Systematic alpha discovery — CLOSED NO CANDIDATE

**Closed 2026-10-07 Europe/Warsaw by owner decision.** ChatGPT PO was skipped for this track.

## Verdict

**NO CANDIDATE.** Discovery: **0 / 28** survivors. Validation and FINAL HOLDOUT were never opened.

## What was frozen before scoring

- Prereg: `spec/research/F014-systematic-alpha-discovery-prereg.md`
- Machine registry: `alpha_discovery_lab/registry.py` → `output/f014_discovery/hypothesis_registry.json`
- Registry sha256: `b742d3fb…c690` (committed `1a4b5b7` before scoring code `2bfaac4`)
- Discovery tip that reported 0 survivors: `4482000`

## Scope scored

- Window: DISCOVERY only, 2024-03-01 → 2025-03-01 (Train-1, hard-clipped)
- Assets: BTCUSDT + ETHUSDT required; SOLUSDT optional where registered
- Horizon focus: 1h states (forward returns at registered horizons)
- Families (28 hyps): price structure, funding/OI, Bybit buyRatio, cross-market residual/lead-lag, vol regime, time-of-day
- Primary test: state-vs-complement mean difference, Newey–West (24 lags); BH family m = 56 (28 × 2 assets)

## Criteria pass counts (of 28)

| Criterion | Pass |
| --- | ---: |
| C1 sign | 17 |
| C2 FDR (BH q ≤ 0.10) | 2 |
| C3 temporal stability (≥3/4 blocks) | 4 |
| C4 BTC/ETH replication | 14 |
| **C5 net @ ≈9.9 bp RT > 0 on both assets** | **0** |

FDR: 10 / 56 tests with BH q ≤ 0.10. Ledger: 244 rows, 0 SKIPPED, 0 INSUFFICIENT.

## Economic reading (not a candidate)

1h states carry a few bp of short-horizon **reversal** information. The strongest registered structures either have the wrong registered sign (not flipped post hoc) or clear FDR/stability but fail the cost hurdle. Even if reversal were re-registered, gross ≈ 3–10 bp/trade is at or below the owner-tier ≈9.9 bp RT taker hurdle and far below 34 bp stress. Vol-compression predicts |return| expansion robustly but is non-tradable on linear perps under C5-by-construction and partly mechanical.

A maker-execution reversal study would require a **new** prereg and a new owner mandate — it is not an F014 continuation.

## Artefacts

- `output/f014_discovery/STATUS.md`, `ledger.jsonl|csv`, `fdr_report.md|json`, `survivors_ranked.md|json`, `discovery_summary.json`, `hypothesis_registry.md|json`, `splits_frozen.json`, `datasets_inventory.md|json`
- Code: `alpha_discovery_lab/`; tests: `tests/test_f014_discovery.py`
- Feature archive: `spec/features/done/F014-systematic-alpha-discovery/` (+ `outcome.md`)

## Collectors / systemd

Untouched. `f011-liq-collector` stays running (REVIEW_AT_N). F012 timers stay disabled.

## Forbidden without new evidence / new mandate

- Opening VALIDATION or FINAL HOLDOUT for any F014 hypothesis
- Post-hoc sign flips of registered hypotheses
- Relabeling F014 as a maker study
- Reopening F011 / F012 / F013 closed tracks
