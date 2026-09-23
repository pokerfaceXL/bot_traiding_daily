"""
F006 -- empirical causality audit of advanced-ta 0.1.8's Lorentzian Classification.

Runs the four checks that spec/research/F006-lorentzian-causality.md's audit section
predicts from reading the source, on REAL Train-1 data (no synthetic fixture), and
writes the numbers to output/f006_lorentzian/audit.json:

  1. L1 (lookahead normalisation). advanced-ta's own MLExtensions.n_cci / n_wt,
     computed on a prefix ending at bar N vs on the same series extended by 50 bars.
     If normalize()'s MinMaxScaler really is fit on the whole array, past feature
     values must move. lorentzian.py's causal replacement must not move at all.
  2. L2 + L1 combined (the library as documented). LorentzianClassification(df[:N])
     vs LorentzianClassification(df[:N+50]): how many of the shared bars change
     their prediction/signal when 50 future bars are appended.
  3. The adapter (lorentzian.compute_lorentzian) under the same truncation test --
     the falsification condition stated in the research note.
  4. Fidelity: for sampled anchors i, what advanced-ta itself assigns to bar i when
     bar i is the LAST bar of the frame handed to it, vs what the adapter assigns to
     bar i. This measures the one deviation the causal reframing introduces (the
     accumulation anchor pinned at the frame start instead of len(df)-maxBarsBack),
     and times the per-anchor walk-forward that would otherwise be needed.

Data discipline: identical to scripts/f006_stop_width_experiment.py -- the frozen
protocol-scoped cache is loaded and its checksum verified against the same
spec/research/F005-validation-protocol.md section 6 table, then sliced to
[2024-01-26T00:00:00Z, 2025-03-01T00:00:00Z) (warm-up + Train 1). Validation and
Holdout bars are never loaded into any computation here.

Needs Python >= 3.10 (advanced-ta's own Requires-Python). Zero network connections.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import data_contract  # noqa: E402
import lorentzian  # noqa: E402

WARMUP_START = "2024-01-26T00:00:00Z"
HOLDOUT_END = "2026-09-01T00:00:00Z"
TRAIN1_END = pd.Timestamp("2025-03-01T00:00:00Z")

# spec/research/F005-validation-protocol.md section 6, same table as
# scripts/f006_stop_width_experiment.py (duplicated, not imported).
EXPECTED_CHECKSUMS = {
    ("SOLUSDT", "240"): "72a6947ba3607e4326cf8a3d655dbc0953103cc66e5f1dd74aa8eb83e45fb731",
    ("ETHUSDT", "60"): "239b32b3348bd11978fdbb43e2d7220f4113625be9e558c4e533e096a312645e",
}

TRUNCATION_TAIL = 50  # bars appended in the truncation test
N_ANCHORS = 8         # sampled anchors for the walk-forward fidelity check


def load_train1(symbol: str, interval: str) -> pd.DataFrame:
    df, manifest = data_contract.load_dataset("data_cache", symbol, interval, WARMUP_START, HOLDOUT_END)
    expected = EXPECTED_CHECKSUMS[(symbol, interval)]
    if manifest.checksum_sha256 != expected:
        raise SystemExit(
            f"STOP: checksum mismatch for {symbol}/{interval}: cache has "
            f"{manifest.checksum_sha256}, protocol section 6 expects {expected}."
        )
    idx = pd.DatetimeIndex(df.index)
    if idx.tz is None:
        idx = idx.tz_localize("UTC")
    train1 = df.loc[(idx >= pd.Timestamp(WARMUP_START)) & (idx < TRAIN1_END)]
    assert not train1.empty and pd.DatetimeIndex(train1.index).max() < TRAIN1_END
    return train1


def lib_classify(frame: pd.DataFrame):
    """advanced-ta at its documented defaults: LorentzianClassification(df)."""
    from advanced_ta import LorentzianClassification

    return LorentzianClassification(frame[["open", "high", "low", "close", "volume"]].astype(float)).data


def check_l1_normalisation(df: pd.DataFrame, n: int) -> dict:
    from advanced_ta.LorentzianClassification import MLExtensions as ml

    short, long = df.iloc[:n], df.iloc[: n + TRUNCATION_TAIL]
    out = {}
    for name, fn in (
        ("n_cci_library", lambda d: ml.n_cci(d["high"], d["low"], d["close"], 20, 2)),
        ("n_wt_library", lambda d: ml.n_wt((d["high"] + d["low"] + d["close"]) / 3, 10, 11)),
        ("n_rsi_library", lambda d: ml.n_rsi(d["close"], 14, 2)),
        ("cci_adapter_causal", lambda d: lorentzian._feature_series(ml, d, "CCI", 20, 2)),
        ("wt_adapter_causal", lambda d: lorentzian._feature_series(ml, d, "WT", 10, 11)),
    ):
        a, b = np.asarray(fn(short), dtype=float)[:n], np.asarray(fn(long), dtype=float)[:n]
        diff = np.abs(np.nan_to_num(a) - np.nan_to_num(b))
        out[name] = {
            "max_abs_diff_on_shared_bars": float(diff.max()),
            "n_bars_changed": int((diff > 0).sum()),
            "pct_bars_changed": round(100.0 * float((diff > 0).mean()), 2),
        }
    return out


def _compare(a: np.ndarray, b: np.ndarray) -> dict:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    changed = a != b
    return {
        "n_bars_compared": int(len(a)),
        "n_bars_changed": int(changed.sum()),
        "pct_bars_changed": round(100.0 * float(changed.mean()), 2),
        "max_abs_diff": float(np.abs(a - b).max()) if len(a) else 0.0,
    }


def check_truncation(df: pd.DataFrame, n: int) -> dict:
    short, long = df.iloc[:n], df.iloc[: n + TRUNCATION_TAIL]

    t0 = time.time()
    lib_short = lib_classify(short)
    lib_secs = time.time() - t0
    lib_long = lib_classify(long)

    t0 = time.time()
    ad_short = lorentzian.compute_lorentzian(short)
    adapter_secs = time.time() - t0
    ad_long = lorentzian.compute_lorentzian(long)

    return {
        "n_bars": int(n),
        "tail_bars_appended": TRUNCATION_TAIL,
        "library_as_documented": {
            "prediction": _compare(lib_short["prediction"].to_numpy(), lib_long["prediction"].to_numpy()[:n]),
            "signal": _compare(
                lib_short["signal"].to_numpy(dtype=float), lib_long["signal"].to_numpy(dtype=float)[:n]
            ),
            "seconds_per_call": round(lib_secs, 2),
        },
        "adapter_causal": {
            "prediction": _compare(ad_short["prediction"].to_numpy(), ad_long["prediction"].to_numpy()[:n]),
            "signal": _compare(
                ad_short["signal"].to_numpy(dtype=float), ad_long["signal"].to_numpy(dtype=float)[:n]
            ),
            "seconds_per_call": round(adapter_secs, 2),
        },
    }


def check_walkforward_fidelity(df: pd.DataFrame, n: int) -> dict:
    """What advanced-ta assigns to bar i when bar i is the most recent bar, vs the adapter."""
    adapter = lorentzian.compute_lorentzian(df.iloc[:n])
    anchors = np.linspace(int(n * 0.55), n - 1, N_ANCHORS).astype(int).tolist()

    rows = []
    t0 = time.time()
    for i in anchors:
        lib = lib_classify(df.iloc[: i + 1])
        rows.append({
            "bar_index": int(i),
            "library_walkforward_prediction": float(lib["prediction"].iloc[-1]),
            "adapter_prediction": float(adapter["prediction"].iloc[i]),
            "library_walkforward_signal": int(lib["signal"].iloc[-1]),
            "adapter_signal": int(adapter["signal"].iloc[i]),
        })
    secs = time.time() - t0

    sign = lambda v: int(np.sign(v))
    return {
        "anchors": rows,
        "seconds_per_anchor": round(secs / max(len(anchors), 1), 2),
        "projected_hours_for_full_walkforward_on_this_series": round(
            (secs / max(len(anchors), 1)) * n / 3600.0, 2
        ),
        "signal_agreement_pct": round(
            100.0 * float(np.mean([r["library_walkforward_signal"] == r["adapter_signal"] for r in rows])), 1
        ),
        "prediction_sign_agreement_pct": round(
            100.0 * float(np.mean([
                sign(r["library_walkforward_prediction"]) == sign(r["adapter_prediction"]) for r in rows
            ])), 1
        ),
        "mean_abs_prediction_diff": round(
            float(np.mean([abs(r["library_walkforward_prediction"] - r["adapter_prediction"]) for r in rows])), 3
        ),
    }


def main():
    t_start = time.time()
    try:
        commit_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        commit_sha = None

    report = {
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit_parent": commit_sha,
        "python_version": sys.version.split()[0],
        "advanced_ta_version": "0.1.8",
        "warmup_start": WARMUP_START,
        "train1_end": str(TRAIN1_END),
        "truncation_tail_bars": TRUNCATION_TAIL,
        "series": {},
    }

    for symbol, interval in EXPECTED_CHECKSUMS:
        df = load_train1(symbol, interval)
        # Keep the L1/L2/truncation checks on a window a bit larger than maxBarsBack
        # so the library's maxBarsBackIndex is non-zero -- the regime it actually runs
        # in on Train 1 -- while keeping the per-anchor walk-forward affordable.
        n = min(len(df) - TRUNCATION_TAIL, lorentzian.DEFAULT_MAX_BARS_BACK + 400)
        print(f"[{symbol}/{interval}] {len(df)} Train-1 bars, using n={n}")
        report["series"][f"{symbol}_{interval}"] = {
            "train1_bars_available": int(len(df)),
            "first_bar": str(df.index[0]),
            "last_bar": str(df.index[-1]),
            "n_bars_used": int(n),
            "l1_normalisation": check_l1_normalisation(df, n),
            "truncation": check_truncation(df, n),
            "walkforward_fidelity": check_walkforward_fidelity(df, n),
        }
        print(json.dumps(report["series"][f"{symbol}_{interval}"], indent=2)[:2000])

    report["elapsed_seconds"] = round(time.time() - t_start, 1)
    os.makedirs("output/f006_lorentzian", exist_ok=True)
    with open("output/f006_lorentzian/audit.json", "w") as f:
        json.dump(report, f, indent=2)
    print(f"ALL DONE in {report['elapsed_seconds']}s -> output/f006_lorentzian/audit.json")


if __name__ == "__main__":
    main()
