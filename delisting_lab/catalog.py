"""Build the F012-C02 delisting event catalog (Bybit + Binance) from cached raw JSON.

Timestamp rules (pre-registered, see ticket):
- Bybit: `dateTimestamp` is the article's displayed date (matches page `date`).
  `publishTime` is sometimes the real push time (small positive/negative gap) and
  sometimes a later edit (gap of days). If |publishTime - dateTimestamp| <= 6h:
  announcement_ts = min(both), first_publicly_observable_ts = max(both).
  Otherwise both = dateTimestamp and `ts_flag` notes the discarded publishTime.
- Binance: CMS `releaseDate` == detail `publishDate` (ms) — used for both.
- effective_ts is parsed from title/description/body text, never day-rounded titles,
  and cross-checked against instrument deliveryTime/deliveryDate where available.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

RAW = Path("data_cache/f012_c02/raw")
TRAIN1_LO = pd.Timestamp("2024-03-01", tz="UTC")
TRAIN1_HI = pd.Timestamp("2025-03-01", tz="UTC")
PUBLISH_GAP_MAX_MS = 6 * 3600 * 1000

MONTHS = {m: i + 1 for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}

_MON = r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?"
_HM = r"(\d{1,2})(?::(\d{2}))?\s*(AM|PM)"
# "Mar 17, 2025, 9:00AM UTC"
PAT_A = re.compile(_MON + r"\s+(\d{1,2}),?\s+(\d{4}),?\s+(?:at\s+)?" + _HM + r"\s*\(?UTC\)?", re.I)
# "12AM UTC on Jun 7, 2024" / "8AM UTC on Mar 11, 2025"
PAT_B = re.compile(_HM + r"\s*\(?UTC\)?\s+on\s+" + _MON + r"\s+(\d{1,2}),?\s+(\d{4})", re.I)
# "2025-01-22 09:00 (UTC)"
PAT_C = re.compile(r"(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2})\s*\(UTC\)")


def _h24(h: str, m: str | None, ap: str) -> tuple[int, int]:
    hh = int(h) % 12 + (12 if ap.upper() == "PM" else 0)
    return hh, int(m or 0)


def _ms(y, mo, d, hh, mi) -> int:
    return int(datetime(int(y), int(mo), int(d), hh, mi, tzinfo=timezone.utc).timestamp() * 1000)


def parse_datetimes(text: str) -> list[tuple[int, int]]:
    """Return [(char_pos, ts_ms)] of every explicit UTC datetime in text, in order."""
    out = []
    for m in PAT_A.finditer(text):
        mon, d, y, h, mi, ap = m.groups()
        hh, mm = _h24(h, mi, ap)
        out.append((m.start(), _ms(y, MONTHS[mon[:3].lower()], d, hh, mm)))
    for m in PAT_B.finditer(text):
        h, mi, ap, mon, d, y = m.groups()
        hh, mm = _h24(h, mi, ap)
        out.append((m.start(), _ms(y, MONTHS[mon[:3].lower()], d, hh, mm)))
    for m in PAT_C.finditer(text):
        y, mo, d, hh, mi = m.groups()
        out.append((m.start(), _ms(y, mo, d, int(hh), int(mi))))
    return sorted(out)


def observable_times(date_ts: int, publish_ts: int | None) -> tuple[int, int, str]:
    """(announcement_ts, first_publicly_observable_ts, flag) per the rule in module doc."""
    if publish_ts is None:
        return date_ts, date_ts, "no_publishTime"
    gap = publish_ts - date_ts
    if abs(gap) <= PUBLISH_GAP_MAX_MS:
        return min(date_ts, publish_ts), max(date_ts, publish_ts), ""
    return date_ts, date_ts, f"publishTime_gap_{gap / 3.6e6:.1f}h_ignored"


PERP_SYM = re.compile(r"\b((?:1000+|10000+)?[0-9A-Z]{2,20}USDT)\b")


def perp_symbols(text: str) -> list[str]:
    seen = []
    for s in PERP_SYM.findall(text):
        if s not in seen and s != "USDT":
            seen.append(s)
    return seen


SETTLE_PAT = re.compile(
    r"(?:automatic settlement|automatic settlements|close all positions)[^\n]*?on (?:the )?(.*?)"
    r"(?:USDⓈ-M )?[Pp]erpetual [Cc]ontracts? at (\d{4}-\d{2}-\d{2} \d{2}:\d{2}) \(UTC\)")
POSTPONE_PAT = re.compile(
    r"postpone the delisting of the USDⓈ-M (\w+) Perpetual Contract to (\d{4}-\d{2}-\d{2} \d{2}:\d{2}) \(UTC\)")
SPOT_CEASE_PAT = re.compile(
    r"cease trading on all (?:spot )?trading pairs for the following token\(s\) at "
    r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}) \(UTC\):\s*\n(.*?)\n\s*\n?(?:Please|Note|The exact)", re.S)
NOT_AFFECTED_PAT = re.compile(r"USDⓈ-M ([\w ,and]+?) Perpetual Contracts? trading is not affected")


def _c_ms(s: str) -> int:
    return _ms(s[0:4], s[5:7], s[8:10], int(s[11:13]), int(s[14:16]))


def binance_article_events(title: str, text: str) -> dict:
    """Parse one Binance CMS-161 article → {category, perps:[(sym, eff_ms)], spot_tokens, ...}."""
    t = title
    res = {"category": "other", "perps": [], "spot_tokens": [], "spot_eff": None,
           "perp_not_affected": [], "postpone": []}
    if re.search(r"Notice of Removal of (Spot|Margin) Trading Pairs|Margin|Earn|Loans", t) and "Futures" not in t:
        res["category"] = "pair_or_product_removal"
        return res
    for m in POSTPONE_PAT.finditer(text):
        res["postpone"].append((m.group(1), _c_ms(m.group(2))))
    if res["postpone"] or "Postpone" in t:
        res["category"] = "revision"
        return res
    for m in SETTLE_PAT.finditer(text):
        syms = perp_symbols(m.group(1))
        if "Coin-M" in m.group(0) or "COIN-M" in m.group(0):
            continue
        for s in syms:
            if s not in [p[0] for p in res["perps"]]:
                res["perps"].append((s, _c_ms(m.group(2))))
    sc = SPOT_CEASE_PAT.search(text)
    if sc:
        res["spot_eff"] = _c_ms(sc.group(1))
        res["spot_tokens"] = re.findall(r"\(([0-9A-Z]+)\)", sc.group(2))
    for m in NOT_AFFECTED_PAT.finditer(text):
        res["perp_not_affected"] += perp_symbols(m.group(1))
    if "COIN-M" in t and not res["perps"]:
        res["category"] = "coinm_perp_delist"
    elif "Futures Will Delist" in t:
        res["category"] = "perp_delist"
    elif "Will Delist" in t or sc:
        res["category"] = "token_delist"
    elif "Delisting Date" in t:
        res["category"] = "revision"
    return res


def bybit_article_events(title: str, desc: str, text: str) -> dict:
    res = {"category": "other", "perps": [], "spot_tokens": [], "spot_eff": None}
    full = f"{title}\n{desc}\n{text}"
    if re.search(r"Leveraged\s+Tokens?", title):
        res["category"] = "leveraged_token"
        return res
    if re.search(r"Relisting|Cease Support|Network", title):
        res["category"] = "other"
        return res
    if re.search(r"Spot Pair|/EUR|/BRL|/TRY", title):
        res["category"] = "pair_or_product_removal"
        return res
    if "Perpetual" in title:
        res["category"] = "perp_delist"
        dts = parse_datetimes(desc) or parse_datetimes(text)
        eff = dts[0][1] if dts else None
        for s in perp_symbols(title + " " + desc):
            res["perps"].append((s, eff))
        return res
    pairs = re.findall(r"\b([0-9A-Z]{1,20})/USDT\b", full)
    if pairs:
        res["category"] = "token_delist"
        res["spot_tokens"] = list(dict.fromkeys(pairs))
        m = re.search(r"Spot[^\n]*\n?[^\n]*?(?:no longer be supported|will no longer)[^\n]*", text)
        dts = parse_datetimes(m.group(0)) if m else []
        if not dts:
            dts = parse_datetimes(desc + "\n" + text)
        res["spot_eff"] = dts[0][1] if dts else None
    return res


# Ticker migration / merger / rebrand delistings (token continues under a new ticker).
# Curated from public knowledge + article text; used ONLY as a robustness split, never
# to define the primary sample.
MIGRATION_BASES = {
    "STRAX": "token swap (article text)",
    "FET": "ASI merger (article text)", "AGIX": "ASI merger (article text)",
    "OCEAN": "ASI merger (article text)",
    "RNDR": "RNDR->RENDER ticker migration", "GAL": "GAL->G (Gravity) rebrand",
    "KLAY": "KLAY->KAIA merger", "FTM": "FTM->S (Sonic) migration",
    "DAR": "DAR->D rebrand", "LIT": "LIT->HEI (Heima) rebrand",
    "BNX": "BNX->FOUR rebrand", "RON": "RON->RONIN ticker change",
}


# Binance composite-index perps (no underlying token / spot market)
INDEX_BASES = {"FOOTBALL", "BLUEBIRD", "BTCDOM", "DEFI"}


def _base(sym: str) -> str:
    b = sym[:-4] if sym.endswith("USDT") else sym
    return re.sub(r"^(1000000|100000|10000|1000)", "", b)


def build_catalog() -> pd.DataFrame:
    by_ann = json.loads((RAW / "bybit_announcements.json").read_text())
    by_body = json.loads((RAW / "bybit_bodies.json").read_text())
    bn_list = json.loads((RAW / "binance_cms161_list.json").read_text())
    bn_body = json.loads((RAW / "binance_bodies.json").read_text())
    by_instr = {s["symbol"]: s for s in json.loads((RAW / "bybit_linear_instruments.json").read_text())
                if s["contractType"] == "LinearPerpetual"}
    bn_instr = {s["symbol"]: s for s in json.loads((RAW / "binance_um_exchangeinfo.json").read_text())}

    rows, articles = [], []
    # ---------------- Bybit ----------------
    for a in by_ann:
        if a["url"] not in by_body:
            continue
        ann, obs, flag = observable_times(a["dateTimestamp"], a.get("publishTime"))
        body = by_body[a["url"]]["text"]
        p = bybit_article_events(a["title"], a.get("description", ""), body)
        cid = "BYBIT-" + a["url"].rstrip("/").split("-")[-1]
        articles.append(dict(exchange="bybit", cluster_id=cid, title=a["title"], category=p["category"],
                             announcement_ts=ann, url=a["url"], n_perps=len(p["perps"]),
                             n_spot_tokens=len(p["spot_tokens"])))
        common = dict(exchange="bybit", announcement_cluster_id=cid, source_url=a["url"], source_id=cid,
                      title=a["title"], announcement_ts=ann, first_publicly_observable_ts=obs,
                      bybit_dateTimestamp=a["dateTimestamp"], bybit_publishTime=a.get("publishTime"),
                      ts_flag=flag, category=p["category"])
        for sym, eff in p["perps"]:
            ins = by_instr.get(sym, {})
            dt = int(ins.get("deliveryTime") or 0) or None
            rows.append(dict(common, symbol=sym, base=_base(sym), contract_type="linear_perp",
                             effective_ts=eff, effective_ts_instrument=dt,
                             spot_also_delisted_same_article=False))
        for tok in p["spot_tokens"]:
            sym = tok + "USDT"
            ins = by_instr.get(sym)
            perp_live = bool(ins) and int(ins["launchTime"]) < ann and (
                ins["status"] == "Trading" or int(ins.get("deliveryTime") or 0) > ann)
            rows.append(dict(common, symbol=tok + "/USDT", base=tok, contract_type="spot",
                             effective_ts=p["spot_eff"], effective_ts_instrument=None,
                             same_venue_perp_live_at_announcement=perp_live,
                             spot_also_delisted_same_article=True))
    # ---------------- Binance ----------------
    postpones = {}
    for a in bn_list:
        if a["code"] not in bn_body:
            continue
        b = bn_body[a["code"]]
        p = binance_article_events(a["title"], b["text"])
        ann = int(a["releaseDate"])
        cid = "BINANCE-" + str(a["id"])
        articles.append(dict(exchange="binance", cluster_id=cid, title=a["title"], category=p["category"],
                             announcement_ts=ann, url="https://www.binance.com/en/support/announcement/" + a["code"],
                             n_perps=len(p["perps"]), n_spot_tokens=len(p["spot_tokens"])))
        for s, e in p["postpone"]:
            postpones.setdefault(s, []).append((ann, e))
        common = dict(exchange="binance", announcement_cluster_id=cid,
                      source_url="https://www.binance.com/en/support/announcement/" + a["code"],
                      source_id=a["code"], title=a["title"], announcement_ts=ann,
                      first_publicly_observable_ts=ann, ts_flag="", category=p["category"])
        perp_bases = {_base(s) for s, _ in p["perps"]}
        for sym, eff in p["perps"]:
            ins = bn_instr.get(sym, {})
            rows.append(dict(common, symbol=sym, base=_base(sym), contract_type="linear_perp",
                             effective_ts=eff, effective_ts_instrument=ins.get("deliveryDate"),
                             spot_also_delisted_same_article=_base(sym) in set(p["spot_tokens"])))
        for tok in p["spot_tokens"]:
            sym = tok + "USDT"
            ins = bn_instr.get(sym)
            live = bool(ins) and int(ins["onboardDate"]) < ann and (
                ins["status"] == "TRADING" or int(ins.get("deliveryDate") or 0) > ann)
            rows.append(dict(common, symbol=tok + "/USDT", base=tok, contract_type="spot",
                             effective_ts=p["spot_eff"], effective_ts_instrument=None,
                             same_venue_perp_live_at_announcement=live and tok not in perp_bases,
                             perp_explicitly_not_affected=sym in p["perp_not_affected"],
                             spot_also_delisted_same_article=True))

    df = pd.DataFrame(rows)
    df["effective_ts_announced"] = df["effective_ts"]
    df["effective_revised"] = False
    for s, lst in postpones.items():
        m = (df.exchange == "binance") & (df.symbol == s) & (df.contract_type == "linear_perp")
        last = max(lst)[1]
        df.loc[m, "effective_ts"] = last
        df.loc[m, "effective_revised"] = True
    for c in ("announcement_ts", "first_publicly_observable_ts", "effective_ts", "effective_ts_announced",
              "effective_ts_instrument"):
        df[c] = pd.to_datetime(pd.to_numeric(df[c], errors="coerce"), unit="ms", utc=True)
    df["notice_duration_h"] = (df.effective_ts - df.announcement_ts).dt.total_seconds() / 3600
    df["observability_lag_s"] = (df.first_publicly_observable_ts - df.announcement_ts).dt.total_seconds()
    df["in_train1"] = (df.announcement_ts >= TRAIN1_LO) & (df.announcement_ts < TRAIN1_HI)
    # Delivery-time cross-check (minutes difference; NaN when venue no longer reports it)
    df["eff_vs_instrument_min"] = (df.effective_ts_instrument - df.effective_ts).dt.total_seconds() / 60
    df = df.sort_values(["announcement_ts", "exchange", "symbol"]).reset_index(drop=True)
    df["event_id"] = (df.exchange.str.upper() + "-" + df.announcement_ts.dt.strftime("%Y%m%d%H%M") + "-"
                      + df.symbol.str.replace("/", ""))
    # Conservative day-batch cluster: same exchange, announcements within 2h of each other
    df["day_batch_cluster_id"] = ""
    for ex, g in df.groupby("exchange"):
        g = g.sort_values("announcement_ts")
        cur, last, k = None, None, 0
        for i, r in g.iterrows():
            if last is None or (r.announcement_ts - last).total_seconds() > 7200:
                k += 1
                cur = f"{ex.upper()}-B{k:03d}"
            df.at[i, "day_batch_cluster_id"] = cur
            last = r.announcement_ts
    _cross_venue(df)
    df["migration_note"] = df.base.map(MIGRATION_BASES).fillna("")
    df["migration_flag"] = df.migration_note != ""
    df["index_contract"] = df.base.isin(INDEX_BASES)
    return df, pd.DataFrame(articles)


def _cross_venue(df: pd.DataFrame) -> None:
    """Earliest prior delisting announcement of the same base token on the OTHER venue (≤30d)."""
    nat = pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns, UTC]")
    df["prior_other_venue_ann_ts"] = nat
    df["prior_same_venue_spot_ann_ts"] = nat.copy()
    for i, r in df.iterrows():
        other = df[(df.base == r.base) & (df.exchange != r.exchange) & (df.announcement_ts < r.announcement_ts)
                   & (df.announcement_ts >= r.announcement_ts - pd.Timedelta(days=30))]
        if len(other):
            df.at[i, "prior_other_venue_ann_ts"] = other.announcement_ts.min()
        same = df[(df.base == r.base) & (df.exchange == r.exchange) & (df.contract_type == "spot")
                  & (df.announcement_ts < r.announcement_ts)
                  & (df.announcement_ts >= r.announcement_ts - pd.Timedelta(days=30))]
        if len(same):
            df.at[i, "prior_same_venue_spot_ann_ts"] = same.announcement_ts.min()
    df["follower_event"] = df.prior_other_venue_ann_ts.notna()
