"""
Dzienna/miesieczna regularnosc equity curve (F005, fala 2).

Standalone modul, ten sam wzorzec co costs.py/equity.py/execution.py (F004):
czyste funkcje na juz gotowych danych, zero polaczen sieciowych, zero
importu strategy.py/backtest_apex.py/backtest_engine.py/main.py/trader.py/
configuration/. Wejsciem jest gotowa mark-to-market equity curve (np.
backtest_engine.BacktestResult.equity_curve) — ten modul jej nie liczy.

Kontrakt z spec/build.md ("Decyzje i granice pracy" / "Cel regularności i
tolerancja", cytowane dosłownie):

  "zmiana equity miedzy koncami dni (zrealizowany + niezrealizowany PnL,
  oplaty, funding), strefa Europe/Warsaw. Dni zerowe licza sie jako dni bez
  zysku; mianownik to wszystkie dni kalendarzowe pelnego miesiaca. Niepelne
  miesiace pokazywac osobno."

  "TARGET_POSITIVE_DAY_PCT = 100 (dzien dodatni = PnL netto > 0).
  DAILY_NONPROFIT_TOLERANCE_PCT = 20 ... N = dni kalendarzowe miesiaca;
  positive_day_pct = 100 x N_plus/N; deviation_pct = 100 x (N_minus +
  N_zero)/N. Cel spelniony, gdy deviation_pct <= 20 ... Brakujace dane
  uniewazniaja ocene miesiaca, nie licza sie jako zero."

Definicja "brakujacego dnia" uzyta ponizej: dzien, dla ktorego nie da sie
wyznaczyc PnL. To obejmuje dwa przypadki:
  1. Brak jakiegokolwiek znacznika equity w tym kalendarzowym dniu (Europe/
     Warsaw) -- realna luka w danych.
  2. Najwczesniejszy dzien calej krzywej equity -- nie ma dnia "przed nim",
     wiec zmiana wzgledem poprzedniego end-of-day jest z definicji
     nieznana. To nie jest luka w danych, to nieunikniona konsekwencja
     definicji "PnL = zmiana miedzy koncami dni" zastosowanej do pierwszego
     dnia jakiejkolwiek historii -- jesli ten dzien wypada w pelnym
     miesiacu, ten miesiac poprawnie staje sie nieoceniany (brakujace dane
     uniewazniaja ocene), zamiast po cichu liczyc go jako zero.

Gdy dzien jest brakujacy (przypadek 1, luka wewnatrz zakresu), kolejny dzien
z realnym znacznikiem equity liczy PnL wzgledem OSTATNIEGO znanego
znacznika (nie koniecznie dnia poprzedniego kalendarzowo) -- to doslowna
"zmiana miedzy KOLEJNYMI (istniejacymi) znacznikami end-of-day", nie
wymuszanie kalendarzowej ciaglosci. Sam brakujacy dzien i tak jest
klasyfikowany missing i uniewaznia swoj miesiac.

Niepelny miesiac (partial) != brakujacy dzien (missing). Niepelny to
miesiac, ktorego kalendarzowy zakres wykracza poza pierwszy/ostatni dzien
calej krzywej equity (np. krzywa zaczyna sie 15. dnia miesiaca) -- taki
miesiac ma N = faktyczna liczba dni pokrytych przez krzywa w tym miesiacu
(nie pelna dlugosc kalendarzowa), i jest oznaczony is_partial=True, zeby
raport nigdy nie porownal go z tolerancja 20% pelnego miesiaca bez
zaznaczenia tej roznicy.
"""

from __future__ import annotations

import calendar as _calendar
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

import pandas as pd

WARSAW_TZ = ZoneInfo("Europe/Warsaw")

TARGET_POSITIVE_DAY_PCT = 100.0
DAILY_NONPROFIT_TOLERANCE_PCT = 20.0


@dataclass
class DayResult:
    day: date  # kalendarzowy dzien, Europe/Warsaw
    equity: Optional[float]  # end-of-day equity, None gdy brak znacznika tego dnia
    pnl: Optional[float]  # zmiana wzgledem ostatniego znanego end-of-day, None gdy missing
    status: str  # "positive" | "non_positive" | "missing"


@dataclass
class MonthResult:
    year: int
    month: int
    n: int  # liczba dni objetych tabela dzienna dla tego miesiaca (patrz docstring modulu)
    n_positive: int
    n_nonpositive: int
    n_missing: int
    is_partial: bool
    is_valid: bool  # False, gdy n_missing > 0 -- ocena uniewazniona
    positive_day_pct: Optional[float]
    deviation_pct: Optional[float]
    target_met: Optional[bool]  # None, gdy is_valid=False (nieoceniany)


