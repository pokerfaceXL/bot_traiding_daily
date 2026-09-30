"""
F006 -- H-ORB-SESSION-ANCHOR-01: London/NY session-anchored opening-range breakout,
TRAIN 1 ONLY, NO_TRAIL.

Pre-registration: spec/research/F006-hypothesis-orb-session-anchor.md (committed
before this script and orb_session_anchor.py existed).

Pass 1: f006_family_runner.run_family() -- the frozen 5x2 basket, checksums, one-shot
mask, NO_TRAIL geometry, DONCHIAN_55 10-row harness control, H1 on mean
train1_net_pnl. Pass 2: the same 50 (name, symbol, interval) cells re-run through
the same engine call to get trade blotters, scoring legacy H2 and
h2_sparse_absent_zero_trade per series (/tmp/F006-eval-policy-sparse-h2-and-exits-
2026-09-29.md section B), bucketed by exit month exactly as
scripts/f006_catalog5_exit_class_grid.summarize does. Pass 2's net_pnl/train1_net_pnl
must match pass 1 row for row, or the script stops.

Writes only output/f006_orb_session_anchor/. Zero network connections.

    python3 scripts/f006_orb_session_anchor_experiment.py
"""
from __future__ import annotations

import json
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts import f006_catalog5_exit_class_grid as exit_grid  # noqa: E402
from scripts import f006_family_runner as runner  # noqa: E402
import entry_masks  # noqa: E402
import orb_session_anchor as osa  # noqa: E402

FAMILY = "orb_session_anchor"
OUT_DIR = f"output/f006_{FAMILY}"
CANDIDATE_NAMES = list(osa.SESSION_WINDOWS)  # exactly the five frozen names
NOTE = "spec/research/F006-hypothesis-orb-session-anchor.md"


def dual_h2_pass(h1_rows: pd.DataFrame, h1_names_passing: list[str]) -> list[dict]:
    """Legacy + sparse H2 for every candidate cell (reported for all; verdict uses
    only H1-clearing names)."""
    out = []
    for symbol in runner.SYMBOLS:
        for interval in runner.INTERVALS:
            train1_df, _ = runner.load_train1(symbol, interval)
            for name in CANDIDATE_NAMES:
                sig = entry_masks.strategy_signal_series(train1_df, name, interval=interval, now=runner.NOW)
                mask = entry_masks.one_shot_entry_mask(sig)
                result = runner.backtest_engine.run_backtest(
                    train1_df, name, interval=interval, now=runner.NOW, symbol=symbol,
                    initial_equity=runner.INITIAL_EQUITY, stake=runner.STAKE,
                    max_sl_pct=runner.MAX_SL_PCT, activate_pct=runner.ACTIVATE_PCT,
                    trail_pct=runner.TRAIL_PCT, cooldown_candles=runner.COOLDOWN,
                    entry_regime_mask=mask, **runner.FIXED_PARAMS,
                )
                row, monthly = exit_grid.summarize(result)
                ref = h1_rows[(h1_rows.strategy == name) & (h1_rows.symbol == symbol)
                              & (h1_rows.interval.astype(str) == interval)].iloc[0]
                if row["net_pnl"] != ref["net_pnl"] or round(row["train1_net_pnl"], 6) != round(ref["train1_net_pnl"], 6):
                    raise SystemExit(f"STOP: pass-2 mismatch {name} {symbol}/{interval}")
                out.append({"strategy": name, "symbol": symbol, "interval": interval,
                            "h1_clearing_name": name in h1_names_passing,
                            **{k: row[k] for k in (
                                "train1_net_pnl", "n_trades", "win_rate", "max_drawdown_pct",
                                "n_valid_months", "all_valid_months_nonnegative", "legacy_h2",
                                "h2_sparse_absent_zero_trade", "n_scored_months")},
                            "monthly": monthly})
    return out


