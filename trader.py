"""
trader.py  - live trading: otwieranie/zamykanie pozycji + zarzadzanie trailing stop.

Architektura:
  - df_cache        : rolling 600-swieczny DataFrame aktualizowany z WebSocket
  - Async executor  : logowanie do Apex, closed PnL  - poza krytyczna sciezka
  - Fill check      : limit/aggressive_limit z fallback na market po timeoucie
  - Circuit breaker : dzienny limit straty equity; halt + alert do Apex
  - Cooldown        : po zamknieciu przez trailing SL odczekaj N swiec
"""

import os
import math
import time
import yaml
import sys
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

import pandas as pd
from pybit.unified_trading import HTTP
from dotenv import load_dotenv

from strategy import run_strategy, add_indicators
from logger_config import setup_logger
from rest_logs import (
    send_last_closed_to_apex, send_bot_config_to_apex,
    send_equity_halt_to_apex, send_error_to_apex,
)
from config import bot_id, bot_name

load_dotenv()

# ──────────────────────────────────────────────────────────────
# KONFIGURACJA
# ──────────────────────────────────────────────────────────────

config             = None
API_KEY            = None
API_SECRET         = None
SYMBOL             = None
LEVERAGE           = None
POSITION_SIZE_USDT = None
ATR_MULTIPLIER     = None
MAX_SL_PCT         = None
ACTIVATE_PCT       = None
TRAIL_PCT          = None
INTERVAL           = None
ORDER_TYPE         = None   # "market" | "limit" | "aggressive_limit"
LIMIT_OFFSET_PCT   = None   # przesuniecie ceny dla aggressive_limit
FILL_TIMEOUT_SEC   = None   # max czas oczekiwania na fill limitu
COOLDOWN_CANDLES   = None   # ile swiec czekamy po trailing SL hit
MIN_TSL_STEP_PCT   = None   # min poprawa SL (%) zeby wyslac aktualizacje do Bybit

GAP_PROTECTION_ENABLED:       bool  = False
GAP_PROTECTION_THRESHOLD_PCT: float = 0.005
GAP_CHECK_INTERVAL_SEC:       float = 30.0

count_profit = None
session      = None
logger       = None

minTradeValue   = None
qty_step        = None
price_step      = None
qty_precision   = None
price_precision = None

START_DATE_TIMESTAMP_MS = int(time.time() * 1000)

# ──────────────────────────────────────────────────────────────
# STAN GLOBALNY (watkowo bezpieczny: modyfikowany tylko z main watku)
# ──────────────────────────────────────────────────────────────

df_cache: pd.DataFrame | None = None   # rolling 600-swieczny cache
_DF_WINDOW = 600                        # ilosc swiec w oknie

_executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="apex")

# Circuit breaker  - oparty o skumulowane PnL bota (nie equity portfela)
_halted_until: datetime | None = None
_loss_limit:   float           = 0.0   # = raw POSITION_SIZE_USDT z configa

# Cooldown po SL hit (initial lub trailing)
_last_close_candle: int = 0
_last_close_reason: str = ""
_candle_counter:    int = 0

# Bot-managed TSL watermark (peak mark_price od aktywacji; Long: max, Short: min)
_tsl_watermark:    float = 0.0
_tsl_current_sl:   float = 0.0   # ostatni SL ustawiony przez bota (tpslMode=Partial nie zwraca go w get_positions)

_pending_close_reason: str  = ""     # ustawiany przed close_position() przez gap_protection
_tsl_was_active:       bool = False  # True gdy TSL watermark aktywowany; rozroznia TSL od SL

CIRCUIT_BREAKER_ENABLED: bool = True

# Deduplicacja raportowania  - zapobiega podwojnemu wysylaniu tej samej pozycji
_reported_order_ids: set = set()


