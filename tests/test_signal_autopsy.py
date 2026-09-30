import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import f006_family_runner as runner
import f006_signal_autopsy as audit
import f006_signal_autopsy_batch as batch


def bars(n=125):
    index = pd.date_range("2024-03-01", periods=n, freq="h", tz="UTC")
    return pd.DataFrame({"open": 100., "high": 102., "low": 98., "close": 101., "volume": 1.}, index=index)


def trade(df, start=1, end=4, direction=1, reason="signal_reverse"):
    return pd.DataFrame([dict(position_id="p1", symbol="TEST", direction=direction,
                             entry_time=df.index[start], entry_price=100.,
                             exit_time=df.index[end], exit_price=101.,
                             exit_reason=reason, net_pnl=0.8)])


def test_empty_trades_have_schema_and_unknown_not_weak(tmp_path):
    result = audit.write_series(tmp_path, bars(), pd.DataFrame(), "60", "TEST", "EMPTY")
    frame = pd.read_csv(tmp_path / result["blotter"])
    assert frame.empty
    assert set(audit.TRADE_COLUMNS + audit.DIAGNOSTIC_COLUMNS) <= set(frame.columns)
    assert result["forward_agreement"] == dict(n=0, n_true=0, rate=None, tag="unknown")
    assert audit.write_summary(tmp_path, [{"strategy": "EMPTY", "signal_autopsy": result}])["by_strategy"]["EMPTY"] == {k: v for k, v in result.items() if k != "blotter"}


def test_calmness_full_warmup_and_entry_bar_is_unseen():
    df = bars()
    calm = audit.entry_calmness(df)
    assert calm.atr_pct.iloc[:14].isna().all()
    assert calm.atr_percentile.iloc[:114].isna().all()
    assert calm.atr_percentile.iloc[114] == 1.
    df.loc[df.index[114]:, ["high", "low", "close"]] = [10000., 1., 9000.]
    changed = audit.entry_calmness(df)
    pd.testing.assert_frame_equal(calm.iloc[:115], changed.iloc[:115])
    blotter = audit.build_blotter(df, trade(df), "60")
    assert pd.isna(blotter.calm.iloc[0])


@pytest.mark.parametrize("direction,agreement", [(1, True), (-1, False)])
def test_forward_window_edge_and_side(direction, agreement):
    df = bars(10)
    valid = audit.build_blotter(df, trade(df, 4, 8, direction), "60")
    edge = audit.build_blotter(df, trade(df, 5, 8, direction), "60")
    assert bool(valid.forward_agreement.iloc[0]) is agreement
    assert pd.isna(edge.forward_agreement.iloc[0])
    assert pd.isna(edge.forward_signed_return_pct.iloc[0])
    assert audit.summarize(edge)["forward_agreement"]["n"] == 0


@pytest.mark.parametrize("direction", [1, -1])
def test_excursions_close_exit_includes_exit_bar_and_stop_does_not(direction):
    df = bars(10)
    df.loc[df.index[4], ["high", "low"]] = [110., 80.]
    close = audit.build_blotter(df, trade(df, direction=direction), "60").iloc[0]
    stop = audit.build_blotter(df, trade(df, direction=direction, reason="initial_sl"), "60").iloc[0]
    assert (close.mfe_pct, close.mae_pct) == ((10., 20.) if direction == 1 else (20., 10.))
    assert (stop.mfe_pct, stop.mae_pct) == (2., 2.)
    assert not close.excursion_lower_bound and stop.excursion_lower_bound
    same = audit.build_blotter(df, trade(df, 4, 4, direction, "initial_sl"), "60").iloc[0]
    assert (same.mfe_pct, same.mae_pct) == ((1., 0.) if direction == 1 else (0., 1.))


def test_quick_reverse_boundary_and_warmup_cohort():
    df = bars(10)
    for end, reason, expected in [(4, "signal_reverse", True), (5, "signal_reverse", False), (4, "initial_sl", False)]:
        result = audit.build_blotter(df, trade(df, end=end, reason=reason), "60")
        assert bool(result.quick_reverse.iloc[0]) is expected
    df.index = df.index - pd.Timedelta(days=10)
    result = audit.build_blotter(df, trade(df), "60")
    assert audit.summarize(result)["n_train1_entries"] == 0


def test_runner_autopsy_is_only_additive(tmp_path, monkeypatch):
    df = bars(150)
    monkeypatch.setitem(runner.strategy.STRATEGY_CATALOG, "DONCHIAN_55",
                        lambda work: pd.Series([1 if i % 10 < 5 else -1 for i in range(len(work))], index=work.index))
    mask = pd.Series(True, index=df.index)
    before = df.copy(deep=True)
    off = runner._run_one(df, mask, "TEST", "60", "DONCHIAN_55", 150)
    on = runner._run_one(df, mask, "TEST", "60", "DONCHIAN_55", 150, autopsy_dir=tmp_path)
    assert off["n_trades"] > 0
    assert "signal_autopsy" not in off
    assert {k: v for k, v in on.items() if k not in ("seconds", "signal_autopsy")} == {k: v for k, v in off.items() if k != "seconds"}
    assert (tmp_path / on["signal_autopsy"]["blotter"]).is_file()
    pd.testing.assert_frame_equal(df, before)


def test_summary_pools_observations_not_series_rates(tmp_path):
    df = bars(125)
    first = audit.write_series(tmp_path, df, trade(df, 114, 116), "60", "A", "TEST")
    second_trades = pd.concat([trade(df, 120, 124), trade(df, 119, 124, -1)], ignore_index=True)
    second = audit.write_series(tmp_path, df, second_trades, "60", "B", "TEST")
    summary = audit.write_summary(tmp_path, [
        {"strategy": "TEST", "signal_autopsy": first},
        {"strategy": "TEST", "signal_autopsy": second},
    ])["by_strategy"]["TEST"]
    assert summary["n_train1_entries"] == 3
    assert summary["forward_agreement"] == dict(n=2, n_true=1, rate=0.5, tag="strong")
    assert summary["calm"]["n"] == 3


def test_batch_replays_current_runner_with_autopsy_and_restores_catalog(tmp_path, monkeypatch):
    calls = []
    def fake_runner(**kwargs):
        calls.append(kwargs)
        if kwargs.get("catalog_entries"):
            runner.register_catalog_entries(kwargs["catalog_entries"])
        return {"checksums_used": {}, "signal_autopsy": {"freeze": audit.FREEZE, "by_strategy": {
            name: audit.summarize(audit.build_blotter(bars(), pd.DataFrame(), "60"))
            for name in [runner.CONTROL_NAME, *kwargs["candidate_names"]]
        }}, "harness_control": {}, "h1_table": [], "h2_status": "falsified"}
    name = batch.SEEDS["liq_range_eqh"][1]
    monkeypatch.setattr(runner, "run_family", fake_runner)
    monkeypatch.setattr(batch, "load_seed", lambda family, directory: (
        {name: lambda df: pd.Series(0, index=df.index)}, {"strategy": name}))
    monkeypatch.setattr(batch, "compare_control", lambda *args: {"rows_equal_excluding_seconds": 10})
    manifest = batch.run_batch(tmp_path, ["liq_range_eqh"])
    assert calls[0].get("autopsy", False) is False
    assert all(call["autopsy"] for call in calls[1:])
    assert [call["candidate_names"] for call in calls] == [[], [], [name]]
    assert name not in runner.strategy.STRATEGY_CATALOG
    assert manifest["window"]["end_exclusive"] == "2025-03-01T00:00:00+00:00"
