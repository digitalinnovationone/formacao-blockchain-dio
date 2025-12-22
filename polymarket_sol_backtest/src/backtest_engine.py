"""
Backtest Engine for AMM Delta-Neutral Strategy
Main simulation engine for backtesting the strategy
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from tqdm import tqdm
import logging

from config import settings
from config.risk_params import RiskParams
from .position_manager import Position, Portfolio, MarketState, Trade
from .risk_manager import RiskManager
from .metrics import PerformanceMetrics

logger = logging.getLogger(__name__)


class BacktestEngine:
    """Main backtest engine for AMM Delta-Neutral Strategy."""

    def __init__(
        self,
        config: Any = None,
        risk_params: RiskParams = None,
        initial_capital: float = None
    ):
        """
        Initialize backtest engine.

        Args:
            config: Configuration settings
            risk_params: Risk parameters
            initial_capital: Starting capital (overrides config)
        """
        self.config = config or settings
        self.risk_params = risk_params or RiskParams()
        self.risk_manager = RiskManager(self.risk_params)

        capital = initial_capital or getattr(self.config, 'INITIAL_CAPITAL', 5000)
        self.portfolio = Portfolio(capital)
        self.trades: List[Trade] = []
        self.metrics_collector = PerformanceMetrics()

    def run(
        self,
        markets_df: pd.DataFrame,
        prices_df: pd.DataFrame,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Execute the backtest.

        Args:
            markets_df: DataFrame with market information
            prices_df: DataFrame with price history
            verbose: Show progress bar

        Returns:
            Dictionary with backtest results
        """
        logger.info("Starting backtest...")
        logger.info(f"Initial capital: ${self.portfolio.initial_capital}")
        logger.info(f"Markets to process: {len(markets_df)}")

        # Ensure datetime columns
        markets_df = markets_df.copy()
        markets_df['start_time'] = pd.to_datetime(markets_df['start_time'])
        markets_df['end_time'] = pd.to_datetime(markets_df['end_time'])

        prices_df = prices_df.copy()
        prices_df['timestamp'] = pd.to_datetime(prices_df['timestamp'])

        # Sort markets by start time
        markets_df = markets_df.sort_values('start_time')

        # Create iterator
        iterator = tqdm(markets_df.iterrows(), total=len(markets_df)) if verbose else markets_df.iterrows()

        for idx, market_row in iterator:
            current_time = market_row['start_time']

            # 1. Settle expired positions
            self._settle_expired_positions(current_time, markets_df)

            # 2. Update active positions
            self._update_active_positions(current_time, prices_df)

            # 3. Check rebalancing
            self._check_rebalancing(prices_df)

            # 4. Evaluate new market entry
            self._evaluate_market_entry(market_row, prices_df)

            # 5. Record portfolio snapshot
            self.portfolio.record_snapshot(current_time)

        # Final settlement
        self._settle_all_positions(markets_df)

        # Generate report
        return self._generate_report()

    def _get_market_state(
        self,
        market_row: pd.Series,
        prices_df: pd.DataFrame,
        timestamp: Optional[datetime] = None
    ) -> Optional[MarketState]:
        """Get current market state from prices."""
        market_id = market_row['market_id']

        # Get prices for this market
        market_prices = prices_df[prices_df['market_id'] == market_id]

        if market_prices.empty:
            # Use default prices if no history
            return MarketState(
                market_id=market_id,
                price_yes=0.50,
                price_no=0.50,
                volume=market_row.get('volume', 0),
                time_remaining=900,  # 15 minutes
                outcome=market_row.get('outcome'),
                current_time=timestamp or market_row['start_time'],
            )

        # Get latest prices
        if timestamp:
            prices_before = market_prices[market_prices['timestamp'] <= timestamp]
            if prices_before.empty:
                prices_before = market_prices
            latest = prices_before.iloc[-1]
        else:
            latest = market_prices.iloc[-1]

        # Calculate time remaining
        end_time = market_row['end_time']
        current = timestamp or market_row['start_time']
        time_remaining = max(0, (end_time - current).total_seconds())

        return MarketState(
            market_id=market_id,
            price_yes=latest.get('price_yes', 0.50),
            price_no=latest.get('price_no', 0.50),
            volume=market_row.get('volume', 0),
            time_remaining=int(time_remaining),
            outcome=market_row.get('outcome'),
            current_time=current,
        )

    def _evaluate_market_entry(
        self,
        market_row: pd.Series,
        prices_df: pd.DataFrame
    ) -> None:
        """Evaluate and potentially enter a new market."""
        market_state = self._get_market_state(market_row, prices_df)

        if market_state is None:
            return

        # Check if already have position in this market
        if self.portfolio.get_position(market_state.market_id):
            return

        # Check entry conditions
        if not self.risk_manager.should_enter(market_state, self.portfolio):
            return

        # Calculate order size
        sizing = self.risk_manager.calculate_order_size(market_state, self.portfolio)

        if sizing['total_cost'] < self.risk_params.MIN_ORDER_SIZE * 2:
            return

        # Simulate execution with slippage
        execution = self._simulate_execution(market_state, sizing)

        # Create and add position
        position = Position(
            market=market_state,
            shares_yes=execution['shares_yes'],
            shares_no=execution['shares_no'],
            cost_yes=execution['cost_yes'],
            cost_no=execution['cost_no'],
            entry_time=market_state.current_time,
            entry_spread=market_state.spread,
        )

        self.portfolio.add_position(position)

    def _simulate_execution(
        self,
        market_state: MarketState,
        sizing: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Simulate order execution with slippage."""
        # Calculate slippage based on volume
        if market_state.volume > 0:
            volume_ratio = sizing['total_cost'] / market_state.volume
        else:
            volume_ratio = 0.1  # Assume significant impact

        if volume_ratio < 0.01:
            slippage = 0.001  # 0.1%
        elif volume_ratio < 0.05:
            slippage = 0.003  # 0.3%
        else:
            slippage = 0.005  # 0.5%

        # Apply slippage (price worsens)
        executed_price_yes = market_state.price_yes * (1 + slippage)
        executed_price_no = market_state.price_no * (1 + slippage)

        return {
            "shares_yes": sizing['shares_yes'],
            "shares_no": sizing['shares_no'],
            "cost_yes": sizing['shares_yes'] * executed_price_yes,
            "cost_no": sizing['shares_no'] * executed_price_no,
            "slippage_paid": slippage * sizing['total_cost'],
        }

    def _settle_expired_positions(
        self,
        current_time: datetime,
        markets_df: pd.DataFrame
    ) -> None:
        """Settle positions for markets that have ended."""
        positions_to_close = []

        for position in self.portfolio.active_positions:
            market_id = position.market.market_id
            market_row = markets_df[markets_df['market_id'] == market_id]

            if market_row.empty:
                continue

            end_time = pd.to_datetime(market_row.iloc[0]['end_time'])

            if current_time >= end_time:
                positions_to_close.append((position, market_row.iloc[0]))

        for position, market_row in positions_to_close:
            self._close_position(position, market_row)

    def _close_position(self, position: Position, market_row: pd.Series) -> None:
        """Close a position at settlement."""
        outcome = market_row.get('outcome', '')

        if pd.isna(outcome) or outcome == '':
            # If no outcome, assume 50/50
            outcome = 'Up' if np.random.random() > 0.5 else 'Down'

        outcome_str = str(outcome).strip()

        if outcome_str.lower() == 'up':
            payout = position.shares_yes * 1.00
        else:
            payout = position.shares_no * 1.00

        trade = self.portfolio.close_position(position, payout, outcome_str)
        self.trades.append(trade)

    def _settle_all_positions(self, markets_df: pd.DataFrame) -> None:
        """Settle all remaining positions at end of backtest."""
        while self.portfolio.active_positions:
            position = self.portfolio.active_positions[0]
            market_id = position.market.market_id
            market_row = markets_df[markets_df['market_id'] == market_id]

            if not market_row.empty:
                self._close_position(position, market_row.iloc[0])
            else:
                # Force close with assumed outcome
                self.portfolio.close_position(position, position.shares_yes * 0.5, "Unknown")

    def _update_active_positions(
        self,
        current_time: datetime,
        prices_df: pd.DataFrame
    ) -> None:
        """Update market state for active positions."""
        for position in self.portfolio.active_positions:
            market_prices = prices_df[
                (prices_df['market_id'] == position.market.market_id) &
                (prices_df['timestamp'] <= current_time)
            ]

            if not market_prices.empty:
                latest = market_prices.iloc[-1]
                position.market.price_yes = latest.get('price_yes', position.market.price_yes)
                position.market.price_no = latest.get('price_no', position.market.price_no)
                position.market.current_time = current_time

    def _check_rebalancing(self, prices_df: pd.DataFrame) -> None:
        """Check and execute rebalancing for active positions."""
        for position in self.portfolio.active_positions:
            if self.risk_manager.should_rebalance(position, position.market):
                rebalance = self.risk_manager.calculate_rebalance(position, position.market)

                if rebalance['action'] != 'HOLD' and rebalance['shares'] > 0:
                    # Execute rebalance (simplified - just adjust shares)
                    if rebalance['action'] == 'BUY_YES':
                        cost = rebalance['shares'] * position.market.price_yes
                        if cost <= self.portfolio.cash:
                            self.portfolio.cash -= cost
                            position.shares_yes += rebalance['shares']
                            position.cost_yes += cost
                    elif rebalance['action'] == 'BUY_NO':
                        cost = rebalance['shares'] * position.market.price_no
                        if cost <= self.portfolio.cash:
                            self.portfolio.cash -= cost
                            position.shares_no += rebalance['shares']
                            position.cost_no += cost

    def _generate_report(self) -> Dict[str, Any]:
        """Generate backtest report."""
        trades_data = [t.to_dict() for t in self.trades]
        trades_df = pd.DataFrame(trades_data) if trades_data else pd.DataFrame()

        history_df = pd.DataFrame(self.portfolio.history)

        # Calculate metrics
        metrics = self.metrics_collector.calculate_all(trades_df, history_df)

        report = {
            "summary": {
                "initial_capital": self.portfolio.initial_capital,
                "final_capital": self.portfolio.total_value,
                "total_return_usd": self.portfolio.total_pnl,
                "total_return_pct": self.portfolio.total_return_pct,
                "total_trades": len(self.trades),
            },
            "metrics": metrics,
            "trades": trades_df,
            "portfolio_history": history_df,
            "portfolio_summary": self.portfolio.get_summary(),
        }

        logger.info("Backtest complete!")
        logger.info(f"Final capital: ${self.portfolio.total_value:.2f}")
        logger.info(f"Total return: {self.portfolio.total_return_pct:.2f}%")
        logger.info(f"Total trades: {len(self.trades)}")

        return report


def run_backtest(
    markets_path: str,
    prices_path: str,
    initial_capital: float = 5000,
    risk_params: RiskParams = None
) -> Dict[str, Any]:
    """
    Convenience function to run backtest from file paths.

    Args:
        markets_path: Path to markets CSV/parquet
        prices_path: Path to prices CSV/parquet
        initial_capital: Starting capital
        risk_params: Risk parameters

    Returns:
        Backtest results
    """
    # Load data
    if markets_path.endswith('.parquet'):
        markets_df = pd.read_parquet(markets_path)
    else:
        markets_df = pd.read_csv(markets_path)

    if prices_path.endswith('.parquet'):
        prices_df = pd.read_parquet(prices_path)
    else:
        prices_df = pd.read_csv(prices_path)

    # Run backtest
    engine = BacktestEngine(
        initial_capital=initial_capital,
        risk_params=risk_params
    )

    return engine.run(markets_df, prices_df)
