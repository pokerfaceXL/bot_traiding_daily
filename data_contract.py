"""
Powtarzalny kontrakt danych OHLCV (F003): cache per symbol/interwal/zakres UTC,
filtr tylko zamknietych swiec, wykrywanie luk i warm-up, manifest z checksuma
i raportem pokrycia. Zero cichego zastepowania brakujacych danych zerami/ffill —
luki poza dozwolonym progiem konczy sie wyjatkiem, chyba ze wywolujacy jawnie
je zaakceptuje.

Modul nie wykonuje polaczen sieciowych. Przyjmuje juz pobrany DataFrame
(np. z strategy.get_bybit_ohlcv) i egzekwuje kontrakt jakosci + cache na dysku.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone

import pandas as pd

INTERVAL_MINUTES = {
    "1": 1, "3": 3, "5": 5, "15": 15, "30": 30,
    "60": 60, "120": 120, "240": 240, "360": 360, "720": 720,
    "D": 1440, "W": 10080,
}

DEFAULT_CACHE_DIR = "data_cache"


class DataContractError(Exception):
    """Naruszenie kontraktu danych (brak/uszkodzony cache, luki, format)."""


class DataGapError(DataContractError):
    """Wykryto luke w danych, ktora nie zostala jawnie zaakceptowana."""


def _interval_minutes(interval: str) -> int:
    if interval not in INTERVAL_MINUTES:
        raise DataContractError(f"Nieznany interwal: {interval!r}")
    return INTERVAL_MINUTES[interval]


def _to_utc(ts) -> pd.Timestamp:
    t = pd.Timestamp(ts)
    if t.tzinfo is None:
        return t.tz_localize("UTC")
    return t.tz_convert("UTC")


@dataclass
class Gap:
    after: pd.Timestamp
    before: pd.Timestamp
    missing_bars: int

    def to_dict(self) -> dict:
        return {
            "after": self.after.isoformat(),
            "before": self.before.isoformat(),
            "missing_bars": self.missing_bars,
        }


@dataclass
class DataManifest:
    symbol: str
    interval: str
    requested_start: pd.Timestamp
    requested_end: pd.Timestamp
    actual_start: pd.Timestamp | None
    actual_end: pd.Timestamp | None
    row_count: int
    expected_bars: int
    coverage_pct: float
    gaps: list[Gap]
    dropped_unclosed_bars: int
    warmup_bars: int
    checksum_sha256: str
    generated_at: pd.Timestamp = field(default_factory=lambda: pd.Timestamp.now(tz="UTC"))

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "interval": self.interval,
            "requested_start": self.requested_start.isoformat(),
            "requested_end": self.requested_end.isoformat(),
            "actual_start": self.actual_start.isoformat() if self.actual_start is not None else None,
            "actual_end": self.actual_end.isoformat() if self.actual_end is not None else None,
            "row_count": self.row_count,
            "expected_bars": self.expected_bars,
            "coverage_pct": round(self.coverage_pct, 4),
            "gaps": [g.to_dict() for g in self.gaps],
            "dropped_unclosed_bars": self.dropped_unclosed_bars,
            "warmup_bars": self.warmup_bars,
            "checksum_sha256": self.checksum_sha256,
            "generated_at": self.generated_at.isoformat(),
        }


def filter_closed_candles(df: pd.DataFrame, interval: str, now: pd.Timestamp | None = None) -> tuple[pd.DataFrame, int]:
    """Odrzuca swiece, ktorych czas zamkniecia (open_time + interwal) jest po `now`.

    Rozbieznosc #5 z F001: backtest musial jawnie odrzucac biezaca, niezamknieta
    swiece zamiast liczyc na to, ze zrodlo danych juz to zrobilo.
    """
    if df.empty:
        return df, 0
    minutes = _interval_minutes(interval)
    now = _to_utc(now) if now is not None else pd.Timestamp.now(tz="UTC")
    idx = df.index
    if idx.tz is None:
        idx = idx.tz_localize("UTC")
    close_time = idx + pd.Timedelta(minutes=minutes)
    keep = close_time <= now
    dropped = int((~keep).sum())
    return df.loc[keep].copy(), dropped


def detect_gaps(df: pd.DataFrame, interval: str) -> list[Gap]:
    """Wykrywa dziury we wspolnej sekwencji swiec (brakujace bary miedzy istniejacymi)."""
    if len(df) < 2:
        return []
    minutes = _interval_minutes(interval)
    step = pd.Timedelta(minutes=minutes)
    idx = df.index
    if idx.tz is None:
        idx = idx.tz_localize("UTC")
    gaps: list[Gap] = []
    diffs = idx.to_series().diff().iloc[1:]
    for prev_ts, delta in zip(idx[:-1], diffs):
        if delta > step:
            missing = int(delta / step) - 1
            gaps.append(Gap(after=prev_ts, before=prev_ts + delta, missing_bars=missing))
    return gaps


def split_warmup(df: pd.DataFrame, warmup_bars: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Dzieli dane na (warmup, usable). Bary warm-up sluza tylko do liczenia
    wskaznikow — nie moga generowac sygnalow/wejsc w backteście."""
    if warmup_bars < 0:
        raise DataContractError("warmup_bars nie moze byc ujemne")
    if warmup_bars >= len(df):
        return df.copy(), df.iloc[0:0].copy()
    return df.iloc[:warmup_bars].copy(), df.iloc[warmup_bars:].copy()


