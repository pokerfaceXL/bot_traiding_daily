# F013 Delisting Informational Alpha — STATUS

**2026-10-07 Europe/Warsaw · FAIL (Gate D KILL on discovery) · ARCHIVED · validation never opened**

## Result
- Gate A PASS (prior job): 151/163 usable; `gate_a_timestamp_audit.{csv,md}`.
- Gate B latency decay (ROUTE) **PASS**: net@34 > 0 at every latency (P+10s 720 … P+5m 528, P+15m 513 bp).
  Every CI includes 0. `gate_b_latency_decay.{csv,md}`.
- Gate C short eligibility (KILL) **PASS**: 73/74 = 98.6 %. `gate_c_short_eligibility.{csv,md}`.
- **Gate D cost ladder (KILL) FAIL**: n = 55 / 32 day-batch clusters. net@34 mean 528.5 bp, CI [−197.1, 1182.8].
  Breakeven 562.5 bp RT. `gate_d_cost_ladder.{csv,md}`.
- Gates E–N, P, Q: NOT RUN (stop at first KILL FAIL). Gate O: NOT SCORED (validation sealed).
- Robustness: Gate-A PASS-only n = 40, mean 692.3, CI [−2.0, 1354.7]. Pre-Gate-K n = 73, mean 492.4,
  CI [−143.8, 1090.6]. Both fail the same bar.
- Per-event table `event_table.csv`; machine summary `summary.json`; decision `decision.md`.

## Funnel
Gate-A usable primary 76 → with perp data 74 (ZKUSDT pre-market, MONUSDT: no archive) → sufficient notice 74 →
eligible 73 → Gate K liquidity-included 55 = scored.

## Data
Fresh downloads in `data_cache/f013/events/<event_id>/` (git-ignored, ≈ 16 MB). Raw archives were deleted after
slicing. C02 artefacts in `output/f012_c02_delisting/` were read-only.

## Next
None. Archived per prereg §10 — no relabeled retry, no live bot, no optimization.
