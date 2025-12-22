"""
Visualizer for AMM Delta-Neutral Strategy Backtest
Generates charts and visual reports
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")


class BacktestVisualizer:
    """Visualizer for backtest results."""

    def __init__(self, figsize: tuple = (12, 6), dpi: int = 100):
        """
        Initialize visualizer.

        Args:
            figsize: Default figure size
            dpi: Figure resolution
        """
        self.figsize = figsize
        self.dpi = dpi

    def generate_all_charts(
        self,
        results: Dict[str, Any],
        output_dir: str = "reports/charts"
    ) -> List[str]:
        """
        Generate all charts for the backtest results.

        Args:
            results: Backtest results dictionary
            output_dir: Directory to save charts

        Returns:
            List of saved chart paths
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        saved_charts = []

        trades_df = results.get('trades', pd.DataFrame())
        history_df = results.get('portfolio_history', pd.DataFrame())
        metrics = results.get('metrics', {})

        # Generate each chart
        try:
            path = self.plot_equity_curve(history_df, output_path / "equity_curve.png")
            saved_charts.append(str(path))
        except Exception as e:
            logger.warning(f"Failed to generate equity curve: {e}")

        try:
            path = self.plot_drawdown(history_df, output_path / "drawdown.png")
            saved_charts.append(str(path))
        except Exception as e:
            logger.warning(f"Failed to generate drawdown chart: {e}")

        try:
            path = self.plot_returns_distribution(trades_df, output_path / "returns_dist.png")
            saved_charts.append(str(path))
        except Exception as e:
            logger.warning(f"Failed to generate returns distribution: {e}")

        try:
            path = self.plot_monthly_returns(trades_df, output_path / "monthly_returns.png")
            saved_charts.append(str(path))
        except Exception as e:
            logger.warning(f"Failed to generate monthly returns: {e}")

        try:
            path = self.plot_win_rate_by_spread(trades_df, output_path / "win_rate_spread.png")
            saved_charts.append(str(path))
        except Exception as e:
            logger.warning(f"Failed to generate win rate by spread: {e}")

        try:
            path = self.plot_exposure_over_time(history_df, output_path / "exposure.png")
            saved_charts.append(str(path))
        except Exception as e:
            logger.warning(f"Failed to generate exposure chart: {e}")

        try:
            path = self.plot_metrics_summary(metrics, output_path / "metrics_summary.png")
            saved_charts.append(str(path))
        except Exception as e:
            logger.warning(f"Failed to generate metrics summary: {e}")

        logger.info(f"Generated {len(saved_charts)} charts in {output_dir}")
        return saved_charts

    def plot_equity_curve(
        self,
        history_df: pd.DataFrame,
        save_path: Optional[str] = None
    ) -> Optional[str]:
        """Plot equity curve over time."""
        if history_df.empty or 'total_value' not in history_df.columns:
            return None

        fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)

        history_df['timestamp'] = pd.to_datetime(history_df['timestamp'])
        ax.plot(history_df['timestamp'], history_df['total_value'], linewidth=2, color='#2ecc71')
        ax.fill_between(history_df['timestamp'], history_df['total_value'],
                       alpha=0.3, color='#2ecc71')

        # Add initial capital line
        initial = history_df['total_value'].iloc[0]
        ax.axhline(y=initial, color='gray', linestyle='--', alpha=0.5, label='Initial Capital')

        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Portfolio Value ($)', fontsize=12)
        ax.set_title('Equity Curve', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            plt.close()
            return str(save_path)

        plt.show()
        return None

    def plot_drawdown(
        self,
        history_df: pd.DataFrame,
        save_path: Optional[str] = None
    ) -> Optional[str]:
        """Plot drawdown over time."""
        if history_df.empty or 'total_value' not in history_df.columns:
            return None

        fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)

        values = history_df['total_value'].values
        peak = np.maximum.accumulate(values)
        drawdown = (values - peak) / peak * 100

        history_df['timestamp'] = pd.to_datetime(history_df['timestamp'])
        ax.fill_between(history_df['timestamp'], drawdown, 0,
                       color='#e74c3c', alpha=0.7)
        ax.plot(history_df['timestamp'], drawdown, color='#c0392b', linewidth=1)

        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Drawdown (%)', fontsize=12)
        ax.set_title('Drawdown Over Time', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            plt.close()
            return str(save_path)

        plt.show()
        return None

    def plot_returns_distribution(
        self,
        trades_df: pd.DataFrame,
        save_path: Optional[str] = None
    ) -> Optional[str]:
        """Plot distribution of trade returns."""
        if trades_df.empty or 'profit' not in trades_df.columns:
            return None

        fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)

        profits = trades_df['profit']

        # Histogram
        ax.hist(profits, bins=30, color='#3498db', alpha=0.7, edgecolor='black')

        # Add mean line
        mean_profit = profits.mean()
        ax.axvline(x=mean_profit, color='#e74c3c', linestyle='--',
                  linewidth=2, label=f'Mean: ${mean_profit:.2f}')
        ax.axvline(x=0, color='black', linestyle='-', linewidth=1, alpha=0.5)

        ax.set_xlabel('Profit ($)', fontsize=12)
        ax.set_ylabel('Frequency', fontsize=12)
        ax.set_title('Distribution of Trade Returns', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            plt.close()
            return str(save_path)

        plt.show()
        return None

    def plot_monthly_returns(
        self,
        trades_df: pd.DataFrame,
        save_path: Optional[str] = None
    ) -> Optional[str]:
        """Plot monthly returns bar chart."""
        if trades_df.empty or 'exit_time' not in trades_df.columns:
            return None

        fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)

        trades_df['exit_time'] = pd.to_datetime(trades_df['exit_time'])
        trades_df['month'] = trades_df['exit_time'].dt.to_period('M')

        monthly_returns = trades_df.groupby('month')['profit'].sum()

        colors = ['#2ecc71' if x >= 0 else '#e74c3c' for x in monthly_returns.values]
        bars = ax.bar(range(len(monthly_returns)), monthly_returns.values, color=colors)

        ax.set_xticks(range(len(monthly_returns)))
        ax.set_xticklabels([str(m) for m in monthly_returns.index], rotation=45)
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)

        ax.set_xlabel('Month', fontsize=12)
        ax.set_ylabel('Profit ($)', fontsize=12)
        ax.set_title('Monthly Returns', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            plt.close()
            return str(save_path)

        plt.show()
        return None

    def plot_win_rate_by_spread(
        self,
        trades_df: pd.DataFrame,
        save_path: Optional[str] = None
    ) -> Optional[str]:
        """Plot win rate by entry spread."""
        if trades_df.empty or 'entry_spread' not in trades_df.columns:
            return None

        fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)

        # Create spread buckets
        trades_df['spread_bucket'] = pd.cut(
            trades_df['entry_spread'],
            bins=[-0.10, -0.05, -0.03, -0.02, -0.01, 0, 0.05],
            labels=['<-5%', '-5% to -3%', '-3% to -2%', '-2% to -1%', '-1% to 0%', '>0%']
        )

        trades_df['is_winner'] = trades_df['profit'] > 0

        win_rates = trades_df.groupby('spread_bucket')['is_winner'].mean() * 100
        counts = trades_df.groupby('spread_bucket').size()

        bars = ax.bar(range(len(win_rates)), win_rates.values, color='#3498db', alpha=0.8)

        # Add count labels
        for i, (bar, count) in enumerate(zip(bars, counts.values)):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                   f'n={count}', ha='center', va='bottom', fontsize=9)

        ax.set_xticks(range(len(win_rates)))
        ax.set_xticklabels(win_rates.index, rotation=45)
        ax.axhline(y=50, color='gray', linestyle='--', alpha=0.5, label='50% baseline')

        ax.set_xlabel('Entry Spread', fontsize=12)
        ax.set_ylabel('Win Rate (%)', fontsize=12)
        ax.set_title('Win Rate by Entry Spread', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        ax.set_ylim(0, 100)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            plt.close()
            return str(save_path)

        plt.show()
        return None

    def plot_exposure_over_time(
        self,
        history_df: pd.DataFrame,
        save_path: Optional[str] = None
    ) -> Optional[str]:
        """Plot exposure over time."""
        if history_df.empty or 'exposure' not in history_df.columns:
            return None

        fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)

        history_df['timestamp'] = pd.to_datetime(history_df['timestamp'])
        ax.fill_between(history_df['timestamp'], history_df['exposure'] * 100, 0,
                       color='#9b59b6', alpha=0.6)
        ax.plot(history_df['timestamp'], history_df['exposure'] * 100,
               color='#8e44ad', linewidth=1)

        # Max exposure line
        ax.axhline(y=70, color='#e74c3c', linestyle='--',
                  alpha=0.7, label='Max Exposure (70%)')

        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Exposure (%)', fontsize=12)
        ax.set_title('Portfolio Exposure Over Time', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 100)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            plt.close()
            return str(save_path)

        plt.show()
        return None

    def plot_metrics_summary(
        self,
        metrics: Dict[str, Any],
        save_path: Optional[str] = None
    ) -> Optional[str]:
        """Plot metrics summary as a table/dashboard."""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10), dpi=self.dpi)

        # 1. Key metrics table
        ax1 = axes[0, 0]
        ax1.axis('off')

        key_metrics = [
            ('Total Return', f"${metrics.get('total_return_usd', 0):.2f}"),
            ('Return %', f"{metrics.get('total_return_pct', 0):.2f}%"),
            ('Win Rate', f"{metrics.get('win_rate', 0):.1f}%"),
            ('Sharpe Ratio', f"{metrics.get('sharpe_ratio', 0):.2f}"),
            ('Max Drawdown', f"{metrics.get('max_drawdown_pct', 0):.2f}%"),
            ('Profit Factor', f"{metrics.get('profit_factor', 0):.2f}"),
            ('Total Trades', f"{metrics.get('total_trades', 0)}"),
        ]

        table = ax1.table(
            cellText=[[m[0], m[1]] for m in key_metrics],
            colLabels=['Metric', 'Value'],
            loc='center',
            cellLoc='center',
            colWidths=[0.5, 0.3]
        )
        table.auto_set_font_size(False)
        table.set_fontsize(11)
        table.scale(1.2, 1.8)
        ax1.set_title('Key Performance Metrics', fontsize=14, fontweight='bold', pad=20)

        # 2. Win/Loss pie chart
        ax2 = axes[0, 1]
        wins = metrics.get('winning_trades', 0)
        losses = metrics.get('losing_trades', 0)

        if wins + losses > 0:
            ax2.pie([wins, losses], labels=['Wins', 'Losses'],
                   colors=['#2ecc71', '#e74c3c'], autopct='%1.1f%%',
                   startangle=90)
            ax2.set_title('Win/Loss Distribution', fontsize=14, fontweight='bold')

        # 3. Benchmark comparison
        ax3 = axes[1, 0]
        benchmark = metrics.get('benchmark', {})

        categories = ['Win Rate', 'Sharpe', 'Drawdown']
        actual = [
            metrics.get('win_rate', 0),
            metrics.get('sharpe_ratio', 0) * 50,  # Scale for visibility
            100 - metrics.get('max_drawdown_pct', 0)  # Invert for "better = higher"
        ]
        target = [85, 100, 90]  # Target values (scaled)

        x = np.arange(len(categories))
        width = 0.35

        ax3.bar(x - width/2, actual, width, label='Actual', color='#3498db')
        ax3.bar(x + width/2, target, width, label='Target', color='#95a5a6', alpha=0.7)

        ax3.set_xticks(x)
        ax3.set_xticklabels(categories)
        ax3.legend()
        ax3.set_title('Performance vs Target', fontsize=14, fontweight='bold')
        ax3.grid(True, alpha=0.3, axis='y')

        # 4. Assessment
        ax4 = axes[1, 1]
        ax4.axis('off')

        assessment = benchmark.get('assessment', 'N/A')
        score = benchmark.get('overall_score', 0)

        color = '#2ecc71' if score >= 2 else '#f39c12' if score == 1 else '#e74c3c'

        ax4.text(0.5, 0.6, assessment, fontsize=36, fontweight='bold',
                ha='center', va='center', color=color)
        ax4.text(0.5, 0.3, f'Score: {score}/3', fontsize=18,
                ha='center', va='center', color='gray')
        ax4.set_title('Overall Assessment', fontsize=14, fontweight='bold')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            plt.close()
            return str(save_path)

        plt.show()
        return None


def generate_report(results: Dict[str, Any], output_dir: str = "reports") -> str:
    """
    Generate complete visual report.

    Args:
        results: Backtest results
        output_dir: Output directory

    Returns:
        Path to report directory
    """
    visualizer = BacktestVisualizer()
    charts = visualizer.generate_all_charts(results, f"{output_dir}/charts")

    logger.info(f"Report generated in {output_dir}")
    return output_dir