def _checksum(df: pd.DataFrame) -> str:
    payload = df.to_csv(index=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_manifest(
    symbol: str,
    interval: str,
    df: pd.DataFrame,
    requested_start,
    requested_end,
    warmup_bars: int = 0,
    dropped_unclosed_bars: int = 0,
) -> DataManifest:
    req_start = _to_utc(requested_start)
    req_end = _to_utc(requested_end)
    minutes = _interval_minutes(interval)
    expected_bars = max(int((req_end - req_start) / pd.Timedelta(minutes=minutes)), 0)
    gaps = detect_gaps(df, interval)
    coverage_pct = (len(df) / expected_bars * 100) if expected_bars > 0 else (100.0 if len(df) else 0.0)
    idx = df.index
    if len(df) and idx.tz is None:
        idx = idx.tz_localize("UTC")
    return DataManifest(
        symbol=symbol,
        interval=interval,
        requested_start=req_start,
        requested_end=req_end,
        actual_start=idx.min() if len(df) else None,
        actual_end=idx.max() if len(df) else None,
        row_count=len(df),
        expected_bars=expected_bars,
        coverage_pct=coverage_pct,
        gaps=gaps,
        dropped_unclosed_bars=dropped_unclosed_bars,
        warmup_bars=warmup_bars,
        checksum_sha256=_checksum(df),
    )


def enforce_no_silent_gaps(manifest: DataManifest, allow_gaps: bool = False) -> None:
    """Domyslnie luka w danych jest bledem twardym — zabrania cichego
    wypelniania brakujacych barow zerami. Wywolujacy musi jawnie ustawic
    allow_gaps=True (i osobno zdecydowac jak traktuje luke), by kontynuowac."""
    if manifest.gaps and not allow_gaps:
        total_missing = sum(g.missing_bars for g in manifest.gaps)
        raise DataGapError(
            f"{manifest.symbol} {manifest.interval}: {len(manifest.gaps)} luk, "
            f"{total_missing} brakujacych barow, pokrycie {manifest.coverage_pct:.2f}%. "
            "Brakujace dane wykluczaja wynik z rankingu, dopoki nie sa jawnie zaakceptowane."
        )


def _dataset_paths(cache_dir: str, symbol: str, interval: str, start, end) -> tuple[str, str]:
    start_s = _to_utc(start).strftime("%Y%m%dT%H%M%SZ")
    end_s = _to_utc(end).strftime("%Y%m%dT%H%M%SZ")
    base = os.path.join(cache_dir, f"{symbol}_{interval}_{start_s}_{end_s}")
    return base + ".csv", base + ".manifest.json"


def save_dataset(
    cache_dir: str,
    symbol: str,
    interval: str,
    start,
    end,
    df: pd.DataFrame,
    manifest: DataManifest,
) -> tuple[str, str]:
    os.makedirs(cache_dir, exist_ok=True)
    csv_path, manifest_path = _dataset_paths(cache_dir, symbol, interval, start, end)
    df.to_csv(csv_path, index=True)
    with open(manifest_path, "w") as f:
        json.dump(manifest.to_dict(), f, indent=2, sort_keys=True)
    return csv_path, manifest_path


def load_dataset(cache_dir: str, symbol: str, interval: str, start, end) -> tuple[pd.DataFrame, DataManifest]:
    """Wczytuje dataset+manifest z cache. Weryfikuje checksume — cache
    niespojny z manifestem to blad twardy, nie ciche przeliczenie."""
    csv_path, manifest_path = _dataset_paths(cache_dir, symbol, interval, start, end)
    if not os.path.exists(csv_path) or not os.path.exists(manifest_path):
        raise DataContractError(
            f"Brak cache dla {symbol}/{interval}/{start}..{end} — uruchom pobranie i build_manifest jawnie."
        )
    df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
    with open(manifest_path) as f:
        raw = json.load(f)
    checksum = _checksum(df)
    if checksum != raw["checksum_sha256"]:
        raise DataContractError(
            f"Checksuma cache {csv_path} nie zgadza sie z manifestem "
            f"({checksum} != {raw['checksum_sha256']}) — dane uszkodzone lub zmienione recznie."
        )
    manifest = DataManifest(
        symbol=raw["symbol"],
        interval=raw["interval"],
        requested_start=pd.Timestamp(raw["requested_start"]),
        requested_end=pd.Timestamp(raw["requested_end"]),
        actual_start=pd.Timestamp(raw["actual_start"]) if raw["actual_start"] else None,
        actual_end=pd.Timestamp(raw["actual_end"]) if raw["actual_end"] else None,
        row_count=raw["row_count"],
        expected_bars=raw["expected_bars"],
        coverage_pct=raw["coverage_pct"],
        gaps=[Gap(after=pd.Timestamp(g["after"]), before=pd.Timestamp(g["before"]), missing_bars=g["missing_bars"]) for g in raw["gaps"]],
        dropped_unclosed_bars=raw["dropped_unclosed_bars"],
        warmup_bars=raw["warmup_bars"],
        checksum_sha256=raw["checksum_sha256"],
        generated_at=pd.Timestamp(raw["generated_at"]),
    )
    return df, manifest


def build_dataset(
    symbol: str,
    interval: str,
    raw_df: pd.DataFrame,
    start,
    end,
    warmup_bars: int = 0,
    now: pd.Timestamp | None = None,
    cache_dir: str = DEFAULT_CACHE_DIR,
    allow_gaps: bool = False,
    persist: bool = True,
) -> tuple[pd.DataFrame, DataManifest]:
    """Pojedynczy punkt wejscia kontraktu: filtruje zakres+zamkniete swiece,
    wykrywa luki, buduje manifest, egzekwuje brak cichych luk, opcjonalnie
    zapisuje do cache. Zwraca (usable_df_po_warmupie, manifest)."""
    start_utc, end_utc = _to_utc(start), _to_utc(end)
    idx = raw_df.index
    if idx.tz is None:
        idx = idx.tz_localize("UTC")
    scoped = raw_df.loc[(idx >= start_utc) & (idx <= end_utc)].copy()
    scoped.index = idx[(idx >= start_utc) & (idx <= end_utc)]

    closed, dropped = filter_closed_candles(scoped, interval, now=now)
    manifest = build_manifest(
        symbol, interval, closed, start_utc, end_utc,
        warmup_bars=warmup_bars, dropped_unclosed_bars=dropped,
    )
    enforce_no_silent_gaps(manifest, allow_gaps=allow_gaps)

    if persist:
        save_dataset(cache_dir, symbol, interval, start, end, closed, manifest)

    _, usable = split_warmup(closed, warmup_bars)
    return usable, manifest
