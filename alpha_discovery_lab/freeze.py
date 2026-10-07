"""Write the F014 freeze artefacts (no scoring): splits, registry (+ sha256), datasets inventory.

Run: python3 -m alpha_discovery_lab.freeze [--data-root PATH]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from alpha_discovery_lab import data as D
from alpha_discovery_lab.registry import (BLOCKS, FROZEN_SPLITS, HYPOTHESES, PROTOCOL, SCORED_SPLIT, SPLITS,
                                          registry_payload, registry_sha256)

OUT = D.REPO / "output" / "f014_discovery"


def registry_md() -> str:
    lines = ["# F014 hypothesis registry (FROZEN before scoring)", "",
             f"sha256 (canonical JSON of registry_payload): `{registry_sha256()}`", "",
             f"Family m = {PROTOCOL['fdr']['m']} (28 hyps x 2 required assets, primary horizon), "
             f"BH q <= {PROTOCOL['fdr']['q_max']}.", "",
             "| # | id | fam | state | expected | d | horizons (primary first) | target | expression | req assets |",
             "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for i, h in enumerate(HYPOTHESES, 1):
        lines.append(f"| {i} | {h['id']} | {h['family']} | {h['state']} | {h['expected']} | {h['d']:+d} | "
                     f"{h['horizons']} | {h['target']} | {h['expression']}{'' if h['tradable'] else ' (NON-TRADABLE)'} "
                     f"| {', '.join(h['required_assets'])} |")
    lines += ["", "## Why / notes", ""]
    for h in HYPOTHESES:
        lines.append(f"- **{h['id']}** — {h['why']}." + (f" Note: {h['notes']}" if h["notes"] else ""))
    lines += ["", "## Protocol", "", "```json", json.dumps(PROTOCOL, indent=2), "```", ""]
    return "\n".join(lines)


def inventory_md(inv: dict) -> str:
    lines = ["# F014 datasets inventory (Train-1 files only)", "", f"data_root: `{inv['data_root']}`",
             f"window loaded: [{inv['window'][0]}, {inv['window'][1]}) — validation/holdout files never read", "",
             "| file | present | rows | first | last |", "| --- | --- | --- | --- | --- |"]
    for k, v in inv["files"].items():
        lines.append(f"| {k} | {v['present']} | {v.get('rows', '')} | {v.get('first', '')} | {v.get('last', '')} |")
    lines += ["", "## Gaps / constraints", ""] + [f"- {g}" for g in inv["gaps"]] + [""]
    return "\n".join(lines)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root")
    a = ap.parse_args(argv)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "splits_frozen.json").write_text(json.dumps(
        {"splits": SPLITS, "blocks": BLOCKS, "scored": SCORED_SPLIT, "frozen_never_scored": FROZEN_SPLITS},
        indent=2) + "\n")
    payload = registry_payload() | {"sha256": registry_sha256()}
    (OUT / "hypothesis_registry.json").write_text(json.dumps(payload, indent=2) + "\n")
    (OUT / "hypothesis_registry.md").write_text(registry_md())
    inv = D.inventory(D.data_root(a.data_root))
    (OUT / "datasets_inventory.json").write_text(json.dumps(inv, indent=2) + "\n")
    (OUT / "datasets_inventory.md").write_text(inventory_md(inv))
    print("registry sha256", registry_sha256())


if __name__ == "__main__":
    main()
