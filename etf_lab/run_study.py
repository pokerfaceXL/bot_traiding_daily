"""Run F012-C01 sequentially: Gate A → (only if PASS) Gate B → (only if PASS) Gate C.

Writes output/f012_c01_etf/*. Usage: python3 -m etf_lab.run_study
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from etf_lab import data as D
from etf_lab import gates as G

OUT = D.OUT


def gate_a(t1: pd.DataFrame) -> tuple[bool, dict, pd.DataFrame]:
    y = t1.y.to_numpy()
    f = G.folds(len(t1))
    t1 = t1.assign(fold=f)
    fit = f == 1
    large = G.pit_quantile_flag(y, 0.80)
    preds = {m: G.predict(t1, m, fit_mask=fit) for m in ["M0", "M1", "M2", "M3", "M3o"]}
    # Selection on F2 by MAE among eligible models (pre-registered).
    sel = {m: float(np.nanmean(np.abs(y[f == 2] - preds[m][f == 2]))) for m in ["M1", "M2", "M3"]}
    primary = min(sel, key=sel.get)
    rows = []
    for m in ["M0", "M1", "M2", "M3", "M3o"]:
        for scope, mask in [("F2", f == 2), ("F3", f == 3), ("F2F3", f >= 2)]:
            p = preds[m]
            pl = G.pit_quantile_flag(p, 0.80) & mask
            s = G.score_a(y[mask], p[mask], preds["M0"][mask], large[mask], pl[mask])
            rows.append({"model": m, "scope": scope, **s})
        if m in ("M3", "M3o"):
            pw = G.predict(t1, m, walk=True)
            mask = ~np.isnan(pw)
            pl = G.pit_quantile_flag(pw, 0.80)
            s = G.score_a(y[mask], pw[mask], preds["M0"][mask], large[mask], pl[mask])
            rows.append({"model": m, "scope": "walk_forward", **s})
            preds[m + "_wf"] = pw
    tab = pd.DataFrame(rows)
    tab.to_csv(OUT / "gate_a_scores.csv", index=False, float_format="%.4f")
    s_primary = tab[(tab.model == primary) & (tab.scope == "F3")].iloc[0].to_dict()
    ok, checks = G.gate_a_verdict(s_primary)
    t1 = t1.assign(**{f"pred_{k}": v for k, v in preds.items()}, large=large)
    return ok, {"primary_model": primary, "selection_mae_F2": sel, "primary_F3": s_primary, "checks": checks}, t1


def gate_a_robustness(t1: pd.DataFrame, primary: str) -> pd.DataFrame:
    """By issuer (own-lag persistence), by period, leave-out top-k |flow| days (F2∪F3)."""
    rows = []
    y, p, b = t1.y.to_numpy(), t1[f"pred_{primary}"].to_numpy(), t1.pred_M0.to_numpy()
    oos = t1.fold.to_numpy() >= 2
    for k in [0, 1, 3, 5]:
        drop = np.zeros(len(y), bool)
        if k:
            drop[np.argsort(-np.abs(np.where(oos, y, 0)))[:k]] = True
        m = oos & ~drop
        rho = pd.Series(p[m]).corr(pd.Series(y[m]), method="spearman")
        rows.append({"check": f"leave_out_top{k}", "n": int(m.sum()), "spearman": rho,
                     "dir_acc": np.mean(np.sign(p[m]) == np.sign(y[m]))})
    for per, m in [("2024", t1.date.dt.year.eq(2024).to_numpy()), ("2025", t1.date.dt.year.eq(2025).to_numpy())]:
        mm = m & oos
        rows.append({"check": f"period_{per}_oos", "n": int(mm.sum()),
                     "spearman": pd.Series(p[mm]).corr(pd.Series(y[mm]), method="spearman"),
                     "dir_acc": np.mean(np.sign(p[mm]) == np.sign(y[mm]))})
    far = D.parse_farside(D.FARSIDE_SNAPSHOT).set_index("date")
    for iss in ["IBIT", "FBTC", "GBTC", "ARKB", "BITB"]:
        s = far[iss]
        dd = pd.DataFrame({"y": s, "lag": s.shift(1)}).loc[t1.date[oos]]
        dd = dd[(dd.y != 0)]
        rows.append({"check": f"issuer_{iss}_own_lag1_oos", "n": len(dd),
                     "spearman": dd.y.corr(dd.lag, method="spearman"),
                     "dir_acc": np.mean(np.sign(dd.lag) == np.sign(dd.y))})
    return pd.DataFrame(rows)


def magnitude(t1: pd.DataFrame, cb, frame, primary: str) -> pd.DataFrame:
    """Predicted/actual flow $ vs BTC $ volume in the 15–16 ET window and full UTC day."""
    rows = []
    for _, r in t1.iterrows():
        a, b = D.et_to_utc(r.date, "15:00"), D.et_to_utc(r.date, "16:00")
        d0 = pd.Timestamp(r.date, tz="UTC")
        rows.append({"date": r.date, "pred_usd_m": r[f"pred_{primary}"], "y_usd_m": r.y,
                     "cb_win_usd_m": cb.usd_vol.loc[a:b - pd.Timedelta(minutes=1)].sum() / 1e6,
                     "cb_day_usd_m": cb.usd_vol.loc[d0:d0 + pd.Timedelta(hours=23, minutes=59)].sum() / 1e6,
                     "bybit_win_usd_m": frame.turnover.loc[a:b - pd.Timedelta(minutes=1)].sum() / 1e6,
                     "binance_win_usd_m": frame.bn_quote_volume.loc[a:b - pd.Timedelta(minutes=1)].sum() / 1e6})
    m = pd.DataFrame(rows)
    m["pred_share_of_cb_window"] = m.pred_usd_m.abs() / m.cb_win_usd_m
    m["y_share_of_cb_window"] = m.y_usd_m.abs() / m.cb_win_usd_m
    m["y_share_of_all3_window"] = m.y_usd_m.abs() / (m.cb_win_usd_m + m.bybit_win_usd_m + m.binance_win_usd_m)
    return m


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    far = D.load_farside()
    cb = D.coinbase_bars()
    frame = D.bybit_bars()
    daily = D.build_daily(far, cb)
    t1 = daily[daily.in_train1].reset_index(drop=True)
    summary = {"inputs": {"farside_snapshot_sha256": D.sha256(D.FARSIDE_SNAPSHOT),
                          "frame_5m": str(D.FRAME_5M), "coinbase_rows": len(cb), "train1_days": len(t1),
                          "pit_violations": int((t1.obs_live_utc >= t1.window_start_utc).sum())}}
    ok_a, res_a, t1 = gate_a(t1)
    summary["gate_a"] = {"pass": ok_a, **res_a}
    rob = gate_a_robustness(t1, res_a["primary_model"])
    rob.to_csv(OUT / "gate_a_robustness.csv", index=False, float_format="%.4f")
    mag = magnitude(t1, cb, frame, res_a["primary_model"])
    mag.to_csv(OUT / "economic_magnitude_daily.csv", index=False, float_format="%.4f")
    summary["magnitude"] = {k: float(v) for k, v in mag[["pred_share_of_cb_window", "y_share_of_cb_window",
                                                         "y_share_of_all3_window"]].median().items()}
    t1.drop(columns=["obs_live_utc", "window_start_utc"]).to_csv(OUT / "daily_pit_frame.csv", index=False, float_format="%.6g")
    if not ok_a:
        summary["gate_b"] = summary["gate_c"] = "NOT REACHED (Gate A FAIL)"
        summary["decision"] = "FAIL"
    else:
        # Sequential gates: Gate B is only built after an owner-reviewed Gate A PASS.
        raise SystemExit("Gate A PASS — implement Gate B per prereg.md before continuing")
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, default=lambda o: o.item() if hasattr(o, "item") else str(o)))
    print(json.dumps(summary, indent=2, default=lambda o: o.item() if hasattr(o, "item") else str(o)))


if __name__ == "__main__":
    main()
