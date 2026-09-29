import os
import sys

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

from f006_phase_fit_audit import compute_phase_fit


LEGS = ("HIGH", "LOW", "MID")


def _trades(index):
    return pd.DataFrame({
        "entry_time": [index[0], index[-1]],
        "net_pnl": [3.0, -2.0],
        "exit_reason": ["signal_reverse", "initial_sl"],
    })


def test_empty_regime_keeps_zero_legs_and_counts_unlabeled_trades():
    index = pd.date_range("2025-01-01", periods=2, freq="h", tz="UTC")
    audit = compute_phase_fit(pd.Series(dtype=object), _trades(index), legs=LEGS, expected_legs=("HIGH",))

    assert audit["n_bars"] == 0
    assert audit["n_unlabeled_trades"] == 2
    assert audit["phase_fit_score"] == 0.0
    assert [(row["leg"], row["n_bars"], row["n_trades"], row["net_pnl"]) for row in audit["legs"]] == [
        ("HIGH", 0, 0, 0.0), ("LOW", 0, 0, 0.0), ("MID", 0, 0, 0.0),
    ]


def test_all_in_one_leg_reports_zero_other_legs_and_full_phase_fit():
    index = pd.date_range("2025-01-01", periods=3, freq="h", tz="UTC")
    audit = compute_phase_fit(pd.Series("HIGH", index=index), _trades(index), legs=LEGS, expected_legs=("HIGH",))

    assert audit["phase_fit_score"] == 1.0
    assert audit["n_unlabeled_trades"] == 0
    high, low, mid = audit["legs"]
    assert (high["n_bars"], high["bar_share"], high["n_trades"], high["trade_share"], high["net_pnl"], high["win_rate"]) == (3, 1.0, 2, 1.0, 1.0, 50.0)
    assert high["exit_mix"] == {"signal_reverse": 1, "initial_sl": 1}
    assert (low["n_bars"], low["n_trades"], mid["n_bars"], mid["n_trades"]) == (0, 0, 0, 0)
