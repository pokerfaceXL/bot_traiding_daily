"""
scripts/f006_cross_family_digest.py -- cross-family H1/H2 digest for F006 signal
families run through scripts/f006_family_runner.py (spec/research/F006-shared-harness.md).

Globs output/f006_*/summary/manifest.json, reads any manifest matching the frozen
schema (h1_table/h1_falsified/h2_status present) into one H1/H2-per-family/name
table, and marks any directory predating that schema (or missing a manifest/results
file) as schema "legacy"/"missing" rather than raising. Suitable for ~every-5-closed-
families reporting: run this, read the Markdown table, done.

Writes output/f006_cross_family_digest.json and output/f006_cross_family_digest.md.
Reads local files only. Zero network connections.
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import sys
from datetime import datetime, timezone

FROZEN_SCHEMA_KEYS = {"h1_table", "h1_falsified", "h1_names_passing", "h2_status"}

EXIT_REASON_COLUMNS = (
    "exit_initial_sl", "exit_trailing_sl", "exit_take_profit",
    "exit_signal_reverse", "exit_end_of_data",
)


def _summary_aggregates(family_dir: str) -> dict | None:
    """Mean n_trades/win_rate/max_drawdown_pct and summed exit-reason mix across every
    row of summary/results.csv, for whichever of those columns the frozen schema this
    family was written with actually has. Returns None if results.csv is absent."""
    results_path = os.path.join(family_dir, "summary", "results.csv")
    if not os.path.exists(results_path):
        return None
    with open(results_path, newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return {"n_rows": 0}

    def _mean(col: str) -> float | None:
        vals = [float(r[col]) for r in rows if col in r and r[col] not in ("", None)]
        return round(sum(vals) / len(vals), 4) if vals else None

    exit_mix_totals = {}
    for col in EXIT_REASON_COLUMNS:
        vals = [int(float(r[col])) for r in rows if col in r and r[col] not in ("", None)]
        if vals:
            exit_mix_totals[col] = sum(vals)

    return {
        "n_rows": len(rows),
        "mean_n_trades": _mean("n_trades"),
        "mean_win_rate": _mean("win_rate"),
        "mean_max_drawdown_pct": _mean("max_drawdown_pct"),
        "exit_mix_totals": exit_mix_totals,
    }


def _load_manifest(family_dir: str) -> dict:
    manifest_path = os.path.join(family_dir, "summary", "manifest.json")
    results_path = os.path.join(family_dir, "summary", "results.csv")
    dir_name = os.path.basename(family_dir.rstrip("/"))

    if not os.path.exists(manifest_path):
        return {"dir": dir_name, "schema": "missing_manifest",
                "has_results_csv": os.path.exists(results_path)}

    with open(manifest_path) as f:
        try:
            manifest = json.load(f)
        except json.JSONDecodeError as exc:
            return {"dir": dir_name, "schema": "unreadable_manifest", "error": str(exc)}

    if not FROZEN_SCHEMA_KEYS.issubset(manifest.keys()):
        return {"dir": dir_name, "schema": "legacy",
                "manifest_keys": sorted(manifest.keys())}

    return {
        "dir": dir_name,
        "schema": "frozen",
        "family": manifest.get("family", dir_name.removeprefix("f006_")),
        "script": manifest.get("script"),
        "git_commit": manifest.get("git_commit"),
        "n_series": manifest.get("n_series"),
        "hypothesis_note": manifest.get("hypothesis_note"),
        "candidate_names": manifest.get("candidate_names", []),
        "h1_table": manifest.get("h1_table", []),
        "h1_names_passing": manifest.get("h1_names_passing", []),
        "h1_falsified": manifest.get("h1_falsified"),
        "h2_status": manifest.get("h2_status"),
        "h2_names_with_a_passing_series": manifest.get("h2_names_with_a_passing_series", []),
        "harness_control": manifest.get("harness_control"),
        "summary_aggregates": _summary_aggregates(family_dir),
    }


def build_digest(output_glob: str = "output/f006_*") -> dict:
    family_dirs = sorted(d for d in glob.glob(output_glob) if os.path.isdir(d))
    entries = [_load_manifest(d) for d in family_dirs]

    frozen = [e for e in entries if e["schema"] == "frozen"]
    legacy = [e for e in entries if e["schema"] == "legacy"]
    other = [e for e in entries if e["schema"] not in ("frozen", "legacy")]

    return {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "output_glob": output_glob,
        "n_family_dirs_found": len(family_dirs),
        "n_frozen_schema": len(frozen),
        "n_legacy_schema": len(legacy),
        "n_other": len(other),
        "families": entries,
    }


def _render_markdown(digest: dict) -> str:
    lines = [
        "# F006 cross-family digest",
        "",
        f"Generated {digest['generated_utc']}. {digest['n_family_dirs_found']} `output/f006_*` "
        f"directories found ({digest['n_frozen_schema']} frozen-schema, "
        f"{digest['n_legacy_schema']} legacy-schema, {digest['n_other']} other/missing).",
        "",
    ]

    frozen = [e for e in digest["families"] if e["schema"] == "frozen"]
    if frozen:
        lines += ["## Frozen-schema families (H1/H2 per name)", "",
                   "| family | name | mean net PnL (10-series) | H1 pass | H2 status |",
                   "| --- | --- | ---: | --- | --- |"]
        for e in frozen:
            if not e["h1_table"]:
                lines.append(f"| {e['family']} | -- | -- | -- | {e['h2_status']} |")
                continue
            for row in e["h1_table"]:
                lines.append(
                    f"| {e['family']} | {row['strategy']} | {row['mean_net_pnl']:.4f} | "
                    f"{row['h1_pass']} | {e['h2_status']} |"
                )
        lines.append("")

        lines += ["## Frozen-schema families -- summary/results.csv aggregates (all rows, incl. control)", "",
                   "| family | rows | mean n_trades | mean win_rate | mean max_drawdown_pct | exit mix totals |",
                   "| --- | ---: | ---: | ---: | ---: | --- |"]
        for e in frozen:
            agg = e.get("summary_aggregates")
            if not agg or agg.get("n_rows") in (None, 0):
                lines.append(f"| {e['family']} | -- | -- | -- | -- | (no results.csv) |")
                continue
            mix = ", ".join(f"{k}={v}" for k, v in agg.get("exit_mix_totals", {}).items()) or "--"
            lines.append(
                f"| {e['family']} | {agg['n_rows']} | {agg['mean_n_trades']} | "
                f"{agg['mean_win_rate']} | {agg['mean_max_drawdown_pct']} | {mix} |"
            )
        lines.append("")

    legacy = [e for e in digest["families"] if e["schema"] != "frozen"]
    if legacy:
        lines += ["## Non-frozen-schema directories (not digestible into the H1/H2 table above)", "",
                   "| dir | schema |", "| --- | --- |"]
        for e in legacy:
            lines.append(f"| {e['dir']} | {e['schema']} |")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--glob", default="output/f006_*", help="glob for family output directories")
    parser.add_argument("--out-dir", default="output", help="directory to write the digest files into")
    args = parser.parse_args()

    digest = build_digest(args.glob)
    os.makedirs(args.out_dir, exist_ok=True)
    json_path = os.path.join(args.out_dir, "f006_cross_family_digest.json")
    md_path = os.path.join(args.out_dir, "f006_cross_family_digest.md")
    with open(json_path, "w") as f:
        json.dump(digest, f, indent=2, default=str)
    with open(md_path, "w") as f:
        f.write(_render_markdown(digest))

    print(f"{digest['n_family_dirs_found']} output/f006_* directories found: "
          f"{digest['n_frozen_schema']} frozen, {digest['n_legacy_schema']} legacy, "
          f"{digest['n_other']} other.")
    print(f"-> {json_path}")
    print(f"-> {md_path}")


if __name__ == "__main__":
    main()
