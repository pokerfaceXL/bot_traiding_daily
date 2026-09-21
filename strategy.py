"""
strategy.py — wskazniki, generatory sygnalow, katalog strategii, silnik backtestow.

Jedna z kluczowych zaleznosci: add_indicators() + STRATEGY_CATALOG + backtest_trailing()
uzywane wspolnie przez backtest_apex.py i trader.py.
"""

import time
import sys
import yaml
import os

import requests
import pandas as pd
import numpy as np

from logger_config import setup_logger

# ──────────────────────────────────────────────────────────────
#  CONFIG (dla zycia bota)
# ──────────────────────────────────────────────────────────────

def _resolve_config_path():
    """Zwraca sciezke do pliku konfiguracyjnego z sys.argv lub domyslna."""
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        return sys.argv[1]
    return "configuration/default.yaml"

_config_path = _resolve_config_path()
with open(_config_path) as _f:
    _config = yaml.safe_load(_f)

SYMBOL   = _config.get("SYMBOL",   "BTCUSDT")
INTERVAL = _config.get("INTERVAL", "240")

_log_file = f"{SYMBOL}_{INTERVAL}.log"
logger    = setup_logger(log_file=_log_file)


# ──────────────────────────────────────────────────────────────
#  POBIERANIE DANYCH
# ──────────────────────────────────────────────────────────────

def get_bybit_ohlcv(symbol=None, interval=None, limit=2000, sleep_sec=0.3):
    """Pobiera OHLCV z Bybit (linear perpetuals). Dziala w partiach po 1000."""
    if symbol   is None: symbol   = _config.get("SYMBOL",   "BTCUSDT")
    if interval is None: interval = _config.get("INTERVAL", "240")

    url          = "https://api.bybit.com/v5/market/kline"
    all_data     = []
    remaining    = limit
    end_time     = int(time.time() * 1000)

    _RATE_LIMIT_WAITS = [10, 30, 60, 120, 300]

    while remaining > 0:
        batch = min(1000, remaining)
        params = {"category": "linear", "symbol": symbol,
                  "interval": interval, "limit": batch, "end": end_time}

        result = None
        for attempt, wait in enumerate(_RATE_LIMIT_WAITS + [None]):
            resp   = requests.get(url, params=params, timeout=20)
            result = resp.json()
            if result.get("retCode") != 10006:
                break
            if wait is None:
                raise RuntimeError(f"Bybit rate limit po {len(_RATE_LIMIT_WAITS)} probach: {result}")
            logger.warning(f"Rate limit 10006 [{symbol}] — czekam {wait}s (proba {attempt+1}/{len(_RATE_LIMIT_WAITS)})")
            time.sleep(wait)

        if "result" not in result or "list" not in result["result"]:
            raise RuntimeError(f"Bybit API error: {result}")

        data = result["result"]["list"]
        if not data:
            break

        if all_data:
            cutoff = all_data[0][0]
            data   = [r for r in data if r[0] < cutoff]
        if not data:
            break

        all_data   = data + all_data
        end_time   = int(data[-1][0]) - 1
        remaining -= len(data)
        time.sleep(sleep_sec)

    df = pd.DataFrame(all_data,
                      columns=["timestamp", "open", "high", "low", "close", "volume", "turnover"])
    df = df.astype({"open": float, "high": float, "low": float, "close": float, "volume": float})
    df["timestamp"] = pd.to_datetime(df["timestamp"].astype("int64"), unit="ms")
    df.set_index("timestamp", inplace=True)
    df = df[~df.index.duplicated(keep="last")].sort_index()
    return df[["open", "high", "low", "close", "volume"]]


# ──────────────────────────────────────────────────────────────
#  WSKAZNIKI
# ──────────────────────────────────────────────────────────────

