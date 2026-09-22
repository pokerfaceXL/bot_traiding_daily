"""
F006 -- stop-width hypothesis experiment, TRAIN 1 ONLY.

Tests the hypothesis in spec/research/F006-hypothesis-stop-width.md: that the
3% stop (max_sl_pct=0.03) used throughout F005 is too tight relative to
normal noise on this basket's 4h/1h candles, and that widening it alone
(signal logic, leverage=1, cooldown_candles=0, costs all held fixed) reduces
stop-out frequency/severity and shifts net PnL/win rate in a less-negative
or positive direction.

Scope discipline (frozen by spec/research/F005-validation-protocol.md section
7.3: F006 selects on train+validation only, holdout stays closed): this
script loads the SAME full protocol-scoped cached dataset and checksums as
spec/research/F005-validation-protocol.md section 6 (warmup_start=2024-01-26
-> holdout_end=2026-09-01), verifies them exactly like
scripts/f005d_leverage_sensitivity.py does, but then SLICES the loaded frame
down to [2024-01-26T00:00:00Z, 2025-03-01T00:00:00Z) -- warm-up + Train 1
only -- before ever calling run_backtest. Validation/Holdout bars are never
passed into the engine by this script.

Does NOT touch strategy.py/backtest_apex.py/backtest_engine.py/costs.py/
equity.py/execution.py/data_contract.py/regularity.py/main.py/trader.py/
configuration/ or any frozen F005 protocol/baseline file -- read-only of all
of those, writes only new files (this script, its output/, and the research
note).
"""
from __future__ import annotations

import json
import subprocess
import time
from datetime import datetime, timezone

import pandas as pd

import backtest_engine
import data_contract
import strategy

SYMBOLS = ["SOLUSDT", "ETHUSDT", "BTCUSDT", "XRPUSDT", "DOGEUSDT"]
INTERVALS = ["240", "60"]

# Full protocol-scoped range (same as F005-validation-protocol.md section 6 /
# scripts/f005d_leverage_sensitivity.py) -- used only to load+checksum-verify
# the cached dataset. The slice actually fed to run_backtest is narrower
# (warm-up + Train 1 only, see TRAIN1_END below).
WARMUP_START = "2024-01-26T00:00:00Z"
HOLDOUT_END = "2026-09-01T00:00:00Z"

# Train 1 boundary, spec/research/F005-validation-protocol.md section 3.2.
TRAIN1_END = pd.Timestamp("2025-03-01T00:00:00Z")
NOW = TRAIN1_END  # fixed, not wall-clock -- filter_closed_candles is deterministic regardless of when this script runs

# Protocol section 6 checksums -- duplicated here (not imported), same
# convention as scripts/f005_run_baseline.py and
# scripts/f005d_leverage_sensitivity.py: this script does not import from or
# modify that frozen file, it re-verifies independently against the same
# protocol table before using cached data.
EXPECTED_CHECKSUMS = {
    ("SOLUSDT", "240"): "72a6947ba3607e4326cf8a3d655dbc0953103cc66e5f1dd74aa8eb83e45fb731",
    ("SOLUSDT", "60"): "25323c766de58648b624435237e47994b0a3ae1cda5cbcf7e091689b4e74c213",
    ("ETHUSDT", "240"): "4e856f13e3da0afa5d8b5d1d102e04a133788f49122694bdba222f90fbe13176",
    ("ETHUSDT", "60"): "239b32b3348bd11978fdbb43e2d7220f4113625be9e558c4e533e096a312645e",
    ("BTCUSDT", "240"): "d690423a3bae1a53f73728a3b178ab14cbf970855163bed32fe6b727b8e6c467",
    ("BTCUSDT", "60"): "cfb39aec9eadb660460f9e0f180184b67690a35c92af8a16e66398ea548e8d69",
    ("XRPUSDT", "240"): "11c203e30f687508833530daa913e133eb42239699ed52339f4f8e3fbd5a89b3",
    ("XRPUSDT", "60"): "cdd81edbe415f3d583bc365ca1e786afa09956a4aa3bf82e739ecf9b0475b4a5",
    ("DOGEUSDT", "240"): "5a05355dd929a844a262cf9a15950974b1cdf18000b7e44c71ff89ebf567abde",
    ("DOGEUSDT", "60"): "748590acb70eed66878380a7ba4890f498ac458038cd7feec20c3ec3fa16e8ff",
}

# Same 10-strategy sample as spec/research/F005-leverage-sensitivity.md --
# reused verbatim (not re-derived) for direct cross-referenceability of this
# experiment's max_sl_pct=0.03/leverage=1/cooldown=0 rows against that
# addendum's leverage=1 rows. Covers all 7 families present in
# strategy.STRATEGY_CATALOG (ADX, BB, EMA, MACD, RSI, STOCH, TS).
STRATEGY_SAMPLE = [
    "EMA_8_21",              # EMA family, plain crossover
    "EMA_13_34_RSI14_55",    # EMA family, EMA+RSI combo variant
    "RSI14_7030",            # RSI family, plain
    "MACD_12_26_hist",       # MACD family, plain
    "MACD_RSI14_50",         # MACD family, MACD+RSI combo variant
    "BB_20_25_breakout",     # Bollinger Bands family, breakout variant
    "BB_20_2_RSI14",         # Bollinger Bands family, BB+RSI combo variant
    "ADX14_DI_20",           # ADX family
    "STOCH14_cross",         # Stochastic family
    "TS_13_34_200_14",       # Triple Screen family
]