def daily_equity_snapshots(equity_curve: pd.DataFrame, tz: ZoneInfo = WARSAW_TZ) -> pd.Series:
    """
    End-of-day equity per kalendarzowy dzien `tz` -- ostatni dostepny znacznik w danym dniu.

    equity_curve: DataFrame z kolumna "equity", indeksowany znacznikami czasu
    (tz-aware lub tz-naive -- naive jest traktowany jako UTC, ten sam wzorzec
    co data_contract.py). Zwraca Series indeksowany datetime.date (Europe/
    Warsaw), posortowany rosnaco, bez dziur -- tylko dni z realnym danymi.
    """
    if equity_curve.empty:
        return pd.Series(dtype=float)

    idx = pd.DatetimeIndex(equity_curve.index)
    if idx.tz is None:
        idx = idx.tz_localize("UTC")
    idx_local = idx.tz_convert(tz)

    series = pd.Series(equity_curve["equity"].to_numpy(), index=idx_local).sort_index()
    daily = series.groupby(series.index.date).last()
    return daily


def classify_days(equity_curve: pd.DataFrame, tz: ZoneInfo = WARSAW_TZ) -> List[DayResult]:
    """
    Pelna kalendarzowa seria dni (Europe/Warsaw) od pierwszego do ostatniego dnia
    krzywej equity, wlacznie, kazdy dzien sklasyfikowany positive/non_positive/missing.

    Patrz docstring modulu co do dokladnej definicji "missing" i sposobu
    liczenia PnL po luce w danych.
    """
    daily = daily_equity_snapshots(equity_curve, tz)
    if daily.empty:
        return []

    first_day = daily.index.min()
    last_day = daily.index.max()
    all_days = [first_day + timedelta(days=i) for i in range((last_day - first_day).days + 1)]

    results: List[DayResult] = []
    last_known_equity: Optional[float] = None
    for day in all_days:
        if day in daily.index:
            equity = float(daily.loc[day])
            if last_known_equity is None:
                # Pierwszy realny znacznik calej krzywej -- brak dnia "przed nim".
                pnl = None
                status = "missing"
            else:
                pnl = equity - last_known_equity
                status = "positive" if pnl > 0 else "non_positive"
            last_known_equity = equity
        else:
            equity = None
            pnl = None
            status = "missing"
            # last_known_equity NIE resetuje sie -- kolejny realny dzien liczy
            # PnL wzgledem ostatniego znanego znacznika sprzed luki.
        results.append(DayResult(day=day, equity=equity, pnl=pnl, status=status))

    return results


def monthly_regularity(day_results: List[DayResult]) -> List[MonthResult]:
    """
    Grupuje DayResult po pelnym miesiacu kalendarzowym (Europe/Warsaw) i liczy
    positive_day_pct/deviation_pct/target_met per miesiac, wzor z build.md.

    is_partial=True, gdy zakres kalendarzowy miesiaca wykracza poza
    pierwszy/ostatni dzien `day_results` (miesiac obciety brzegiem krzywej).
    is_valid=False, gdy jakikolwiek dzien tego miesiaca jest missing --
    positive_day_pct/deviation_pct/target_met sa wtedy None (nieoceniane),
    nie liczone z missing potraktowanym jako zero.
    """
    if not day_results:
        return []

    first_day = day_results[0].day
    last_day = day_results[-1].day

    by_month: Dict[Tuple[int, int], List[DayResult]] = defaultdict(list)
    for d in day_results:
        by_month[(d.day.year, d.day.month)].append(d)

    results: List[MonthResult] = []
    for (year, month) in sorted(by_month.keys()):
        days = by_month[(year, month)]
        month_start = date(year, month, 1)
        month_end = date(year, month, _calendar.monthrange(year, month)[1])
        is_partial = month_start < first_day or month_end > last_day

        n = len(days)
        n_positive = sum(1 for d in days if d.status == "positive")
        n_nonpositive = sum(1 for d in days if d.status == "non_positive")
        n_missing = sum(1 for d in days if d.status == "missing")
        is_valid = n_missing == 0

        if is_valid and n > 0:
            positive_day_pct = 100.0 * n_positive / n
            deviation_pct = 100.0 * n_nonpositive / n
            target_met = deviation_pct <= DAILY_NONPROFIT_TOLERANCE_PCT
        else:
            positive_day_pct = None
            deviation_pct = None
            target_met = None

        results.append(
            MonthResult(
                year=year,
                month=month,
                n=n,
                n_positive=n_positive,
                n_nonpositive=n_nonpositive,
                n_missing=n_missing,
                is_partial=is_partial,
                is_valid=is_valid,
                positive_day_pct=positive_day_pct,
                deviation_pct=deviation_pct,
                target_met=target_met,
            )
        )

    return results


def compute_regularity(
    equity_curve: pd.DataFrame, tz: ZoneInfo = WARSAW_TZ
) -> Tuple[List[DayResult], List[MonthResult]]:
    """Orkiestrator: classify_days + monthly_regularity w jednym wywolaniu."""
    days = classify_days(equity_curve, tz)
    months = monthly_regularity(days)
    return days, months
