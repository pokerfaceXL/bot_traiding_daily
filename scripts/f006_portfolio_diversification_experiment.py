"""F006 exploratory: sum monthly net PnL of 5 already-measured NO_TRAIL series.

Pure pandas aggregation of already-computed backtest results (no engine re-run).
Method pre-registered in spec/research/F006-portfolio-diversification-exploration.md
before this script was run.
"""
import json
from pathlib import Path

import pandas as pd

SELECTED = [
    ("DOGEUSDT", 60, "DONCHIAN_55"),
    ("ETHUSDT", 60, "BB_20_25_breakout"),
    ("SOLUSDT", 60, "BB_20_25_EMA200"),
    ("BTCUSDT", 240, "DONCHIAN_PULLBACK_55"),
    ("XRPUSDT", 240, "EMA3_21_50_200"),
]


def _find(symbol: str, interval: int, strategy: str) -> Path:
    for base in ("output/f006_notrail_monthly/raw", "output/f006_notrail_monthly_catalog5/raw"):
        p = Path(base) / f"{symbol}_{interval}_{strategy}.json"
        if p.exists():
            return p
    raise FileNotFoundError(f"{symbol}_{interval}_{strategy}.json not found in either raw dir")


def main() -> None:
    frames = {}
    best_alone_neg = None
    for symbol, interval, strategy in SELECTED:
        path = _find(symbol, interval, strategy)
        data = json.loads(path.read_text())
        assert data["symbol"] == symbol and int(data["interval"]) == interval and data["strategy"] == strategy
        rows = data["monthly"]
        n_neg = sum(1 for m in rows if m["is_valid"] and m["net_pnl"] is not None and m["net_pnl"] < 0)
        label = f"{symbol}/{interval}/{strategy}"
        print(f"{label}: n_neg_months={n_neg}, train1_net_pnl={data['train1_net_pnl']:.2f}")
        if best_alone_neg is None or n_neg < best_alone_neg:
            best_alone_neg = n_neg
        df = pd.DataFrame(rows)
        df["label"] = label
        frames[label] = df

    combined = None
    for label, df in frames.items():
        s = df.set_index(["year", "month"])[["is_valid", "net_pnl"]]
        s = s.rename(columns={"is_valid": f"valid_{label}", "net_pnl": f"pnl_{label}"})
        combined = s if combined is None else combined.join(s, how="outer")

    valid_cols = [c for c in combined.columns if c.startswith("valid_")]
    pnl_cols = [c for c in combined.columns if c.startswith("pnl_")]

    combined["all_valid"] = combined[valid_cols].all(axis=1)
    combined["n_negative_constituents"] = (combined[pnl_cols] < 0).sum(axis=1)
    combined["combined_net_pnl"] = combined[pnl_cols].sum(axis=1)

    print("\nPer-month combined result (Train-1, 2024-03..2025-02):")
    print(combined[["all_valid", "n_negative_constituents", "combined_net_pnl"]].to_string())

    evaluated = combined[combined["all_valid"]]
    n_combined_neg = int((evaluated["combined_net_pnl"] < 0).sum())
    n_months_evaluated = len(evaluated)

    print(f"\nBest individual constituent: {best_alone_neg} losing months (of 12)")
    print(f"Combined portfolio: {n_combined_neg} losing months (of {n_months_evaluated} evaluated)")
    print(f"Combined clears zero-tolerance monthly criterion: {n_combined_neg == 0}")

    out_dir = Path("output/f006_portfolio_diversification")
    out_dir.mkdir(parents=True, exist_ok=True)
    combined.reset_index().to_csv(out_dir / "combined_monthly.csv", index=False)
    summary = {
        "selected_series": [f"{s}/{i}/{st}" for s, i, st in SELECTED],
        "best_alone_neg_months": best_alone_neg,
        "combined_neg_months": n_combined_neg,
        "n_months_evaluated": n_months_evaluated,
        "clears_zero_tolerance_criterion": n_combined_neg == 0,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    print(f"\nWrote {out_dir / 'combined_monthly.csv'} and {out_dir / 'summary.json'}")


if __name__ == "__main__":
    main()
