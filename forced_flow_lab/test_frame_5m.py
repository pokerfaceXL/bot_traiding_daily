"""F011 5m frame: causality, OI reconciliation, and built-artifact integrity.

Causality and reconciliation are synthetic unit tests with no dependency on the
25 GB trade cache or network. Integration tests run only when the full frame and
hourly cache are present, matching how the 1h frame tests consume built outputs.
"""
import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from forced_flow_lab import build_frame_5m as bf

OUTPUT = Path("output/f011_forced_flow/frame_5m")
CACHE = Path("data_cache")


def synthetic_inputs(index):
    """Deterministic, non-degenerate inputs covering every compute_frame key."""
    n = len(index)
    rng = np.random.default_rng(0)
    close = 100 + np.cumsum(rng.normal(0, 1, n))
    high = close + rng.uniform(0.1, 1.0, n)
    low = close - rng.uniform(0.1, 1.0, n)
    ohlcv = pd.DataFrame({"open": close, "high": high, "low": low, "close": close,
                          "volume": rng.uniform(1, 10, n), "turnover": rng.uniform(1e4, 1e5, n)}, index=index)
    oi = pd.DataFrame({"openInterest": 5000 + np.cumsum(rng.normal(0, 2, n))}, index=index)
    buy = rng.uniform(0.3, 0.7, n)
    ratio = pd.DataFrame({"buyRatio": buy, "sellRatio": 1 - buy}, index=index)
    buy_vol = rng.uniform(1, 5, n)
    sell_vol = rng.uniform(1, 5, n)
    trades = pd.DataFrame({"taker_buy_vol": buy_vol, "taker_sell_vol": sell_vol,
                           "ofi": (buy_vol - sell_vol) / (buy_vol + sell_vol),
                           "delta_cvd": buy_vol - sell_vol, "trade_count": rng.integers(1, 100, n)}, index=index)
    funding_index = index[::96]  # every 8h on the 5m grid
    funding = pd.DataFrame({"funding_rate": rng.normal(0, 1e-4, len(funding_index))}, index=funding_index)
    metrics = pd.DataFrame({"sum_open_interest": rng.uniform(1e4, 2e4, n),
                            "sum_taker_long_short_vol_ratio": rng.uniform(0.5, 2, n)}, index=index)
    klines = pd.DataFrame({"close": close + rng.normal(0, 0.5, n),
                           "taker_buy_volume": rng.uniform(1, 5, n)}, index=index)
    return {"ohlcv": ohlcv, "oi": oi, "ratio": ratio, "funding": funding,
            "metrics": metrics, "klines": klines, "trades": trades}


def test_compute_frame_is_prefix_causal():
    """Row i uses only data at or before i: truncating after i cannot change it."""
    full_index = bf.grid("2024-01-26", "2024-02-02")  # 2016 bars = one warm-up window
    inputs = synthetic_inputs(full_index)
    full = bf.compute_frame(inputs, full_index)
    for k in (300, 1200, 2000):
        prefix_index = full_index[:k]
        prefix_inputs = {key: value.loc[value.index <= prefix_index[-1]] for key, value in inputs.items()}
        prefix = bf.compute_frame(prefix_inputs, prefix_index)
        overlap = full.iloc[:k]
        assert list(prefix.columns) == list(overlap.columns)
        for column in prefix.columns:
            a, b = prefix[column], overlap[column]
            if np.issubdtype(np.asarray(a).dtype, np.number):
                mask = a.notna() & b.notna()
                assert (a.isna() == b.isna()).all(), f"{column} NaN pattern diverged at k={k}"
                np.testing.assert_allclose(a[mask], b[mask], rtol=1e-12, atol=0,
                                           err_msg=f"{column} changed when truncated after bar {k}")
            else:
                assert a.equals(b), f"{column} changed when truncated after bar {k}"


def test_cvd_is_continuous_not_daily_reset():
    index = bf.grid("2024-01-26", "2024-01-29")  # 3 days
    inputs = synthetic_inputs(index)
    frame = bf.compute_frame(inputs, index)
    np.testing.assert_allclose(frame["cvd"].to_numpy(), inputs["trades"]["delta_cvd"].cumsum().to_numpy(), rtol=1e-12)
    # A daily reset would force cvd back toward zero at each midnight boundary.
    midnights = frame.index.normalize() == frame.index
    assert frame.loc[midnights, "cvd"].iloc[1:].abs().min() > 0


def test_liquidation_columns_typed_null():
    index = bf.grid("2024-01-26", "2024-01-27")
    frame = bf.compute_frame(synthetic_inputs(index), index)
    for column in bf.LIQUIDATIONS:
        assert str(frame[column].dtype) == "float64"
        assert frame[column].isna().all()


