"""
Model kosztow realizacji zlecen OHLCV backtestu (F004, fala 1).

Zastepuje rozbieznosc #1 z spec/research/F001-current-state.md: obecny
_make_trade w strategy.py liczy pnl_usd = raw_pnl_pct * leverage * stake bez
zadnego odjecia prowizji/spreadu/poslizgu/fundingu. Ten modul dostarcza
czyste, deterministyczne funkcje kosztow do uzycia przez pozniejsze fale
(F004b equity/margin, F004c zegar wykonania) — nie modyfikuje ani nie
rozszerza strategy.py._make_trade.

Zero polaczen sieciowych. Wszystkie funkcje przyjmuja juz znane liczby
(notional, ceny, stawki) i zwracaja liczby — brak efektow ubocznych.

Konwencja znakow:
- commission / spread_cost / slippage_cost zwracaja nieujemny koszt (kwote
  do odjecia od gross pnl), niezaleznie od kierunku pozycji.
- funding_payment / funding_pnl zwracaja podpisany cash flow (ujemny =
  odplyw z konta, dodatni = wplyw), bo funding moze isc w obie strony
  zaleznie od znaku stawki i kierunku pozycji.
"""

from __future__ import annotations

from typing import Iterable, Tuple


def commission(notional: float, rate_bps: float) -> float:
    """Prowizja (taker lub maker — zalezne tylko od podanej stawki bps) od notional."""
    return abs(notional) * (rate_bps / 10_000.0)


def spread_cost(notional: float, half_spread_bps: float) -> float:
    """Koszt polowy spreadu, zawsze przeciwko traderowi (kupujesz drozej / sprzedajesz taniej)."""
    return abs(notional) * (half_spread_bps / 10_000.0)


def slippage_cost(notional: float, bps: float = 0.0, fixed: float = 0.0) -> float:
    """Poslizg jako suma skladnika proporcjonalnego (bps od notional) i stalej kwoty."""
    return abs(notional) * (bps / 10_000.0) + fixed


def funding_payment(direction: int, notional: float, funding_rate: float) -> float:
    """
    Podpisany cash flow z jednego zdarzenia funding.

    direction: +1 dla long, -1 dla short.
    funding_rate: ulamek dziesietny (np. 0.0001 = 1bp) za okres rozliczeniowy.
    Dodatnia stawka: longi placa shortom (konwencja rynkow perpetual).
    """
    if direction not in (1, -1):
        raise ValueError(f"direction musi byc +1 (long) albo -1 (short), otrzymano: {direction!r}")
    return -direction * abs(notional) * funding_rate


def funding_pnl(
    direction: int,
    notional: float,
    entry_time,
    exit_time,
    funding_events: Iterable[Tuple[object, float]],
) -> float:
    """
    Suma funding_payment dla zdarzen funding, ktore zaszly w trakcie trzymania pozycji.

    funding_events: iterowalna kolekcja par (timestamp, funding_rate).
    Zdarzenie liczy sie, gdy pozycja byla otwarta w danym momencie:
    entry_time <= timestamp < exit_time (wejscie dokladnie w momencie
    fundingu jest juz obciazone, wyjscie dokladnie w momencie fundingu —
    nie, bo pozycja jest juz zamknieta).
    """
    total = 0.0
    for ts, rate in funding_events:
        if entry_time <= ts < exit_time:
            total += funding_payment(direction, notional, rate)
    return total
