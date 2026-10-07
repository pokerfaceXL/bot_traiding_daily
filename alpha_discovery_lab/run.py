"""F014 discovery runner — scores the frozen registry on DISCOVERY only, then STOPS.

Run: python3 -m alpha_discovery_lab.run --data-root PATH
Writes output/f014_discovery/{ledger.jsonl, ledger.csv, fdr_report.*, survivors_ranked.*,
discovery_summary.json, STATUS.md}. Refuses to run if the registry differs from the frozen JSON.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from alpha_discovery_lab import data as D
from alpha_discovery_lab import stats as St
from alpha_discovery_lab.freeze import OUT
from alpha_discovery_lab.registry import BLOCKS, HYPOTHESES, PROTOCOL, registry_sha256
from alpha_discovery_lab.states import Case, Skip, build

C_PRI = PROTOCOL["cost_bp_rt"]["primary_owner_tier"]
C_STRESS = PROTOCOL["cost_bp_rt"]["stress_historical"]
Q_MAX = PROTOCOL["fdr"]["q_max"]
LAGS = PROTOCOL["hac_lags"]
N_MIN = PROTOCOL["min_state_n_full"]
N_MIN_BLOCK = PROTOCOL["min_state_n_block"]


def check_frozen() -> str:
    frozen = json.loads((OUT / "hypothesis_registry.json").read_text())["sha256"]
    if frozen != registry_sha256():
        raise SystemExit(f"registry changed after freeze: {registry_sha256()} != {frozen}")
    return frozen


def _sgn(x: float) -> int:
    return 0 if not np.isfinite(x) or x == 0 else int(np.sign(x))


def score_case(c: Case, h: int, d: int | None) -> dict:
    """All statistics for one (case, horizon). d None -> two-sided (resolved later by the caller)."""
    y = c.y[h]
    m = c.pop & y.notna() & c.score.notna()
    yy, ss = y[m], c.S[m]
    row: dict = {"n_pop": int(m.sum()), "n_state": int(ss.sum())}
    test = St.hac_state_test(yy.values, ss.values.astype(float), LAGS)
    row.update(test)
    row["ic"], row["ic_p"] = St.spearman_ic(c.score[m].values, yy.values)
    row["state"] = St.describe(yy[ss])
    row["complement"] = St.describe(yy[~ss])
    blocks = {}
    for k, (a, b) in BLOCKS.items():
        bm = (yy.index >= pd.Timestamp(a)) & (yy.index < pd.Timestamp(b))
        yb, sb = yy[bm], ss[bm]
        n1 = int(sb.sum())
        diff = float(yb[sb].mean() - yb[~sb].mean()) if 0 < n1 < len(yb) else float("nan")
        blocks[k] = {"n_state": n1, "b": diff}
    row["blocks"] = blocks
    # tradable expression
    tm = (c.trade_mask if c.trade_mask is not None else c.S) & m
    row["n_trades"] = int(tm.sum())
    row["cost_mult"] = float(c.cost_mult[tm].mean()) if tm.any() else float("nan")
    row["_tm"] = tm
    return row


def finish_row(row: dict, c: Case, h: int, d: int, tradable: bool) -> dict:
    """Apply the (resolved) direction: block OK flags, gross/net, MFE/MAE."""
    for blk in row["blocks"].values():
        blk["ok"] = bool(blk["n_state"] >= N_MIN_BLOCK and _sgn(blk["b"]) == d)
    row["n_blocks_ok"] = sum(b["ok"] for b in row["blocks"].values())
    tm = row.pop("_tm")
    tsign = c.trade_sign if c.trade_sign is not None else d
    if tradable and tm.any():
        gross = float((tsign * c.y[h][tm]).mean())
        cm = row["cost_mult"]
        row.update(gross_bp=gross, net_9p9=gross - C_PRI * cm, net_34=gross - C_STRESS * cm)
        if c.px is not None:
            mfe, mae = St.mfe_mae(c.px, tsign * c.pos_base, h)
            row.update(mfe_mean=float(mfe[tm].mean()), mae_mean=float(mae[tm].mean()))
    else:
        row.update(gross_bp=None, net_9p9=None, net_34=None)
    return row


def run(frames: dict) -> dict:
    frozen = check_frozen()
    ts = datetime.now(timezone.utc).isoformat()
    ledger: list[dict] = []
    primary_keys: list[tuple] = []
    for hyp in HYPOTHESES:
        hid, H = hyp["id"], hyp["primary_horizon"]
        assets = [(a, "required") for a in hyp["required_assets"]]
        if hyp["bonus_asset"]:
            assets.append((hyp["bonus_asset"], "bonus"))
        cases, rows = {}, {}
        for a, role in assets:
            try:
                cases[a] = build(hid, frames, a)
            except Skip as e:
                for h in hyp["horizons"]:
                    ledger.append({"hyp_id": hid, "family": hyp["family"], "asset": a, "role": role, "horizon": h,
                                   "primary": h == H, "status": "SKIPPED", "skip_reason": str(e), "p": 1.0,
                                   "d": hyp["d"], "scored_utc": ts})
                    if h == H and role == "required":
                        primary_keys.append((hid, a))
                continue
            for h in hyp["horizons"]:
                rows[(a, h)] = score_case(cases[a], h, hyp["d"] or None)
        d = hyp["d"]
        if d == 0:  # two-sided: predicted sign = sign(b) of first required asset at primary horizon
            r0 = rows.get((hyp["required_assets"][0], H))
            d = _sgn(r0["b"]) if r0 else 1
            d = d or 1
        for (a, h), row in rows.items():
            role = "required" if a in hyp["required_assets"] else "bonus"
            row = finish_row(row, cases[a], h, d, hyp["tradable"])
            status = "SCORED" if row["n_state"] >= N_MIN else "INSUFFICIENT"
            if status == "INSUFFICIENT":
                row["p"] = 1.0
            ledger.append({"hyp_id": hid, "family": hyp["family"], "asset": a, "role": role, "horizon": h,
                           "primary": h == H, "status": status, "d": d, "d_registered": hyp["d"], **row,
                           "scored_utc": ts})
            if h == H and role == "required":
                primary_keys.append((hid, a))
    # ---- BH-FDR over the frozen primary family
    prim = {(r["hyp_id"], r["asset"]): r for r in ledger if r["primary"] and r["role"] == "required"}
    assert len(prim) == PROTOCOL["fdr"]["m"], len(prim)
    keys = list(prim)
    qs = St.bh_qvalues([prim[k]["p"] for k in keys])
    for k, q in zip(keys, qs):
        prim[k]["q"] = q
    return {"ledger": ledger, "verdicts": verdicts(prim), "registry_sha256": frozen, "scored_utc": ts}


def verdicts(prim: dict) -> list[dict]:
    out = []
    for hyp in HYPOTHESES:
        rs = [prim[(hyp["id"], a)] for a in hyp["required_assets"]]
        ok = all(r["status"] == "SCORED" for r in rs)
        d = rs[0]["d"]
        c1 = ok and all(_sgn(r["b"]) == d or _sgn(r.get("ic", np.nan)) == d for r in rs)
        c2 = ok and all(r["q"] <= Q_MAX for r in rs)
        c3 = ok and all(r["n_blocks_ok"] >= 3 for r in rs)
        c4 = ok and all(_sgn(r["b"]) == d for r in rs)
        c5 = ok and hyp["tradable"] and all(r.get("net_9p9") is not None and r["net_9p9"] > 0 for r in rs)
        margin = 0.0
        if ok and hyp["tradable"] and all(r.get("gross_bp") is not None for r in rs):
            margin = float(np.clip(min((r["gross_bp"] - C_PRI * r["cost_mult"]) / (C_PRI * r["cost_mult"])
                                       for r in rs), 0, 1))
        score = (np.mean([r.get("n_blocks_ok", 0) for r in rs]) / 4 + float(c4) + float(c2) + margin) if ok else 0.0
        fails = [n for n, v in zip(["C1", "C2", "C3", "C4", "C5"], [c1, c2, c3, c4, c5]) if not v]
        out.append({"hyp_id": hyp["id"], "family": hyp["family"], "d": d, "primary_horizon": hyp["primary_horizon"],
                    "assets": hyp["required_assets"], "C1": c1, "C2": c2, "C3": c3, "C4": c4, "C5": c5,
                    "survives": not fails, "fails": fails, "robustness": round(float(score), 4),
                    "per_asset": {r["asset"]: {k: r.get(k) for k in
                                               ["status", "n_state", "b", "p", "q", "ic", "n_blocks_ok",
                                                "gross_bp", "net_9p9", "net_34", "cost_mult"]} for r in rs}})
    return out


# ---------------------------------------------------------------- writers
def _flat(r: dict) -> dict:
    f = {k: v for k, v in r.items() if not isinstance(v, dict)}
    for part in ("state", "complement"):
        for k, v in (r.get(part) or {}).items():
            f[f"{part}_{k}"] = v
    for blk, v in (r.get("blocks") or {}).items():
        for k, x in v.items():
            f[f"{blk}_{k}"] = x
    return f


def _fmt(x, nd=2):
    return "—" if x is None or (isinstance(x, float) and not np.isfinite(x)) else (f"{x:.{nd}f}" if isinstance(x, float) else str(x))


def write(res: dict) -> None:
    L, V = res["ledger"], res["verdicts"]
    with open(OUT / "ledger.jsonl", "w") as f:
        for r in L:
            f.write(json.dumps(r, default=float) + "\n")
    pd.DataFrame([_flat(r) for r in L]).to_csv(OUT / "ledger.csv", index=False)
    prim = sorted([r for r in L if r["primary"] and r["role"] == "required"], key=lambda r: r["p"])
    fdr = {"method": "Benjamini-Hochberg", "m": len(prim), "q_max": Q_MAX,
           "family": PROTOCOL["fdr"]["family"], "n_q_le_max": sum(r["q"] <= Q_MAX for r in prim),
           "tests": [{k: r.get(k) for k in ["hyp_id", "asset", "horizon", "status", "d", "n_state", "b", "se",
                                             "z", "p", "q", "ic"]} for r in prim]}
    (OUT / "fdr_report.json").write_text(json.dumps(fdr, indent=2, default=float) + "\n")
    md = ["# F014 FDR report (discovery only)", "",
          f"Family: {fdr['family']}", f"m = {fdr['m']}, BH q ≤ {Q_MAX}: **{fdr['n_q_le_max']}** tests", "",
          "| hyp | asset | h | status | d | n_state | b (bp) | z | p | q | IC |",
          "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in prim:
        md.append(f"| {r['hyp_id']} | {r['asset']} | {r['horizon']} | {r['status']} | {r['d']:+d} | "
                  f"{r.get('n_state', '—')} | {_fmt(r.get('b'))} | {_fmt(r.get('z'))} | {_fmt(r['p'], 4)} | "
                  f"{_fmt(r['q'], 4)} | {_fmt(r.get('ic'), 4)} |")
    (OUT / "fdr_report.md").write_text("\n".join(md) + "\n")

    surv = sorted([v for v in V if v["survives"]], key=lambda v: -v["robustness"])[:3]
    near = sorted(V, key=lambda v: (len(v["fails"]), -v["robustness"]))[:8]
    sj = {"n_survivors": len([v for v in V if v["survives"]]), "recommended": surv,
          "closest_non_survivors": [v for v in near if not v["survives"]]}
    (OUT / "survivors_ranked.json").write_text(json.dumps(sj, indent=2, default=float) + "\n")
    md = ["# F014 survivors (discovery only; ranked by robustness, not return)", "",
          f"Survivors: **{sj['n_survivors']}** of 28 (criteria C1–C5 all required).", ""]
    if surv:
        md += ["| rank | hyp | robustness | per-asset gross / net@9.9 / net@34 (bp) |", "| --- | --- | --- | --- |"]
        for i, v in enumerate(surv, 1):
            pa = "; ".join(f"{a}: {_fmt(x['gross_bp'])} / {_fmt(x['net_9p9'])} / {_fmt(x['net_34'])}"
                           for a, x in v["per_asset"].items())
            md.append(f"| {i} | {v['hyp_id']} | {v['robustness']} | {pa} |")
    else:
        md.append("No hypothesis survives. Nothing is recommended for validation.")
    md += ["", "## Closest non-survivors (fewest failed criteria, then robustness)", "",
           "| hyp | fails | robustness | per-asset b / q / blocks_ok / gross / net@9.9 |", "| --- | --- | --- | --- |"]
    for v in sj["closest_non_survivors"]:
        pa = "; ".join(f"{a}: {_fmt(x['b'])} / {_fmt(x['q'], 3)} / {x['n_blocks_ok']} / {_fmt(x['gross_bp'])} / "
                       f"{_fmt(x['net_9p9'])}" for a, x in v["per_asset"].items())
        md.append(f"| {v['hyp_id']} | {','.join(v['fails'])} | {v['robustness']} | {pa} |")
    (OUT / "survivors_ranked.md").write_text("\n".join(md) + "\n")

    summary = {"feature": "F014", "scored_split": "discovery", "validation_opened": False, "holdout_opened": False,
               "registry_sha256": res["registry_sha256"], "scored_utc": res["scored_utc"],
               "n_hypotheses": len(V), "n_ledger_rows": len(L),
               "n_skipped_rows": sum(r["status"] == "SKIPPED" for r in L),
               "n_insufficient_rows": sum(r["status"] == "INSUFFICIENT" for r in L),
               "fdr_m": fdr["m"], "fdr_n_q_le_0p10": fdr["n_q_le_max"],
               "criteria_pass_counts": {c: sum(v[c] for v in V) for c in ["C1", "C2", "C3", "C4", "C5"]},
               "n_survivors": sj["n_survivors"], "survivors": [v["hyp_id"] for v in surv],
               "verdicts": V}
    (OUT / "discovery_summary.json").write_text(json.dumps(summary, indent=2, default=float) + "\n")


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root")
    a = ap.parse_args(argv)
    root = D.data_root(a.data_root)
    frames = {s: D.load_asset(root, s) for s in D.SYMBOLS}
    res = run(frames)
    write(res)
    print(json.dumps({k: v for k, v in json.loads((OUT / "discovery_summary.json").read_text()).items()
                      if k != "verdicts"}, indent=1))


if __name__ == "__main__":
    main()
