"""Retrospective analytics only; never used by signals, execution, or H1/H2."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

FREEZE = {
    "atr_bars": 14, "percentile_bars": 100, "forward_bars": 5,
    "quick_reverse_bars": 3, "calm_percentile_max": 0.5,
    "agreement_strong_min": 0.5, "calm_strong_min": 0.5,
    "reverse_strong_max": 0.25,
    "entry_cohort": "2024-03-01 <= entry_time < 2025-03-01 UTC",
    "excursions": "percent of fill; stop/TP exit-bar extremes excluded (lower bound)",
}
TRADE_COLUMNS = [
    "position_id", "symbol", "direction", "entry_time", "entry_price",
    "exit_time", "exit_price", "exit_reason", "net_pnl",
]
DIAGNOSTIC_COLUMNS = [
    "train1_entry", "atr_pct", "atr_percentile", "calm", "forward_signed_return_pct",
    "forward_agreement", "bars_held", "quick_reverse", "mfe_pct", "mae_pct",
    "excursion_lower_bound",
]


def entry_calmness(bars: pd.DataFrame) -> pd.DataFrame:
    """Only completed bars; percentile compares against 100 strictly prior ATR%s."""
    previous = bars.close.shift(1)
    tr = pd.concat([bars.high - bars.low, (bars.high - previous).abs(),
                    (bars.low - previous).abs()], axis=1).max(axis=1)
    atr_pct = 100 * tr.rolling(FREEZE["atr_bars"]).mean() / bars.close
    window = FREEZE["percentile_bars"]
    percentile = atr_pct.rolling(window + 1).apply(
        lambda values: (values[:-1] <= values[-1]).mean(), raw=True,
    )
    return pd.DataFrame({"atr_pct": atr_pct.shift(1), "atr_percentile": percentile.shift(1)})


def build_blotter(bars: pd.DataFrame, trades: pd.DataFrame, interval: str) -> pd.DataFrame:
    """Attach diagnostics to closed trades, keeping input frames untouched.

    Close-based exits see the entire exit bar. For intrabar stops/TP the unknown
    path cannot justify using that bar's high/low: report conservative excursions
    over earlier bars plus the actual exit fill, explicitly labelled lower bounds.
    """
    blotter = trades.copy() if not trades.empty else pd.DataFrame(columns=TRADE_COLUMNS)
    if trades.empty:
        return blotter.reindex(columns=list(blotter.columns) + DIAGNOSTIC_COLUMNS)
    calmness = entry_calmness(bars)
    rows = []
    for trade in trades.itertuples(index=False):
        start = bars.index.get_loc(trade.entry_time)
        end = bars.index.get_loc(trade.exit_time)
        close_exit = trade.exit_reason in ("signal_reverse", "end_of_data")
        held = bars.iloc[start:end + int(close_exit)]
        high = max(trade.entry_price, trade.exit_price, held.high.max())
        low = min(trade.entry_price, trade.exit_price, held.low.min())
        favorable, adverse = ((high - trade.entry_price, trade.entry_price - low)
                              if trade.direction == 1 else
                              (trade.entry_price - low, high - trade.entry_price))
        entry = pd.Timestamp(trade.entry_time)
        atr = calmness.iloc[start]
        forward = start + FREEZE["forward_bars"]
        signed_return = (100 * trade.direction * (bars.close.iloc[forward] / trade.entry_price - 1)
                         if forward < len(bars) else None)
        bars_held = (pd.Timestamp(trade.exit_time) - entry).total_seconds() / (60 * int(interval))
        rows.append({
            "train1_entry": pd.Timestamp("2024-03-01", tz="UTC") <= entry < pd.Timestamp("2025-03-01", tz="UTC"),
            "atr_pct": atr.atr_pct, "atr_percentile": atr.atr_percentile,
            "calm": None if pd.isna(atr.atr_percentile) else bool(atr.atr_percentile <= FREEZE["calm_percentile_max"]),
            "forward_signed_return_pct": signed_return,
            "forward_agreement": None if signed_return is None else bool(signed_return > 0),
            "bars_held": bars_held,
            "quick_reverse": trade.exit_reason == "signal_reverse" and bars_held <= FREEZE["quick_reverse_bars"],
            "mfe_pct": 100 * favorable / trade.entry_price,
            "mae_pct": 100 * adverse / trade.entry_price,
            "excursion_lower_bound": not close_exit,
        })
    for column in DIAGNOSTIC_COLUMNS:
        blotter[column] = [row[column] for row in rows]
    return blotter


def summarize(blotter: pd.DataFrame) -> dict:
    cohort = blotter.loc[blotter.train1_entry == True]  # noqa: E712
    result = {"n_closed_trades": len(blotter), "n_train1_entries": len(cohort)}
    for column, threshold, higher in (
        ("calm", FREEZE["calm_strong_min"], True),
        ("forward_agreement", FREEZE["agreement_strong_min"], True),
        ("quick_reverse", FREEZE["reverse_strong_max"], False),
    ):
        values = cohort[column].dropna()
        rate = float(values.astype(float).mean()) if len(values) else None
        strong = rate is not None and (rate >= threshold if higher else rate <= threshold)
        result[column] = {"n": len(values), "n_true": int(values.sum()), "rate": rate,
                          "tag": "unknown" if rate is None else "strong" if strong else "weak"}
    return result


def write_series(directory, bars, trades, interval, symbol, strategy_name) -> dict:
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    blotter = build_blotter(bars, trades, interval)
    filename = f"{symbol}_{interval}_{strategy_name}.csv"
    blotter.to_csv(path / filename, index=False)
    return {"blotter": filename, **summarize(blotter)}


def write_summary(directory, rows) -> dict:
    """Pool counts, not unweighted per-series rates; control stays a separate name."""
    families = {}
    for row in rows:
        families.setdefault(row["strategy"], []).append(
            pd.read_csv(Path(directory) / row["signal_autopsy"]["blotter"])
        )
    summary = {"freeze": FREEZE, "by_strategy": {
        name: summarize(pd.concat(frames, ignore_index=True)) for name, frames in families.items()
    }}
    with open(Path(directory) / "summary.json", "w") as handle:
        json.dump(summary, handle, indent=2, allow_nan=False)
    return summary
