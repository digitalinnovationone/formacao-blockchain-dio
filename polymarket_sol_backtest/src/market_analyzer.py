"""
Market Analyzer for SOL 15-min Markets
Analyzes market patterns, outcomes, and liquidity
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class MarketAnalyzer:
    """Analyzer for Polymarket SOL markets."""

    def __init__(self, markets_df: pd.DataFrame, prices_df: Optional[pd.DataFrame] = None):
        """
        Initialize analyzer.

        Args:
            markets_df: DataFrame with market information
            prices_df: Optional DataFrame with price history
        """
        self.markets = markets_df.copy()
        self.prices = prices_df.copy() if prices_df is not None else None

        # Ensure datetime columns
        if 'start_time' in self.markets.columns:
            self.markets['start_time'] = pd.to_datetime(self.markets['start_time'])
        if 'end_time' in self.markets.columns:
            self.markets['end_time'] = pd.to_datetime(self.markets['end_time'])

    def analyze_outcomes(self) -> Dict[str, Any]:
        """
        Analyze market outcomes distribution.

        Returns:
            Dictionary with outcome statistics
        """
        if 'outcome' not in self.markets.columns:
            return {"error": "No outcome data available"}

        outcomes = self.markets['outcome'].dropna()
        total = len(outcomes)

        if total == 0:
            return {"error": "No outcome data"}

        up_count = (outcomes.str.lower() == 'up').sum()
        down_count = (outcomes.str.lower() == 'down').sum()

        # Calculate streaks
        outcomes_binary = (outcomes.str.lower() == 'up').astype(int)
        streaks = self._calculate_streaks(outcomes_binary)

        # Autocorrelation
        if len(outcomes_binary) > 1:
            autocorr = outcomes_binary.autocorr(lag=1)
        else:
            autocorr = None

        return {
            "total_markets": total,
            "up_count": up_count,
            "down_count": down_count,
            "pct_up": up_count / total * 100,
            "pct_down": down_count / total * 100,
            "max_up_streak": streaks.get("max_up_streak", 0),
            "max_down_streak": streaks.get("max_down_streak", 0),
            "avg_streak_length": streaks.get("avg_streak", 0),
            "autocorrelation": autocorr,
        }

    def _calculate_streaks(self, binary_series: pd.Series) -> Dict[str, float]:
        """Calculate streak statistics."""
        if len(binary_series) == 0:
            return {"max_up_streak": 0, "max_down_streak": 0, "avg_streak": 0}

        values = binary_series.values
        streaks_up = []
        streaks_down = []
        current_streak = 1
        current_value = values[0]

        for i in range(1, len(values)):
            if values[i] == current_value:
                current_streak += 1
            else:
                if current_value == 1:
                    streaks_up.append(current_streak)
                else:
                    streaks_down.append(current_streak)
                current_streak = 1
                current_value = values[i]

        # Don't forget the last streak
        if current_value == 1:
            streaks_up.append(current_streak)
        else:
            streaks_down.append(current_streak)

        all_streaks = streaks_up + streaks_down

        return {
            "max_up_streak": max(streaks_up) if streaks_up else 0,
            "max_down_streak": max(streaks_down) if streaks_down else 0,
            "avg_streak": np.mean(all_streaks) if all_streaks else 0,
        }

    def analyze_liquidity(self) -> Dict[str, Any]:
        """
        Analyze market liquidity patterns.

        Returns:
            Dictionary with liquidity statistics
        """
        if 'volume' not in self.markets.columns:
            return {"error": "No volume data available"}

        volume = self.markets['volume'].dropna()

        stats = {
            "avg_volume_per_market": volume.mean(),
            "median_volume_per_market": volume.median(),
            "min_volume": volume.min(),
            "max_volume": volume.max(),
            "std_volume": volume.std(),
            "total_volume": volume.sum(),
        }

        # Volume by hour
        if 'start_time' in self.markets.columns:
            self.markets['hour'] = self.markets['start_time'].dt.hour
            self.markets['weekday'] = self.markets['start_time'].dt.dayofweek

            stats["volume_by_hour"] = (
                self.markets.groupby('hour')['volume'].mean().to_dict()
            )
            stats["volume_by_weekday"] = (
                self.markets.groupby('weekday')['volume'].mean().to_dict()
            )

        # Correlation with spread (if available)
        if self.prices is not None and 'spread' in self.prices.columns:
            merged = self.markets.merge(
                self.prices.groupby('market_id')['spread'].mean().reset_index(),
                on='market_id',
                how='inner'
            )
            if len(merged) > 1:
                stats["correlation_volume_spread"] = merged['volume'].corr(merged['spread'])

        return stats

    def analyze_temporal_patterns(self) -> Dict[str, Any]:
        """
        Analyze temporal patterns in markets.

        Returns:
            Dictionary with temporal analysis
        """
        if 'start_time' not in self.markets.columns:
            return {"error": "No timestamp data available"}

        self.markets['hour'] = self.markets['start_time'].dt.hour
        self.markets['weekday'] = self.markets['start_time'].dt.dayofweek
        self.markets['date'] = self.markets['start_time'].dt.date

        return {
            "markets_by_hour": self.markets.groupby('hour').size().to_dict(),
            "markets_by_weekday": self.markets.groupby('weekday').size().to_dict(),
            "markets_per_day": self.markets.groupby('date').size().describe().to_dict(),
            "date_range": {
                "start": str(self.markets['start_time'].min()),
                "end": str(self.markets['start_time'].max()),
            },
            "total_days": self.markets['date'].nunique(),
            "total_markets": len(self.markets),
            "avg_markets_per_day": len(self.markets) / max(1, self.markets['date'].nunique()),
        }

    def get_market_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive market summary.

        Returns:
            Dictionary with full market analysis
        """
        return {
            "outcomes": self.analyze_outcomes(),
            "liquidity": self.analyze_liquidity(),
            "temporal": self.analyze_temporal_patterns(),
        }

    def find_best_trading_windows(self, top_n: int = 5) -> pd.DataFrame:
        """
        Find best trading windows based on volume and spread.

        Args:
            top_n: Number of top windows to return

        Returns:
            DataFrame with best trading windows
        """
        if 'start_time' not in self.markets.columns:
            return pd.DataFrame()

        self.markets['hour'] = self.markets['start_time'].dt.hour
        self.markets['weekday'] = self.markets['start_time'].dt.dayofweek

        # Group by hour and weekday
        grouped = self.markets.groupby(['weekday', 'hour']).agg({
            'volume': 'mean',
            'market_id': 'count'
        }).reset_index()

        grouped.columns = ['weekday', 'hour', 'avg_volume', 'market_count']

        # Add spread if available
        if self.prices is not None and 'spread' in self.prices.columns:
            self.prices['hour'] = pd.to_datetime(self.prices['timestamp']).dt.hour
            self.prices['weekday'] = pd.to_datetime(self.prices['timestamp']).dt.dayofweek

            spread_by_time = self.prices.groupby(['weekday', 'hour'])['spread'].mean().reset_index()
            grouped = grouped.merge(spread_by_time, on=['weekday', 'hour'], how='left')

            # Score: higher volume and lower (more negative) spread is better
            grouped['score'] = grouped['avg_volume'] * (-grouped['spread'])
            grouped = grouped.sort_values('score', ascending=False)
        else:
            grouped = grouped.sort_values('avg_volume', ascending=False)

        return grouped.head(top_n)
