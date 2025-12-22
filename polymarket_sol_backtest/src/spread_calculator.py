"""
Spread Calculator for AMM Delta-Neutral Strategy
Analyzes spreads and identifies trading opportunities
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class SpreadCalculator:
    """Calculator for spread analysis."""

    def __init__(self, prices_df: pd.DataFrame):
        """
        Initialize with price data.

        Args:
            prices_df: DataFrame with columns [timestamp, market_id, price_yes, price_no]
        """
        self.prices = prices_df.copy()

        if 'spread' not in self.prices.columns:
            self.prices['spread'] = (
                self.prices['price_yes'] + self.prices['price_no'] - 1.0
            )

    def calculate_spread_stats(self) -> Dict[str, Any]:
        """
        Calculate comprehensive spread statistics.

        Returns:
            Dictionary with spread statistics
        """
        spreads = self.prices['spread'].dropna()

        stats = {
            # Basic distribution
            "mean": spreads.mean(),
            "std": spreads.std(),
            "min": spreads.min(),
            "max": spreads.max(),
            "median": spreads.median(),

            # Percentiles
            "p5": spreads.quantile(0.05),
            "p25": spreads.quantile(0.25),
            "p75": spreads.quantile(0.75),
            "p95": spreads.quantile(0.95),

            # Opportunities (negative spread = profit opportunity)
            "pct_below_99": (spreads < -0.01).mean() * 100,  # YES+NO < 0.99
            "pct_below_98": (spreads < -0.02).mean() * 100,  # YES+NO < 0.98
            "pct_below_97": (spreads < -0.03).mean() * 100,  # YES+NO < 0.97

            # Count
            "total_observations": len(spreads),
        }

        # Temporal analysis
        if 'timestamp' in self.prices.columns:
            self.prices['hour'] = pd.to_datetime(self.prices['timestamp']).dt.hour
            self.prices['weekday'] = pd.to_datetime(self.prices['timestamp']).dt.dayofweek

            stats["avg_spread_by_hour"] = (
                self.prices.groupby('hour')['spread'].mean().to_dict()
            )
            stats["avg_spread_by_weekday"] = (
                self.prices.groupby('weekday')['spread'].mean().to_dict()
            )

        # Per market analysis
        if 'market_id' in self.prices.columns:
            market_spreads = self.prices.groupby('market_id')['spread'].mean()
            stats["avg_spread_per_market"] = market_spreads.mean()
            stats["markets_with_opportunity"] = (market_spreads < -0.02).sum()
            stats["total_markets"] = len(market_spreads)

        return stats

    def find_opportunities(
        self,
        min_spread: float = -0.02,
        min_volume: Optional[float] = None
    ) -> pd.DataFrame:
        """
        Find trading opportunities based on spread threshold.

        Args:
            min_spread: Maximum spread (negative = opportunity)
            min_volume: Minimum volume filter

        Returns:
            DataFrame with opportunities
        """
        opportunities = self.prices[self.prices['spread'] <= min_spread].copy()

        if min_volume and 'volume' in opportunities.columns:
            opportunities = opportunities[opportunities['volume'] >= min_volume]

        return opportunities.sort_values('spread')

    def get_best_hours(self, top_n: int = 5) -> pd.Series:
        """
        Get best hours to trade based on average spread.

        Args:
            top_n: Number of top hours to return

        Returns:
            Series with best hours and their average spreads
        """
        if 'hour' not in self.prices.columns:
            self.prices['hour'] = pd.to_datetime(self.prices['timestamp']).dt.hour

        hourly_avg = self.prices.groupby('hour')['spread'].mean()
        return hourly_avg.nsmallest(top_n)

    def calculate_expected_profit(
        self,
        price_yes: float,
        price_no: float,
        shares: int = 100
    ) -> Dict[str, float]:
        """
        Calculate expected profit for a delta-neutral position.

        Args:
            price_yes: YES token price
            price_no: NO token price
            shares: Number of shares to buy of each

        Returns:
            Dictionary with profit calculations
        """
        cost_yes = shares * price_yes
        cost_no = shares * price_no
        total_cost = cost_yes + cost_no

        # At settlement, one side pays $1 per share
        guaranteed_payout = shares  # min(shares, shares) = shares

        profit = guaranteed_payout - total_cost
        roi = profit / total_cost if total_cost > 0 else 0

        return {
            "cost_yes": cost_yes,
            "cost_no": cost_no,
            "total_cost": total_cost,
            "guaranteed_payout": guaranteed_payout,
            "profit": profit,
            "roi": roi,
            "roi_pct": roi * 100,
            "spread": price_yes + price_no - 1.0,
        }


def analyze_spreads(prices_path: str) -> Dict[str, Any]:
    """
    Analyze spreads from a prices file.

    Args:
        prices_path: Path to prices parquet or CSV file

    Returns:
        Spread statistics
    """
    if prices_path.endswith('.parquet'):
        prices_df = pd.read_parquet(prices_path)
    else:
        prices_df = pd.read_csv(prices_path)

    calculator = SpreadCalculator(prices_df)
    return calculator.calculate_spread_stats()
