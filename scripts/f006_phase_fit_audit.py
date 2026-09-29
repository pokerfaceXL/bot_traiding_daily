"""Phase-fit metrics for F006 regime/wrap/switch harness runs.

A phase label belongs to a bar; a trade is attributed to the label on its entry-fill
bar.  This module deliberately receives the completed trade table rather than
changing the engine or its H1/H2 gates.  ``--self-check`` exercises the empty-label
and all-in-one-leg contracts with synthetic data only.
"""
from __future__ import annotations

import json
from collections.abc import Sequence

import pandas as pd


def compute_phase_fit(
    labels: pd.Series,
    trades: pd.DataFrame,
    *,
    legs: Sequence[str],
    expected_legs: Sequence[str] | None,
) -> dict:
    """Return bar/trade-conditioned diagnostics for a labelled regime series.

    Labels are matched to ``trades.entry_time`` (the next-bar-open fill), not to the
    preceding signal bar.  Shares use all supplied bars/all completed trades as their
    denominators, so an empty or stuck leg remains visible.  A missing entry label is
    counted as an unlabeled trade and cannot improve the phase-fit score.
    """
    labels = pd.Series(labels).copy()
    if labels.index.has_duplicates:
        raise ValueError("phase labels must have a unique bar index")
    configured_legs = list(dict.fromkeys(str(leg) for leg in legs))
    observed_legs = [str(value) for value in labels.dropna().unique()]
    leg_names = list(dict.fromkeys(configured_legs + observed_legs))
    normalized = labels.map(lambda value: str(value) if pd.notna(value) else None)
    n_bars = int(len(normalized))

    n_trades = int(len(trades))
    if n_trades:
        if "entry_time" not in trades:
            raise ValueError("phase-fit trade table requires entry_time")
        entry_times = pd.DatetimeIndex(pd.to_datetime(trades["entry_time"]))
        trade_labels = [value if pd.notna(value) else None for value in normalized.reindex(entry_times).tolist()]
    else:
        trade_labels = []

    expected = None if expected_legs is None else [str(leg) for leg in expected_legs]
    rows = []
    for leg in leg_names:
        bar_count = int((normalized == leg).sum())
        positions = [i for i, label in enumerate(trade_labels) if label == leg]
        leg_trades = trades.iloc[positions] if positions else trades.iloc[0:0]
        exits = (leg_trades["exit_reason"].value_counts().to_dict()
                 if len(leg_trades) and "exit_reason" in leg_trades else {})
        rows.append({
            "leg": leg,
            "n_bars": bar_count,
            "bar_share": round(bar_count / n_bars, 6) if n_bars else 0.0,
            "n_trades": int(len(leg_trades)),
            "trade_share": round(len(leg_trades) / n_trades, 6) if n_trades else 0.0,
            "net_pnl": round(float(leg_trades["net_pnl"].sum()), 6) if len(leg_trades) else 0.0,
            "win_rate": round(float((leg_trades["net_pnl"] > 0).mean() * 100), 4) if len(leg_trades) else 0.0,
            "exit_mix": {str(reason): int(count) for reason, count in exits.items()},
        })

    unlabeled = sum(label is None for label in trade_labels)
    expected_count = sum(label in expected for label in trade_labels) if expected is not None else None
    return {
        "entry_label": "entry_fill_bar",
        "expected_legs": expected,
        "n_bars": n_bars,
        "n_trades": n_trades,
        "n_unlabeled_trades": unlabeled,
        "phase_fit_score": (round(expected_count / n_trades, 6) if expected is not None and n_trades else 0.0)
        if expected is not None else None,
        "legs": rows,
    }


def _self_check() -> None:
    index = pd.date_range("2025-01-01", periods=3, freq="h", tz="UTC")
    trades = pd.DataFrame({
        "entry_time": [index[0], index[2]], "net_pnl": [2.0, -1.0],
        "exit_reason": ["signal_reverse", "initial_sl"],
    })
    empty = compute_phase_fit(pd.Series(dtype=object), trades, legs=("HIGH", "LOW", "MID"), expected_legs=("HIGH",))
    all_high = compute_phase_fit(pd.Series("HIGH", index=index), trades, legs=("HIGH", "LOW", "MID"), expected_legs=("HIGH",))
    assert empty["n_unlabeled_trades"] == 2 and empty["phase_fit_score"] == 0.0
    assert [row["n_bars"] for row in empty["legs"]] == [0, 0, 0]
    assert all_high["phase_fit_score"] == 1.0
    assert [row["n_trades"] for row in all_high["legs"]] == [2, 0, 0]
    print(json.dumps({"empty_regime": empty, "all_high": all_high}, indent=2))


if __name__ == "__main__":
    _self_check()
