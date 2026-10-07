# F014 — Systematic alpha discovery (owner mandate 2026-10-07 Europe/Warsaw)

Status: **DISCOVERY ONLY** — validation [2025-03-01, 2026-03-01) and final holdout [2026-03-01, 2026-09-01) are FROZEN and never opened by this ticket.

## Goal
Find repeatable, executable 1h market states in BTC/ETH (SOL optional) whose forward-return information beats owner-tier cost (≈ 9.9 bp RT; 34 bp stress) on the Train-1 discovery window, under aggressive multiple-testing control. Zero survivors is an acceptable result.

## Scope / rules
- 28 pre-registered hypotheses in 6 families (price structure, derivatives, positioning proxy, cross-market, vol regime, time). No additions after scoring starts.
- F011/F012/F013 closed — not reopened. No collector or systemd changes. No live orders, no ML, no leverage-as-edge.
- Prereg: `prereg.md` (this folder) = SSOT copy of `spec/research/F014-systematic-alpha-discovery-prereg.md`; machine freeze `alpha_discovery_lab/registry.py` → `output/f014_discovery/hypothesis_registry.json` (sha256 checked by the runner).

## Deliverables
- `alpha_discovery_lab/` (data, states, stats, run CLI), `tests/test_f014_*.py`
- `output/f014_discovery/` (inventory, splits, registry, ledger, FDR report, survivors, summary, STATUS)

## Stop
After discovery scoring: STOP, awaiting owner approval before any validation run.
