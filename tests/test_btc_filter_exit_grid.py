"""Discriminating checks for the frozen BTC-FILTER exit-grid continuation."""
import json
import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
from scripts import f006_btc_filter_exit_grid as grid


def trades(*items):
    return pd.DataFrame(items, columns=["entry_time", "exit_time", "net_pnl"])


def test_frozen_names_and_exit_cells():
    assert grid.NAMES == ("BTC_FILTER_ER20_DONCHIAN_5", "BTC_FILTER_ER20_DONCHIAN_10",
                          "BTC_FILTER_ER20_DONCHIAN_20")
    assert grid.EXIT_GRID == {
        "NO_TRAIL": dict(activate_pct=10.0, trail_pct=0.04, take_profit_multiple=None),
        "TP_x2": dict(activate_pct=10.0, trail_pct=0.04, take_profit_multiple=2.0),
        "TRAIL_a0.06_t0.04": dict(activate_pct=.06, trail_pct=.04, take_profit_multiple=None),
        "TRAIL_a0.03_t0.02": dict(activate_pct=.03, trail_pct=.02, take_profit_multiple=None),
    }


def test_zero_trade_month_absent_losing_scored_month_fails():
    frame = trades(("2024-03-01Z", "2024-04-03T00:00Z", 7), ("2024-05-01Z", "2024-06-03T00:00Z", -2))
    months = grid.sparse_months(frame)
    assert months[0]["status"] == "ABSENT" and months[0]["net_pnl"] is None
    assert not grid.sparse_pass(months, train1_net_pnl=5, max_dd=1)
    clean = grid.sparse_months(frame.iloc[:1])
    assert sum(m["status"] == "ABSENT" for m in clean) == 11
    assert grid.sparse_pass(clean, train1_net_pnl=7, max_dd=1)
    assert not grid.sparse_pass(grid.sparse_months(pd.DataFrame()), 0, 0)


def test_no_trail_guard_against_parent_raw():
    old = json.loads((grid.PRIOR / "raw/XRPUSDT_240_BTC_FILTER_ER20_DONCHIAN_20.json").read_text())
    row = {**old, "exit_cell": "NO_TRAIL", "legacy_h2": old["promotion_pass"]}
    assert grid.verify_prior([row])["mismatches"] == 0
    row["train1_net_pnl"] += 1e-6
    with pytest.raises(AssertionError, match="train1_net_pnl"):
        grid.verify_prior([row])


def test_s8_regression_flags_higher_wr_lower_pnl_only():
    common = dict(strategy="BTC_FILTER_ER20_DONCHIAN_20", symbol="XRPUSDT", max_drawdown_pct=1,
                  legacy_h2=False, h2_sparse_absent_zero_trade=False)
    data = pd.DataFrame([
        {**common, "exit_cell": "NO_TRAIL", "n_trades": 10, "n_wins": 2, "train1_net_pnl": 100},
        {**common, "exit_cell": "TP_x2", "n_trades": 10, "n_wins": 4, "train1_net_pnl": 50},
        {**common, "exit_cell": "TRAIL_a0.06_t0.04", "n_trades": 10, "n_wins": 5, "train1_net_pnl": 120},
        {**common, "exit_cell": "TRAIL_a0.03_t0.02", "n_trades": 10, "n_wins": 1, "train1_net_pnl": 10},
    ])
    ranked = grid.rank_table(data).set_index("exit_cell")
    assert list(grid.rank_table(data).exit_cell) == ["TRAIL_a0.06_t0.04", "TP_x2", "NO_TRAIL", "TRAIL_a0.03_t0.02"]
    assert ranked.s8_regression.to_dict() == {"NO_TRAIL": False, "TP_x2": True,
                                              "TRAIL_a0.06_t0.04": False, "TRAIL_a0.03_t0.02": False}
    assert ranked.loc["TP_x2", "delta_mean_train1_vs_no_trail"] == -50