def add_indicators(df):
    """
    Dodaje wszystkie wskazniki potrzebne do strategii.
    Zmienia df in-place i go zwraca.
    Kolumna ATR: atr14 (uzywana przez silnik backtestow).
    """
    c = df["close"].astype(float)
    h = df["high"].astype(float)
    l = df["low"].astype(float)
    v = df["volume"].astype(float)

    # --- EMA ---
    for p in [8, 13, 21, 34, 50, 100, 200]:
        df[f"ema{p}"] = c.ewm(span=p, adjust=False).mean()

    # --- RSI ---
    for p in [7, 14, 21]:
        delta = c.diff()
        gain  = delta.clip(lower=0).rolling(p).mean()
        loss  = (-delta.clip(upper=0)).rolling(p).mean()
        df[f"rsi{p}"] = 100 - 100 / (1 + gain / loss.replace(0, np.nan))

    # --- MACD (dwie wersje) ---
    for fast, slow, sig in [(12, 26, 9), (8, 21, 5)]:
        line   = c.ewm(span=fast, adjust=False).mean() - c.ewm(span=slow, adjust=False).mean()
        signal = line.ewm(span=sig, adjust=False).mean()
        key    = f"macd_{fast}_{slow}"
        df[f"{key}_line"]   = line
        df[f"{key}_signal"] = signal
        df[f"{key}_hist"]   = line - signal

    # --- Bollinger Bands ---
    for p, k in [(20, 2.0), (20, 2.5), (10, 2.0)]:
        mid  = c.rolling(p).mean()
        std  = c.rolling(p).std()
        key  = f"bb_{p}_{k}"
        df[f"{key}_mid"]   = mid
        df[f"{key}_upper"] = mid + k * std
        df[f"{key}_lower"] = mid - k * std
        df[f"{key}_width"] = (2 * k * std) / mid.replace(0, np.nan)

    # --- ATR ---
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    for p in [14, 21]:
        df[f"atr{p}"] = tr.ewm(span=p, adjust=False).mean()

    # --- ADX / +DI / -DI ---
    for p in [14]:
        plus_dm  = h.diff().clip(lower=0)
        minus_dm = (-l.diff()).clip(lower=0)
        plus_dm  = plus_dm.where(plus_dm  > (-l.diff()).clip(lower=0), 0.0)
        minus_dm = minus_dm.where(minus_dm > h.diff().clip(lower=0),   0.0)
        atr_p    = tr.ewm(span=p, adjust=False).mean()
        pdi      = 100 * plus_dm.ewm(span=p, adjust=False).mean()  / atr_p.replace(0, np.nan)
        ndi      = 100 * minus_dm.ewm(span=p, adjust=False).mean() / atr_p.replace(0, np.nan)
        dx       = (100 * (pdi - ndi).abs() / (pdi + ndi).replace(0, np.nan))
        df[f"adx{p}"] = dx.ewm(span=p, adjust=False).mean()
        df[f"pdi{p}"] = pdi
        df[f"ndi{p}"] = ndi

    # --- Stochastic ---
    for k_p in [5, 14]:
        ll      = l.rolling(k_p).min()
        hh      = h.rolling(k_p).max()
        stoch_k = 100 * (c - ll) / (hh - ll).replace(0, np.nan)
        df[f"stoch_k{k_p}"] = stoch_k
        df[f"stoch_d{k_p}"] = stoch_k.rolling(3).mean()

    # --- Volume ratio ---
    df["vol_ma20"]  = v.rolling(20).mean()
    df["vol_ratio"] = v / df["vol_ma20"].replace(0, np.nan)

    return df


# ──────────────────────────────────────────────────────────────
#  GENERATORY SYGNALOW
#  Konwencja: +1 = long, -1 = short, 0 = brak pozycji
# ──────────────────────────────────────────────────────────────

def _s(df): return pd.Series(0, index=df.index, dtype=int)


def sig_ema_cross(df, fast, slow):
    s = _s(df)
    s[df[f"ema{fast}"] > df[f"ema{slow}"]] =  1
    s[df[f"ema{fast}"] < df[f"ema{slow}"]] = -1
    return s

def sig_ema3_cross(df, e1, e2, e3):
    s = _s(df)
    s[(df[f"ema{e1}"] > df[f"ema{e2}"]) & (df[f"ema{e2}"] > df[f"ema{e3}"])] =  1
    s[(df[f"ema{e1}"] < df[f"ema{e2}"]) & (df[f"ema{e2}"] < df[f"ema{e3}"])] = -1
    return s

def sig_ema_rsi(df, fast, slow, rsi_p, ob=55, os=45):
    s = _s(df)
    s[(df[f"ema{fast}"] > df[f"ema{slow}"]) & (df[f"rsi{rsi_p}"] > ob)] =  1
    s[(df[f"ema{fast}"] < df[f"ema{slow}"]) & (df[f"rsi{rsi_p}"] < os)] = -1
    return s

def sig_macd_hist(df, fast, slow, rsi_p=None, rsi_th=50):
    hist = df[f"macd_{fast}_{slow}_hist"]
    s    = _s(df)
    s[hist > 0] =  1
    s[hist < 0] = -1
    if rsi_p:
        s[(s ==  1) & (df[f"rsi{rsi_p}"] < rsi_th)]       = 0
        s[(s == -1) & (df[f"rsi{rsi_p}"] > 100 - rsi_th)] = 0
    return s

def sig_macd_signal(df, fast, slow):
    s = _s(df)
    s[df[f"macd_{fast}_{slow}_line"] > df[f"macd_{fast}_{slow}_signal"]] =  1
    s[df[f"macd_{fast}_{slow}_line"] < df[f"macd_{fast}_{slow}_signal"]] = -1
    return s

def sig_rsi_macd(df, rsi_p, macd_fast, macd_slow, rsi_th=50):
    hist = df[f"macd_{macd_fast}_{macd_slow}_hist"]
    rsi  = df[f"rsi{rsi_p}"]
    s    = _s(df)
    s[(rsi > rsi_th) & (hist > 0)] =  1
    s[(rsi < rsi_th) & (hist < 0)] = -1
    return s

def sig_bb_breakout(df, bb_p, bb_k):
    key = f"bb_{bb_p}_{bb_k}"
    s   = _s(df)
    s[df["close"] > df[f"{key}_upper"]] =  1
    s[df["close"] < df[f"{key}_lower"]] = -1
    return s

def sig_bb_mid(df, bb_p, bb_k):
    key = f"bb_{bb_p}_{bb_k}"
    s   = _s(df)
    s[df["close"] > df[f"{key}_mid"]] =  1
    s[df["close"] < df[f"{key}_mid"]] = -1
    return s

def sig_bb_revert(df, bb_p, bb_k):
    key = f"bb_{bb_p}_{bb_k}"
    s   = _s(df)
    s[df["close"] < df[f"{key}_lower"]] =  1
    s[df["close"] > df[f"{key}_upper"]] = -1
    return s

