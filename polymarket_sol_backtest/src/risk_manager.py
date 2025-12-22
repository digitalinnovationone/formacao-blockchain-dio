"""
Risk Manager for AMM Delta-Neutral Strategy
Implements entry logic, sizing, and rebalancing rules
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging

from config.risk_params import RiskParams
from .position_manager import Position, Portfolio, MarketState

logger = logging.getLogger(__name__)


class RiskManager:
    """Risk manager implementing strategy rules."""

    def __init__(self, risk_params: RiskParams = None):
        """
        Initialize risk manager.

        Args:
            risk_params: Risk parameters (uses defaults if None)
        """
        self.params = risk_params or RiskParams()

    def should_enter(
        self,
        market_state: MarketState,
        portfolio: Portfolio
    ) -> bool:
        """
        Check if should enter a market position.

        Args:
            market_state: Current market state
            portfolio: Current portfolio state

        Returns:
            True if should enter the market
        """
        # 1. Spread check
        if market_state.spread >= self.params.MIN_SPREAD_TO_ENTER:
            logger.debug(f"Spread too high: {market_state.spread}")
            return False

        # 2. Volume check (proxy for liquidity)
        if market_state.volume < self.params.MIN_VOLUME:
            logger.debug(f"Volume too low: {market_state.volume}")
            return False

        # 3. Time remaining check
        if market_state.time_remaining < self.params.MIN_TIME_REMAINING:
            logger.debug(f"Time remaining too short: {market_state.time_remaining}s")
            return False

        # 4. Capital check
        min_required = self.params.MIN_ORDER_SIZE * 2
        if portfolio.available_cash < min_required:
            logger.debug(f"Insufficient cash: {portfolio.available_cash} < {min_required}")
            return False

        # 5. Active markets limit
        if portfolio.active_markets >= self.params.MAX_ACTIVE_MARKETS:
            logger.debug(f"Max active markets reached: {portfolio.active_markets}")
            return False

        # 6. Total exposure check
        if portfolio.total_exposure >= self.params.MAX_TOTAL_EXPOSURE:
            logger.debug(f"Max exposure reached: {portfolio.total_exposure}")
            return False

        return True

    def calculate_order_size(
        self,
        market_state: MarketState,
        portfolio: Portfolio
    ) -> Dict[str, Any]:
        """
        Calculate optimal order size for a market.

        Args:
            market_state: Current market state
            portfolio: Current portfolio state

        Returns:
            Dictionary with sizing information
        """
        # Max capital for this market
        max_by_pct = portfolio.available_cash * self.params.MAX_PER_MARKET_PCT
        max_by_usd = self.params.MAX_PER_MARKET_USD
        max_for_market = min(max_by_pct, max_by_usd)

        # Price info
        price_yes = market_state.price_yes
        price_no = market_state.price_no
        total_price = price_yes + price_no

        # Calculate pairs to buy
        if total_price <= 0:
            return self._empty_sizing()

        pairs_to_buy = max_for_market / total_price

        # Round down to integer shares
        shares_yes = int(pairs_to_buy)
        shares_no = int(pairs_to_buy)

        if shares_yes < 1 or shares_no < 1:
            return self._empty_sizing()

        cost_yes = shares_yes * price_yes
        cost_no = shares_no * price_no
        total_cost = cost_yes + cost_no

        # Check minimum order size
        if total_cost < self.params.MIN_ORDER_SIZE * 2:
            return self._empty_sizing()

        return {
            "shares_yes": shares_yes,
            "shares_no": shares_no,
            "cost_yes": cost_yes,
            "cost_no": cost_no,
            "total_cost": total_cost,
            "expected_payout": min(shares_yes, shares_no),
            "expected_profit": min(shares_yes, shares_no) - total_cost,
            "expected_roi": (min(shares_yes, shares_no) - total_cost) / total_cost if total_cost > 0 else 0,
        }

    def _empty_sizing(self) -> Dict[str, Any]:
        """Return empty sizing result."""
        return {
            "shares_yes": 0,
            "shares_no": 0,
            "cost_yes": 0,
            "cost_no": 0,
            "total_cost": 0,
            "expected_payout": 0,
            "expected_profit": 0,
            "expected_roi": 0,
        }

    def should_rebalance(
        self,
        position: Position,
        market_state: MarketState
    ) -> bool:
        """
        Check if position needs rebalancing.

        Args:
            position: Current position
            market_state: Current market state

        Returns:
            True if should rebalance
        """
        ratio = position.ratio

        # Check if too unbalanced
        if ratio > self.params.MAX_RATIO or ratio < self.params.MIN_RATIO:
            return True

        # Check if spread improved significantly (opportunity to add)
        current_spread = market_state.spread
        if current_spread < position.entry_spread - self.params.SPREAD_IMPROVEMENT_THRESHOLD:
            return True

        return False

    def calculate_rebalance(
        self,
        position: Position,
        market_state: MarketState
    ) -> Dict[str, Any]:
        """
        Calculate rebalancing action.

        Args:
            position: Current position
            market_state: Current market state

        Returns:
            Dictionary with rebalancing action
        """
        ratio = position.ratio

        if ratio > self.params.MAX_RATIO:
            # Too much YES, need to buy NO
            target_no = position.shares_yes / self.params.TARGET_RATIO
            shares_to_buy = target_no - position.shares_no
            return {
                "action": "BUY_NO",
                "shares": max(0, int(shares_to_buy)),
                "cost": max(0, int(shares_to_buy)) * market_state.price_no,
            }

        elif ratio < self.params.MIN_RATIO:
            # Too much NO, need to buy YES
            target_yes = position.shares_no * self.params.TARGET_RATIO
            shares_to_buy = target_yes - position.shares_yes
            return {
                "action": "BUY_YES",
                "shares": max(0, int(shares_to_buy)),
                "cost": max(0, int(shares_to_buy)) * market_state.price_yes,
            }

        return {"action": "HOLD", "shares": 0, "cost": 0}

    def calculate_exit(
        self,
        position: Position,
        outcome: str
    ) -> Dict[str, Any]:
        """
        Calculate exit/settlement result.

        Args:
            position: Position being closed
            outcome: Market outcome ("Up" or "Down")

        Returns:
            Dictionary with exit calculations
        """
        if outcome == "Up":
            # YES = $1.00, NO = $0.00
            payout = position.shares_yes * 1.00
        else:
            # YES = $0.00, NO = $1.00
            payout = position.shares_no * 1.00

        profit = payout - position.total_cost
        roi = profit / position.total_cost if position.total_cost > 0 else 0

        return {
            "payout": payout,
            "profit": profit,
            "roi": roi,
            "outcome": outcome,
        }

    def check_stop_loss(
        self,
        position: Position,
        market_state: MarketState
    ) -> bool:
        """
        Check if stop loss is triggered.

        Args:
            position: Current position
            market_state: Current market state

        Returns:
            True if stop loss triggered
        """
        current_value = position.current_value(market_state)
        loss_pct = (position.total_cost - current_value) / position.total_cost

        return loss_pct >= self.params.STOP_LOSS_PCT

    def get_decision_matrix(
        self,
        market_state: MarketState,
        portfolio: Portfolio,
        position: Optional[Position] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive decision based on current state.

        Args:
            market_state: Current market state
            portfolio: Current portfolio state
            position: Existing position if any

        Returns:
            Dictionary with decision info
        """
        spread = market_state.spread
        exposure = portfolio.total_exposure

        # Spread decision
        if spread > -0.01:
            spread_decision = "NO_ENTRY"
            spread_strength = 0
        elif spread > -0.02:
            spread_decision = "CONSIDER"
            spread_strength = 1
        elif spread > -0.03:
            spread_decision = "ENTER"
            spread_strength = 2
        else:
            spread_decision = "ENTER_STRONG"
            spread_strength = 3

        # Exposure decision
        if exposure > 0.70:
            exposure_decision = "NO_NEW_MARKETS"
        elif exposure > 0.50:
            exposure_decision = "SELECTIVE"
        else:
            exposure_decision = "FREE"

        # Position decision
        position_decision = None
        if position:
            ratio = position.ratio
            if ratio > 1.3:
                position_decision = "BUY_NO"
            elif ratio < 0.7:
                position_decision = "BUY_YES"
            elif ratio > 1.1:
                position_decision = "PREFER_NO"
            elif ratio < 0.9:
                position_decision = "PREFER_YES"
            else:
                position_decision = "BALANCED"

        return {
            "spread": spread,
            "spread_decision": spread_decision,
            "spread_strength": spread_strength,
            "exposure": exposure,
            "exposure_decision": exposure_decision,
            "position_decision": position_decision,
            "should_enter": self.should_enter(market_state, portfolio),
        }
