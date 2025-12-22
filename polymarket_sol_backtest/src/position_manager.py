"""
Position and Portfolio Management for AMM Delta-Neutral Strategy
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class MarketState:
    """Current state of a market."""
    market_id: str
    price_yes: float
    price_no: float
    volume: float
    time_remaining: int  # seconds
    outcome: Optional[str] = None
    current_time: Optional[datetime] = None

    @property
    def spread(self) -> float:
        """Calculate spread: YES + NO - 1.0"""
        return self.price_yes + self.price_no - 1.0

    @property
    def mid_price(self) -> float:
        """Calculate mid price."""
        return (self.price_yes + (1 - self.price_no)) / 2


@dataclass
class Position:
    """Represents a position in a market."""
    market: MarketState
    shares_yes: float
    shares_no: float
    cost_yes: float
    cost_no: float
    entry_time: datetime
    entry_spread: float

    @property
    def total_cost(self) -> float:
        """Total cost of the position."""
        return self.cost_yes + self.cost_no

    @property
    def ratio(self) -> float:
        """YES/NO ratio."""
        if self.shares_no == 0:
            return float('inf')
        return self.shares_yes / self.shares_no

    @property
    def guaranteed_payout(self) -> float:
        """Minimum guaranteed payout at settlement."""
        return min(self.shares_yes, self.shares_no)

    @property
    def expected_profit(self) -> float:
        """Expected profit based on guaranteed payout."""
        return self.guaranteed_payout - self.total_cost

    def current_value(self, market_state: MarketState) -> float:
        """Calculate current market value of position."""
        return (
            self.shares_yes * market_state.price_yes +
            self.shares_no * market_state.price_no
        )

    def unrealized_pnl(self, market_state: MarketState) -> float:
        """Calculate unrealized P&L."""
        return self.current_value(market_state) - self.total_cost


@dataclass
class Trade:
    """Represents a completed trade."""
    market_id: str
    entry_time: datetime
    exit_time: datetime
    shares_yes: float
    shares_no: float
    cost: float
    payout: float
    profit: float
    roi: float
    outcome: str
    entry_spread: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "market_id": self.market_id,
            "entry_time": self.entry_time.isoformat() if self.entry_time else None,
            "exit_time": self.exit_time.isoformat() if self.exit_time else None,
            "shares_yes": self.shares_yes,
            "shares_no": self.shares_no,
            "cost": self.cost,
            "payout": self.payout,
            "profit": self.profit,
            "roi": self.roi,
            "outcome": self.outcome,
            "entry_spread": self.entry_spread,
        }


class Portfolio:
    """Portfolio manager for tracking positions and cash."""

    def __init__(self, initial_capital: float):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.active_positions: List[Position] = []
        self.closed_positions: List[Trade] = []
        self.history: List[Dict[str, Any]] = []

    @property
    def total_invested(self) -> float:
        """Total amount invested in active positions."""
        return sum(p.total_cost for p in self.active_positions)

    @property
    def total_exposure(self) -> float:
        """Exposure as percentage of initial capital."""
        return self.total_invested / self.initial_capital

    @property
    def available_cash(self) -> float:
        """Available cash for new positions."""
        return self.cash

    @property
    def active_markets(self) -> int:
        """Number of active market positions."""
        return len(self.active_positions)

    @property
    def total_value(self) -> float:
        """Total portfolio value (cash + positions at cost)."""
        return self.cash + self.total_invested

    @property
    def total_pnl(self) -> float:
        """Total realized P&L."""
        return sum(t.profit for t in self.closed_positions)

    @property
    def total_return_pct(self) -> float:
        """Total return as percentage."""
        return (self.total_value - self.initial_capital) / self.initial_capital * 100

    def add_position(self, position: Position) -> bool:
        """
        Add a new position to the portfolio.

        Args:
            position: Position to add

        Returns:
            True if position was added successfully
        """
        cost = position.total_cost

        if cost > self.cash:
            logger.warning(f"Insufficient cash: {self.cash} < {cost}")
            return False

        self.cash -= cost
        self.active_positions.append(position)

        logger.info(
            f"Opened position in {position.market.market_id}: "
            f"YES={position.shares_yes}, NO={position.shares_no}, "
            f"Cost=${cost:.2f}"
        )

        return True

    def remove_position(self, position: Position) -> None:
        """Remove a position from active positions."""
        if position in self.active_positions:
            self.active_positions.remove(position)

    def close_position(self, position: Position, payout: float, outcome: str) -> Trade:
        """
        Close a position and record the trade.

        Args:
            position: Position to close
            payout: Amount received at settlement
            outcome: Market outcome ("Up" or "Down")

        Returns:
            Trade record
        """
        self.cash += payout
        self.remove_position(position)

        profit = payout - position.total_cost
        roi = profit / position.total_cost if position.total_cost > 0 else 0

        trade = Trade(
            market_id=position.market.market_id,
            entry_time=position.entry_time,
            exit_time=position.market.current_time or datetime.now(),
            shares_yes=position.shares_yes,
            shares_no=position.shares_no,
            cost=position.total_cost,
            payout=payout,
            profit=profit,
            roi=roi,
            outcome=outcome,
            entry_spread=position.entry_spread,
        )

        self.closed_positions.append(trade)

        logger.info(
            f"Closed position in {trade.market_id}: "
            f"Outcome={outcome}, Payout=${payout:.2f}, "
            f"Profit=${profit:.2f} ({roi*100:.2f}%)"
        )

        return trade

    def get_position(self, market_id: str) -> Optional[Position]:
        """Get position by market ID."""
        for position in self.active_positions:
            if position.market.market_id == market_id:
                return position
        return None

    def record_snapshot(self, timestamp: datetime) -> Dict[str, Any]:
        """Record a portfolio snapshot for history."""
        snapshot = {
            "timestamp": timestamp,
            "cash": self.cash,
            "total_invested": self.total_invested,
            "total_value": self.total_value,
            "active_markets": self.active_markets,
            "exposure": self.total_exposure,
            "total_pnl": self.total_pnl,
        }
        self.history.append(snapshot)
        return snapshot

    def get_summary(self) -> Dict[str, Any]:
        """Get portfolio summary."""
        return {
            "initial_capital": self.initial_capital,
            "current_cash": self.cash,
            "total_invested": self.total_invested,
            "total_value": self.total_value,
            "total_pnl": self.total_pnl,
            "total_return_pct": self.total_return_pct,
            "active_positions": self.active_markets,
            "closed_trades": len(self.closed_positions),
        }
