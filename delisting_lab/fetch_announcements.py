"""Fetch + cache delisting announcement lists and bodies (Bybit API, Binance CMS 161).

Raw JSON lands under data_cache/f012_c02/raw/ (git-ignored). Bodies are fetched for
articles in a padded Train-1 window only.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

import requests

RAW = Path("data_cache/f012_c02/raw")
H = {"User-Agent": "Mozilla/5.0"}
WIN_LO_MS = 1706745600000  # 2024-02-01 (pad before Train-1)
WIN_HI_MS = 1741132800000  # 2025-03-05


def _get(url, params=None, tries=6):
    for k in range(tries):
        try:
            r = requests.get(url, params=params, headers=H, timeout=30)
            if r.status_code == 200:
                return r
        except requests.RequestException:
            pass
        time.sleep(4 * (k + 1))
    raise RuntimeError(f"fetch failed {url} {params}")


def binance_node_text(node) -> str:
    """Flatten Binance CMS body node-tree JSON into plain text (block-separated)."""
    if isinstance(node, str):
        node = json.loads(node)
    out: list[str] = []

    def walk(n):
        if n.get("node") == "text":
            out.append(n.get("text", ""))
        for c in n.get("child", []) or []:
            walk(c)
        if n.get("tag") in ("p", "h1", "h2", "h3", "li", "tr", "td", "br", "div"):
            out.append("\n" if n.get("tag") != "td" else " | ")

    walk(node)
    txt = "".join(out).replace("&nbsp;", " ").replace("&amp;", "&")
    return re.sub(r"[ \t]+", " ", txt)


def html_text(html: str) -> str:
    html = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
    html = re.sub(r"(?i)<br\s*/?>|</p>|</li>|</tr>|</h\d>", "\n", html)
    html = re.sub(r"(?s)<[^>]+>", " ", html)
    for a, b in (("&nbsp;", " "), ("&amp;", "&"), ("&#x27;", "'"), ("&quot;", '"'), ("&lt;", "<"), ("&gt;", ">")):
        html = html.replace(a, b)
    return re.sub(r"[ \t]+", " ", html)


def fetch_binance_bodies():
    lst = json.loads((RAW / "binance_cms161_list.json").read_text())
    out_p = RAW / "binance_bodies.json"
    cache = json.loads(out_p.read_text()) if out_p.exists() else {}
    for a in lst:
        if not (WIN_LO_MS <= a["releaseDate"] < WIN_HI_MS) or a["code"] in cache:
            continue
        d = _get("https://www.binance.com/bapi/composite/v1/public/cms/article/detail/query",
                 {"articleCode": a["code"]}).json()["data"]
        cache[a["code"]] = {"title": d["title"], "publishDate": d["publishDate"],
                            "text": binance_node_text(d["body"])}
        out_p.write_text(json.dumps(cache))
        time.sleep(1.5)
    return cache


def bybit_doc_text(node) -> str:
    """Flatten Bybit article content.json (Contentstack rich text) into plain text."""
    out: list[str] = []

    def walk(n):
        if "text" in n and isinstance(n["text"], str):
            out.append(n["text"])
        for c in n.get("children", []) or []:
            walk(c)
        if n.get("type") in ("p", "h1", "h2", "h3", "h4", "li", "tr"):
            out.append("\n")
        elif n.get("type") == "td":
            out.append(" | ")

    walk(node)
    return re.sub(r"[ \t]+", " ", "".join(out))


def bybit_article_text(url: str) -> dict:
    html = _get(url).text
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    d = json.loads(m.group(1))["props"]["pageProps"]["articleDetail"]
    return {"page_date": d.get("date"), "text": bybit_doc_text(d["content"]["json"])}


def fetch_bybit_bodies():
    lst = json.loads((RAW / "bybit_announcements.json").read_text())
    out_p = RAW / "bybit_bodies.json"
    cache = json.loads(out_p.read_text()) if out_p.exists() else {}
    for a in lst:
        if not (WIN_LO_MS <= a["dateTimestamp"] < WIN_HI_MS) or a["url"] in cache:
            continue
        cache[a["url"]] = bybit_article_text(a["url"])
        out_p.write_text(json.dumps(cache))
        time.sleep(1.0)
    return cache


if __name__ == "__main__":
    print("binance", len(fetch_binance_bodies()))
    print("bybit", len(fetch_bybit_bodies()))


def fetch_instruments():
    """Bybit linear instruments (Trading+Closed, paginated) and Binance USD-M exchangeInfo."""
    rows = []
    for st in ("Trading", "Closed"):
        cur = ""
        while True:
            p = {"category": "linear", "status": st, "limit": 1000}
            if cur:
                p["cursor"] = cur
            r = _get("https://api.bybit.com/v5/market/instruments-info", p).json()["result"]
            rows += r["list"]
            cur = r.get("nextPageCursor") or ""
            if not cur or not r["list"]:
                break
            time.sleep(0.3)
    (RAW / "bybit_linear_instruments.json").write_text(json.dumps(rows))
    bn = _get("https://fapi.binance.com/fapi/v1/exchangeInfo").json()["symbols"]
    (RAW / "binance_um_exchangeinfo.json").write_text(json.dumps(bn))
    sp = _get("https://api.bybit.com/v5/market/instruments-info", {"category": "spot"}).json()["result"]["list"]
    (RAW / "bybit_spot_instruments.json").write_text(json.dumps(sp))
    return len(rows), len(bn), len(sp)
