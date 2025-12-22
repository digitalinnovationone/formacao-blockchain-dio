"""
Unit tests for AMM Delta-Neutral Strategy Backtest
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.risk_params import RiskParams
from src.position_manager import Position, Portfolio, MarketState, Trade
from src.risk_manager import RiskManager
from src.spread_calculator import SpreadCalculator
from src.metrics import PerformanceMetrics


class TestMarketState:
    """Tests for MarketState class."""

    def test_spread_calculation(self):
        """Test spread is calculated correctly."""
        state = MarketState(
            market_id="test",
            price_yes=0.48,
            price_no=0.49,
            volume=1000,
            time_remaining=600
        )
        assert state.spread == pytest.approx(-0.03, abs=0.001)

    def test_mid_price_calculation(self):
        """Test mid price calculation."""
        state = MarketState(
            market_id="test",
            price_yes=0.50,
            price_no=0.50,
            volume=1000,
            time_remaining=600
        )
        assert state.mid_price == pytest.approx(0.50, abs=0.001)


class TestPortfolio:
    """Tests for Portfolio class."""

    def test_initial_state(self):
        """Test portfolio initialization."""
        portfolio = Portfolio(5000)
        assert portfolio.cash == 5000
        assert portfolio.initial_capital == 5000
        assert portfolio.active_markets == 0
        assert portfolio.total_exposure == 0

    def test_add_position(self):
        """Test adding a position."""
        portfolio = Portfolio(5000)
        market = MarketState(
            market_id="test",
            price_yes=0.48,
            price_no=0.49,
            volume=1000,
            time_remaining=600
        )
        position = Position(
            market=market,
            shares_yes=100,
            shares_no=100,
            cost_yes=48,
            cost_no=49,
            entry_time=datetime.now(),
            entry_spread=-0.03
        )

        result = portfolio.add_position(position)

        assert result is True
        assert portfolio.cash == 5000 - 97
        assert portfolio.active_markets == 1

    def test_close_position_up(self):
        """Test closing position with Up outcome."""
        portfolio = Portfolio(5000)
        market = MarketState(
            market_id="test",
            price_yes=0.48,
            price_no=0.49,
            volume=1000,
            time_remaining=600
        )
        position = Position(
            market=market,
            shares_yes=100,
            shares_no=100,
            cost_yes=48,
            cost_no=49,
            entry_time=datetime.now(),
            entry_spread=-0.03
        )

        portfolio.add_position(position)
        trade = portfolio.close_position(position, 100, "Up")

        assert trade.profit == pytest.approx(3, abs=0.01)
        assert portfolio.cash == pytest.approx(5003, abs=0.01)

    def test_close_position_down(self):
        """Test closing position with Down outcome."""
        portfolio = Portfolio(5000)
        market = MarketState(
            market_id="test",
            price_yes=0.48,
            price_no=0.49,
            volume=1000,
            time_remaining=600
        )
        position = Position(
            market=market,
            shares_yes=100,
            shares_no=100,
            cost_yes=48,
            cost_no=49,
            entry_time=datetime.now(),
            entry_spread=-0.03
        )

        portfolio.add_position(position)
        trade = portfolio.close_position(position, 100, "Down")

        assert trade.profit == pytest.approx(3, abs=0.01)


class TestRiskManager:
    """Tests for RiskManager class."""

    def test_should_enter_good_opportunity(self):
        """Test entry with good spread opportunity."""
        risk_manager = RiskManager()
        portfolio = Portfolio(5000)
        market = MarketState(
            market_id="test",
            price_yes=0.48,
            price_no=0.49,
            volume=1000,
            time_remaining=600
        )

        assert risk_manager.should_enter(market, portfolio) is True

    def test_should_not_enter_bad_spread(self):
        """Test no entry with bad spread."""
        risk_manager = RiskManager()
        portfolio = Portfolio(5000)
        market = MarketState(
            market_id="test",
            price_yes=0.50,
            price_no=0.51,
            volume=1000,
            time_remaining=600
        )

        assert risk_manager.should_enter(market, portfolio) is False

    def test_should_not_enter_low_volume(self):
        """Test no entry with low volume."""
        risk_manager = RiskManager()
        portfolio = Portfolio(5000)
        market = MarketState(
            market_id="test",
            price_yes=0.48,
            price_no=0.49,
            volume=100,  # Below MIN_VOLUME
            time_remaining=600
        )

        assert risk_manager.should_enter(market, portfolio) is False

    def test_calculate_order_size(self):
        """Test order sizing calculation."""
        risk_manager = RiskManager()
        portfolio = Portfolio(5000)
        market = MarketState(
            market_id="test",
            price_yes=0.48,
            price_no=0.49,
            volume=1000,
            time_remaining=600
        )

        sizing = risk_manager.calculate_order_size(market, portfolio)

        assert sizing['shares_yes'] > 0
        assert sizing['shares_no'] > 0
        assert sizing['total_cost'] <= 750  # MAX_PER_MARKET_USD
        assert sizing['expected_profit'] > 0

    def test_calculate_exit_up(self):
        """Test exit calculation for Up outcome."""
        risk_manager = RiskManager()
        market = MarketState(
            market_id="test",
            price_yes=0.48,
            price_no=0.49,
            volume=1000,
            time_remaining=0
        )
        position = Position(
            market=market,
            shares_yes=100,
            shares_no=100,
            cost_yes=48,
            cost_no=49,
            entry_time=datetime.now(),
            entry_spread=-0.03
        )

        result = risk_manager.calculate_exit(position, "Up")

        assert result['payout'] == 100
        assert result['profit'] == pytest.approx(3, abs=0.01)


class TestSpreadCalculator:
    """Tests for SpreadCalculator class."""

    def test_calculate_spread_stats(self):
        """Test spread statistics calculation."""
        prices_df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=100, freq='1min'),
            'market_id': ['market_1'] * 100,
            'price_yes': np.random.uniform(0.45, 0.55, 100),
            'price_no': np.random.uniform(0.45, 0.55, 100),
        })

        calculator = SpreadCalculator(prices_df)
        stats = calculator.calculate_spread_stats()

        assert 'mean' in stats
        assert 'std' in stats
        assert 'pct_below_98' in stats

    def test_calculate_expected_profit(self):
        """Test expected profit calculation."""
        prices_df = pd.DataFrame({
            'timestamp': [datetime.now()],
            'market_id': ['test'],
            'price_yes': [0.48],
            'price_no': [0.49],
        })

        calculator = SpreadCalculator(prices_df)
        result = calculator.calculate_expected_profit(0.48, 0.49, 100)

        assert result['profit'] == pytest.approx(3, abs=0.01)
        assert result['spread'] == pytest.approx(-0.03, abs=0.001)


class TestPerformanceMetrics:
    """Tests for PerformanceMetrics class."""

    def test_calculate_trade_stats(self):
        """Test trade statistics calculation."""
        trades_df = pd.DataFrame({
            'market_id': ['m1', 'm2', 'm3', 'm4'],
            'profit': [10, -5, 15, 8],
            'cost': [100, 100, 100, 100],
            'roi': [0.10, -0.05, 0.15, 0.08],
            'entry_spread': [-0.02, -0.01, -0.03, -0.02],
            'shares_yes': [100, 100, 100, 100],
            'shares_no': [100, 100, 100, 100],
        })

        metrics = PerformanceMetrics()
        stats = metrics._calculate_trade_stats(trades_df)

        assert stats['total_trades'] == 4
        assert stats['winning_trades'] == 3
        assert stats['losing_trades'] == 1
        assert stats['win_rate'] == 75.0

    def test_empty_trades(self):
        """Test with empty trades DataFrame."""
        trades_df = pd.DataFrame()
        history_df = pd.DataFrame()

        metrics = PerformanceMetrics()
        result = metrics.calculate_all(trades_df, history_df)

        assert result['total_trades'] == 0
        assert result['win_rate'] == 0


def test_integration_backtest_flow():
    """Integration test for complete backtest flow."""
    from src.backtest_engine import BacktestEngine

    # Create test data
    np.random.seed(42)
    n_markets = 10

    markets = []
    base_time = datetime.now() - timedelta(days=1)

    for i in range(n_markets):
        start = base_time + timedelta(minutes=15 * i)
        end = start + timedelta(minutes=15)

        markets.append({
            'market_id': f'market_{i}',
            'condition_id': f'cond_{i}',
            'question': f'Test Market {i}',
            'start_time': start,
            'end_time': end,
            'outcome': 'Up' if np.random.random() > 0.5 else 'Down',
            'yes_token_id': f'yes_{i}',
            'no_token_id': f'no_{i}',
            'volume': 1000,
            'liquidity': 5000,
        })

    markets_df = pd.DataFrame(markets)

    # Create prices with opportunity
    prices = []
    for market in markets:
        for j in range(5):
            ts = pd.to_datetime(market['start_time']) + timedelta(minutes=j * 3)
            prices.append({
                'timestamp': ts,
                'market_id': market['market_id'],
                'price_yes': 0.48 + np.random.normal(0, 0.01),
                'price_no': 0.49 + np.random.normal(0, 0.01),
            })

    prices_df = pd.DataFrame(prices)
    prices_df['spread'] = prices_df['price_yes'] + prices_df['price_no'] - 1.0

    # Run backtest
    engine = BacktestEngine(initial_capital=5000)
    results = engine.run(markets_df, prices_df, verbose=False)

    # Verify results
    assert 'summary' in results
    assert 'metrics' in results
    assert 'trades' in results
    assert results['summary']['initial_capital'] == 5000


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