def initialize_trader_config(config_path):
    global config, API_KEY, API_SECRET, SYMBOL, LEVERAGE, POSITION_SIZE_USDT
    global ATR_MULTIPLIER, MAX_SL_PCT, ACTIVATE_PCT, TRAIL_PCT, INTERVAL
    global ORDER_TYPE, LIMIT_OFFSET_PCT, FILL_TIMEOUT_SEC
    global COOLDOWN_CANDLES, CIRCUIT_BREAKER_ENABLED, MIN_TSL_STEP_PCT
    global GAP_PROTECTION_ENABLED, GAP_PROTECTION_THRESHOLD_PCT, GAP_CHECK_INTERVAL_SEC
    global logger, session, count_profit
    global minTradeValue, qty_step, price_step, qty_precision, price_precision
    global df_cache, _loss_limit

    with open(config_path) as f:
        config = yaml.safe_load(f)

    API_KEY    = os.getenv("BYBIT_API_KEY")
    API_SECRET = os.getenv("BYBIT_API_SECRET")

    SYMBOL             = config.get("SYMBOL",           "BTCUSDT")
    LEVERAGE           = int(config.get("LEVERAGE",     10))
    POSITION_SIZE_USDT = float(config.get("POSITION_SIZE_USDT", 20)) * LEVERAGE
    ATR_MULTIPLIER     = float(config.get("ATR_MULTIPLIER",  2.5))
    MAX_SL_PCT         = float(config.get("MAX_SL_PCT",      0.06))
    ACTIVATE_PCT       = float(config.get("ACTIVATE_PCT",    0.03))
    TRAIL_PCT          = float(config.get("TRAIL_PCT",        0.015))
    INTERVAL           = config.get("INTERVAL", "240")
    ORDER_TYPE         = config.get("ORDER_TYPE",         "market")
    LIMIT_OFFSET_PCT   = float(config.get("LIMIT_OFFSET_PCT",   0.0003))
    FILL_TIMEOUT_SEC   = float(config.get("FILL_TIMEOUT_SEC",   15.0))
    COOLDOWN_CANDLES          = int(config.get("COOLDOWN_CANDLES",          3))
    CIRCUIT_BREAKER_ENABLED   = bool(config.get("CIRCUIT_BREAKER_ENABLED",  True))
    MIN_TSL_STEP_PCT          = float(config.get("MIN_TSL_STEP_PCT",         0.001))
    GAP_PROTECTION_ENABLED       = bool(config.get("GAP_PROTECTION_ENABLED",       False))
    GAP_PROTECTION_THRESHOLD_PCT = float(config.get("GAP_PROTECTION_THRESHOLD_PCT", 0.005))
    GAP_CHECK_INTERVAL_SEC       = float(config.get("GAP_CHECK_INTERVAL_SEC",       30.0))

    _loss_limit  = float(config.get("POSITION_SIZE_USDT", 20))   # raw, bez lewara
    count_profit = 0.0

    log_filename = f"{SYMBOL}_{INTERVAL}.log"
    logger       = setup_logger(
        log_file=log_filename,
        bot_id=bot_id, bot_name=bot_name, symbol=SYMBOL,
        apex_level=logging.INFO,
    )

    session = HTTP(
        api_key=API_KEY,
        api_secret=API_SECRET,
        testnet=False,
    )

    sym_info        = session.get_instruments_info(category="linear", symbol=SYMBOL)["result"]["list"][0]
    minTradeValue   = float(sym_info["lotSizeFilter"]["minNotionalValue"])
    qty_step        = float(sym_info["lotSizeFilter"]["qtyStep"])
    price_step      = float(sym_info["priceFilter"]["tickSize"])
    qty_precision   = abs(round(-math.log10(qty_step)))
    price_precision = abs(round(-math.log10(price_step)))

    positions = session.get_positions(category="linear", symbol=SYMBOL)["result"]["list"]
    if positions and positions[0].get("leverage") != str(LEVERAGE):
        session.set_leverage(
            category="linear",
            symbol=SYMBOL,
            buyLeverage=str(LEVERAGE),
            sellLeverage=str(LEVERAGE),
        )

    # Inicjalne pobranie danych  - tylko przy starcie
    from strategy import get_bybit_ohlcv
    logger.info(f"Ladowanie poczatkowego cache ({_DF_WINDOW} swiec)...")
    raw = get_bybit_ohlcv(symbol=SYMBOL, interval=INTERVAL, limit=_DF_WINDOW)
    df_cache = raw.iloc[:-1].copy()   # pomijamy niezakonczona swiece
    logger.info(f"Cache zaladowany: {len(df_cache)} swiec  "
                f"({df_cache.index[0]} → {df_cache.index[-1]})")

    logger.info(f"Trader gotowy: {SYMBOL} @ {INTERVAL}m  lev={LEVERAGE}x  "
                f"order_type={ORDER_TYPE}  loss_limit={_loss_limit:.2f}  "
                f"cooldown={COOLDOWN_CANDLES}  "
                f"strategy={config.get('STRATEGY', 'BB_20_25_SQ')}")