def sig_bb_breakout_rsi(df, bb_p, bb_k, rsi_p, rsi_th=50):
    key = f"bb_{bb_p}_{bb_k}"
    rsi = df[f"rsi{rsi_p}"]
    s   = _s(df)
    s[(df["close"] > df[f"{key}_upper"]) & (rsi > rsi_th)] =  1
    s[(df["close"] < df[f"{key}_lower"]) & (rsi < rsi_th)] = -1
    return s

def sig_bb_breakout_ema(df, bb_p, bb_k, ema_p):
    key = f"bb_{bb_p}_{bb_k}"
    s   = _s(df)
    s[(df["close"] > df[f"{key}_upper"]) & (df["close"] > df[f"ema{ema_p}"])] =  1
    s[(df["close"] < df[f"{key}_lower"]) & (df["close"] < df[f"ema{ema_p}"])] = -1
    return s

def sig_bb_breakout_adx(df, bb_p, bb_k, adx_p, adx_th=20):
    key      = f"bb_{bb_p}_{bb_k}"
    trending = df[f"adx{adx_p}"] > adx_th
    s        = _s(df)
    s[(df["close"] > df[f"{key}_upper"]) & trending] =  1
    s[(df["close"] < df[f"{key}_lower"]) & trending] = -1
    return s

def sig_bb_breakout_vol(df, bb_p, bb_k, vol_mult=1.2):
    key    = f"bb_{bb_p}_{bb_k}"
    vol_ok = df["vol_ratio"] > vol_mult
    s      = _s(df)
    s[(df["close"] > df[f"{key}_upper"]) & vol_ok] =  1
    s[(df["close"] < df[f"{key}_lower"]) & vol_ok] = -1
    return s

def sig_bb_breakout_squeeze(df, bb_p, bb_k):
    """Breakout TYLKO gdy szerokosc BB > 30-periodowa srednia (prawdziwy breakout z konsolidacji)."""
    key       = f"bb_{bb_p}_{bb_k}"
    width     = df[f"{key}_width"]
    expanding = width > width.rolling(30).mean()
    s         = _s(df)
    s[(df["close"] > df[f"{key}_upper"]) & expanding] =  1
    s[(df["close"] < df[f"{key}_lower"]) & expanding] = -1
    return s

def sig_bb_breakout_macd(df, bb_p, bb_k, macd_fast, macd_slow):
    key  = f"bb_{bb_p}_{bb_k}"
    hist = df[f"macd_{macd_fast}_{macd_slow}_hist"]
    s    = _s(df)
    s[(df["close"] > df[f"{key}_upper"]) & (hist > 0)] =  1
    s[(df["close"] < df[f"{key}_lower"]) & (hist < 0)] = -1
    return s

def sig_rsi_trend(df, rsi_p, mid=50):
    s = _s(df)
    s[df[f"rsi{rsi_p}"] > mid] =  1
    s[df[f"rsi{rsi_p}"] < mid] = -1
    return s

def sig_rsi_extreme(df, rsi_p, ob=70, os=30):
    rsi = df[f"rsi{rsi_p}"]
    s   = _s(df)
    s[rsi < os] =  1
    s[rsi > ob] = -1
    return s

def sig_adx_ema(df, adx_p, ema_fast, ema_slow, adx_th=25):
    trending = df[f"adx{adx_p}"] > adx_th
    s        = _s(df)
    s[trending & (df[f"ema{ema_fast}"] > df[f"ema{ema_slow}"])] =  1
    s[trending & (df[f"ema{ema_fast}"] < df[f"ema{ema_slow}"])] = -1
    return s

def sig_adx_di(df, adx_p, adx_th=20):
    trending = df[f"adx{adx_p}"] > adx_th
    s        = _s(df)
    s[trending & (df[f"pdi{adx_p}"] > df[f"ndi{adx_p}"])] =  1
    s[trending & (df[f"pdi{adx_p}"] < df[f"ndi{adx_p}"])] = -1
    return s

def sig_stoch_cross(df, k_p):
    s = _s(df)
    s[df[f"stoch_k{k_p}"] > df[f"stoch_d{k_p}"]] =  1
    s[df[f"stoch_k{k_p}"] < df[f"stoch_d{k_p}"]] = -1
    return s

def sig_stoch_ema(df, k_p, ema_fast, ema_slow, ob=70, os=30):
    k    = df[f"stoch_k{k_p}"]
    bull = df[f"ema{ema_fast}"] > df[f"ema{ema_slow}"]
    bear = df[f"ema{ema_fast}"] < df[f"ema{ema_slow}"]
    s    = _s(df)
    s[bull & (k < os)] =  1
    s[bear & (k > ob)] = -1
    return s

def sig_ema_vol(df, fast, slow, vol_mult=1.2):
    vol_ok = df["vol_ratio"] > vol_mult
    s      = _s(df)
    s[(df[f"ema{fast}"] > df[f"ema{slow}"]) & vol_ok] =  1
    s[(df[f"ema{fast}"] < df[f"ema{slow}"]) & vol_ok] = -1
    return s

def sig_ema_bb_adx(df, fast, slow, bb_p, bb_k, adx_p, adx_th=20):
    key    = f"bb_{bb_p}_{bb_k}"
    wide   = df[f"{key}_width"] > df[f"{key}_width"].rolling(20).mean()
    adx_ok = df[f"adx{adx_p}"] > adx_th
    s      = _s(df)
    s[(df[f"ema{fast}"] > df[f"ema{slow}"]) & wide & adx_ok] =  1
    s[(df[f"ema{fast}"] < df[f"ema{slow}"]) & wide & adx_ok] = -1
    return s

