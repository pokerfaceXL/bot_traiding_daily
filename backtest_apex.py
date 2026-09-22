"""
backtest_apex.py — backtest jednego symbolu dla wybranych (lub wszystkich) strategii.

Uruchomienie:
    python backtest_apex.py configuration/default.yaml
    python backtest_apex.py configuration/default.yaml --strategies BB_20_25_SQ BB_20_2_SQ
    python backtest_apex.py configuration/default.yaml --param-optimization
"""

import argparse
import json
import uuid
from datetime import datetime, timezone
import os
import pathlib
import sys
import time
import yaml
import pandas as pd

from strategy import (
    get_bybit_ohlcv, add_indicators,
    STRATEGY_CATALOG, backtest_trailing,
    _SUB_INTERVAL_MAP, _build_sub_lookup,
)
from logger_config import setup_logger


# ──────────────────────────────────────────────────────────────
# ARGUMENTY
# ──────────────────────────────────────────────────────────────

parser = argparse.ArgumentParser(description="Backtest dla jednego symbolu")
parser.add_argument("config", nargs="?", default="configuration/default.yaml",
                    help="Sciezka do pliku konfiguracyjnego YAML")
parser.add_argument("--strategies", nargs="*", default=None,
                    help="Lista strategii do przetestowania (domyslnie: wszystkie)")
parser.add_argument("--param-optimization", action="store_true",
                    help="Optuna optimization po leverage/max_sl_pct/trail_pct/activate_pct")
parser.add_argument("--cooldown", type=int, default=None,
                    help="Ile swiec przerwy po initial SL (nadpisuje YAML; 0 = wylaczone)")
parser.add_argument("--optuna-trials", type=int, default=None,
                    help="Liczba prob Optuna (nadpisuje YAML OPTUNA_TRIALS; domyslnie 150)")
parser.add_argument("--quote", type=float, default=None,
                    help="Kapital bazowy w USD (nadpisuje YAML POSITION_SIZE_USDT; domyslnie 100)")
parser.add_argument("--local-csv", type=str, default=None,
                    help="Sciezka do lokalnego CSV (timestamp,open,high,low,close,volume) "
                         "zamiast pobierania z Bybit — tryb offline, bez zapytan sieciowych")
args = parser.parse_args()

OPTIMIZATION = args.param_optimization

# ──────────────────────────────────────────────────────────────
# KONFIGURACJA
# ──────────────────────────────────────────────────────────────

with open(args.config) as f:
    config = yaml.safe_load(f)

SYMBOL       = config.get("SYMBOL",       "BTCUSDT")
INTERVAL     = config.get("INTERVAL",     "240")
CANDLES      = int(config.get("CANDLES",  8000))
LEVERAGE      = int(config.get("LEVERAGE", 10))
ATR_MULT      = float(config.get("ATR_MULTIPLIER", 2.5))
MAX_SL_PCT    = float(config.get("MAX_SL_PCT",     0.06))
ACTIVATE_PCT  = float(config.get("ACTIVATE_PCT",   0.03))
TRAIL_PCT     = float(config.get("TRAIL_PCT",       0.015))
ENTRY_ON_OPEN    = bool(config.get("ENTRY_ON_OPEN",    True))
COOLDOWN_CANDLES = int(config.get("COOLDOWN_CANDLES", 0))
if args.cooldown is not None:
    COOLDOWN_CANDLES = args.cooldown   # CLI nadpisuje YAML
POSITION_SIZE_USDT = float(config.get("POSITION_SIZE_USDT", 100.0))
if args.quote is not None:
    POSITION_SIZE_USDT = args.quote   # CLI nadpisuje YAML
bot_id           = int(os.getenv("BOT_ID", 0)) or int(time.time())

CALMAR_RATIO = float(config.get("BACKTEST_CALMAR_RATIO", 0.90))
N_TRIALS     = int(config.get("OPTUNA_TRIALS", 150))
if args.optuna_trials is not None:
    N_TRIALS = args.optuna_trials

_bt_cfg_dir = pathlib.Path("configuration") / "backtest"
_bt_cfg_dir.mkdir(parents=True, exist_ok=True)
BACKTEST_CONFIG_OUT = str(_bt_cfg_dir / pathlib.Path(args.config).name)

log_file = f"backtest/{SYMBOL}_{INTERVAL}_backtest.log"
logger   = setup_logger(name=f"backtest_{SYMBOL}_{INTERVAL}", log_file=log_file)