def main():
    manifest = runner.run_family(
        family=FAMILY,
        candidate_names=CANDIDATE_NAMES,
        catalog_entries=osa.catalog_entries(),
        hypothesis_note=NOTE,
        script_path="scripts/f006_orb_session_anchor_experiment.py",
        output_dir=OUT_DIR,
    )
    summary = pd.read_csv(f"{OUT_DIR}/summary/results.csv")
    cand = summary[summary.strategy.isin(CANDIDATE_NAMES)]

    per_name = []
    for name in CANDIDATE_NAMES:
        sub = cand[cand.strategy == name]
        per_name.append({
            "strategy": name, "or_window_utc": list(osa.SESSION_WINDOWS[name]),
            "mean_train1_net_pnl": round(float(sub.train1_net_pnl.mean()), 4),
            "sum_train1_net_pnl": round(float(sub.train1_net_pnl.sum()), 4),
            "n_profitable_series": int((sub.train1_net_pnl > 0).sum()),
            "mean_n_trades": round(float(sub.n_trades.mean()), 2),
            "mean_win_rate": round(float(sub.win_rate.mean()), 4),
            "max_drawdown_pct_max": round(float(sub.max_drawdown_pct.max()), 4),
            "zero_trade_series": [f"{r.symbol}/{r.interval}" for r in sub.itertuples() if r.n_trades == 0],
            "h1_pass": bool(sub.train1_net_pnl.mean() > 0),
        })

    h1_passing = manifest["h1_names_passing"]
    dual = dual_h2_pass(summary, h1_passing)
    with open(f"{OUT_DIR}/summary/h2_dual.json", "w") as f:
        json.dump(dual, f, indent=2, default=str)
    pd.DataFrame([{k: v for k, v in r.items() if k != "monthly"} for r in dual]).to_csv(
        f"{OUT_DIR}/summary/h2_dual.csv", index=False)

    scoped = [r for r in dual if r["h1_clearing_name"]]
    if manifest["h1_falsified"]:
        h2_dual_status = "not_applicable_h1_failed"
    elif any(r["legacy_h2"] or r["h2_sparse_absent_zero_trade"] for r in scoped):
        h2_dual_status = "cleared"
    else:
        h2_dual_status = "falsified"

    manifest.update({
        "card": "/tmp/F006-card-H-ORB-SESSION-ANCHOR-01.md",
        "session_windows_utc_half_open_on_bar_open": osa.SESSION_WINDOWS,
        "per_name_report": per_name,
        "h2_dual_status": h2_dual_status,
        "h2_dual_scope": "H1-clearing names only for the verdict; all 50 cells reported in h2_dual.csv",
        "h2_dual_legacy_series": [f"{r['strategy']} {r['symbol']}/{r['interval']}" for r in scoped if r["legacy_h2"]],
        "h2_dual_sparse_series": [f"{r['strategy']} {r['symbol']}/{r['interval']}" for r in scoped if r["h2_sparse_absent_zero_trade"]],
        "sparse_month_bucket": "exit month Europe/Warsaw; zero exits ABSENT; Train-1 months only",
    })
    with open(f"{OUT_DIR}/summary/manifest.json", "w") as f:
        json.dump(manifest, f, indent=2, default=str)

    print(f"harness control: {manifest['harness_control']}")
    for r in per_name:
        print(f"  {r['strategy']:<11} mean_train1={r['mean_train1_net_pnl']:9.2f} "
              f"prof={r['n_profitable_series']}/10 mean_n={r['mean_n_trades']:7.1f} "
              f"maxDD={r['max_drawdown_pct_max']:6.2f} zero={r['zero_trade_series']} h1={r['h1_pass']}")
    print(f"H1 falsified: {manifest['h1_falsified']} passing={h1_passing}")
    print(f"H2 (runner legacy): {manifest['h2_status']}  H2 dual: {h2_dual_status}")


if __name__ == "__main__":
    main()