def sig_triple_screen(df, fast, slow, trend_ema, rsi_p, rsi_th=50):
    bull = df["close"] > df[f"ema{trend_ema}"]
    bear = df["close"] < df[f"ema{trend_ema}"]
    s    = _s(df)
    s[bull & (df[f"ema{fast}"] > df[f"ema{slow}"]) & (df[f"rsi{rsi_p}"] > rsi_th)] =  1
    s[bear & (df[f"ema{fast}"] < df[f"ema{slow}"]) & (df[f"rsi{rsi_p}"] < rsi_th)] = -1
    return s


# ──────────────────────────────────────────────────────────────
#  KATALOG STRATEGII  (name → callable(df) → pd.Series sygnalu)
# ──────────────────────────────────────────────────────────────

STRATEGY_CATALOG: dict[str, callable] = {
    # EMA cross
    "EMA_8_21":   lambda df: sig_ema_cross(df, 8,  21),
    "EMA_13_34":  lambda df: sig_ema_cross(df, 13, 34),
    "EMA_8_34":   lambda df: sig_ema_cross(df, 8,  34),
    "EMA_21_50":  lambda df: sig_ema_cross(df, 21, 50),
    "EMA_13_50":  lambda df: sig_ema_cross(df, 13, 50),
    "EMA_21_100": lambda df: sig_ema_cross(df, 21, 100),
    "EMA_34_100": lambda df: sig_ema_cross(df, 34, 100),
    "EMA_50_200": lambda df: sig_ema_cross(df, 50, 200),
    # EMA + RSI
    "EMA_8_21_RSI14_55":   lambda df: sig_ema_rsi(df, 8,  21, 14, 55, 45),
    "EMA_8_21_RSI14_60":   lambda df: sig_ema_rsi(df, 8,  21, 14, 60, 40),
    "EMA_13_34_RSI14_55":  lambda df: sig_ema_rsi(df, 13, 34, 14, 55, 45),
    "EMA_13_34_RSI7_55":   lambda df: sig_ema_rsi(df, 13, 34,  7, 55, 45),
    "EMA_21_50_RSI14_55":  lambda df: sig_ema_rsi(df, 21, 50, 14, 55, 45),
    "EMA_8_34_RSI14_60":   lambda df: sig_ema_rsi(df, 8,  34, 14, 60, 40),
    # Triple EMA
    "EMA3_8_21_50":    lambda df: sig_ema3_cross(df, 8,  21,  50),
    "EMA3_8_21_100":   lambda df: sig_ema3_cross(df, 8,  21, 100),
    "EMA3_13_34_100":  lambda df: sig_ema3_cross(df, 13, 34, 100),
    "EMA3_8_34_100":   lambda df: sig_ema3_cross(df, 8,  34, 100),
    "EMA3_13_50_200":  lambda df: sig_ema3_cross(df, 13, 50, 200),
    "EMA3_21_50_200":  lambda df: sig_ema3_cross(df, 21, 50, 200),
    # MACD
    "MACD_12_26_hist": lambda df: sig_macd_hist(df, 12, 26),
    "MACD_8_21_hist":  lambda df: sig_macd_hist(df, 8,  21),
    "MACD_12_26_sig":  lambda df: sig_macd_signal(df, 12, 26),
    "MACD_8_21_sig":   lambda df: sig_macd_signal(df, 8,  21),
    # MACD + RSI
    "MACD_RSI14_50": lambda df: sig_rsi_macd(df, 14, 12, 26, 50),
    "MACD_RSI14_55": lambda df: sig_rsi_macd(df, 14, 12, 26, 55),
    "MACD_RSI7_50":  lambda df: sig_rsi_macd(df,  7,  8, 21, 50),
    "MACD_RSI7_55":  lambda df: sig_rsi_macd(df,  7,  8, 21, 55),
    # BB breakout (czyste)
    "BB_20_2_breakout":   lambda df: sig_bb_breakout(df, 20, 2.0),
    "BB_20_25_breakout":  lambda df: sig_bb_breakout(df, 20, 2.5),
    "BB_10_2_breakout":   lambda df: sig_bb_breakout(df, 10, 2.0),
    "BB_20_2_mid":        lambda df: sig_bb_mid(df, 20, 2.0),
    "BB_20_2_revert":     lambda df: sig_bb_revert(df, 20, 2.0),
    "BB_20_25_revert":    lambda df: sig_bb_revert(df, 20, 2.5),
    # BB + RSI
    "BB_20_2_RSI14":      lambda df: sig_bb_breakout_rsi(df, 20, 2.0, 14, 50),
    "BB_20_25_RSI14":     lambda df: sig_bb_breakout_rsi(df, 20, 2.5, 14, 50),
    "BB_20_2_RSI14_55":   lambda df: sig_bb_breakout_rsi(df, 20, 2.0, 14, 55),
    "BB_20_25_RSI14_55":  lambda df: sig_bb_breakout_rsi(df, 20, 2.5, 14, 55),
    "BB_20_2_RSI7_50":    lambda df: sig_bb_breakout_rsi(df, 20, 2.0,  7, 50),
    "BB_10_2_RSI14":      lambda df: sig_bb_breakout_rsi(df, 10, 2.0, 14, 50),
    # BB + EMA
    "BB_20_2_EMA50":    lambda df: sig_bb_breakout_ema(df, 20, 2.0,  50),
    "BB_20_25_EMA50":   lambda df: sig_bb_breakout_ema(df, 20, 2.5,  50),
    "BB_20_2_EMA100":   lambda df: sig_bb_breakout_ema(df, 20, 2.0, 100),
    "BB_20_25_EMA100":  lambda df: sig_bb_breakout_ema(df, 20, 2.5, 100),
    "BB_20_2_EMA200":   lambda df: sig_bb_breakout_ema(df, 20, 2.0, 200),
    "BB_20_25_EMA200":  lambda df: sig_bb_breakout_ema(df, 20, 2.5, 200),
    # BB + ADX
    "BB_20_2_ADX20":    lambda df: sig_bb_breakout_adx(df, 20, 2.0, 14, 20),
    "BB_20_25_ADX20":   lambda df: sig_bb_breakout_adx(df, 20, 2.5, 14, 20),
    "BB_20_25_ADX25":   lambda df: sig_bb_breakout_adx(df, 20, 2.5, 14, 25),
    # BB + Volume
    "BB_20_25_VOL12":   lambda df: sig_bb_breakout_vol(df, 20, 2.5, 1.2),
    "BB_20_2_VOL12":    lambda df: sig_bb_breakout_vol(df, 20, 2.0, 1.2),
    # BB Squeeze (najlepsza rodzina!)
    "BB_20_2_SQ":   lambda df: sig_bb_breakout_squeeze(df, 20, 2.0),
    "BB_20_25_SQ":  lambda df: sig_bb_breakout_squeeze(df, 20, 2.5),
    # BB + MACD
    "BB_20_2_MACD":   lambda df: sig_bb_breakout_macd(df, 20, 2.0, 12, 26),
    "BB_20_25_MACD":  lambda df: sig_bb_breakout_macd(df, 20, 2.5, 12, 26),
    # RSI
    "RSI14_trend50": lambda df: sig_rsi_trend(df, 14),
    "RSI7_trend50":  lambda df: sig_rsi_trend(df,  7),
    "RSI14_7030":    lambda df: sig_rsi_extreme(df, 14, 70, 30),
    "RSI14_6535":    lambda df: sig_rsi_extreme(df, 14, 65, 35),
    "RSI21_7030":    lambda df: sig_rsi_extreme(df, 21, 70, 30),
    "RSI7_6535":     lambda df: sig_rsi_extreme(df,  7, 65, 35),
    # ADX
    "ADX14_EMA8_21":   lambda df: sig_adx_ema(df, 14,  8,  21, 25),
    "ADX14_EMA13_34":  lambda df: sig_adx_ema(df, 14, 13,  34, 25),
    "ADX14_EMA21_50":  lambda df: sig_adx_ema(df, 14, 21,  50, 20),
    "ADX14_DI_20":     lambda df: sig_adx_di(df, 14, 20),
    "ADX14_DI_25":     lambda df: sig_adx_di(df, 14, 25),
    # Stochastic
    "STOCH14_cross":     lambda df: sig_stoch_cross(df, 14),
    "STOCH5_cross":      lambda df: sig_stoch_cross(df,  5),
    "STOCH14_EMA8_21":   lambda df: sig_stoch_ema(df, 14,  8, 21),
    "STOCH14_EMA13_34":  lambda df: sig_stoch_ema(df, 14, 13, 34),
    # EMA + Volume
    "EMA_8_21_VOL12":   lambda df: sig_ema_vol(df,  8, 21, 1.2),
    "EMA_13_34_VOL12":  lambda df: sig_ema_vol(df, 13, 34, 1.2),
    "EMA_8_21_VOL15":   lambda df: sig_ema_vol(df,  8, 21, 1.5),
    # EMA + BB + ADX
    "EMA_BB_ADX_8_21":   lambda df: sig_ema_bb_adx(df,  8, 21, 20, 2.0, 14, 20),
    "EMA_BB_ADX_13_34":  lambda df: sig_ema_bb_adx(df, 13, 34, 20, 2.0, 14, 20),
    # Triple Screen
    "TS_8_21_100_14":   lambda df: sig_triple_screen(df,  8, 21, 100, 14, 50),
    "TS_13_34_200_14":  lambda df: sig_triple_screen(df, 13, 34, 200, 14, 50),
    "TS_8_21_50_14":    lambda df: sig_triple_screen(df,  8, 21,  50, 14, 55),
    "TS_13_34_100_14":  lambda df: sig_triple_screen(df, 13, 34, 100, 14, 55),
}