def reload_trader_config(config_path):
    initialize_trader_config(config_path)


_config_path = sys.argv[1] if len(sys.argv) > 1 else "configuration/default.yaml"
initialize_trader_config(_config_path)


# ──────────────────────────────────────────────────────────────
# INKREMENTALNA AKTUALIZACJA CACHE
# ──────────────────────────────────────────────────────────────

def update_candle_cache(candle_ws: dict):
    """
    Wywolywana z main.py po potwierdzeniu zamkniecia swiece przez WebSocket.
    Dodaje nowa swiece do cache i utrzymuje okno _DF_WINDOW swiec.
    """
    global df_cache, _candle_counter
    if df_cache is None:
        return

    ts = pd.to_datetime(int(candle_ws["start"]), unit="ms")
    new_row = pd.DataFrame([{
        "open":   float(candle_ws["open"]),
        "high":   float(candle_ws["high"]),
        "low":    float(candle_ws["low"]),
        "close":  float(candle_ws["close"]),
        "volume": float(candle_ws["volume"]),
    }], index=[ts])

    df_cache = pd.concat([df_cache, new_row])
    df_cache = df_cache[~df_cache.index.duplicated(keep="last")]
    df_cache = df_cache.tail(_DF_WINDOW)
    _candle_counter += 1


# ──────────────────────────────────────────────────────────────
# EQUITY CIRCUIT BREAKER
# ──────────────────────────────────────────────────────────────

