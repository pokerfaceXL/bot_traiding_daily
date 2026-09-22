"""
Zegar wykonania OHLC dla backtestu (F004, fala 3 -- zegar wykonania).

Buduje na costs.py (fala 1) i equity.py (fala 2). Standalone, bez sieci,
nie integruje sie z backtest_apex.py/strategy.py/main.py/trader.py/
configuration/ -- integracja to F004d, kolejna i ostatnia fala.

Adresuje trzy rozbieznosci z spec/research/F001-current-state.md:

- #5 (brak jawnego odrzucenia biezacej niezamknietej swiecy): ten modul
  zaklada, ze sygnal na swiecy N zostal juz policzony PO jej zamknieciu
  (data_contract.py's filter_closed_candles robi to wyzej w lancuchu --
  ten modul tego nie powtarza). Najwczesniejsza mozliwa realizacja to
  OTWARCIE swiecy N+1 -- nigdy cena zamkniecia swiecy N. Uzycie close(N)
  jako ceny wykonania bylby look-ahead: w momencie, w ktorym sygnal na N
  staje sie znany (dopiero po zamknieciu N), jedyna cena jeszcze nie
  ustalona "z gory" to otwarcie kolejnej swiecy.
- #6 (Bar Magnifier -- niejednoznaczna kolejnosc zdarzen wewnatrz swiecy):
  gdy SL i TP oba miesza sie w zakresie [low, high] tej samej swiecy,
  z samego OHLC nie da sie odtworzyc ktory zostal dotkniety pierwszy.
  `resolve_stop_take_within_bar` przyjmuje jawne, konserwatywne zalozenie
  worst-case (SL wygrywa) zamiast zgadywania korzystnej dla strategii
  kolejnosci -- patrz docstring tej funkcji po uzasadnienie.
- #7 (live uzywa MarkPrice, backtest OHLC): ten modul pracuje wylacznie
  na OHLC (jak istniejacy backtest) -- nie probuje symulowac MarkPrice.
  To jest udokumentowana, akceptowana roznica zrodla ceny miedzy live
  a backtestem, nie blad do naprawienia w tej fali.

Zero polaczen sieciowych, brak efektow ubocznych -- czyste funkcje na juz
znanych liczbach (OHLC, poziomy zlecen).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"


class TriggerKind(Enum):
    NONE = "none"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"


@dataclass(frozen=True)
class Bar:
    """Pojedyncza swieca OHLC uzywana jako wejscie do rozstrzygniec ponizej."""

    open: float
    high: float
    low: float
    close: float


@dataclass(frozen=True)
class EntryFill:
    filled: bool
    fill_price: Optional[float]
    order_type: OrderType


@dataclass(frozen=True)
class ExitTrigger:
    kind: TriggerKind
    fill_price: Optional[float]
    is_gap_fill: bool


def _check_direction(direction: int) -> None:
    if direction not in (1, -1):
        raise ValueError(f"direction musi byc +1 (long) albo -1 (short), otrzymano: {direction!r}")


def resolve_entry_fill(
    order_type: OrderType,
    direction: int,
    next_bar: Bar,
    limit_price: Optional[float] = None,
) -> EntryFill:
    """
    Rozwiazuje cene wejscia na podstawie OHLC swiecy N+1 (nastepnej po
    swiecy N, na ktorej zapadl juz zamkniety sygnal -- patrz docstring
    modulu, rozbieznosc #5).

    Market: wypelnienie zawsze po cenie OTWARCIA swiecy N+1 -- to
    najwczesniejsza mozliwa cena wykonania, nigdy cena zamkniecia N (look-ahead).

    Limit: wypelnienie tylko jesli zakres [low, high] swiecy N+1 dotyka
    lub przekracza limit_price w kierunku korzystnym dla zlecenia; w
    przeciwnym razie zlecenie NIE jest wypelnione (filled=False,
    fill_price=None) -- nigdy cichego wypelnienia po gorszej cenie.
    direction=+1 (kupno/long): limit fills, gdy low <= limit_price (cena
    spadla do poziomu lub nizej); fill_price = min(open, limit_price), bo
    jesli swieca otworzyla sie juz ponizej limitu, wykonanie jest lepsze
    (nizsze) niz sam limit. direction=-1 (sprzedaz/short): limit fills,
    gdy high >= limit_price; fill_price = max(open, limit_price)
    analogicznie w druga strone.
    """
    _check_direction(direction)

    if order_type == OrderType.MARKET:
        return EntryFill(filled=True, fill_price=next_bar.open, order_type=order_type)

    if order_type == OrderType.LIMIT:
        if limit_price is None:
            raise ValueError("limit_price wymagany dla OrderType.LIMIT")
        if direction == 1:
            if next_bar.low <= limit_price:
                return EntryFill(filled=True, fill_price=min(next_bar.open, limit_price), order_type=order_type)
        else:
            if next_bar.high >= limit_price:
                return EntryFill(filled=True, fill_price=max(next_bar.open, limit_price), order_type=order_type)
        return EntryFill(filled=False, fill_price=None, order_type=order_type)

    raise ValueError(f"Nieznany order_type: {order_type!r}")


def resolve_level_fill(direction: int, bar: Bar, level: float, kind: TriggerKind) -> ExitTrigger:
    """
    Gap handling (F004c, punkt 3 tickieta): rozstrzyga cene wypelnienia dla
    poziomu (SL albo TP), o ktorym juz wiadomo, ze zostal dotkniety w danej
    swiecy (wywolujacy -- resolve_stop_take_within_bar -- ustalil to wczesniej).

    Gap: swieca OTWIERA SIE juz poza `level` w kierunku, ktory by go
    aktywowal (dla SL long: open <= level; dla SL short: open >= level;
    analogicznie odwrotnie dla TP) -- rynek "przeskoczyl" przez poziom
    zanim mozliwe bylo wypelnienie po samym `level`. Realistyczna cena
    wykonania to wtedy cena OTWARCIA swiecy (gorsza od level dla SL,
    lepsza dla TP), NIE sam poziom `level`. Oznaczone is_gap_fill=True,
    zeby odroznic gap-fill od normalnego wypelnienia po poziomie (np. do
    innego modelowania poslizgu/kosztow gap-fill w pozniejszej integracji).

    Normalny (bez gapu) fill: swieca nie otworzyla sie juz za poziomem,
    ale jej zakres pozniej go osiaga -- wypelnienie dokladnie po `level`.
    """
    _check_direction(direction)

    if kind == TriggerKind.STOP_LOSS:
        gapped = bar.open <= level if direction == 1 else bar.open >= level
    elif kind == TriggerKind.TAKE_PROFIT:
        gapped = bar.open >= level if direction == 1 else bar.open <= level
    else:
        raise ValueError(f"kind musi byc STOP_LOSS albo TAKE_PROFIT, otrzymano: {kind!r}")

    if gapped:
        return ExitTrigger(kind=kind, fill_price=bar.open, is_gap_fill=True)
    return ExitTrigger(kind=kind, fill_price=level, is_gap_fill=False)


def resolve_stop_take_within_bar(
    direction: int,
    bar: Bar,
    stop_loss: Optional[float] = None,
    take_profit: Optional[float] = None,
) -> ExitTrigger:
    """
    Rozwiazuje, czy i gdzie SL/TP zostalyby dotkniete w obrebie jednej swiecy OHLC.

    Zalozenie konserwatywne (worst-case) dla niejednoznacznej kolejnosci
    wewnatrz-swiecowej (F001 rozbieznosc #6, "Bar Magnifier"): jesli OBA
    poziomy -- SL i TP -- miesza sie w zakresie [low, high] tej samej
    swiecy, samo OHLC nie mowi, ktory zostal dotkniety pierwszy (kod
    strategy.py to przyznaje wprost przez ambiguous_count/ambiguous_pct,
    strategy.py:619-621,628-630 -- mierzy niepewnosc, nie eliminuje jej).
    Ten modul ZAWSZE zaklada, ze cena poszla NAJPIERW w strone SL, wiec
    SL wygrywa nad TP w takim przypadku. Uzasadnienie: to jest zalozenie
    konserwatywne (pesymistyczne), nie optymistyczne -- backtest nigdy nie
    zawyzy wyniku strategii przez ciche przyjecie korzystnej dla niej
    kolejnosci zdarzen, ktorej po prostu nie ma w danych (OHLC nie
    zawiera sciezki cenowej wewnatrz swiecy). Odwrotne zalozenie
    (TP zawsze wygrywa) systematycznie zawyzalby win-rate/PnL strategii
    bez zadnego dowodu, ze tak faktycznie bylo.

    Gap: patrz resolve_level_fill -- jesli trafiony poziom zostal
    "przeskoczony" przez otwarcie swiecy, wypelnienie jest po cenie
    otwarcia i oznaczone is_gap_fill=True.
    """
    _check_direction(direction)

    sl_hit = stop_loss is not None and (bar.low <= stop_loss if direction == 1 else bar.high >= stop_loss)
    tp_hit = take_profit is not None and (bar.high >= take_profit if direction == 1 else bar.low <= take_profit)

    if not sl_hit and not tp_hit:
        return ExitTrigger(kind=TriggerKind.NONE, fill_price=None, is_gap_fill=False)

    if sl_hit:
        # Worst-case: gdy oba trafione, SL wygrywa (patrz docstring wyzej).
        return resolve_level_fill(direction, bar, stop_loss, TriggerKind.STOP_LOSS)

    return resolve_level_fill(direction, bar, take_profit, TriggerKind.TAKE_PROFIT)