# ──────────────────────────────────────────────────────────────
#  SILNIK BACKTESTOW z trailing stop (ATR-based + aktywacja)
# ──────────────────────────────────────────────────────────────

_SUB_INTERVAL_MAP = {
    "1440": "240",
    "240":  "60",
    "120":  "30",
    "60":   "15",
    "30":   "5",
    "15":   "5",
}


def _build_sub_lookup(sub_df, main_interval_min):
    """Grupuje sub-swiece po zaokraglonym timestampie glownej swieczki."""
    tmp = sub_df[["open", "high", "low", "close"]].copy()
    tmp.index = tmp.index.floor(f"{main_interval_min}min")
    return {ts: grp.to_numpy(dtype=float) for ts, grp in tmp.groupby(level=0)}


def _calc_initial_sl(direction, price, atr_value, atr_multiplier, max_sl_pct):
    # dist     = min(atr_multiplier * atr_value, price * max_sl_pct)
    dist     =  price * max_sl_pct
    sl_level = (price - dist) if direction == 1 else (price + dist)
    return max(sl_level, 0.0) if direction == 1 else sl_level


def backtest_trailing(df,
                      atr_multiplier=1.5,
                      max_sl_pct=0.05,
                      activate_pct=0.03,
                      trail_pct=0.02,
                      leverage=10,
                      stake=100.0,
                      atr_col="atr14",
                      entry_on_open=False,
                      cooldown_candles=0,
                      sub_lookup=None,
                      main_interval_min=None):
    """
    Backtest z ATR Stop Loss + Trailing Stop z progiem aktywacji + dzwignia.

    Parametry
    ---------
    atr_multiplier   : mnoznik ATR dla initial SL
    max_sl_pct       : max odleglosc SL od ceny wejscia (bez dzwigni)
    activate_pct     : % zysku ceny od entry aktywujacy trailing
    trail_pct        : % cofniecia od best_price dla trailing SL
    leverage         : dzwignia
    stake            : wielkosc pozycji bazowej w USD
    atr_col          : kolumna ATR (domyslnie atr14)
    entry_on_open    : True = wejscie na open kolejnej swiece (bardziej realistyczne)
    cooldown_candles : ile swiec czekamy po initial SL przed kolejnym wejsciem
    sub_lookup       : dict {timestamp -> np.ndarray (n,4)} z sub-swiecami (Bar Magnifier)
                       None = stare zachowanie optymistyczne (backward compat)
    main_interval_min: minuty glownego interwalu (wymagane gdy sub_lookup podany)

    Zwraca
    ------
    (trades_df, metrics_dict)
    metrics: total_pnl, win_rate, profit_factor, max_drawdown,
             n_trades, calmar, ambiguous_pct
    """
    n = len(df)
    if n == 0:
        return pd.DataFrame(), _empty_metrics()

    # Pre-extract numpy arrays — eliminuje narzut pandas per-row
    idx_arr  = df.index.values
    close_a  = df["close"].to_numpy(dtype=float)
    open_a   = df["open"].to_numpy(dtype=float)  if "open"  in df.columns else close_a
    high_a   = df["high"].to_numpy(dtype=float)  if "high"  in df.columns else close_a
    low_a    = df["low"].to_numpy(dtype=float)   if "low"   in df.columns else close_a

    _raw_atr = df[atr_col].to_numpy(dtype=float) if atr_col in df.columns else np.zeros(n)
    atr_a    = np.where(np.isnan(_raw_atr), 0.0, _raw_atr)

    _raw_sig = df["signal"].to_numpy(dtype=float) if "signal" in df.columns else np.zeros(n)
    sig_a    = np.where(np.isnan(_raw_sig) | (_raw_sig == 0), 0, _raw_sig.astype(int))

    pos             = 0
    entry_price     = 0.0
    entry_date      = None
    initial_sl      = 0.0
    trailing_sl     = 0.0
    best_price      = 0.0
    trail_active    = False
    trades          = []
    pending_signal  = 0
    pending_atr     = 0.0
    candle_idx      = 0
    cooldown_until  = -1
    ambiguous_count = 0
    sl_checks_total = 0

    use_sub = sub_lookup is not None

    for i in range(n):
        candle_idx += 1
        open_  = open_a[i]
        close  = close_a[i]
        high   = high_a[i]
        low    = low_a[i]
        atr    = atr_a[i]
        idx    = idx_arr[i]
        signal = sig_a[i]

        # 0. Wejscie oczekujace (entry_on_open)
        if entry_on_open and pending_signal != 0 and pos == 0:
            pos, entry_price, entry_date, initial_sl, trailing_sl, best_price, trail_active = \
                _open(pending_signal, open_, idx, pending_atr, atr_multiplier, max_sl_pct)
            pending_signal = 0

        # 1+2. Aktualizacja trailing SL i sprawdzenie SL
        sl_hit    = False
        sl_reason = ""

        if pos != 0:
            if use_sub:
                # ── Bar Magnifier: pesymistyczna kolejnosc wewnatrz sub-swiec ──
                sub_bars = sub_lookup.get(idx)
                if sub_bars is None:
                    # fallback: traktujemy glowna swiece jako jedna sub-swiece
                    sub_bars = np.array([[0.0, high, low, 0.0]])

                exit_sl = 0.0
                n_sub   = len(sub_bars)

                if pos == 1:
                    for j in range(n_sub):
                        sub_h    = sub_bars[j, 1]
                        sub_l    = sub_bars[j, 2]
                        active_sl = max(initial_sl, trailing_sl) if trail_active else initial_sl
                        sl_checks_total += 1
                        if sub_l <= active_sl:
                            # wykrywamy ambiwalentnosc: HIGH tez wybilby aktywacje
                            if not trail_active and sub_h >= entry_price * (1 + activate_pct):
                                ambiguous_count += 1
                            sl_reason = "trailing_sl" if (trail_active and trailing_sl >= initial_sl) else "initial_sl"
                            exit_sl   = active_sl
                            sl_hit    = True
                            break
                        # LOW nie wybil SL — aktualizujemy trailing z HIGH
                        best_price = max(best_price, sub_h)
                        if not trail_active and best_price >= entry_price * (1 + activate_pct):
                            trail_active = True
                            trailing_sl  = best_price * (1 - trail_pct)
                        if trail_active:
                            trailing_sl = max(trailing_sl, best_price * (1 - trail_pct))

                elif pos == -1:
                    for j in range(n_sub):
                        sub_h    = sub_bars[j, 1]
                        sub_l    = sub_bars[j, 2]
                        active_sl = min(initial_sl, trailing_sl) if trail_active else initial_sl
                        sl_checks_total += 1
                        if sub_h >= active_sl:
                            if not trail_active and sub_l <= entry_price * (1 - activate_pct):
                                ambiguous_count += 1
                            sl_reason = "trailing_sl" if (trail_active and trailing_sl <= initial_sl) else "initial_sl"
                            exit_sl   = active_sl
                            sl_hit    = True
                            break
                        # HIGH nie wybil SL — aktualizujemy trailing z LOW
                        best_price = min(best_price, sub_l)
                        if not trail_active and best_price <= entry_price * (1 - activate_pct):
                            trail_active = True
                            trailing_sl  = best_price * (1 + trail_pct)
                        if trail_active:
                            trailing_sl = min(trailing_sl, best_price * (1 + trail_pct))

                if sl_hit:
                    raw_pnl = (exit_sl - entry_price) / entry_price if pos == 1 \
                         else (entry_price - exit_sl) / entry_price
                    t = "Long" if pos == 1 else "Short"
                    trades.append(_make_trade(entry_date, idx, t, entry_price, exit_sl,
                                              initial_sl, trailing_sl, trail_active,
                                              raw_pnl, sl_reason, leverage, stake))
                    pos = 0; trail_active = False

            else:
                # ── Oryginalny tryb optymistyczny (sub_lookup=None) ──
                if pos == 1:
                    best_price = max(best_price, high)
                    if not trail_active and best_price >= entry_price * (1 + activate_pct):
                        trail_active = True
                        trailing_sl  = best_price * (1 - trail_pct)
                    if trail_active:
                        trailing_sl = max(trailing_sl, best_price * (1 - trail_pct))
                    active_sl = max(initial_sl, trailing_sl) if trail_active else initial_sl
                elif pos == -1:
                    best_price = min(best_price, low)
                    if not trail_active and best_price <= entry_price * (1 - activate_pct):
                        trail_active = True
                        trailing_sl  = best_price * (1 + trail_pct)
                    if trail_active:
                        trailing_sl = min(trailing_sl, best_price * (1 + trail_pct))
                    active_sl = min(initial_sl, trailing_sl) if trail_active else initial_sl

                if pos == 1 and low <= active_sl:
                    raw_pnl   = (active_sl - entry_price) / entry_price
                    sl_reason = "trailing_sl" if (trail_active and trailing_sl >= initial_sl) else "initial_sl"
                    trades.append(_make_trade(entry_date, idx, "Long", entry_price, active_sl,
                                              initial_sl, trailing_sl, trail_active,
                                              raw_pnl, sl_reason, leverage, stake))
                    pos = 0; trail_active = False; sl_hit = True
                elif pos == -1 and high >= active_sl:
                    raw_pnl   = (entry_price - active_sl) / entry_price
                    sl_reason = "trailing_sl" if (trail_active and trailing_sl <= initial_sl) else "initial_sl"
                    trades.append(_make_trade(entry_date, idx, "Short", entry_price, active_sl,
                                              initial_sl, trailing_sl, trail_active,
                                              raw_pnl, sl_reason, leverage, stake))
                    pos = 0; trail_active = False; sl_hit = True

        if sl_hit:
            if sl_reason == "initial_sl" and cooldown_candles > 0:
                cooldown_until = candle_idx + cooldown_candles
            if signal != 0 and candle_idx > cooldown_until:
                if entry_on_open:
                    pending_signal = signal
                    pending_atr    = atr
                else:
                    pos, entry_price, entry_date, initial_sl, trailing_sl, best_price, trail_active = \
                        _open(signal, close, idx, atr, atr_multiplier, max_sl_pct)
            continue

        # 3. Odwrocenie sygnalu
        if pos != 0 and signal != 0 and signal != pos:
            raw_pnl = (close - entry_price) / entry_price if pos == 1 \
                 else (entry_price - close) / entry_price
            t = "Long" if pos == 1 else "Short"
            trades.append(_make_trade(entry_date, idx, t, entry_price, close,
                                      initial_sl, trailing_sl, trail_active,
                                      raw_pnl, "signal_reverse", leverage, stake))
            pos = 0; trail_active = False

        # 4. Otwarcie
        if pos == 0 and signal != 0 and candle_idx > cooldown_until:
            if entry_on_open:
                pending_signal = signal
                pending_atr    = atr
            else:
                pos, entry_price, entry_date, initial_sl, trailing_sl, best_price, trail_active = \
                    _open(signal, close, idx, atr, atr_multiplier, max_sl_pct)

    # 5. Zamkniecie na ostatniej swiecie
    if pos != 0:
        last_close = close_a[-1]
        last_date  = idx_arr[-1]
        raw_pnl    = (last_close - entry_price) / entry_price if pos == 1 \
                else (entry_price - last_close) / entry_price
        t = "Long (Open)" if pos == 1 else "Short (Open)"
        trades.append(_make_trade(entry_date, last_date, t, entry_price, last_close,
                                  initial_sl, trailing_sl, trail_active,
                                  raw_pnl, "open", leverage, stake))

    if not trades:
        return pd.DataFrame(), _empty_metrics()

    trades_df = pd.DataFrame(trades)
    trades_df["exit_date"] = pd.to_datetime(trades_df["exit_date"])
    monthly_pnl = trades_df.groupby(pd.Grouper(key="exit_date", freq="ME"))["pnl_usd"].sum()
    negative_months = int((monthly_pnl < 0).sum())
    total_months    = int(monthly_pnl.shape[0])

    metrics   = _compute_metrics(trades_df, stake)
    metrics["negative_months"] = negative_months
    metrics["total_months"]    = total_months
    metrics["ambiguous_pct"] = round(
        ambiguous_count / sl_checks_total * 100, 1
    ) if sl_checks_total > 0 else 0.0
    return trades_df, metrics


