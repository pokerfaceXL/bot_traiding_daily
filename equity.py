"""
Equity/margin portfela dla backtestu (F004, fala 2 — equity/margin).

Buduje na costs.py (fala 1): dostarcza Portfolio/Ledger ktory sledzi jeden
wspolny initial_equity (domyslnie 500 USD) dla WSZYSTKICH otwartych pozycji
i symboli naraz — nie kazda pozycja ze swoim wlasnym 500 USD.

Kontrakt stawki/dzwigni/DD z spec/build.md ("Decyzje i granice pracy"):
- stake = 100 USD/wejscie, PRZED dzwignia.
- notional = stake * leverage.
- margin = notional / leverage = stake (margin nie zalezy od leverage —
  to co wplacasz jako zabezpieczenie pozycji to sam stake; leverage tylko
  mnozy notional/ekspozycje, nie kwote zablokowanego marginu).
- initial_equity = 500 USD, wspolne dla wszystkich pozycji/symboli.
- Max DD 50% liczone od biezacego historycznego szczytu equity, z kosztami
  i otwartymi pozycjami (mark-to-market) — ten modul tylko liczy i sledzi
  peak/DD, nie egzekwuje limitu (egzekwowanie to kolejna fala/integracja).

Rozliczanie kosztow przy zamknieciu pozycji uzywa czterech funkcji z
costs.py: commission i spread_cost na obu nogach (entry+exit), slippage_cost
na notional wejscia, funding_pnl za caly okres trzymania pozycji — ta sama
konwencja co w scenariuszach z tests/test_costs.py (fala 1).

Interpretacja "available equity" z tickieta F004b: dostepny margin do
otwarcia nowej pozycji to biezace equity mark-to-market (initial_equity +
zrealizowany PnL + niezrealizowany PnL wszystkich otwartych pozycji przy
podanych cenach rynkowych) minus margin juz zaangazowany w inne otwarte
pozycje minus opcjonalny bufor na koszty zamkniecia. Literalne
"initial_equity - margin - buffer" z tickieta jest tego szczegolnym
przypadkiem, gdy jeszcze nie bylo zadnego PnL — uzycie biezacego equity
zamiast stalej initial_equity jest konieczne, zeby wymog (2) (mark-to-market
wliczone do equity w kazdej chwili) i wymog (3) (blokada braku srodkow) byly
spojne: po stracie na jednej pozycji kolejna pozycja NIE powinna miec
dostepu do "widmowych" pieniedzy z initial_equity, ktorych juz nie ma.

Zero polaczen sieciowych, brak efektow ubocznych poza stanem samego
Portfolio.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple

import costs


class InsufficientMarginError(Exception):
    """Podniesione, gdy otwarcie pozycji zostaloby cicho przekroczylo dostepny margin."""


@dataclass
class Position:
    position_id: str
    symbol: str
    direction: int  # +1 long, -1 short
    entry_price: float
    entry_time: object
    stake: float
    leverage: float
    notional: float
    margin: float
    quantity: float

    def unrealized_pnl(self, mark_price: float) -> float:
        """Niezrealizowany PnL przy podanej cenie rynkowej (mark price)."""
        return self.direction * (mark_price - self.entry_price) * self.quantity


@dataclass
class ClosedTrade:
    position: Position
    exit_price: float
    exit_time: object
    gross_pnl: float
    total_costs: float
    funding_pnl: float
    net_pnl: float


@dataclass
class Portfolio:
    """
    Ledger equity/margin wspolny dla wszystkich otwartych pozycji i symboli.

    initial_equity: kapital startowy portfela (domyslnie 500 USD, wspolny).
    """

    initial_equity: float = 500.0
    realized_pnl: float = 0.0
    committed_margin: float = 0.0
    positions: Dict[str, Position] = field(default_factory=dict)
    closed_trades: List[ClosedTrade] = field(default_factory=list)
    peak_equity: float = field(init=False)
    current_drawdown_pct: float = field(init=False, default=0.0)

    def __post_init__(self):
        self.peak_equity = self.initial_equity

    def _unrealized_pnl_total(self, mark_prices: Optional[Dict[str, float]]) -> float:
        mark_prices = mark_prices or {}
        total = 0.0
        for position_id, pos in self.positions.items():
            mark_price = mark_prices.get(position_id, pos.entry_price)
            total += pos.unrealized_pnl(mark_price)
        return total

    def equity(self, mark_prices: Optional[Dict[str, float]] = None) -> float:
        """Biezace equity mark-to-market: initial + zrealizowany PnL + niezrealizowany PnL otwartych pozycji."""
        return self.initial_equity + self.realized_pnl + self._unrealized_pnl_total(mark_prices)

    def available_margin(self, mark_prices: Optional[Dict[str, float]] = None, fee_buffer: float = 0.0) -> float:
        """Margin dostepny na nowa pozycje: biezace equity minus margin juz zaangazowany minus bufor na koszty."""
        return self.equity(mark_prices) - self.committed_margin - fee_buffer

    def mark_to_market(self, mark_prices: Optional[Dict[str, float]] = None) -> Tuple[float, float]:
        """
        Aktualizuje sledzony szczyt equity i zwraca (equity, drawdown_pct) przy podanych cenach.

        drawdown_pct = 100 * (peak_equity - equity) / peak_equity (0.0, gdy equity >= peak lub peak <= 0).
        """
        current_equity = self.equity(mark_prices)
        if current_equity > self.peak_equity:
            self.peak_equity = current_equity
        if self.peak_equity > 0:
            drawdown_pct = 100.0 * (self.peak_equity - current_equity) / self.peak_equity
        else:
            drawdown_pct = 0.0
        self.current_drawdown_pct = drawdown_pct
        return current_equity, drawdown_pct

    def open_position(
        self,
        position_id: str,
        symbol: str,
        direction: int,
        entry_price: float,
        entry_time,
        stake: float = 100.0,
        leverage: float = 1.0,
        mark_prices: Optional[Dict[str, float]] = None,
        fee_buffer: float = 0.0,
    ) -> Position:
        """
        Otwiera pozycje, jesli jest wystarczajacy dostepny margin; w przeciwnym razie podnosi InsufficientMarginError.

        notional = stake * leverage; margin = notional / leverage = stake.
        """
        if position_id in self.positions:
            raise ValueError(f"position_id juz otwarty: {position_id!r}")
        if direction not in (1, -1):
            raise ValueError(f"direction musi byc +1 (long) albo -1 (short), otrzymano: {direction!r}")

        notional = stake * leverage
        margin = notional / leverage  # == stake, patrz docstring modulu

        available = self.available_margin(mark_prices, fee_buffer=fee_buffer)
        if available < margin:
            raise InsufficientMarginError(
                f"Brak srodkow na otwarcie {symbol} ({position_id}): "
                f"wymagany margin={margin:.4f}, dostepny={available:.4f} "
                f"(equity={self.equity(mark_prices):.4f}, "
                f"committed_margin={self.committed_margin:.4f}, fee_buffer={fee_buffer:.4f})"
            )

        quantity = notional / entry_price
        position = Position(
            position_id=position_id,
            symbol=symbol,
            direction=direction,
            entry_price=entry_price,
            entry_time=entry_time,
            stake=stake,
            leverage=leverage,
            notional=notional,
            margin=margin,
            quantity=quantity,
        )
        self.positions[position_id] = position
        self.committed_margin += margin
        return position

    def close_position(
        self,
        position_id: str,
        exit_price: float,
        exit_time,
        commission_rate_bps: float = 0.0,
        half_spread_bps: float = 0.0,
        slippage_bps: float = 0.0,
        slippage_fixed: float = 0.0,
        funding_events: Iterable[Tuple[object, float]] = (),
    ) -> ClosedTrade:
        """
        Zamyka pozycje: realizuje jej PnL (po kosztach z costs.py) do equity i zwalnia margin.

        Koszty: commission i spread_cost na obu nogach (entry notional + exit notional),
        slippage_cost na notional wejscia, funding_pnl za caly okres trzymania — ta sama
        konwencja co w tests/test_costs.py (fala 1).
        """
        if position_id not in self.positions:
            raise KeyError(f"brak otwartej pozycji o id {position_id!r}")
        position = self.positions.pop(position_id)

        gross_pnl = position.unrealized_pnl(exit_price)
        exit_notional = abs(exit_price * position.quantity)

        entry_commission = costs.commission(position.notional, commission_rate_bps)
        exit_commission = costs.commission(exit_notional, commission_rate_bps)
        entry_spread = costs.spread_cost(position.notional, half_spread_bps)
        exit_spread = costs.spread_cost(exit_notional, half_spread_bps)
        slippage = costs.slippage_cost(position.notional, bps=slippage_bps, fixed=slippage_fixed)
        total_costs = entry_commission + exit_commission + entry_spread + exit_spread + slippage

        funding = costs.funding_pnl(
            position.direction, position.notional, position.entry_time, exit_time, funding_events
        )

        net_pnl = gross_pnl - total_costs + funding

        self.realized_pnl += net_pnl
        self.committed_margin -= position.margin

        trade = ClosedTrade(
            position=position,
            exit_price=exit_price,
            exit_time=exit_time,
            gross_pnl=gross_pnl,
            total_costs=total_costs,
            funding_pnl=funding,
            net_pnl=net_pnl,
        )
        self.closed_trades.append(trade)
        return trade
