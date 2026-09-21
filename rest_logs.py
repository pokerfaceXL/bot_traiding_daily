import logging
import requests
import json
import urllib.parse

_log = logging.getLogger("bot_logger")


def report_bot_alive(bot_id, bot_name, p_type):
    url = "https://g6005f98fc66f55-boty.adb.eu-frankfurt-1.oraclecloudapps.com/ords/boty/lorenzian/heart_beat/"

    headers = {
        "p_bot_id"  : str(bot_id),
        "p_bot_name": bot_name,
        "p_type"    : str(p_type),
    }

    try:
        response = requests.post(url, headers=headers, timeout=5)
        if response.status_code != 200:
            _log.warning(f"report_bot_alive HTTP {response.status_code}: {response.text[:200]}")
    except Exception as e:
        _log.warning(f"report_bot_alive failed: {e}")


def send_bot_config_to_apex(bot_id, bot_name, config):
    url = "https://g6005f98fc66f55-boty.adb.eu-frankfurt-1.oraclecloudapps.com/ords/boty/lorenzian/bot_config/"

    headers = {
        "p_bot_id":   str(bot_id),
        "p_bot_name": bot_name,
    }
    try:
        resp = requests.post(url, headers=headers, json=config, timeout=10)
        if not resp.ok:
            _log.warning(f"send_bot_config_to_apex HTTP {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        _log.warning(f"send_bot_config_to_apex failed: {e}")


def send_last_closed_to_apex(p_closed_position, close_reason, bot_id, bot_name):
    url = "https://g6005f98fc66f55-boty.adb.eu-frankfurt-1.oraclecloudapps.com/ords/boty/lorenzian/closed_position/"

    headers = {
        "p_closed_position": json.dumps(p_closed_position),
        "p_stop_loss":       str(close_reason),   # naglowek zgodny z APEX endpoint
        "p_bot_name":        bot_name,
        "p_bot_id":          str(bot_id),
    }
    try:
        resp = requests.post(url, headers=headers, timeout=10)
        if not resp.ok:
            _log.error(f"send_last_closed_to_apex HTTP {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        _log.error(f"send_last_closed_to_apex failed: {e}")


def send_equity_halt_to_apex(bot_id, bot_name, equity_data):
    url = "https://g6005f98fc66f55-boty.adb.eu-frankfurt-1.oraclecloudapps.com/ords/boty/lorenzian/equity_halt/"
    headers = {
        "p_bot_id":      str(bot_id),
        "p_bot_name":    bot_name,
        "p_equity_data": json.dumps(equity_data),
    }
    try:
        resp = requests.post(url, headers=headers, timeout=10)
        if not resp.ok:
            _log.error(f"send_equity_halt_to_apex HTTP {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        _log.error(f"send_equity_halt_to_apex failed: {e}")


def _sanitize_header(value: str, max_len: int = 4000) -> str:
    """Usuwa znaki niedozwolone w naglowkach HTTP (newliny, non-latin1)."""
    value = value.replace("\r\n", " ").replace("\n", " ").replace("\r", " ")
    return value.encode("latin-1", errors="replace").decode("latin-1")[:max_len]


def send_error_to_apex(bot_id, bot_name, error_message):
    url = "https://g6005f98fc66f55-boty.adb.eu-frankfurt-1.oraclecloudapps.com/ords/boty/lorenzian/bot_error/"
    headers = {
        "p_bot_id":        str(bot_id),
        "p_bot_name":      bot_name,
        "p_error_message": _sanitize_header(str(error_message)),
    }
    try:
        resp = requests.post(url, headers=headers, timeout=5)
        if not resp.ok:
            _log.warning(f"send_error_to_apex HTTP {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        _log.warning(f"send_error_to_apex failed: {e}")


def send_backtest_result_to_apex(p_json, bot_id, bot_name, optimization=False):
    url = "https://g6005f98fc66f55-boty.adb.eu-frankfurt-1.oraclecloudapps.com/ords/boty/lorenzian_backtest/backtest_result/"
    headers = {
        "Content-Type":   "application/json",
        "p_bot_name":     bot_name,
        "p_bot_id":       str(bot_id),
        "p_optimization": "1" if optimization else "0",
    }
    try:
        resp = requests.post(url, headers=headers, json=p_json, timeout=30)
        if not resp.ok:
            _log.error(f"send_backtest_result_to_apex HTTP {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        _log.error(f"send_backtest_result_to_apex failed: {e}")