MAX_SL_PCT_SWEEP = [0.03, 0.05, 0.08, 0.12]

# Fixed params: leverage=1 is the F006 research placeholder (spec/build.md);
# atr_multiplier/activate_pct/trail_pct left at backtest_engine.run_backtest's
# own function-signature defaults (not F005 baseline's overridden values),
# per the ticket. Costs match F005's defaults (also run_backtest's defaults).
FIXED_PARAMS = dict(
    leverage=1.0,
    cooldown_candles=0,
    atr_multiplier=1.5,
    activate_pct=0.03,
    trail_pct=0.02,
    commission_rate_bps=10.0,
    half_spread_bps=5.0,
    slippage_bps=2.0,
)
INITIAL_EQUITY = 500.0
STAKE = 100.0
REENTRY_FLOOR = 100.0


def _run_one(df, symbol, interval, strategy_name, max_sl_pct) -> dict:
    result = backtest_engine.run_backtest(
        df, strategy_name, interval=interval, now=NOW, symbol=symbol,
        initial_equity=INITIAL_EQUITY, stake=STAKE, max_sl_pct=max_sl_pct,
        **FIXED_PARAMS,
    )
    m = result.metrics
    return {
        "symbol": symbol, "interval": interval, "strategy": strategy_name,
        "max_sl_pct": max_sl_pct,
        "net_pnl": m["total_net_pnl"],
        "win_rate": m["win_rate"],
        "n_trades": int(len(result.trades)),
        "max_drawdown_pct": m["max_drawdown_pct"],
        "final_equity": m["final_equity"],
        "survived": bool(m["final_equity"] >= REENTRY_FLOOR),
    }


def main():
    t_start = time.time()
    try:
        commit_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        commit_sha = None

    for name in STRATEGY_SAMPLE:
        assert name in strategy.STRATEGY_CATALOG, f"strategy {name!r} not in strategy.STRATEGY_CATALOG"

    rows = []
    n_runs = 0
    for symbol in SYMBOLS:
        for interval in INTERVALS:
            checksum_expected = EXPECTED_CHECKSUMS[(symbol, interval)]
            try:
                full_df, manifest = data_contract.load_dataset(
                    "data_cache", symbol, interval, WARMUP_START, HOLDOUT_END
                )
            except data_contract.DataContractError as exc:
                raise SystemExit(
                    f"STOP: cannot load frozen dataset for {symbol}/{interval} "
                    f"from data_cache -- {exc}."
                ) from exc
            if manifest.checksum_sha256 != checksum_expected:
                raise SystemExit(
                    f"STOP: checksum mismatch for {symbol}/{interval}: "
                    f"cache has {manifest.checksum_sha256}, protocol section 6 "
                    f"expects {checksum_expected}."
                )

            # Train 1 slice only -- warm-up start through Train1_end,
            # exclusive, per the protocol's [start, end) window convention.
            # Validation/Holdout bars are never included in what run_backtest sees.
            idx = pd.DatetimeIndex(full_df.index)
            if idx.tz is None:
                idx = idx.tz_localize("UTC")
            train1_df = full_df.loc[(idx >= pd.Timestamp(WARMUP_START)) & (idx < TRAIN1_END)]
            assert not train1_df.empty, f"empty Train 1 slice for {symbol}/{interval}"
            assert pd.DatetimeIndex(train1_df.index).max() < TRAIN1_END

            for strategy_name in STRATEGY_SAMPLE:
                for max_sl_pct in MAX_SL_PCT_SWEEP:
                    n_runs += 1
                    rows.append(_run_one(train1_df, symbol, interval, strategy_name, max_sl_pct))

            print(f"done {symbol}/{interval} ({n_runs} runs so far, {time.time() - t_start:.1f}s elapsed)")

    results_df = pd.DataFrame(rows)
    results_df.to_csv("output/f006_stop_width/summary/results.csv", index=False)

    with open("output/f006_stop_width/summary/manifest.json", "w") as f:
        json.dump({
            "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "git_commit_parent": commit_sha,
            "n_runs": n_runs,
            "strategy_sample": STRATEGY_SAMPLE,
            "max_sl_pct_sweep": MAX_SL_PCT_SWEEP,
            "symbols": SYMBOLS,
            "intervals": INTERVALS,
            "fixed_params": {**FIXED_PARAMS, "initial_equity": INITIAL_EQUITY, "stake": STAKE},
            "warmup_start": WARMUP_START,
            "train1_end": str(TRAIN1_END),
            "now_fixed": str(NOW),
            "data_checksums_verified": {f"{sym}_{intv}": chk for (sym, intv), chk in EXPECTED_CHECKSUMS.items()},
            "elapsed_seconds": time.time() - t_start,
        }, f, indent=2)

    print(f"ALL DONE: {n_runs} runs in {time.time() - t_start:.1f}s")


if __name__ == "__main__":
    main()