def _open(direction, price, date, atr, atr_mult, max_sl_pct):
    sl = _calc_initial_sl(direction, price, atr, atr_mult, max_sl_pct)
    return direction, price, date, sl, 0.0, price, False


def _make_trade(entry_date, exit_date, type_str, entry_price, exit_price,
                initial_sl, trailing_sl, trail_active, raw_pnl_pct,
                close_by, leverage, stake):
    lev_pnl = raw_pnl_pct * leverage
    suffix  = " (SL)" if close_by in ("initial_sl", "trailing_sl") else ""
    return {
        "entry_date":      entry_date,
        "exit_date":       exit_date,
        "type":            type_str + suffix,
        "entry_price":     entry_price,
        "exit_price":      exit_price,
        "initial_sl":      initial_sl,
        "trailing_sl":     trailing_sl if trail_active else None,
        "trailing_active": trail_active,
        "pnl_usd":         lev_pnl * stake,
        "pnl_pct":         lev_pnl * 100,
        "pnl_pct_raw":     raw_pnl_pct * 100,
        "close_by":        close_by,
        "leverage":        leverage,
    }


def _empty_metrics():
    return {"total_pnl": 0.0, "win_rate": 0.0, "profit_factor": 0.0,
            "max_drawdown": 0.0, "max_drawdown_usd": 0.0, "max_drawdown_abs_pct": 0.0,
            "n_trades": 0, "calmar": 0.0,
            "ambiguous_pct": 0.0}


