"""Discriminating checks for the frozen Sube exit-grid continuation."""
import os
import sys
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import f006_sube_inv_fvg_exit_grid as grid


def trades(*items):
    return pd.DataFrame(items, columns=["entry_time", "exit_time", "net_pnl"])


def test_zero_trade_month_is_absent_but_losing_exit_month_fails():
    frame = trades(("2024-03-01Z", "2024-04-03T00:00Z", 7),
                   ("2024-05-01Z", "2024-06-03T00:00Z", -2))
    months = grid.sparse_months(frame)
    assert months[0] == dict(year=2024, month=3, status="ABSENT", n_trades=0, net_pnl=None)
    assert months[1]["net_pnl"] == 7
    assert months[3]["net_pnl"] == -2
    assert not grid.sparse_pass(months, train1_net_pnl=5, max_dd=1)
    # Removing the loss makes that month absent; ten other absent months do not block PASS.
    clean = grid.sparse_months(frame.iloc[:1])
    assert grid.sparse_pass(clean, train1_net_pnl=7, max_dd=1)
    assert sum(m["n_trades"] > 0 for m in clean) == 1


def test_exit_month_uses_warsaw_and_does_not_count_warmup_or_boundary():
    frame = trades(("2024-01-01Z", "2024-02-28T12:00Z", 100),
                   ("2024-02-01Z", "2024-03-31T22:30Z", 3),
                   ("2024-02-01Z", "2025-02-28T23:30Z", -100))
    months = grid.sparse_months(frame)
    assert months[0]["status"] == "ABSENT"
    assert months[1]["n_trades"] == 1  # April in Warsaw, March in UTC.
    assert months[1]["net_pnl"] == 3
    assert sum(m["n_trades"] for m in months) == 1


@pytest.mark.parametrize("pnl,dd,expected", [(0, 50, True), (-.01, 1, False), (1, 50.01, False)])
def test_sparse_requires_equity_pnl_and_drawdown_even_with_clean_exit_month(pnl, dd, expected):
    months = grid.sparse_months(trades(("2024-01-01Z", "2024-03-05T00:00Z", 0)))
    assert grid.sparse_pass(months, pnl, dd) == expected


def test_empty_series_cannot_pass_vacuously():
    months = grid.sparse_months(pd.DataFrame())
    assert all(m["status"] == "ABSENT" for m in months)
    assert not grid.sparse_pass(months, 0, 0)


def test_frozen_exit_kwargs_and_baseline_guard():
    assert grid.EXIT_GRID == {
        "NO_TRAIL": dict(activate_pct=10.0, trail_pct=0.04, take_profit_multiple=None),
        "TP_x2": dict(activate_pct=10.0, trail_pct=0.04, take_profit_multiple=2.0),
        "TRAIL_a0.06_t0.04": dict(activate_pct=.06, trail_pct=.04, take_profit_multiple=None),
        "TRAIL_a0.03_t0.02": dict(activate_pct=.03, trail_pct=.02, take_profit_multiple=None),
    }
    import json
    old_path = grid.PRIOR / "raw/SOLUSDT_240_SINV_FIRST_FVG.json"
    old = json.loads(old_path.read_text())
    row = {**old, "exit_cell": "NO_TRAIL", "legacy_h2": old["promotion_pass"]}
    assert grid.verify_prior([row])["mismatches"] == 0
    row["train1_net_pnl"] += 1
    with pytest.raises(AssertionError, match="train1_net_pnl"):
        grid.verify_prior([row])


def test_rank_uses_trade_weighted_win_rate_not_mean_series_wr():
    common = dict(strategy="SINV_FIRST_FVG", max_drawdown_pct=1,
                  legacy_h2=False, h2_sparse_absent_zero_trade=True)
    data = pd.DataFrame([
        {**common, "exit_cell": "NO_TRAIL", "n_trades": 1, "n_wins": 1, "train1_net_pnl": 10},
        {**common, "exit_cell": "NO_TRAIL", "n_trades": 9, "n_wins": 0, "train1_net_pnl": 10},
        {**common, "exit_cell": "TP_x2", "n_trades": 10, "n_wins": 4, "train1_net_pnl": -1},
    ])
    ranked = grid.rank_table(data)
    assert list(ranked.exit_cell) == ["TP_x2", "NO_TRAIL"]
    assert list(ranked.win_rate) == [40, 10]
    assert not ranked.iloc[0].h1_pass
    assert ranked.iloc[0].sparse_h2_series == 1
    assert ranked.iloc[0].sparse_h2_after_h1 == 0