def _check_circuit_breaker() -> bool:
    """
    Zwraca True jesli skumulowane straty bota przekroczyly POSITION_SIZE_USDT.
    Halt do polnocy  - bot liczy tylko wlasne transakcje, nie equity calego portfela.
    Wylaczony gdy CIRCUIT_BREAKER_ENABLED=false w configu.
    """
    global _halted_until, count_profit

    if not CIRCUIT_BREAKER_ENABLED:
        return False

    if _halted_until is not None:
        if datetime.now() < _halted_until:
            logger.warning(f"Circuit breaker aktywny  - halt do {_halted_until}")
            return True
        _halted_until = None
        count_profit = 0.0   # reset PnL na nowy dzien  - bez tego CB odpala sie od razu ponownie
        logger.info("Circuit breaker zresetowany  - wznawiamy trading")

    if count_profit <= -_loss_limit:
        tomorrow = (datetime.now() + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        _halted_until = tomorrow
        alert = {
            "count_profit":  round(count_profit, 2),
            "loss_limit":    round(_loss_limit,  2),
            "halted_until":  str(tomorrow),
            "symbol":        SYMBOL,
        }
        logger.warning(
            f"CIRCUIT BREAKER AKTYWOWANY: PnL={count_profit:.2f} <= limit={-_loss_limit:.2f} | "
            f"halt do {tomorrow}"
        )
        _executor.submit(send_equity_halt_to_apex, bot_id, bot_name, alert)
        return True

    return False


# ──────────────────────────────────────────────────────────────
# COOLDOWN PO TRAILING SL
# ──────────────────────────────────────────────────────────────

def _cooldown_ok() -> bool:
    """Zwraca False jesli jestesmy w oknie cooldown po SL hit (tylko initial SL, nie TSL)."""
    sl_reasons = {"initial_sl", "StopLoss"}
    if _last_close_reason in sl_reasons and COOLDOWN_CANDLES > 0:
        candles_since = _candle_counter - _last_close_candle
        if candles_since < COOLDOWN_CANDLES:
            logger.info(
                f"Cooldown: {candles_since}/{COOLDOWN_CANDLES} swiec po SL ({_last_close_reason})  - pomijam sygnal"
            )
            return False
    return True


# ──────────────────────────────────────────────────────────────
# ZARZADZANIE POZYCJA
# ──────────────────────────────────────────────────────────────

def get_current_position():
    positions = session.get_positions(category="linear", symbol=SYMBOL)["result"]["list"]
    for p in positions:
        if (p["symbol"] == SYMBOL
                and p["positionStatus"] == "Normal"
                and float(p["size"]) > 0):
            return p
    return None


def _calc_sl(side, price, atr_value):
    # dist = min(ATR_MULTIPLIER * atr_value, price * MAX_SL_PCT)
    dist=  price * MAX_SL_PCT
    if side == "Buy":
        return round(max(price - dist, 0.0), price_precision)
    return round(price + dist, price_precision)


def _get_best_ask_bid():
    resp = session.get_tickers(category="linear", symbol=SYMBOL)
    item = resp["result"]["list"][0]
    return float(item["ask1Price"]), float(item["bid1Price"])


def _wait_for_fill(order_id: str) -> bool:
    """
    Sprawdza status zlecenia co 500ms przez FILL_TIMEOUT_SEC.
    Zwraca True jesli zlecenie zostalo wypelnione.
    Najlepsza praktyka: krotki poll zamiast webhooks (nizsza latencja niz WS orderUpdate).
    """
    deadline = time.time() + FILL_TIMEOUT_SEC
    while time.time() < deadline:
        time.sleep(0.5)
        try:
            resp  = session.get_order_history(
                category="linear", symbol=SYMBOL, orderId=order_id
            )
            items = resp["result"].get("list", [])
            if items and items[0]["orderStatus"] == "Filled":
                return True
        except Exception as e:
            logger.warning(f"Fill check error: {e}")
    return False


def open_position(side, price, atr_value):
    """
    Otwiera pozycje wg ORDER_TYPE z configa:
      market            - zlecenie rynkowe (natychmiastowe)
      limit             - limit na aktualnym ask/bid
      aggressive_limit  - limit z LIMIT_OFFSET_PCT za rynkiem (gwarantuje fill)
                         fallback: market po FILL_TIMEOUT_SEC
    """
    stop_loss = _calc_sl(side, price, atr_value)
    qty     = math.floor((POSITION_SIZE_USDT / price) / qty_step) * qty_step
    qty     = max(qty, qty_step)
    qty_str = str(int(qty)) if qty_step >= 1 else str(round(qty, qty_precision))
    sl_qty  = qty_str   # tpslMode=Partial wymaga slSize = pelna wielkosc pozycji

    if ORDER_TYPE == "market":
        order = session.place_order(
            category="linear", symbol=SYMBOL, isLeverage=1,
            side=side, orderType="Market", qty=qty_str,
            stopLoss=str(stop_loss), slTriggerBy="MarkPrice",
            slOrderType="Limit", slLimitPrice=str(stop_loss),
            tpslMode="Full",
        )
        logger.info(f"Market order {side} | ~{price:.4f} SL={stop_loss}(limit) qty={qty}")
        return order

    # Limit lub aggressive_limit
    ask, bid = _get_best_ask_bid()
    if ORDER_TYPE == "aggressive_limit":
        if side == "Buy":
            limit_price = round(ask * (1 + LIMIT_OFFSET_PCT), price_precision)
        else:
            limit_price = round(bid * (1 - LIMIT_OFFSET_PCT), price_precision)
    else:
        limit_price = round(ask if side == "Buy" else bid, price_precision)

    order = session.place_order(
        category="linear", symbol=SYMBOL, isLeverage=1,
        side=side, orderType="Limit", qty=qty_str,
        price=str(limit_price),
        stopLoss=str(stop_loss), slTriggerBy="MarkPrice",
        slOrderType="Limit", slLimitPrice=str(stop_loss),
        tpslMode="Partial", slSize=sl_qty,
        timeInForce="GTC",
    )
    if order["retCode"] != 0:
        logger.error(f"Limit order error: {order}")
        return order

    order_id = order["result"]["orderId"]
    logger.info(f"Limit order {side} @ {limit_price} SL={stop_loss} qty={qty} id={order_id}")

    if _wait_for_fill(order_id):
        logger.info(f"Limit order wypelniony: {order_id}")
        return order

    # Timeout  - anuluj i wejdz market
    logger.warning(
        f"Limit {order_id} nie wypelniony po {FILL_TIMEOUT_SEC:.0f}s  - cancel + market fallback"
    )
    try:
        session.cancel_order(category="linear", symbol=SYMBOL, orderId=order_id)
    except Exception as e:
        logger.warning(f"Cancel error: {e}")

    fallback = session.place_order(
        category="linear", symbol=SYMBOL, isLeverage=1,
        side=side, orderType="Market", qty=qty_str,
        stopLoss=str(stop_loss), slTriggerBy="MarkPrice",
        slOrderType="Limit", slLimitPrice=str(stop_loss),
        tpslMode="Full",
    )
    logger.info(f"Market fallback {side} qty={qty} SL={stop_loss}(limit)")
    return fallback


def close_position(position):
    side = "Sell" if position["side"] == "Buy" else "Buy"
    order = session.place_order(
        category="linear", symbol=SYMBOL,
        side=side, orderType="Market",
        qty=position["size"], reduceOnly=True,
    )
    logger.info(f"Zamknieto pozycje | {order}")
    return order["result"].get("orderId") if order["retCode"] == 0 else None


def _update_tsl_bot_managed(position: dict):
    """
    Bot-managed trailing stop: sledzi watermark (peak mark_price od aktywacji TSL)
    i przesuwa stopLoss (limit) w gore (Long) lub dol (Short). Nigdy cofa SL.
    Zastepuje Bybit server-side trailingStop, ktory wykonuje sie jako Market order.

    tpslMode=Full: kazdy set_trading_stop zastepuje istniejacy SL (nie tworzy nowego).
    MIN_TSL_STEP_PCT: minimalna poprawa SL (%) potrzebna zeby wyslac aktualizacje.
    """
    global _tsl_watermark, _tsl_current_sl, _pending_close_reason, _tsl_was_active

    # --- Gap Protection ---
    if GAP_PROTECTION_ENABLED:
        _side = position["side"]
        _mark = float(position.get("markPrice") or 0)
        _sl   = float(position.get("stopLoss")  or 0)
        if _mark > 0 and _sl > 0:
            gap_triggered = (
                (_side == "Buy"  and _mark < _sl * (1 - GAP_PROTECTION_THRESHOLD_PCT)) or
                (_side == "Sell" and _mark > _sl * (1 + GAP_PROTECTION_THRESHOLD_PCT))
            )
            if gap_triggered:
                logger.warning(
                    f"GAP PROTECTION: mark={_mark:.4f} przeskoczyl SL={_sl:.4f} "
                    f"(threshold={GAP_PROTECTION_THRESHOLD_PCT*100:.2f}%) - zamykam market"
                )
                _tsl_watermark        = 0.0
                _tsl_current_sl       = 0.0
                _tsl_was_active       = False
                _pending_close_reason = "gap_protection"
                order_id = close_position(position)
                if order_id:
                    _report_closed_pnl_async(order_id, int(time.time() * 1000), "gap_protection")
                return
    # --- koniec Gap Protection ---

    if ACTIVATE_PCT <= 0 or TRAIL_PCT <= 0:
        return

    side        = position["side"]
    entry_price = float(position.get("avgPrice")  or 0)
    mark_price  = float(position.get("markPrice") or entry_price)
    pos_sl      = float(position.get("stopLoss") or 0)
    current_sl  = pos_sl if pos_sl > 0 else _tsl_current_sl

    if entry_price <= 0 or mark_price <= 0:
        return

    if side == "Buy":
        active_price = entry_price * (1 + ACTIVATE_PCT)
        if mark_price < active_price:
            _tsl_watermark = 0.0
            return
        _tsl_watermark = max(_tsl_watermark, mark_price)
        new_sl = round(_tsl_watermark * (1 - TRAIL_PCT), price_precision)
        if new_sl <= current_sl:
            return
    else:  # Sell
        active_price = entry_price * (1 - ACTIVATE_PCT)
        if mark_price > active_price:
            _tsl_watermark = 0.0
            return
        _tsl_watermark = min(_tsl_watermark, mark_price) if _tsl_watermark > 0 else mark_price
        new_sl = round(_tsl_watermark * (1 + TRAIL_PCT), price_precision)
        if current_sl > 0 and new_sl >= current_sl:
            return

    # Nie wysylaj jesli poprawa jest mniejsza niz MIN_TSL_STEP_PCT
    if current_sl > 0 and MIN_TSL_STEP_PCT > 0:
        if abs(new_sl - current_sl) / current_sl < MIN_TSL_STEP_PCT:
            return

    pos_size = str(position.get("size", "0"))

    try:
        sl_orders = session.get_open_orders(
            category="linear", symbol=SYMBOL, orderFilter="StopOrder"
        )
        if sl_orders.get("retCode") == 0:
            for o in sl_orders.get("result", {}).get("list", []):
                if o.get("stopOrderType") == "PartialStopLoss":
                    session.cancel_order(
                        category="linear", symbol=SYMBOL, orderId=o["orderId"]
                    )
    except Exception as e:
        logger.warning(f"Blad anulowania starych SL orders: {e}")

    try:
        resp = session.set_trading_stop(
            category="linear", symbol=SYMBOL,
            positionIdx=0,
            stopLoss=str(new_sl),
            slTriggerBy="MarkPrice",
            slOrderType="Limit",
            slLimitPrice=str(new_sl),
            tpslMode="Partial",
            slSize=pos_size,
							
        )
        if resp.get("retCode", -1) != 0:
            logger.error(
                f"set_trading_stop blad retCode={resp.get('retCode')} "
                f"msg={resp.get('retMsg')} SL={new_sl}"
            )
            return
        _tsl_current_sl = new_sl
        logger.info(
            f"TSL zaktualizowany: watermark={_tsl_watermark:.4f} -> SL={new_sl:.4f} "
            f"({TRAIL_PCT*100:.2f}% * watermark, poprzedni SL={current_sl:.4f})"
        )
    except Exception as e:
        logger.error(f"Blad aktualizacji TSL: {e}")


def update_tsl():
    """Publiczny wrapper  - bot-managed TSL update co 90s z keepalive."""
    try:
        position = get_current_position()
    except Exception as e:
        logger.warning(f"Nie mozna pobrac pozycji w update_tsl: {e}")
        return
    if position:
        _update_tsl_bot_managed(position)


# ──────────────────────────────────────────────────────────────
# RAPORTOWANIE (async  - poza krytyczna sciezka)
# ──────────────────────────────────────────────────────────────

def _report_closed_pnl_async(order_id: str, close_ts_ms: int, reason: str = ""):
    """
    Pobiera i wysyla closed PnL do Apex w tle. 5 prob co 3s.

    Uwaga: get_closed_pnl zwraca orderId otwarcia pozycji, nie zamkniecia.
    Dlatego nie matchujemy po orderId  - uzywamy startTime i bierzemy
    pierwszy (najnowszy) rekord dla symbolu od momentu zamkniecia.

    reason: bot-level close reason wstrzykiwany do stopOrderType gdy Bybit go nie wypelnia
      "signal_close"  - bot zamknal na sygnal strategii
    """
    def _task():
        global count_profit, START_DATE_TIMESTAMP_MS, _last_close_reason, _last_close_candle
        global _reported_order_ids, _pending_close_reason, _tsl_was_active
        for attempt in range(5):
            time.sleep(20)
            try:
                resp = session.get_closed_pnl(
                    category="linear", symbol=SYMBOL, startTime=close_ts_ms
                )
                if resp["retCode"] != 0:
                    logger.error(f"get_closed_pnl blad: {resp}")
                    return
                items = resp["result"].get("list", [])
                if not items:
                    logger.debug(f"Proba {attempt+1}/5  - brak rekordow closed PnL (startTime={close_ts_ms})")
                    continue
                item     = items[0]   # najnowsza zamknieta pozycja od close_ts_ms
                dedup_id = item.get("orderId", order_id)
                if dedup_id in _reported_order_ids:
                    return
                _reported_order_ids.add(dedup_id)
                # Zawsze nadpisuj stopOrderType wlasnym powodem
                if reason:
                    item = dict(item)
                    item["stopOrderType"] = reason
                send_last_closed_to_apex(item, 0, bot_id, bot_name)
                pnl = float(item.get("closedPnl", 0))
                count_profit           += pnl
                START_DATE_TIMESTAMP_MS = int(time.time() * 1000)
                _last_close_reason      = item.get("stopOrderType", "")
                _last_close_candle      = _candle_counter
                _pending_close_reason   = ""
                _tsl_was_active         = False
                logger.info(f"Closed PnL: {pnl:.4f} | total: {count_profit:.4f} | reason: {_last_close_reason}")
                return
            except Exception as e:
                logger.exception(f"Wyjatek w closed PnL task (proba {attempt+1}): {e}")
        logger.error(f"Nie znaleziono closed PnL po 5 probach (order_id={order_id})")
        send_error_to_apex(bot_id, bot_name,
                           f"Closed PnL not found after 5 retries: order_id={order_id} symbol={SYMBOL}")

    _executor.submit(_task)


def fetch_and_report_closed_pnl(order_id: str, close_ts_ms: int, reason: str = ""):
    """Wrapper  - zleca raportowanie asynchronicznie z opcjonalnym bot-level reason."""
    _report_closed_pnl_async(order_id, close_ts_ms, reason)


def check_for_new_closed_positions():
    """
    Synchronicznie pobiera nowe zamkniete pozycje i aktualizuje count_profit.
    Raportowanie do Apex odbywa sie asynchronicznie (poza krytyczna sciezka).
    Wywolywana PRZED _check_circuit_breaker()  - zapobiega race condition gdzie
    PnL z server-side TSL bylby znany dopiero po otwarciu nowej pozycji.
    """
    global count_profit, START_DATE_TIMESTAMP_MS
    global _last_close_reason, _last_close_candle, _reported_order_ids
    global _pending_close_reason, _tsl_was_active
    global _tsl_watermark, _tsl_current_sl
    try:
        resp = session.get_closed_pnl(
            category="linear", symbol=SYMBOL, startTime=START_DATE_TIMESTAMP_MS
        )
        if resp["retCode"] != 0:
            return
        new_items = []
        for item in resp["result"].get("list", []):
            oid = item.get("orderId")
            if oid in _reported_order_ids:
                continue
            _reported_order_ids.add(oid)
            # Zawsze nadpisuj stopOrderType wlasnym powodem (priorytet: pending > TSL > SL)
            item = dict(item)
            if _pending_close_reason:
                item["stopOrderType"] = _pending_close_reason
                _pending_close_reason = ""
            elif _tsl_was_active:
                item["stopOrderType"] = "trailing_sl"
                _tsl_was_active = False
            else:
                item["stopOrderType"] = "StopLoss"
            pnl            = float(item.get("closedPnl", 0))
            count_profit  += pnl
            _last_close_reason = item["stopOrderType"]
            _last_close_candle = _candle_counter
            logger.info(f"Nowa zamknieta pozycja: {oid} PnL={pnl:.4f} reason={_last_close_reason}")
            new_items.append(item)
        START_DATE_TIMESTAMP_MS = int(time.time() * 1000)
        if new_items:
            _tsl_watermark  = 0.0
            _tsl_current_sl = 0.0
        for item in new_items:
            _executor.submit(send_last_closed_to_apex, item, 1, bot_id, bot_name)
    except Exception as e:
        logger.exception(f"Wyjatek w check_closed: {e}")


# ──────────────────────────────────────────────────────────────
# GLOWNA FUNKCJA TRADINGOWA
# ──────────────────────────────────────────────────────────────

def TraderBot(current_config=None):
    global count_profit

    # 0. Synchroniczny check zamknietych pozycji (TSL server-side, SL z poprzednich swiec)
    #    MUSI byc przed circuit breakerem  - inaczej bot otworzy pozycje zanim dowie sie o stracie
    check_for_new_closed_positions()

    # 1. Circuit breaker (PnL-based)  - count_profit jest juz aktualny
    if _check_circuit_breaker():
        return

    # 3. Pobierz sygnaly z cache (bez HTTP  - wskazniki przeliczane na miejscu)
    if df_cache is None or len(df_cache) < 50:
        logger.warning("Cache za maly  - pomijam iteracje")
        return

    strategy_name = (current_config or config).get("STRATEGY", "BB_20_25_SQ")
    df = run_strategy(df=df_cache.copy(), strategy_name=strategy_name)

    last      = df.iloc[-1]
    price     = float(last["close"])
    atr_value = float(last.get("atr14", 0.0)) if pd.notna(last.get("atr14")) else 0.0
    signal    = int(last["signal"])

    logger.info(
        f"Sygnal [{strategy_name}] | signal={signal} "
        f"cena={price:.4f} atr={atr_value:.4f} "
        f"order_type={ORDER_TYPE}"
    )

    # 4. Stan pozycji + bot-managed TSL (watermark)
    position = get_current_position()
    if position:
        _update_tsl_bot_managed(position)

    # 5. Cooldown check (zanim otworzymy nowa pozycje)
    can_open = _cooldown_ok()

    # 6. Logika otwierania/zamykania
    if signal == 1 and (not position or position["side"] == "Sell"):
        if position:
            close_ts = int(time.time() * 1000)
            order_id = close_position(position)
            if order_id:
                fetch_and_report_closed_pnl(order_id, close_ts, reason="signal_close")
        if can_open:
            open_position("Buy", price, atr_value)

    elif signal == -1 and (not position or position["side"] == "Buy"):
        if position:
            close_ts = int(time.time() * 1000)
            order_id = close_position(position)
            if order_id:
                fetch_and_report_closed_pnl(order_id, close_ts, reason="signal_close")
        if can_open:
            open_position("Sell", price, atr_value)

    else:
        logger.info("Brak sygnalu  - nic nie robimy")