def _compute_metrics(trades_df, initial_equity=1000.0):
    closed = trades_df[~trades_df["type"].str.contains("Open", na=False)]
    if closed.empty:
        return _empty_metrics()

    pnl = closed["pnl_usd"].astype(float).values
    equity = initial_equity + np.cumsum(pnl)
    peak = np.maximum.accumulate(equity)

    dd_usd = peak - equity
    dd_pct = np.where(peak > 0, dd_usd / peak * 100, 0.0)

    max_dd_usd = float(dd_usd.max())
    max_dd_pct = float(dd_pct.max())

    total_pnl = float(trades_df["pnl_usd"].sum())
    win_rate = float((closed["pnl_usd"] > 0).mean() * 100)
    losing = closed[closed["pnl_usd"] <= 0]["pnl_usd"].sum()
    profitable = closed[closed["pnl_usd"] > 0]["pnl_usd"].sum()
    pf = float(profitable / abs(losing)) if losing != 0 else 9999.0
    calmar = total_pnl / (max_dd_usd + 1e-9)

    return {
        "total_pnl": round(total_pnl, 2),
        "win_rate": round(win_rate, 1),
        "profit_factor": round(pf, 2),
        "max_drawdown": round(max_dd_pct, 1),
        "max_drawdown_usd": round(max_dd_usd, 2),
        "max_drawdown_abs_pct": round(max_dd_pct, 1),
        "n_trades": len(closed),
        "calmar": round(calmar, 3),
        "ambiguous_pct": 0.0,
    }


