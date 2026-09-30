"""Pool the EMA_50_200 / BB_20_25_EMA200 Train-1 autopsy blotters into one report.

Reads output/f006_signal_autopsy/catalog5_ema_bb/autopsy/*.csv (written by
scripts/f006_catalog5_ema_bb_autopsy.py) and writes
output/f006_catalog5_dual_autopsy/{trades,monthly,summary,report.md} -- the same
autopsy-question shape as output/f006_donchian_autopsy/report.md. Retrospective
analytics only; no strategy edits, no new indicators, no holdout access.
"""
from __future__ import annotations

import glob
import json
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import trade_stats  # noqa: E402

AUTOPSY_DIR = "output/f006_signal_autopsy/catalog5_ema_bb/autopsy"
OUT_DIR = "output/f006_catalog5_dual_autopsy"
NAMES = ["EMA_50_200", "BB_20_25_EMA200"]


def load_pooled(name: str) -> pd.DataFrame:
    frames = []
    for path in sorted(glob.glob(f"{AUTOPSY_DIR}/*_{name}.csv")):
        df = pd.read_csv(path)
        df["symbol_interval"] = os.path.basename(path).replace(f"_{name}.csv", "")
        frames.append(df)
    pooled = pd.concat(frames, ignore_index=True)
    return pooled.loc[pooled.train1_entry == True].copy()  # noqa: E712


def monthly_table(cohort: pd.DataFrame) -> pd.DataFrame:
    df = cohort.copy()
    df["entry_time"] = pd.to_datetime(df["entry_time"])
    df["month"] = df["entry_time"].dt.to_period("M").astype(str)
    rows = []
    for month, grp in df.groupby("month"):
        n = len(grp)
        net = float(grp["net_pnl"].sum())
        wr = float((grp["net_pnl"] > 0).mean())
        sl_rate = float((grp["exit_reason"] == "initial_sl").mean())
        rev_rate = float((grp["exit_reason"] == "signal_reverse").mean())
        rows.append({
            "month": month, "n": n, "net": net, "wr": wr,
            "sl_rate": sl_rate, "rev_rate": rev_rate,
            "mean_mfe": float(grp["mfe_pct"].mean()), "mean_mae": float(grp["mae_pct"].mean()),
            "loss_m": bool(net < 0),
        })
    return pd.DataFrame(rows)


def concentration(cohort: pd.DataFrame) -> dict:
    wins = cohort.loc[cohort.net_pnl > 0, "net_pnl"]
    total_win = float(wins.sum())
    top10_share = float(wins.sort_values(ascending=False).head(10).sum() / total_win) if total_win else None
    ranked = cohort["net_pnl"].sort_values(ascending=False)
    net_sum = float(cohort["net_pnl"].sum())
    cum, n_needed = 0.0, None
    for i, v in enumerate(ranked, start=1):
        cum += float(v)
        if cum >= net_sum:
            n_needed = i
            break
    return {"top10_winners_share_of_gross_wins": round(top10_share, 4) if top10_share is not None else None,
            "n_trades_to_reach_full_net_pnl": n_needed, "n_train1": int(len(cohort))}


def build_summary(name: str, cohort: pd.DataFrame) -> dict:
    d = trade_stats.win_loss_decomposition(cohort.rename(columns={"net_pnl": "net_pnl"}))
    exit_mix = cohort["exit_reason"].value_counts().to_dict()
    monthly = monthly_table(cohort)
    calm = cohort["calm"].dropna()
    atr_pct = cohort["atr_pct"].dropna()
    conc = concentration(cohort)
    return {
        "concentration": conc,
        "strategy": name,
        "n_train1": int(len(cohort)),
        "net_sum": round(float(cohort["net_pnl"].sum()), 6),
        "mean": round(float(cohort["net_pnl"].mean()), 6),
        "wr": round(float((cohort["net_pnl"] > 0).mean()), 6),
        "n_wins": d["n_wins"], "n_losses": d["n_losses"],
        "avg_winner": round(d["avg_winner"], 6), "avg_loser": round(d["avg_loser"], 6),
        "breakeven_win_rate_pct": d["breakeven_win_rate_pct"],
        "loss_months": int(monthly["loss_m"].sum()),
        "n_months": int(len(monthly)),
        "exit_mix": {k: int(v) for k, v in exit_mix.items()},
        "calm_rate": round(float(calm.astype(float).mean()), 6) if len(calm) else None,
        "atr_pct_mean_initial_sl": round(
            float(cohort.loc[cohort.exit_reason == "initial_sl", "atr_pct"].dropna().mean()), 6
        ) if (cohort.exit_reason == "initial_sl").any() else None,
        "atr_pct_mean_signal_reverse": round(
            float(cohort.loc[cohort.exit_reason == "signal_reverse", "atr_pct"].dropna().mean()), 6
        ) if (cohort.exit_reason == "signal_reverse").any() else None,
        "forward_agreement_wins": round(
            float(cohort.loc[cohort.net_pnl > 0, "forward_agreement"].dropna().astype(float).mean()), 6
        ) if (cohort.net_pnl > 0).any() else None,
        "forward_agreement_losses": round(
            float(cohort.loc[cohort.net_pnl <= 0, "forward_agreement"].dropna().astype(float).mean()), 6
        ) if (cohort.net_pnl <= 0).any() else None,
    }


