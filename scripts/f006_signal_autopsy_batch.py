"""Replay digest-listed closed tips with the current runner, never old harnesses.

Only the reviewed seed list below is executable; source modules are archived
verbatim from immutable Git tips. No checkout, strategy edit, network, or holdout.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f006_family_runner as runner

NOTE = "spec/research/F006-hypothesis-signal-autopsy.md"
DIGEST = "output/f006_cross_family_digest.md"
# Existing names, not new alpha freezes. Tips are the closed local limen branches
# corresponding to the digest's six seed families, resolved before replay.
SEEDS = {
    "btc_filter": ("e5186821754db007c450906cf1d334d1aaedf274", "BTC_FILTER_ER20_DONCHIAN_20"),
    "liq_range_eqh": ("785d5cf8e2e1b38a5f46c916bdff844aba999e32", "RANGE_EQH_RECLAIM_WIDE"),
    "vol_regime_wrap": ("73411829a9e07da4636b3b78938738f1a3f3948b", "VOLW_HIGH_BRK_20"),
    "multi_tf_pa": ("3fc50ec55695dca2026aeb64c6203f6b6e121553", "MTFP_HTF_BRK20"),
    "liq_cascade_proxy": ("80c013ca7062548e17b8c60fac8ad3e027925ba8", "LIQ_CASCADE_20_120_6_R15_V25_C75"),
    "beta_gate": ("54fd498b705aaa39f42a0a1ff9d9d92bf5af8777", "BETA_GATE_DONCH20"),
}


def load_seed(family: str, directory: Path):
    tip, name = SEEDS[family]
    source = subprocess.check_output(["git", "show", f"{tip}:{family}.py"])
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{family}.py"
    path.write_bytes(source)
    module_name = f"autopsy_closed_{family}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    if family == "btc_filter":
        entries = module.catalog_entries({interval: runner.load_train1("BTCUSDT", interval)[0]
                                          for interval in runner.INTERVALS})
    else:
        entries = module.catalog_entries()
    return {name: entries[name]}, {
        "family": family, "strategy": name, "closed_tip": tip,
        "source_path": f"{family}.py", "source_sha256": hashlib.sha256(source).hexdigest(),
        "archived_source": str(path),
    }


def compare_control(off_path: Path, on_path: Path) -> dict:
    off = pd.read_csv(off_path)
    on = pd.read_csv(on_path)
    off = off[off.strategy == runner.CONTROL_NAME].reset_index(drop=True)
    on = on[on.strategy == runner.CONTROL_NAME].reset_index(drop=True)
    pd.testing.assert_frame_equal(off.drop(columns="seconds"), on.drop(columns="seconds"))
    mean = float(off.train1_net_pnl.mean())
    if abs(mean - 58.3870526) > 0.000001:
        raise AssertionError(f"DONCHIAN_55 off-path mean changed: {mean}")
    return {"rows_equal_excluding_seconds": len(off), "off_mean_train1_net_pnl": mean}


def run_batch(output: Path, families) -> dict:
    digest_bytes = Path(DIGEST).read_bytes()
    digest = digest_bytes.decode()
    for family in families:
        if SEEDS[family][1] not in digest:
            raise ValueError(f"{family} is absent from the frozen digest")
    producing_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    manifest = {
        "producing_commit": producing_commit,
        "digest": DIGEST, "digest_sha256": hashlib.sha256(digest_bytes).hexdigest(),
        "window": {"start": runner.WARMUP_START, "end_exclusive": runner.TRAIN1_END.isoformat(),
                   "holdout_loaded": False},
        "hypothesis_note": NOTE, "families": [],
    }
    off_path = output / "control_off"
    runner.run_family(family="signal_autopsy_control_off", candidate_names=[],
                      hypothesis_note=NOTE, script_path=__file__, output_dir=str(off_path))
    # The control itself is a completed closed-tip replay even with no extra seeds.
    on_path = output / "control_on"
    control = runner.run_family(family="signal_autopsy_control_on", candidate_names=[],
                                hypothesis_note=NOTE, script_path=__file__,
                                output_dir=str(on_path), autopsy=True)
    manifest["control_source"] = {"implementation_base": "2cc712e", "strategy": runner.CONTROL_NAME,
                                   "source": "output/f006_runner_selfcheck/summary/results.csv"}
    manifest["control_equivalence"] = compare_control(off_path / "summary/results.csv", on_path / "summary/results.csv")
    manifest["checksums_used"] = control["checksums_used"]
    manifest["freeze"] = control["signal_autopsy"]["freeze"]
    tags = {runner.CONTROL_NAME: control["signal_autopsy"]["by_strategy"][runner.CONTROL_NAME]}
    for family in families:
        entries, provenance = load_seed(family, output / "sources")
        try:
            result = runner.run_family(
                family=family, candidate_names=list(entries), catalog_entries=entries,
                hypothesis_note=NOTE, script_path=__file__, output_dir=str(output / family), autopsy=True,
            )
        finally:
            for name in entries:
                runner.strategy.STRATEGY_CATALOG.pop(name, None)
        provenance["control_equivalence"] = compare_control(off_path / "summary/results.csv", output / family / "summary/results.csv")
        provenance["harness_control"] = result["harness_control"]
        provenance["h1_table"] = result["h1_table"]
        provenance["h2_status"] = result["h2_status"]
        manifest["families"].append(provenance)
        tags[provenance["strategy"]] = result["signal_autopsy"]["by_strategy"][provenance["strategy"]]
        print(f"{family}: Train-1 replay complete; control identical", flush=True)
    manifest["tags_by_strategy"] = tags
    with open(output / "manifest.json", "w") as handle:
        json.dump(manifest, handle, indent=2, allow_nan=False)
    lines = ["# Signal autopsy — Train-1 entry cohorts", "",
             "Retrospective descriptions only; no strategy tuning or H1/H2 changes. Rates exclude null diagnostics.",
             "Stop/TP MFE/MAE are conservative lower bounds; warmup entries are excluded from tags.", "",
             "| Existing strategy | Entries | Calm rate/tag | Forward agreement rate/tag | Quick reverse rate/tag |",
             "| --- | ---: | --- | --- | --- |"]
    for name, stats in tags.items():
        cells = [f"{stats[key]['rate']} / {stats[key]['tag']} (n={stats[key]['n']})"
                 for key in ("calm", "forward_agreement", "quick_reverse")]
        lines.append(f"| {name} | {stats['n_train1_entries']} | " + " | ".join(cells) + " |")
    (output / "report.md").write_text("\n".join(lines) + "\n")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("output/f006_signal_autopsy"))
    parser.add_argument("--families", nargs="*", choices=list(SEEDS), default=list(SEEDS))
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists; choose a fresh directory to retain provenance")
    run_batch(args.output, args.families)


if __name__ == "__main__":
    main()