# ──────────────────────────────────────────────────────────────
#  FUNKCJA DLA LIVE BOTA
# ──────────────────────────────────────────────────────────────

def run_strategy(df=None, strategy_name=None):
    """
    Generuje sygnaly dla biezacej swiece.
    Uzywana przez trader.py.

    df            — gotowy DataFrame ze swieczkami (bez ostatniej niezakonczonej).
                    Jesli None, pobiera dane przez HTTP (tryb bez cache).
    strategy_name — nadpisuje wartosc z configa (przydatne przy reload).
    Zwraca df z kolumnami: signal, green_dot (1=long), red_dot (1=short).
    """
    if strategy_name is None:
        strategy_name = _config.get("STRATEGY", "BB_20_25_SQ")
    if strategy_name not in STRATEGY_CATALOG:
        raise ValueError(f"Nieznana strategia: '{strategy_name}'. "
                         f"Dostepne: {sorted(STRATEGY_CATALOG.keys())}")

    if df is None:
        df = get_bybit_ohlcv(limit=500)
        df = df.iloc[:-1]   # pomijamy ostatnia (niezakonczona) swiece

    df = add_indicators(df)
    df["signal"] = STRATEGY_CATALOG[strategy_name](df)

    logger.info(f"run_strategy [{strategy_name}] | "
                f"last signal={int(df['signal'].iloc[-1])} "
                f"price={df['close'].iloc[-1]:.4f}")
    return df