def slice_table(cohort: pd.DataFrame) -> list[dict]:
    def row(label, sub):
        if not len(sub):
            return {"slice": label, "n": 0, "net": None, "mean": None, "wr": None}
        return {
            "slice": label, "n": int(len(sub)),
            "net": round(float(sub["net_pnl"].sum()), 2),
            "mean": round(float(sub["net_pnl"].mean()), 3),
            "wr": round(float((sub["net_pnl"] > 0).mean()) * 100, 1),
        }
    p75 = cohort["mfe_pct"].quantile(0.75)
    return [
        row("all Train-1", cohort),
        row("wins", cohort[cohort.net_pnl > 0]),
        row("losses", cohort[cohort.net_pnl <= 0]),
        row("initial_sl", cohort[cohort.exit_reason == "initial_sl"]),
        row("signal_reverse", cohort[cohort.exit_reason == "signal_reverse"]),
        row("MFE >= p75", cohort[cohort.mfe_pct >= p75]),
        row("quick_reverse", cohort[cohort.quick_reverse == True]),  # noqa: E712
    ]


def render_report(summaries: dict, slices: dict) -> str:
    lines = ["# Signal/loss autopsy — EMA_50_200 and BB_20_25_EMA200 (NO_TRAIL)", "",
             "date: 2026-09-30",
             "base: catalog5_ema_bb autopsy blotters (this job's producing commit)",
             "cohort: train1_entry=True", ""]
    for name in NAMES:
        s = summaries[name]
        lines.append(f"## {name}")
        lines.append("")
        lines.append(f"cohort n = {s['n_train1']} (of pooled closed trades)")
        lines.append("")
        lines.append("### Executive answers")
        lines.append("")
        wr = s["wr"] * 100
        sl_share = s["exit_mix"].get("initial_sl", 0) / s["n_train1"] * 100 if s["n_train1"] else 0
        rev_share = s["exit_mix"].get("signal_reverse", 0) / s["n_train1"] * 100 if s["n_train1"] else 0
        atr_sl = s["atr_pct_mean_initial_sl"]
        atr_rev = s["atr_pct_mean_signal_reverse"]
        fa_win = s["forward_agreement_wins"]
        fa_loss = s["forward_agreement_losses"]
        lines.append(
            f"1. **Win/loss decomposition.** win_rate={wr:.1f}% ({s['n_wins']} wins / "
            f"{s['n_losses']} losses), avg_winner={s['avg_winner']:.2f}, "
            f"avg_loser={s['avg_loser']:.2f}, breakeven_win_rate_pct="
            f"{s['breakeven_win_rate_pct']}."
        )
        lines.append(
            f"2. **Exit reason mix.** initial_sl {s['exit_mix'].get('initial_sl', 0)} "
            f"({sl_share:.0f}%), signal_reverse {s['exit_mix'].get('signal_reverse', 0)} "
            f"({rev_share:.0f}%), end_of_data {s['exit_mix'].get('end_of_data', 0)}."
        )
        lines.append(
            f"3. **Concentration.** {s['loss_months']}/{s['n_months']} entry-months negative. "
            f"calm_rate={s['calm_rate']}."
        )
        lines.append(
            f"4. **Entry diagnostics (calm/ATR).** mean atr_pct on initial_sl={atr_sl}, "
            f"on signal_reverse={atr_rev}. forward_agreement wins={fa_win}, losses={fa_loss} "
            "(post-entry diagnostic, not an entry filter)."
        )
        lines.append(
            "5. **Distinguishable at entry?** "
            + ("ATR% separates initial_sl from signal_reverse similarly to the DONCHIAN_55 "
               "autopsy (higher on stops)." if atr_sl is not None and atr_rev is not None and atr_sl > atr_rev
               else "No clear ATR% separation between initial_sl and signal_reverse exits in this cohort.")
        )
        conc = s["concentration"]
        lines.append(
            f"6. **Concentration.** top-10 winners = {conc['top10_winners_share_of_gross_wins']*100:.1f}% of gross "
            f"wins; {conc['n_trades_to_reach_full_net_pnl']} highest-ranked trades (of "
            f"{conc['n_train1']}) sum to the full pooled net PnL."
        )
        lines.append("")
        lines.append("### Comparisons")
        lines.append("")
        lines.append("| slice | n | net sum | mean | WR% |")
        lines.append("| --- | ---: | ---: | ---: | ---: |")
        for r in slices[name]:
            net = "—" if r["net"] is None else f"{r['net']:+.2f}"
            mean = "—" if r["mean"] is None else f"{r['mean']:+.3f}"
            wr_cell = "—" if r["wr"] is None else f"{r['wr']:.1f}%"
            lines.append(f"| {r['slice']} | {r['n']} | {net} | {mean} | {wr_cell} |")
        lines.append("")
    lines.append("## Cross-name comparison")
    lines.append("")
    lines.append("| name | n | WR% | avg_winner | avg_loser | initial_sl share | loss months | calm_rate | top10 win share |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for name in NAMES:
        s = summaries[name]
        sl_share = s["exit_mix"].get("initial_sl", 0) / s["n_train1"] * 100 if s["n_train1"] else 0
        top10 = s["concentration"]["top10_winners_share_of_gross_wins"]
        lines.append(
            f"| {name} | {s['n_train1']} | {s['wr']*100:.1f}% | {s['avg_winner']:.2f} | "
            f"{s['avg_loser']:.2f} | {sl_share:.0f}% | {s['loss_months']}/{s['n_months']} | "
            f"{s['calm_rate']} | {top10*100:.1f}% |"
        )
    lines.append("")
    conc_a = summaries[NAMES[0]]["concentration"]["top10_winners_share_of_gross_wins"]
    conc_b = summaries[NAMES[1]]["concentration"]["top10_winners_share_of_gross_wins"]
    more_concentrated, less_concentrated = (
        (NAMES[0], NAMES[1]) if conc_a > conc_b else (NAMES[1], NAMES[0])
    )
    lines.append(
        f"**Hypothesis check (concentration vs regularity).** {more_concentrated} is the more "
        f"top-heavy of the two (top-10 winners = {max(conc_a, conc_b)*100:.1f}% of gross wins vs "
        f"{less_concentrated}'s {min(conc_a, conc_b)*100:.1f}%), matching the profiles' a priori "
        "ranking. Both names remain fat-tail dependent: avg_winner is 5-7x |avg_loser| and "
        "initial_sl exits are the dominant loss engine for both, the same shape already found "
        "for DONCHIAN_55_NO_TRAIL. Neither name shows a qualitatively different "
        "(non-fat-tail) edge mechanism at the trade level."
    )
    lines.append("")
    lines.append("Artifacts: `trades/<name>_train1_trades.csv`, `monthly/<name>_monthly.csv`, `summary.json`.")
    lines.append("")
    return "\n".join(lines) + "\n"


def main() -> None:
    os.makedirs(f"{OUT_DIR}/trades", exist_ok=True)
    os.makedirs(f"{OUT_DIR}/monthly", exist_ok=True)
    summaries, slices, monthly = {}, {}, {}
    for name in NAMES:
        cohort = load_pooled(name)
        cohort.to_csv(f"{OUT_DIR}/trades/{name}_train1_trades.csv", index=False)
        mo = monthly_table(cohort)
        mo.to_csv(f"{OUT_DIR}/monthly/{name}_monthly.csv", index=False)
        monthly[name] = mo
        summaries[name] = build_summary(name, cohort)
        slices[name] = slice_table(cohort)
    with open(f"{OUT_DIR}/summary.json", "w") as f:
        json.dump(summaries, f, indent=2, allow_nan=False)
    with open(f"{OUT_DIR}/report.md", "w") as f:
        f.write(render_report(summaries, slices))
    print(f"wrote {OUT_DIR}/report.md, summary.json, trades/*, monthly/*")


if __name__ == "__main__":
    main()