# Wybor strategii
strategy_names = args.strategies if args.strategies else list(STRATEGY_CATALOG.keys())
unknown = [s for s in strategy_names if s not in STRATEGY_CATALOG]
if unknown:
    print(f"[BLAD] Nieznane strategie: {unknown}")
    print(f"Dostepne: {sorted(STRATEGY_CATALOG.keys())}")
    sys.exit(1)

# ──────────────────────────────────────────────────────────────
# OPTYMALIZACJA (tylko w trybie optymalizacji)
# ──────────────────────────────────────────────────────────────

ATR_MULT_FIXED = ATR_MULT


def _compute_max_leverage(df_ind):
    """Max leverage based on recent ATR/price volatility — higher vol = lower cap."""
    recent  = df_ind.tail(252)
    atr_pct = (recent["atr14"] / recent["close"]).mean() * 100
    if atr_pct < 1.0:
        max_lev = 20
    elif atr_pct < 1.5:
        max_lev = 15
    elif atr_pct < 2.5:
        max_lev = 10
    elif atr_pct < 4.0:
        max_lev = 7
    elif atr_pct < 6.0:
        max_lev = 5
    else:
        max_lev = 3
    logger.info(f"ATR_PCT={atr_pct:.2f}% -> max_leverage={max_lev}")
    return max_lev


def _run_optuna_strategy(df, max_leverage, atr_mult, position_size,
                         entry_on_open, cooldown_candles,
                         sub_lookup=None, main_interval_min=None):
    """Optuna TPE search over leverage/sl/trail/activate. Returns best combo dict."""
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    _SENTINEL = -1e9

    def objective(trial):
        lev   = trial.suggest_int("leverage", 4, max_leverage)
        # SL max 1%–10%
        sl    = round(trial.suggest_float("max_sl_pct",    0.01, 0.10, step=0.005), 3)
        # trail 5%–10%
        trail = round(trial.suggest_float("trail_pct",     0.05, 0.10, step=0.005), 3)
        # activate 5%–15%
        act   = round(trial.suggest_float("activate_pct",  0.05, 0.15, step=0.005), 3)

        # sanity check – skrajnie agresywne combo
        if lev * sl >= 1.0:
            return _SENTINEL

        trades_df, m = backtest_trailing(
            df,
            atr_multiplier=atr_mult,
            max_sl_pct=sl,
            activate_pct=act,
            trail_pct=trail,
            leverage=lev,
            stake=position_size,
            atr_col="atr14",
            entry_on_open=entry_on_open,
            cooldown_candles=cooldown_candles,
            sub_lookup=sub_lookup,
            main_interval_min=main_interval_min,
        )

        n_trades = m["n_trades"]
        if n_trades < 30:
            # odrzucamy zbyt małą próbę
            return _SENTINEL

        # udział transakcji zamkniętych na initial SL
        if n_trades > 0:
            sl_rate = (trades_df["close_by"] == "initial_sl").mean()
        else:
            sl_rate = 1.0

        # za wysoki odsetek SL -> odrzucamy
        if sl_rate > 0.5:
            return _SENTINEL

        calmar  = m["calmar"]
        maxdd   = m["max_drawdown"]   # w %
        pnl_usd = m["total_pnl"]

        # --- komponent zysku (Pnl) ---
        # normalizujemy PnL po czasie i wielkości pozycji, żeby była porównywalna z Calmar
        period_years = max(1.0, (df.index[-1] - df.index[0]).days / 365.0)
        pnl_per_year = pnl_usd / period_years
        # dimensionless: ile stake'ów rocznie zarabia strategia
        pnl_score = pnl_per_year / position_size

        # --- Negative months penalty ---
        neg_months   = m.get("negative_months", 0)
        total_months = max(1, m.get("total_months", 1))
        neg_ratio    = neg_months / total_months
    
        # zakładamy, że akceptowalne jest ok. 15% stratnych miesięcy
        target_neg_ratio = 0.15
        # kara rośnie proporcjonalnie powyżej target_neg_ratio
        neg_penalty = max(0.0, neg_ratio - target_neg_ratio) / target_neg_ratio

        # długość okresu backtestu w latach
        period_years = max(1.0, (df.index[-1] - df.index[0]).days / 365.0)
        trades_per_year = n_trades / period_years

        min_trades_per_year = 250
        max_trades_per_year = 400

        # miękka kara – poza zakresem
        if trades_per_year < min_trades_per_year or trades_per_year > max_trades_per_year:
            trades_penalty = 1.0
        else:
            trades_penalty = 0.0

        # wagi do dostrojenia ręcznie
        w_calmar  = 0.5   # waga Calmaru
        w_pnl     = 0.5   # waga zysku (pnl_score)
        alpha_sl  = 0.7   # kara za SL-rate
        beta_tr   = 0.3   # kara za nadmiar transakcji
        gamma_dd  = 0.4   # kara za duży DD powyżej 35%
        delta_neg = 2.0   # mocna kara za zbyt dużo stratnych miesięcy

        score = (
            w_calmar * calmar
            + w_pnl    * pnl_score
            - alpha_sl * sl_rate
            - beta_tr  * trades_penalty
            - gamma_dd * max(0, (maxdd - 35) / 35.0)
            - delta_neg * neg_penalty
        )

        return score
    
    study = optuna.create_study(
        direction="maximize",
        sampler=optuna.samplers.TPESampler(seed=42),
    )
    study.optimize(objective, n_trials=N_TRIALS, show_progress_bar=False)

    valid = [t for t in study.trials if t.value is not None and t.value > _SENTINEL]
    if not valid:
        lev_fb = min(3, max_leverage)
        t_df, m = backtest_trailing(
            df, atr_multiplier=atr_mult, max_sl_pct=0.05, activate_pct=0.05,
            trail_pct=0.02, leverage=lev_fb, stake=position_size,
            atr_col="atr14", entry_on_open=entry_on_open,
            cooldown_candles=cooldown_candles,
            sub_lookup=sub_lookup, main_interval_min=main_interval_min,
        )
        return {"t_df": t_df, "metrics": m,
                "params": {"leverage": lev_fb, "max_sl_pct": 0.05,
                           "trail_pct": 0.02, "activate_pct": 0.05,
                           "cooldown_candles": cooldown_candles}}

    p = study.best_trial.params
    t_df, m = backtest_trailing(
        df,
        atr_multiplier=atr_mult,
        max_sl_pct=p["max_sl_pct"],
        activate_pct=p["activate_pct"],
        trail_pct=p["trail_pct"],
        leverage=p["leverage"],
        stake=position_size,
        atr_col="atr14",
        entry_on_open=entry_on_open,
        cooldown_candles=cooldown_candles,
        sub_lookup=sub_lookup,
        main_interval_min=main_interval_min,
    )
    return {
        "t_df":    t_df,
        "metrics": m,
        "params": {
            "leverage":         p["leverage"],
            "max_sl_pct":       p["max_sl_pct"],
            "trail_pct":        p["trail_pct"],
            "activate_pct":     p["activate_pct"],
            "cooldown_candles": cooldown_candles,
        },
    }


