import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import btc_filter


def _frame(closes, index=None):
    index = index if index is not None else pd.date_range("2024-01-01", periods=len(closes), freq="h", tz="UTC")
    close = pd.Series(closes, index=index, dtype=float)
    return pd.DataFrame({"open": close, "high": close + 1, "low": close - 1,
                         "close": close, "volume": 1.0}, index=index)


def test_er_permission_uses_only_current_and_prior_btc_closes():
    btc = _frame([100.0] * 20 + [140.0, 141.0])
    permission = btc_filter.btc_er_permission(btc)
    assert permission.iloc[:20].eq(0).all()
    assert permission.iloc[20] == 1

    changed_future = btc.copy()
    changed_future.iloc[21:, changed_future.columns.get_loc("close")] = 1.0
    assert btc_filter.btc_er_permission(changed_future).iloc[:21].tolist() == permission.iloc[:21].tolist()


def test_filter_passes_only_matching_alt_breakout_and_neutral_is_flat():
    btc = _frame([100.0] * 20 + [140.0, 141.0, 141.0])
    alt = _frame([10.0] * 20 + [12.0, 14.0, 11.0])
    signal = btc_filter.filtered_breakout(alt, btc, 5)
    assert signal.iloc[20] == 1
    assert signal.iloc[21] == 1
    assert signal.iloc[22] == 0


def test_missing_btc_timestamp_and_btc_itself_are_flat():
    btc = _frame([100.0] * 20 + [140.0, 141.0])
    alt = _frame([10.0] * 20 + [12.0, 13.0])
    missing = btc.drop(btc.index[20])
    assert btc_filter.filtered_breakout(alt, missing, 5).iloc[20] == 0
    assert btc_filter.filtered_breakout(btc, btc, 5).eq(0).all()


def test_alt_breakout_excludes_its_current_bar_and_catalog_requires_both_intervals():
    alt = _frame([10.0] * 5 + [12.0])
    assert btc_filter.alt_breakout(alt, 5).iloc[5] == 1
    with pytest.raises(ValueError, match="missing BTC"):
        btc_filter.catalog_entries({"60": alt})
