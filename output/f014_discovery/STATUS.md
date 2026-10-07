# F014 STATUS — STOP, awaiting owner approval

**Discovery verdict: 0 / 28 survivors. Nothing recommended for validation.**

- Scored window: DISCOVERY 2024-03-01 → 2025-03-01 only (Train-1 files, hard-clipped < 2025-03-01).
- VALIDATION (2025-03-01 → 2026-03-01) **not opened**; FINAL HOLDOUT (2026-03-01 → 2026-09-01) **not opened**.
- Registry frozen and committed (`1a4b5b7`, sha256 `b742d3fb…c690`) before the scoring code existed (`2bfaac4`).
  The runner checks that hash before scoring.
- Ledger: 244 rows (28 hyps × assets × horizons), 0 SKIPPED, 0 INSUFFICIENT; FDR family m = 56, 10 tests with BH q ≤ 0.10.
- Criteria pass counts (of 28): C1 sign 17, C2 FDR 2, C3 stability 4, C4 replication 14, **C5 cost 0**.

## Economic reading

- **No state clears owner-tier cost (9.9 bp RT) in its registered direction on both required assets**, let alone 34 bp.
  The forward-return information in 1h states is mostly a few bp per trade.
- **Strongest structure = 1h bar reversal, registered with the wrong sign.** H-PS-RANGE-LOC / -DN were registered as
  continuation; the data show reversal (close near the high → lower next 1h; close near the low → higher). The effect
  is in BTC, ETH and SOL, mostly 4/4 blocks, BTC LOC-DN p < 1e-5. It fails C1/C4 as registered and is **not flipped
  post hoc**. Even reversed, the gross is ≈ 3–10 bp per trade at 1–4h (BTC LOC-DN state mean +6.3 bp @1h, +10.0 bp
  @4h), so it is at or below 9.9 bp and far below 34 bp. H-PS-REV-DN (buy large down bars) has the right sign, 4/4
  blocks on both assets, q ≈ 0.17–0.24 (fails FDR), gross 4.8 / 6.1 bp @1h → net@9.9 ≈ −5 / −4 bp. Same short-horizon
  liquidity reversal, too small to pay taker costs.
- H-PS-VOL-COMPRESS: strong and stable vol expansion after compression (q ≈ 0, 4/4 blocks, BTC+ETH+SOL). It is
  non-tradable on linear perps (C5 by construction) and partly mechanical: the move is normalised by a low trailing σ.
- Derivatives (funding / OI), positioning (buyRatio), cross-market residuals, lead-lag and time-of-day: no state passes
  FDR on both assets. H-PS-TREND-UP is significantly *negative* on ETH and SOL (breakouts revert at 1h), which also
  contradicts the registered continuation.

## Hypothesis-generating only (NOT a candidate; would need a NEW prereg + owner approval)

1h close-location / large-bar **reversal** could only pay with maker-side execution (≈ 5 bp RT bound in
`spec/research/F012-owner-cost-hurdle.md`). That is an execution question, not a discovered edge. No reversal test was
run here.

## Next

Owner decision only. Do not open validation or holdout for any F014 hypothesis: there are no survivors to validate.

Artefacts: `ledger.jsonl|csv`, `fdr_report.md|json`, `survivors_ranked.md|json`, `discovery_summary.json`,
`hypothesis_registry.md|json`, `splits_frozen.json`, `datasets_inventory.md|json`.
Re-run: `python3 -m alpha_discovery_lab.run --data-root <path with Train-1 1h OHLCV + account_ratio_5m>`.
