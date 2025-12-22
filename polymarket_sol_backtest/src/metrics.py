"""
Performance Metrics for AMM Delta-Neutral Strategy Backtest
Calculates comprehensive trading metrics
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


# Expected metrics for benchmarking
EXPECTED_METRICS = {
    # Optimistic targets
    "target_monthly_return": 0.05,     # 5% per month
    "target_win_rate": 0.85,           # 85% winning trades
    "target_sharpe": 2.0,              # Sharpe ratio > 2
    "target_max_drawdown": 0.10,       # Max drawdown < 10%
    "target_profit_factor": 3.0,       # Profit factor > 3

    # Realistic expectations
    "realistic_monthly_return": 0.02,  # 2% per month
    "realistic_win_rate": 0.70,        # 70% win rate
    "realistic_sharpe": 1.0,           # Sharpe ~ 1
    "realistic_max_drawdown": 0.15,    # Max drawdown ~ 15%
}


class PerformanceMetrics:
    """Calculator for backtest performance metrics."""

    def __init__(self, risk_free_rate: float = 0.05):
        """
        Initialize metrics calculator.

        Args:
            risk_free_rate: Annual risk-free rate for Sharpe calculation
        """
        self.risk_free_rate = risk_free_rate

    def calculate_all(
        self,
        trades_df: pd.DataFrame,
        portfolio_history: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Calculate all performance metrics.

        Args:
            trades_df: DataFrame with trade records
            portfolio_history: DataFrame with portfolio snapshots

        Returns:
            Dictionary with all metrics
        """
        metrics = {}

        # Return metrics
        metrics.update(self._calculate_return_metrics(trades_df, portfolio_history))

        # Risk metrics
        metrics.update(self._calculate_risk_metrics(portfolio_history))

        # Trade statistics
        metrics.update(self._calculate_trade_stats(trades_df))

        # Spread analysis
        metrics.update(self._calculate_spread_metrics(trades_df))

        # Balance analysis
        metrics.update(self._calculate_balance_metrics(trades_df))

        # Exposure analysis
        metrics.update(self._calculate_exposure_metrics(portfolio_history))

        # Benchmark comparison
        metrics["benchmark"] = self._compare_to_benchmark(metrics)

        return metrics

    def _calculate_return_metrics(
        self,
        trades_df: pd.DataFrame,
        portfolio_history: pd.DataFrame
    ) -> Dict[str, Any]:
        """Calculate return-related metrics."""
        metrics = {}

        if trades_df.empty:
            return {
                "total_return_usd": 0,
                "total_return_pct": 0,
                "avg_return_per_trade": 0,
                "avg_return_per_day": 0,
            }

        # Total return
        total_profit = trades_df['profit'].sum()
        total_cost = trades_df['cost'].sum()

        metrics["total_return_usd"] = total_profit
        metrics["total_return_pct"] = (total_profit / total_cost * 100) if total_cost > 0 else 0

        # Average return per trade
        metrics["avg_return_per_trade"] = trades_df['profit'].mean()
        metrics["avg_roi_per_trade"] = trades_df['roi'].mean() * 100

        # Daily returns
        if not portfolio_history.empty and 'timestamp' in portfolio_history.columns:
            portfolio_history['date'] = pd.to_datetime(portfolio_history['timestamp']).dt.date
            daily_values = portfolio_history.groupby('date')['total_value'].last()

            if len(daily_values) > 1:
                daily_returns = daily_values.pct_change().dropna()
                metrics["avg_return_per_day"] = daily_returns.mean() * 100
                metrics["total_days"] = len(daily_values)
            else:
                metrics["avg_return_per_day"] = 0
                metrics["total_days"] = 1
        else:
            metrics["avg_return_per_day"] = 0
            metrics["total_days"] = 0

        return metrics

    def _calculate_risk_metrics(
        self,
        portfolio_history: pd.DataFrame
    ) -> Dict[str, Any]:
        """Calculate risk-related metrics."""
        metrics = {}

        if portfolio_history.empty or 'total_value' not in portfolio_history.columns:
            return {
                "max_drawdown_usd": 0,
                "max_drawdown_pct": 0,
                "volatility": 0,
                "sharpe_ratio": 0,
                "sortino_ratio": 0,
            }

        values = portfolio_history['total_value'].values

        # Maximum drawdown
        peak = np.maximum.accumulate(values)
        drawdown = (peak - values)
        drawdown_pct = drawdown / peak

        metrics["max_drawdown_usd"] = drawdown.max()
        metrics["max_drawdown_pct"] = drawdown_pct.max() * 100

        # Volatility (annualized)
        if len(values) > 1:
            returns = np.diff(values) / values[:-1]
            metrics["volatility"] = returns.std() * np.sqrt(252) * 100  # Annualized

            # Sharpe ratio
            if metrics["volatility"] > 0:
                avg_return = returns.mean() * 252  # Annualized
                metrics["sharpe_ratio"] = (avg_return - self.risk_free_rate) / (returns.std() * np.sqrt(252))
            else:
                metrics["sharpe_ratio"] = 0

            # Sortino ratio (downside deviation)
            negative_returns = returns[returns < 0]
            if len(negative_returns) > 0:
                downside_std = negative_returns.std() * np.sqrt(252)
                if downside_std > 0:
                    metrics["sortino_ratio"] = (returns.mean() * 252 - self.risk_free_rate) / downside_std
                else:
                    metrics["sortino_ratio"] = 0
            else:
                metrics["sortino_ratio"] = float('inf')  # No negative returns
        else:
            metrics["volatility"] = 0
            metrics["sharpe_ratio"] = 0
            metrics["sortino_ratio"] = 0

        return metrics

    def _calculate_trade_stats(self, trades_df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate trade statistics."""
        if trades_df.empty:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0,
                "avg_winner": 0,
                "avg_loser": 0,
                "profit_factor": 0,
                "largest_win": 0,
                "largest_loss": 0,
            }

        winners = trades_df[trades_df['profit'] > 0]
        losers = trades_df[trades_df['profit'] < 0]

        total_wins = winners['profit'].sum() if not winners.empty else 0
        total_losses = abs(losers['profit'].sum()) if not losers.empty else 0

        return {
            "total_trades": len(trades_df),
            "winning_trades": len(winners),
            "losing_trades": len(losers),
            "win_rate": len(winners) / len(trades_df) * 100 if len(trades_df) > 0 else 0,
            "avg_winner": winners['profit'].mean() if not winners.empty else 0,
            "avg_loser": losers['profit'].mean() if not losers.empty else 0,
            "profit_factor": total_wins / total_losses if total_losses > 0 else float('inf'),
            "largest_win": winners['profit'].max() if not winners.empty else 0,
            "largest_loss": losers['profit'].min() if not losers.empty else 0,
        }

    def _calculate_spread_metrics(self, trades_df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate spread-related metrics."""
        if trades_df.empty or 'entry_spread' not in trades_df.columns:
            return {
                "avg_entry_spread": 0,
                "avg_spread_captured": 0,
                "best_entry_spread": 0,
                "worst_entry_spread": 0,
            }

        return {
            "avg_entry_spread": trades_df['entry_spread'].mean(),
            "avg_spread_captured": -trades_df['entry_spread'].mean(),  # Negative spread = profit
            "best_entry_spread": trades_df['entry_spread'].min(),
            "worst_entry_spread": trades_df['entry_spread'].max(),
        }

    def _calculate_balance_metrics(self, trades_df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate YES/NO balance metrics."""
        if trades_df.empty:
            return {
                "avg_yes_no_ratio": 0,
                "pct_balanced_trades": 0,
            }

        if 'shares_yes' in trades_df.columns and 'shares_no' in trades_df.columns:
            ratios = trades_df['shares_yes'] / trades_df['shares_no'].replace(0, np.nan)
            ratios = ratios.dropna()

            # Balanced = ratio between 0.9 and 1.1
            balanced = ((ratios >= 0.9) & (ratios <= 1.1)).sum()

            return {
                "avg_yes_no_ratio": ratios.mean() if not ratios.empty else 0,
                "pct_balanced_trades": balanced / len(ratios) * 100 if len(ratios) > 0 else 0,
            }

        return {
            "avg_yes_no_ratio": 0,
            "pct_balanced_trades": 0,
        }

    def _calculate_exposure_metrics(
        self,
        portfolio_history: pd.DataFrame
    ) -> Dict[str, Any]:
        """Calculate exposure metrics."""
        if portfolio_history.empty:
            return {
                "avg_exposure": 0,
                "max_exposure": 0,
                "avg_markets_active": 0,
            }

        metrics = {}

        if 'exposure' in portfolio_history.columns:
            metrics["avg_exposure"] = portfolio_history['exposure'].mean() * 100
            metrics["max_exposure"] = portfolio_history['exposure'].max() * 100
        else:
            metrics["avg_exposure"] = 0
            metrics["max_exposure"] = 0

        if 'active_markets' in portfolio_history.columns:
            metrics["avg_markets_active"] = portfolio_history['active_markets'].mean()
        else:
            metrics["avg_markets_active"] = 0

        return metrics

    def _compare_to_benchmark(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Compare metrics to benchmark expectations."""
        comparison = {}

        # Win rate comparison
        win_rate = metrics.get("win_rate", 0)
        comparison["win_rate_vs_target"] = win_rate - EXPECTED_METRICS["target_win_rate"] * 100
        comparison["win_rate_vs_realistic"] = win_rate - EXPECTED_METRICS["realistic_win_rate"] * 100

        # Sharpe comparison
        sharpe = metrics.get("sharpe_ratio", 0)
        comparison["sharpe_vs_target"] = sharpe - EXPECTED_METRICS["target_sharpe"]
        comparison["sharpe_vs_realistic"] = sharpe - EXPECTED_METRICS["realistic_sharpe"]

        # Drawdown comparison
        max_dd = metrics.get("max_drawdown_pct", 0) / 100
        comparison["drawdown_vs_target"] = EXPECTED_METRICS["target_max_drawdown"] - max_dd
        comparison["drawdown_vs_realistic"] = EXPECTED_METRICS["realistic_max_drawdown"] - max_dd

        # Overall assessment
        score = 0
        if win_rate >= EXPECTED_METRICS["realistic_win_rate"] * 100:
            score += 1
        if sharpe >= EXPECTED_METRICS["realistic_sharpe"]:
            score += 1
        if max_dd <= EXPECTED_METRICS["realistic_max_drawdown"]:
            score += 1

        comparison["overall_score"] = score
        comparison["assessment"] = (
            "Excellent" if score == 3 else
            "Good" if score == 2 else
            "Needs Improvement" if score == 1 else
            "Poor"
        )

        return comparison

    def generate_summary_report(self, metrics: Dict[str, Any]) -> str:
        """Generate a text summary report."""
        report = []
        report.append("=" * 60)
        report.append("BACKTEST PERFORMANCE REPORT")
        report.append("=" * 60)
        report.append("")

        # Returns
        report.append("RETURNS")
        report.append("-" * 40)
        report.append(f"Total Return: ${metrics.get('total_return_usd', 0):.2f}")
        report.append(f"Total Return %: {metrics.get('total_return_pct', 0):.2f}%")
        report.append(f"Avg Return/Trade: ${metrics.get('avg_return_per_trade', 0):.2f}")
        report.append("")

        # Risk
        report.append("RISK METRICS")
        report.append("-" * 40)
        report.append(f"Max Drawdown: ${metrics.get('max_drawdown_usd', 0):.2f} ({metrics.get('max_drawdown_pct', 0):.2f}%)")
        report.append(f"Volatility (Ann.): {metrics.get('volatility', 0):.2f}%")
        report.append(f"Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
        report.append(f"Sortino Ratio: {metrics.get('sortino_ratio', 0):.2f}")
        report.append("")

        # Trades
        report.append("TRADE STATISTICS")
        report.append("-" * 40)
        report.append(f"Total Trades: {metrics.get('total_trades', 0)}")
        report.append(f"Winning Trades: {metrics.get('winning_trades', 0)}")
        report.append(f"Losing Trades: {metrics.get('losing_trades', 0)}")
        report.append(f"Win Rate: {metrics.get('win_rate', 0):.2f}%")
        report.append(f"Profit Factor: {metrics.get('profit_factor', 0):.2f}")
        report.append("")

        # Benchmark
        benchmark = metrics.get('benchmark', {})
        report.append("BENCHMARK COMPARISON")
        report.append("-" * 40)
        report.append(f"Assessment: {benchmark.get('assessment', 'N/A')}")
        report.append(f"Overall Score: {benchmark.get('overall_score', 0)}/3")
        report.append("")

        report.append("=" * 60)

        return "\n".join(report)
