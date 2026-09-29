"""Run the five frozen H-SUBE-INV-FVG-01 names on the shared Train-1 harness."""
from __future__ import annotations

import json
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sube_inv_fvg
from scripts import f006_family_runner as runner

FAMILY = "sube_inv_fvg"
NAMES = list(sube_inv_fvg.NAMES)
NOTE = "spec/research/F006-hypothesis-sube-inv-fvg.md"


def _references() -> dict:
    """Load only frozen Train-1 frames and map each target close stream to its SMT peer."""
    refs = {}
    for interval in runner.INTERVALS:
        frames = {symbol: runner.load_train1(symbol, interval)[0] for symbol in runner.SYMBOLS}
        for symbol, frame in frames.items():
            peer = frames["ETHUSDT"] if symbol == "BTCUSDT" else frames["BTCUSDT"]
            refs[tuple(frame["close"].astype(float))] = peer
    return refs


def main() -> None:
    manifest = runner.run_family(
        family=FAMILY, candidate_names=NAMES,
        catalog_entries=sube_inv_fvg.catalog_entries(_references()), hypothesis_note=NOTE,
        script_path="scripts/f006_sube_inv_fvg_experiment.py",
    )
    results = pd.read_csv("output/f006_sube_inv_fvg/summary/results.csv")
    candidates = results[results.strategy.isin(NAMES)]
    density = []
    for name in NAMES:
        mean_trades = float(candidates[candidates.strategy == name].n_trades.mean())
        density.append({"strategy": name, "mean_trades_per_series": mean_trades,
                        "sparsity_falsified": mean_trades < 10})
    with open("output/f006_sube_inv_fvg/summary/sparsity_check.json", "w") as f:
        json.dump(density, f, indent=2)
    print(json.dumps({"h1": manifest["h1_table"], "h2": manifest["h2_status"], "density": density}, indent=2))


if __name__ == "__main__":
    main()