def _select_best(pool):
    calmar_max = max(r["metrics"]["calmar"] for r in pool)
    if calmar_max > 0:
        pareto = [r for r in pool if r["metrics"]["calmar"] >= CALMAR_RATIO * calmar_max]
    else:
        pareto = [max(pool, key=lambda r: r["metrics"]["calmar"])]

    if any(r["params"] is not None for r in pareto):
        return min(pareto, key=lambda r: r["params"]["leverage"])
    return max(pareto, key=lambda r: r["metrics"]["calmar"])


# ──────────────────────────────────────────────────────────────
# POBIERANIE DANYCH (raz dla wszystkich strategii)
# ──────────────────────────────────────────────────────────────

if args.local_csv:
    logger.info(f"Wczytywanie lokalnego CSV [{args.local_csv}] — tryb offline, bez Bybit.")
    df_raw = pd.read_csv(args.local_csv, parse_dates=["timestamp"], index_col="timestamp")
    df_raw = df_raw[["open", "high", "low", "close", "volume"]].astype(float)
    df_raw = df_raw[~df_raw.index.duplicated(keep="last")].sort_index()
else:
    logger.info(f"Pobieranie {CANDLES} swiec [{SYMBOL} {INTERVAL}]...")
    df_raw = get_bybit_ohlcv(symbol=SYMBOL, interval=INTERVAL, limit=CANDLES)
logger.info(f"Dane wejsciowe: {len(df_raw)} swiec. Zakres: {df_raw.index[0]} -> {df_raw.index[-1]}")

df_ind = add_indicators(df_raw.copy())

