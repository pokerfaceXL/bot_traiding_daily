"""Offline digest checks: drift, sparse names, optional metrics and archived control."""
import csv
import json
from pathlib import Path

import pytest

from scripts.f006_cross_family_digest import (
    EXIT_REASON_COLUMNS,
    _aggregates,
    _control_sanity,
    _load_manifest,
    _render_markdown,
    build_digest,
    main,
)


def _family(tmp_path, rows):
    family = tmp_path / "f006_example"
    summary = family / "summary"
    summary.mkdir(parents=True)
    manifest = {
        "family": "example", "candidate_names": ["A", "B"],
        "h1_table": [
            {"strategy": "A", "mean_net_pnl": 999, "h1_pass": True},
            {"strategy": "B", "mean_net_pnl": -999, "h1_pass": False},
        ],
        "h1_falsified": False, "h1_names_passing": ["A"], "h2_status": "cleared",
    }
    (summary / "manifest.json").write_text(json.dumps(manifest))
    with (summary / "results.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return str(family)


def test_csv_train1_overrides_manifest_and_diagnostic_pnl(tmp_path):
    family = _family(tmp_path, [
        dict(strategy="A", train1_net_pnl=-4, net_pnl=1000, n_trades=1, promotion_pass=True),
        dict(strategy="B", train1_net_pnl=2, net_pnl=-1000, n_trades=15, promotion_pass=False),
    ])
    entry = _load_manifest(family)
    assert entry["h1_names_passing"] == ["B"]
    assert entry["h1_table"][0]["mean_net_pnl"] == -4
    assert entry["h1_table"][1]["mean_net_pnl"] == 2
    assert entry["h1_source"] == "results.csv train1_net_pnl"
    assert entry["manifest_h1_table"][0]["mean_net_pnl"] == 999
    assert entry["h2_status"] == "falsified"  # A cannot clear H2 after failing H1
    assert entry["name_aggregates"]["A"]["thin_series"] is True
    assert entry["name_aggregates"]["B"]["thin_series"] is False
    md = _render_markdown(build_digest(str(tmp_path / "f006_*")))
    assert md.index("| example | B |") < md.index("| example | A |")


@pytest.mark.parametrize("pnl,status", [(0, "not_applicable_h1_failed"), (1, "cleared")])
def test_h1_strict_positive_and_h2_gate(tmp_path, pnl, status):
    entry = _load_manifest(_family(tmp_path, [
        dict(strategy=name, train1_net_pnl=pnl, n_trades=1, promotion_pass=True)
        for name in ("A", "B")
    ]))
    assert entry["h2_status"] == status
    assert entry["h1_falsified"] == (pnl == 0)


def test_missing_train1_falls_back_explicitly(tmp_path):
    entry = _load_manifest(_family(tmp_path, [
        dict(strategy=name, net_pnl=1000, n_trades=2) for name in ("A", "B")
    ]))
    assert entry["h1_source"] == "manifest"
    assert entry["h1_table"] == entry["manifest_h1_table"]
    assert entry["h2_source"] == "manifest"


def test_optional_metrics_and_exit_histograms():
    rows = [dict(n_trades="2", win_rate="50", max_drawdown_pct="3",
                 profit_factor="1.5", calmar="2", max_drawdown_usd="15", phase_fit_score="0.2",
                 **{col: "1" for col in EXIT_REASON_COLUMNS}),
            dict(n_trades="4", win_rate="25", max_drawdown_pct="5",
                 profit_factor="2.5", calmar="4", max_drawdown_usd="25", phase_fit_score="0.6",
                 **{col: "2" for col in EXIT_REASON_COLUMNS})]
    agg = _aggregates(rows)
    assert agg["exit_mix_totals"] == {col: 3 for col in EXIT_REASON_COLUMNS}
    assert agg["mean_n_trades"] == 3
    assert agg["mean_win_rate"] == 37.5
    assert agg["mean_max_drawdown_pct"] == 4
    assert agg["mean_profit_factor"] == 2
    assert agg["mean_calmar"] == 3
    assert agg["mean_max_drawdown_usd"] == 20
    assert agg["mean_phase_fit_score"] == 0.4
    assert agg["thin_series"] is True
    sparse = _aggregates([dict(n_trades="15", exit_trailing_sl="0")])
    assert sparse["mean_profit_factor"] is None
    assert sparse["exit_mix_totals"] == {"exit_trailing_sl": 0}
    assert sparse["thin_series"] is False
    assert _aggregates(None) is None
    assert _aggregates([]) == {"n_rows": 0}
    assert _aggregates([dict(profit_factor="inf")])["mean_profit_factor"] is None


def test_missing_legacy_and_empty_results_are_reported(tmp_path):
    missing = tmp_path / "f006_missing"
    missing.mkdir()
    assert _load_manifest(str(missing))["schema"] == "missing_manifest"
    family = Path(_family(tmp_path, [dict(strategy="A", n_trades=1)]))
    (family / "summary/results.csv").write_text("strategy,n_trades\n")
    entry = _load_manifest(str(family))
    assert entry["summary_aggregates"] == {"n_rows": 0}
    assert entry["h1_source"] == "manifest"
    (family / "summary/manifest.json").write_text("{}")
    assert _load_manifest(str(family))["schema"] == "legacy"


def test_control_failures_are_not_success():
    entry = dict(dir="f006_runner_selfcheck", schema="frozen",
                 control_train1_pnl=[58.39] * 10,
                 harness_control=dict(rows_compared=10, n_mismatches=0))
    assert _control_sanity([entry])["status"] == "PASS"
    entry["control_train1_pnl"] = [58.41] * 10
    assert _control_sanity([entry])["status"] == "FAIL"
    entry["control_train1_pnl"] = [58.39] * 9
    assert _control_sanity([entry])["status"] == "FAIL"
    entry["control_train1_pnl"] = [58.39] * 10
    entry["harness_control"]["n_mismatches"] = 1
    assert _control_sanity([entry])["status"] == "FAIL"
    assert _control_sanity([])["status"] == "FAIL"


def test_cli_writes_report_but_exits_nonzero_without_control(tmp_path, monkeypatch):
    monkeypatch.setattr("sys.argv", ["digest", "--glob", str(tmp_path / "f006_*"),
                                     "--out-dir", str(tmp_path)])
    with pytest.raises(SystemExit, match="FAIL: runner_selfcheck"):
        main()
    report = json.loads((tmp_path / "f006_cross_family_digest.json").read_text())
    assert report["control_sanity"]["status"] == "FAIL"
    assert "Control sanity: **FAIL**" in (tmp_path / "f006_cross_family_digest.md").read_text()


def test_closed_artifacts_cover_ten_families_and_reproduce_control():
    root = Path(__file__).resolve().parents[1]
    digest = build_digest(str(root / "output/f006_*"))
    families = {e["family"]: e for e in digest["families"] if e["schema"] == "frozen"}
    assert set(families) >= {
        "vol_regime_wrap", "beta_gate", "liq_cascade_proxy", "liq_range_eqh",
        "htf_gap_midfill", "btc_filter", "multi_tf_pa", "session_regime",
        "runner_selfcheck", "sube_inv_fvg",
    }
    control = digest["control_sanity"]
    assert control["status"] == "PASS"
    assert control["mean_train1_net_pnl"] == pytest.approx(58.3870526)
    assert control["delta"] == pytest.approx(-0.0029474)
    assert set(families["runner_selfcheck"]["summary_aggregates"]["exit_mix_totals"]) == set(EXIT_REASON_COLUMNS)
    assert families["sube_inv_fvg"]["name_aggregates"]["SINV_FIRST_H4"]["thin_series"] is True
    for entry in families.values():
        assert entry["h1_source"] == "results.csv train1_net_pnl"
        assert entry["summary_aggregates"]["n_rows"] > 0
    md = _render_markdown(digest)
    assert "Control sanity: **PASS**" in md
    assert "exit_initial_sl=" in md
    assert "mean profit_factor" in md
    assert "thin-series" in md