def test_funding_backward_only_with_flag_and_age():
    index = bf.grid("2024-01-26", "2024-01-28")
    inputs = synthetic_inputs(index)
    frame = bf.compute_frame(inputs, index)
    settlements = set(inputs["funding"].index)
    assert (~frame["funding_filled"]).sum() == len(settlements)
    assert frame.loc[frame.index.isin(settlements), "funding_filled"].eq(False).all()
    assert (frame["funding_age_minutes"] >= 0).all()
    assert (frame["funding_age_minutes"] < 8 * 60).all()
    # Every bar's funding equals the latest settlement at or before it (no look-ahead).
    expected = inputs["funding"]["funding_rate"].reindex(index, method="ffill")
    np.testing.assert_allclose(frame["funding_rate"].to_numpy(), expected.to_numpy(), rtol=1e-12)


def test_bn_layer_prefixed_and_separate_from_bybit_oi():
    index = bf.grid("2024-01-26", "2024-01-27")
    frame = bf.compute_frame(synthetic_inputs(index), index)
    assert "bn_sum_open_interest" in frame.columns
    assert "open_interest" in frame.columns
    # Cross-venue OI is never written into the Bybit OI column.
    assert not np.allclose(frame["open_interest"], frame["bn_sum_open_interest"])


def test_reconcile_hourly_oi_exact_and_mismatch():
    hours = pd.date_range("2024-01-26", periods=48, freq="h", tz="UTC")
    minutes = pd.date_range("2024-01-26", periods=48 * 12, freq="5min", tz="UTC")
    hourly = pd.Series(np.arange(48, dtype=float) + 5000, index=hours)
    oi_5m = pd.Series(np.nan, index=minutes)
    oi_5m.loc[hours] = hourly.to_numpy()
    oi_5m = oi_5m.ffill()
    result = bf.reconcile_hourly_oi(oi_5m, hourly)
    assert result == {"matched": 48, "max_abs_difference": 0.0}
    broken = oi_5m.copy()
    broken.loc[hours[10]] += 1.0
    with pytest.raises(ValueError, match="OI mismatch"):
        bf.reconcile_hourly_oi(broken, hourly)
    with pytest.raises(ValueError, match="missing"):
        bf.reconcile_hourly_oi(oi_5m.drop(hours[5]), hourly)


# ----------------------------------------------------------------- integration
def _load_built(symbol):
    frame_path = OUTPUT / f"{symbol}.csv.gz"
    if not frame_path.exists():
        pytest.skip(f"built frame absent: {frame_path} (run build_frame_5m)")
    with gzip.open(frame_path, "rt") as fh:
        frame = pd.read_csv(fh, index_col=0, parse_dates=True)
    manifest = json.loads((OUTPUT / f"{symbol}.manifest.json").read_text())
    return frame, manifest


@pytest.mark.parametrize("symbol", ["BTCUSDT", "ETHUSDT"])
def test_built_frame_shape_and_core_completeness(symbol):
    frame, manifest = _load_built(symbol)
    assert len(frame) == 115200
    post = frame.iloc[bf.WARMUP:]
    core = post.drop(columns=[c for c in frame.columns if c.startswith("bn_")] + list(bf.LIQUIDATIONS))
    assert not core.isna().any().any(), core.isna().sum()[core.isna().sum() > 0].to_dict()
    numeric = core.select_dtypes(include=np.number)
    assert not np.isinf(numeric).any().any()
    for column in bf.LIQUIDATIONS:
        assert frame[column].isna().all()
    assert {k: len(v) for k, v in manifest["gaps"].items() if k in bf.CORE_INPUTS} == {
        "ohlcv": 0, "oi": 0, "ratio": 0, "trades": 0}


@pytest.mark.parametrize("symbol", ["BTCUSDT", "ETHUSDT"])
def test_built_frame_hourly_oi_reconciliation(symbol):
    _, manifest = _load_built(symbol)
    assert manifest["hourly_oi_reconciliation"] == {"matched": 9600, "max_abs_difference": 0.0}
    oi_path = CACHE / "open_interest_5m" / f"{symbol}_oi_5min_{bf.TAG}.csv"
    hourly_path = CACHE / "open_interest" / f"{symbol}_oi_1h_{bf.TAG}.csv"
    if not (oi_path.exists() and hourly_path.exists()):
        pytest.skip("5m/1h OI caches absent")
    oi_5m = bf.indexed(oi_path, unit="ms").openInterest
    hourly = bf.indexed(hourly_path).open_interest
    assert bf.reconcile_hourly_oi(oi_5m, hourly)["max_abs_difference"] == 0.0