_sub_iv = _SUB_INTERVAL_MAP.get(INTERVAL)
if _sub_iv is None:
    raise ValueError(f"Brak mapowania sub-interwalu dla INTERVAL={INTERVAL}. "
                     f"Dostepne: {list(_SUB_INTERVAL_MAP.keys())}")

if args.local_csv:
    # Offline: brak drugiego zapytania o sub-swiece, uzywamy glownych swiec z CSV
    # jako jedynej sub-swiecy na kazda glowna swiece (Bar Magnifier w trybie degenerowanym).
    _sub_df_raw = df_raw
    logger.info("Bar Magnifier (offline): sub-swiece = glowne swiece z lokalnego CSV.")
else:
    _sub_limit = CANDLES * (int(INTERVAL) // int(_sub_iv)) + 100
    logger.info(f"Pobieranie {_sub_limit} sub-swiec [{SYMBOL} {_sub_iv}m] (Bar Magnifier)...")
    time.sleep(1.0)
    _sub_df_raw = get_bybit_ohlcv(symbol=SYMBOL, interval=_sub_iv, limit=_sub_limit, sleep_sec=0.5)
sub_lookup = _build_sub_lookup(_sub_df_raw, int(INTERVAL))
logger.info(f"Bar Magnifier gotowy: {len(_sub_df_raw)} sub-swiec [{_sub_iv}m]")

if len(df_ind) < 500:
    logger.warning(f"Za malo danych ({len(df_ind)} swiec) dla {SYMBOL}. Pomijam.")
    sys.exit(1)

# ──────────────────────────────────────────────────────────────
# PETLA PO STRATEGIACH
# ──────────────────────────────────────────────────────────────

results = []   # {"strategy": str, "metrics": dict, "trades_df": DataFrame, "params": dict}

if OPTIMIZATION:
    max_lev = _compute_max_leverage(df_ind)

for strategy_name in strategy_names:
    try:
        df = df_ind.copy()
        df["signal"] = STRATEGY_CATALOG[strategy_name](df)

        if OPTIMIZATION:
            best_combo = _run_optuna_strategy(
                df,
                max_leverage=max_lev,
                atr_mult=ATR_MULT_FIXED,
                position_size=POSITION_SIZE_USDT,
                entry_on_open=ENTRY_ON_OPEN,
                cooldown_candles=COOLDOWN_CANDLES,
                sub_lookup=sub_lookup,
                main_interval_min=int(INTERVAL),
            )

            trades_df  = best_combo["t_df"]
            metrics    = best_combo["metrics"]
            opt_params = best_combo["params"]
            logger.info(
                f"[{strategy_name:<25}] OPT  lev={opt_params['leverage']}  "
                f"sl={opt_params['max_sl_pct']:.3f}  trail={opt_params['trail_pct']:.3f}  "
                f"act={opt_params['activate_pct']:.3f}  cd={opt_params['cooldown_candles']}  "
                f"PnL=${metrics['total_pnl']:8.2f}  Calmar={metrics['calmar']:.3f}  "
                f"Ambig={metrics['ambiguous_pct']:.1f}%"
            )
        else:
            trades_df, metrics = backtest_trailing(
                df,
                atr_multiplier=ATR_MULT,
                max_sl_pct=MAX_SL_PCT,
                activate_pct=ACTIVATE_PCT,
                trail_pct=TRAIL_PCT,
                leverage=LEVERAGE,
                stake=POSITION_SIZE_USDT,
                atr_col="atr14",
                entry_on_open=ENTRY_ON_OPEN,
                cooldown_candles=COOLDOWN_CANDLES,
                sub_lookup=sub_lookup,
                main_interval_min=int(INTERVAL),
            )
            opt_params = None
            logger.info(
                f"[{strategy_name:<25}] PnL=${metrics['total_pnl']:8.2f}  "
                f"WR={metrics['win_rate']:5.1f}%  DD={metrics['max_drawdown']:6.1f}%  "
                f"N={metrics['n_trades']}  Ambig={metrics['ambiguous_pct']:.1f}%"
            )

        results.append({
            "strategy":  strategy_name,
            "metrics":   metrics,
            "trades_df": trades_df,
            "params":    opt_params,
        })
    except Exception as e:
        logger.error(f"[{strategy_name}] BLAD: {e}", exc_info=True)

if not results:
    logger.warning("Brak wynikow.")
    sys.exit(1)

# ──────────────────────────────────────────────────────────────
# NAJLEPSZA STRATEGIA
# ──────────────────────────────────────────────────────────────

best = _select_best(results)
best_name = best["strategy"]
best_m    = best["metrics"]
best_tdf  = best["trades_df"]
best_p    = best["params"]   # None jesli nie w trybie optymalizacji

# ──────────────────────────────────────────────────────────────
# RAPORT LOKALNY
# ──────────────────────────────────────────────────────────────

# 2. Config z wynikami
apex_config = {
    "symbol":             SYMBOL,
    "interval":           INTERVAL,
    "candles":            len(df_ind),
    "date_from":          str(df_ind.index[0]),
    "date_to":            str(df_ind.index[-1]),
    "optimization":       OPTIMIZATION,
    "POSITION_SIZE_USDT": POSITION_SIZE_USDT,
    "best_strategy":      best_name,
    "best_pnl":           best_m["total_pnl"],
    "best_win_rate":      best_m["win_rate"],
    "best_max_drawdown":         best_m["max_drawdown"],
    "best_max_drawdown_usd":     best_m["max_drawdown_usd"],
    "best_max_drawdown_abs_pct": best_m["max_drawdown_abs_pct"],
    "best_profit_factor": best_m["profit_factor"],
    "best_n_trades":      best_m["n_trades"],
    "best_calmar":        best_m["calmar"],
    "best_ambiguous_pct": best_m["ambiguous_pct"],
    "bar_magnifier_sub_interval": _sub_iv,
}

if OPTIMIZATION and best_p:
    apex_config.update({
        "opt_leverage":          best_p["leverage"],
        "opt_max_sl_pct":        best_p["max_sl_pct"],
        "opt_trail_pct":         best_p["trail_pct"],
        "opt_activate_pct":      best_p["activate_pct"],
        "opt_cooldown_candles":  best_p["cooldown_candles"],
        "ATR_MULTIPLIER":        ATR_MULT_FIXED,
    })
else:
    apex_config.update({
        "leverage":         LEVERAGE,
        "ATR_MULTIPLIER":   ATR_MULT,
        "MAX_SL_PCT":       MAX_SL_PCT,
        "ACTIVATE_PCT":     ACTIVATE_PCT,
        "TRAIL_PCT":        TRAIL_PCT,
        "COOLDOWN_CANDLES": COOLDOWN_CANDLES,
    })

apex_config["all_strategies_ranked"] = [
    {"strategy": r["strategy"],
     "pnl":      r["metrics"]["total_pnl"],
     "win_rate": r["metrics"]["win_rate"],
     "calmar":   r["metrics"]["calmar"],
     "max_drawdown": r["metrics"]["max_drawdown"],
     **({"params": r["params"]} if r["params"] else {})}
    for r in sorted(results, key=lambda x: x["metrics"]["total_pnl"], reverse=True)
]

# Parametry live — te same klucze co YAML
live_params = {
    "STRATEGY":         best_name,
    "LEVERAGE":         best_p["leverage"]          if OPTIMIZATION and best_p else LEVERAGE,
    "ATR_MULTIPLIER":   ATR_MULT_FIXED              if OPTIMIZATION and best_p else ATR_MULT,
    "MAX_SL_PCT":       round(best_p["max_sl_pct"],   3) if OPTIMIZATION and best_p else MAX_SL_PCT,
    "ACTIVATE_PCT":     round(best_p["activate_pct"], 3) if OPTIMIZATION and best_p else ACTIVATE_PCT,
    "TRAIL_PCT":        round(best_p["trail_pct"],    3) if OPTIMIZATION and best_p else TRAIL_PCT,
    "COOLDOWN_CANDLES": best_p["cooldown_candles"]  if OPTIMIZATION and best_p else COOLDOWN_CANDLES,
}
apex_config.update(live_params)

# Lokalne artefakty badan; wysylka do Apex jest zawieszona.
run_id = (
    datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    + "_" + uuid.uuid4().hex
)
run_dir = pathlib.Path("output") / "backtests" / run_id
run_dir.mkdir(parents=True, exist_ok=False)
report = {
    "run_id": run_id,
    "created_at": datetime.now(timezone.utc).isoformat(),
    "status": "baseline_unvalidated",
    "limitations": [
        "Legacy backtest: fees, slippage and funding are not included.",
        "Portfolio equity and daily-profit tolerance are not evaluated yet.",
        "Optimization and ranking do not use an independent holdout yet.",
    ],
    "input_config": config.copy(),
    "summary": apex_config,
    "results": [
        {"strategy": r["strategy"], "metrics": r["metrics"], "params": r["params"]}
        for r in results
    ],
}
(run_dir / "report.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False),
    encoding="utf-8",
)
trade_frames = [
    r["trades_df"].assign(strategy=r["strategy"])
    for r in results
    if r["trades_df"] is not None and not r["trades_df"].empty
]
all_trades = (
    pd.concat(trade_frames, ignore_index=True)
    if trade_frames else pd.DataFrame(columns=["strategy"])
)
all_trades.to_csv(run_dir / "trades.csv", index=False, encoding="utf-8")
candidate_config = {**config, **live_params}
(run_dir / "candidate.yaml").write_text(
    yaml.safe_dump(candidate_config, allow_unicode=True, sort_keys=False),
    encoding="utf-8",
)
logger.info(f"Wyniki lokalne: {run_dir.resolve()} | Apex: wysylka zawieszona")
print(f"Raport lokalny: {run_dir.resolve()}")

# Zachowanie dotychczasowego eksportu konfiguracji backtestowej.
try:
    config.update(live_params)
    with open(BACKTEST_CONFIG_OUT, "w") as _f:
        yaml.dump(config, _f, default_flow_style=False, allow_unicode=True)
    logger.info(f"YAML zaktualizowany: {args.config}  STRATEGY={best_name}")
except Exception as e:
    logger.error(f"Blad zapisu YAML {args.config}: {e}")

# ──────────────────────────────────────────────────────────────
# PODSUMOWANIE W KONSOLI
# ──────────────────────────────────────────────────────────────

summary_rows = []
for r in results:
    row = {
        "Strategy": r["strategy"],
        "PnL $":    r["metrics"]["total_pnl"],
        "WR %":     r["metrics"]["win_rate"],
        "MaxDD %":  r["metrics"]["max_drawdown"],
        "Trades":   r["metrics"]["n_trades"],
        "Calmar":   r["metrics"]["calmar"],
    }
    if r["params"]:
        row["Lev"]   = r["params"]["leverage"]
        row["SL%"]   = r["params"]["max_sl_pct"]
        row["Trail"] = r["params"]["trail_pct"]
    summary_rows.append(row)

summary = pd.DataFrame(summary_rows).sort_values("PnL $", ascending=False)
mode_label = "OPTYMALIZACJA" if OPTIMIZATION else "BACKTEST"

print(f"\n=== {mode_label} {SYMBOL} @ {INTERVAL}m | {len(df_ind)} swiec | stake={POSITION_SIZE_USDT:.0f} USD ===")
print(summary.to_string(index=False))
print(f"\n>>> Najlepsza: {best_name}")
print(f"    PnL ${best_m['total_pnl']:.2f}  |  WR {best_m['win_rate']:.1f}%  |  "
      f"MaxDD {best_m['max_drawdown']:.1f}%  |  Calmar {best_m['calmar']:.3f}  |  "
      f"Trades {best_m['n_trades']}")

if OPTIMIZATION and best_p:
    print(f"\n    Optymalne parametry dla {SYMBOL}:")
    print(f"    STRATEGY:         {best_name}")
    print(f"    LEVERAGE:         {best_p['leverage']}")
    print(f"    ATR_MULTIPLIER:   {ATR_MULT_FIXED}")
    print(f"    MAX_SL_PCT:       {best_p['max_sl_pct']}")
    print(f"    ACTIVATE_PCT:     {best_p['activate_pct']}")
    print(f"    TRAIL_PCT:        {best_p['trail_pct']}")
    print(f"    COOLDOWN_CANDLES: {best_p['cooldown_candles']}")
else:
    print(f"\n    Parametry live dla {SYMBOL}:")
    print(f"    STRATEGY:         {best_name}")
    print(f"    LEVERAGE:         {LEVERAGE}")
    print(f"    ATR_MULTIPLIER:   {ATR_MULT}")
    print(f"    MAX_SL_PCT:       {MAX_SL_PCT}")
    print(f"    ACTIVATE_PCT:     {ACTIVATE_PCT}")
    print(f"    TRAIL_PCT:        {TRAIL_PCT}")
    print(f"    COOLDOWN_CANDLES: {COOLDOWN_CANDLES}")
