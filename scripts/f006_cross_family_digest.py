"""
scripts/f006_cross_family_digest.py -- cross-family H1/H2 digest for F006 signal
families run through scripts/f006_family_runner.py (spec/research/F006-shared-harness.md).

Globs output/f006_*/summary/manifest.json, reads any manifest matching the frozen
schema (h1_table/h1_falsified/h2_status present) into one H1/H2-per-family/name
table, and marks any directory predating that schema (or missing a manifest/results
file) as schema "legacy"/"missing" rather than raising. Suitable for ~every-5-closed-
families reporting: run this, read the Markdown table, done.

Writes output/f006_cross_family_digest.json and output/f006_cross_family_digest.md.
Reads local files only. Zero network connections. The CLI exits nonzero unless
runner_selfcheck's archived DONCHIAN_55 control passes sanity (include it in --glob).
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import math
import os
from datetime import datetime, timezone

FROZEN_SCHEMA_KEYS = {"h1_table", "h1_falsified", "h1_names_passing", "h2_status"}

EXIT_REASON_COLUMNS = (
    "exit_initial_sl", "exit_trailing_sl", "exit_take_profit",
    "exit_signal_reverse", "exit_end_of_data",
)


def _read_results(family_dir: str) -> list[dict] | None:
    results_path = os.path.join(family_dir, "summary", "results.csv")
    if not os.path.exists(results_path):
        return None
    with open(results_path, newline="") as f:
        return list(csv.DictReader(f))


def _aggregates(rows: list[dict] | None) -> dict | None:
    """Available finite-value means and observed exit counts; no missing-column zeros."""
    if rows is None:
        return None
    if not rows:
        return {"n_rows": 0}

    def _mean(col: str) -> float | None:
        vals = [float(r[col]) for r in rows if r.get(col) not in ("", None)]
        vals = [v for v in vals if math.isfinite(v)]
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
        "mean_phase_fit_score": _mean("phase_fit_score"),
        "mean_profit_factor": _mean("profit_factor"),
        "mean_calmar": _mean("calmar"),
        "mean_max_drawdown_usd": _mean("max_drawdown_usd"),
        "thin_series": (sum(float(r["n_trades"]) for r in rows) / len(rows) < 15)
        if all(r.get("n_trades") not in ("", None) for r in rows) else None,
        "exit_mix_totals": exit_mix_totals,
    }


def _summary_aggregates(family_dir: str) -> dict | None:
    return _aggregates(_read_results(family_dir))


def _csv_h1_table(rows: list[dict], names: list[str]) -> list[dict] | None:
    """Use Train-1 only, falling back explicitly if any candidate is incomplete."""
    table = []
    for name in names:
        sub = [r for r in rows if r["strategy"] == name]
        if not sub or any(r.get("train1_net_pnl") in ("", None) for r in sub):
            return None
        pnl = [float(r["train1_net_pnl"]) for r in sub]
        if not all(math.isfinite(v) for v in pnl):
            return None
        table.append({
            "strategy": name,
            "sum_net_pnl": round(sum(pnl), 4),
            "mean_net_pnl": round(sum(pnl) / len(pnl), 4),
            "n_series": len(sub),
            "n_profitable_series": sum(v > 0 for v in pnl),
            "n_trades_total": sum(int(r["n_trades"]) for r in sub),
            "h1_pass": sum(pnl) > 0,
        })
    return table


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

    rows = _read_results(family_dir)
    names = manifest.get("candidate_names") or [r["strategy"] for r in manifest["h1_table"]]
    csv_h1 = _csv_h1_table(rows, names) if rows else None
    h1_table = csv_h1 if csv_h1 is not None else manifest["h1_table"]
    passing = [r["strategy"] for r in h1_table if r["h1_pass"]]
    h2_status = manifest["h2_status"]
    h2_names = manifest.get("h2_names_with_a_passing_series", [])
    h2_source = "manifest"
    if csv_h1 is not None and all(r.get("promotion_pass") in ("True", "False") for r in rows):
        h2_names = sorted({r["strategy"] for r in rows if r["strategy"] in passing
                           and r["promotion_pass"] == "True" and float(r["train1_net_pnl"]) >= 0})
        h2_status = "not_applicable_h1_failed" if not passing else (
            "cleared" if h2_names else "falsified")
        h2_source = "results.csv promotion_pass gated by Train-1 H1"

    return {
        "dir": dir_name,
        "schema": "frozen",
        "family": manifest.get("family", dir_name.removeprefix("f006_")),
        "script": manifest.get("script"),
        "git_commit": manifest.get("git_commit"),
        "n_series": manifest.get("n_series"),
        "hypothesis_note": manifest.get("hypothesis_note"),
        "candidate_names": manifest.get("candidate_names", []),
        "h1_table": h1_table,
        "h1_source": "results.csv train1_net_pnl" if csv_h1 is not None else "manifest",
        "manifest_h1_table": manifest["h1_table"],
        "h1_names_passing": passing,
        "h1_falsified": not passing,
        "h2_status": h2_status,
        "h2_source": h2_source,
        "manifest_h2_status": manifest["h2_status"],
        "h2_names_with_a_passing_series": h2_names,
        "harness_control": manifest.get("harness_control"),
        "summary_aggregates": _aggregates(rows),
        "name_aggregates": {name: _aggregates([r for r in rows if r["strategy"] == name])
                            for name in sorted({r["strategy"] for r in rows})} if rows else {},
        "control_train1_pnl": [float(r["train1_net_pnl"]) for r in (rows or [])
                               if r["strategy"] == "DONCHIAN_55"
                               and r.get("train1_net_pnl") not in ("", None)],
    }


def _control_sanity(entries: list[dict]) -> dict:
    control = next((e for e in entries if e["dir"] == "f006_runner_selfcheck"
                    and e["schema"] == "frozen"), {})
    vals = control.get("control_train1_pnl", [])
    observed = sum(vals) / len(vals) if vals else None
    delta = observed - 58.39 if observed is not None else None
    harness = control.get("harness_control") or {}
    return {
        "status": "PASS" if (len(vals) == 10 and delta is not None and abs(delta) < 0.01
                              and harness.get("n_mismatches") == 0
                              and harness.get("rows_compared") == 10) else "FAIL",
        "source": "f006_runner_selfcheck/summary/results.csv: DONCHIAN_55",
        "n_series": len(vals),
        "mean_train1_net_pnl": round(observed, 7) if observed is not None else None,
        "reference_mean": 58.39,
        "delta": round(delta, 7) if delta is not None else None,
        "tolerance_usd": 0.01,
        "harness_control": harness,
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
        "control_sanity": _control_sanity(entries),
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

    control = digest["control_sanity"]
    lines += [
        "Learning only: imported Train-1 artifacts; no reruns, holdout or promotion.",
        "H1 uses CSV `train1_net_pnl` when complete (manifest fallback is labelled). "
        "H2 uses stored CSV `promotion_pass`, gated by Train-1 H1; it is not a new validation.",
        "Trade/WR/DD/exit metrics cover the stored simulation rows, including warm-up/boundary "
        "where present; only PnL/H1 is Train-1-filtered. Means are unweighted over finite values. "
        "Missing columns are unavailable, not zero. Thin-series means mean n_trades < 15.",
        "",
        f"Control sanity: **{control['status']}** — DONCHIAN_55 / runner_selfcheck, "
        f"{control['n_series']} series, mean Train-1 = {control['mean_train1_net_pnl']}; "
        f"delta vs +58.39 = {control['delta']} (tolerance $0.01). "
        "This checks archived CSV plus the stored harness comparison, not a fresh experiment.",
        "",
    ]
    frozen = [e for e in digest["families"] if e["schema"] == "frozen"]
    if frozen:
        lines += ["## Frozen-schema families (H1/H2 per name)", "",
                   "Names ranked within each family by mean Train-1 PnL; control excluded from ranking.", "",
                   "| family | name | mean Train-1 PnL | H1 pass | family H2 status | H1 source | mean n_trades | mean WR | mean DD % | thin-series | exit mix totals |",
                   "| --- | --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |"]
        for e in frozen:
            if not e["h1_table"]:
                lines.append(f"| {e['family']} | -- | -- | -- | {e['h2_status']} | {e['h1_source']} | -- | -- | -- | -- | -- |")
                continue
            for row in sorted(e["h1_table"], key=lambda r: r["mean_net_pnl"], reverse=True):
                agg = e["name_aggregates"].get(row["strategy"], {})
                mix = ", ".join(f"{k}={v}" for k, v in agg.get("exit_mix_totals", {}).items()) or "--"
                lines.append(
                    f"| {e['family']} | {row['strategy']} | {row['mean_net_pnl']:.4f} | "
                    f"{row['h1_pass']} | {e['h2_status']} | {e['h1_source']} | "
                    f"{agg.get('mean_n_trades')} | {agg.get('mean_win_rate')} | "
                    f"{agg.get('mean_max_drawdown_pct')} | {agg.get('thin_series')} | {mix} |"
                )
        lines.append("")

        lines += ["## Frozen-schema families -- summary/results.csv aggregates (all rows, incl. control)", "",
                   "| family | rows | mean n_trades | mean win_rate | mean max_drawdown_pct | mean phase-fit | mean profit_factor | mean calmar | mean DD USD | thin-series | exit mix totals |",
                   "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |"]
        for e in frozen:
            agg = e.get("summary_aggregates")
            if not agg or agg.get("n_rows") in (None, 0):
                lines.append(f"| {e['family']} | -- | -- | -- | -- | -- | -- | -- | -- | -- | (no results.csv rows) |")
                continue
            mix = ", ".join(f"{k}={v}" for k, v in agg.get("exit_mix_totals", {}).items()) or "--"
            lines.append(
                f"| {e['family']} | {agg['n_rows']} | {agg['mean_n_trades']} | "
                f"{agg['mean_win_rate']} | {agg['mean_max_drawdown_pct']} | "
                f"{agg['mean_phase_fit_score']} | {agg['mean_profit_factor']} | "
                f"{agg['mean_calmar']} | {agg['mean_max_drawdown_usd']} | {agg['thin_series']} | {mix} |"
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
    print(f"Control sanity: {digest['control_sanity']['status']}")
    if digest["control_sanity"]["status"] != "PASS":
        raise SystemExit("FAIL: runner_selfcheck DONCHIAN_55 control sanity")


if __name__ == "__main__":
    main()
