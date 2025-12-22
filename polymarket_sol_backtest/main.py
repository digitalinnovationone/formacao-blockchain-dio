#!/usr/bin/env python3
"""
AMM Delta-Neutral Strategy Backtest
Polymarket SOL 15-min Markets

Main entry point for running the backtest
"""

import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import settings
from config.risk_params import RiskParams
from src.data_collector import DataCollector
from src.backtest_engine import BacktestEngine, run_backtest
from src.metrics import PerformanceMetrics
from src.visualizer import BacktestVisualizer, generate_report
from src.market_analyzer import MarketAnalyzer
from src.spread_calculator import SpreadCalculator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def collect_data(args):
    """Collect market data from Polymarket API."""
    logger.info("Starting data collection...")

    end_date = datetime.now()
    start_date = end_date - timedelta(days=args.days)

    collector = DataCollector()

    try:
        # Fetch markets
        markets_df = collector.fetch_sol_15min_markets(
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            save_path=f"{settings.DATA_RAW_PATH}/sol_markets.csv"
        )

        logger.info(f"Found {len(markets_df)} markets")

        if not markets_df.empty and args.fetch_prices:
            # Fetch prices
            prices_df = collector.fetch_all_prices(
                markets_df,
                save_dir=f"{settings.DATA_RAW_PATH}/price_history"
            )

            if not prices_df.empty:
                # Save consolidated prices
                Path(settings.DATA_PROCESSED_PATH).mkdir(parents=True, exist_ok=True)
                prices_df.to_parquet(
                    f"{settings.DATA_PROCESSED_PATH}/all_prices.parquet",
                    index=False
                )
                logger.info(f"Saved {len(prices_df)} price records")

        logger.info("Data collection complete!")

    finally:
        collector.close()


def run_analysis(args):
    """Run exploratory analysis on collected data."""
    import pandas as pd

    logger.info("Running analysis...")

    # Load data
    markets_path = args.markets or f"{settings.DATA_RAW_PATH}/sol_markets.csv"
    prices_path = args.prices or f"{settings.DATA_PROCESSED_PATH}/all_prices.parquet"

    markets_df = pd.read_csv(markets_path)

    if Path(prices_path).exists():
        if prices_path.endswith('.parquet'):
            prices_df = pd.read_parquet(prices_path)
        else:
            prices_df = pd.read_csv(prices_path)
    else:
        prices_df = None

    # Market analysis
    analyzer = MarketAnalyzer(markets_df, prices_df)
    summary = analyzer.get_market_summary()

    print("\n" + "=" * 60)
    print("MARKET ANALYSIS SUMMARY")
    print("=" * 60)

    print("\n--- Outcomes ---")
    outcomes = summary.get('outcomes', {})
    print(f"Total Markets: {outcomes.get('total_markets', 0)}")
    print(f"Up: {outcomes.get('pct_up', 0):.1f}%")
    print(f"Down: {outcomes.get('pct_down', 0):.1f}%")

    print("\n--- Liquidity ---")
    liquidity = summary.get('liquidity', {})
    print(f"Avg Volume: ${liquidity.get('avg_volume_per_market', 0):.2f}")
    print(f"Median Volume: ${liquidity.get('median_volume_per_market', 0):.2f}")

    print("\n--- Temporal ---")
    temporal = summary.get('temporal', {})
    print(f"Total Days: {temporal.get('total_days', 0)}")
    print(f"Avg Markets/Day: {temporal.get('avg_markets_per_day', 0):.1f}")

    # Spread analysis
    if prices_df is not None:
        spread_calc = SpreadCalculator(prices_df)
        spread_stats = spread_calc.calculate_spread_stats()

        print("\n--- Spread Statistics ---")
        print(f"Mean Spread: {spread_stats.get('mean', 0):.4f}")
        print(f"Median Spread: {spread_stats.get('median', 0):.4f}")
        print(f"% Below 0.98: {spread_stats.get('pct_below_98', 0):.1f}%")
        print(f"% Below 0.97: {spread_stats.get('pct_below_97', 0):.1f}%")

        print("\n--- Best Trading Hours ---")
        best_hours = spread_calc.get_best_hours(5)
        for hour, spread in best_hours.items():
            print(f"  Hour {hour}: avg spread = {spread:.4f}")

    print("\n" + "=" * 60)


def run_backtest_cmd(args):
    """Run the backtest."""
    import pandas as pd

    logger.info("Starting backtest...")

    # Load data
    markets_path = args.markets or f"{settings.DATA_RAW_PATH}/sol_markets.csv"
    prices_path = args.prices or f"{settings.DATA_PROCESSED_PATH}/all_prices.parquet"

    if not Path(markets_path).exists():
        logger.error(f"Markets file not found: {markets_path}")
        logger.info("Run with --collect first to gather data")
        return

    markets_df = pd.read_csv(markets_path)

    if Path(prices_path).exists():
        if prices_path.endswith('.parquet'):
            prices_df = pd.read_parquet(prices_path)
        else:
            prices_df = pd.read_csv(prices_path)
    else:
        logger.warning("No price data found, using simulated prices")
        # Create simulated prices
        prices_df = _create_simulated_prices(markets_df)

    # Setup risk params
    risk_params = RiskParams()

    if args.spread_threshold:
        risk_params.MIN_SPREAD_TO_ENTER = args.spread_threshold

    if args.max_exposure:
        risk_params.MAX_TOTAL_EXPOSURE = args.max_exposure

    # Run backtest
    engine = BacktestEngine(
        initial_capital=args.capital,
        risk_params=risk_params
    )

    results = engine.run(markets_df, prices_df, verbose=True)

    # Print summary
    metrics = PerformanceMetrics()
    report = metrics.generate_summary_report(results['metrics'])
    print(report)

    # Generate visual report
    if args.output:
        output_dir = args.output
    else:
        output_dir = f"{settings.DATA_RESULTS_PATH}/backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    generate_report(results, output_dir)
    logger.info(f"Report saved to {output_dir}")

    # Save results
    results['trades'].to_csv(f"{output_dir}/trades.csv", index=False)
    results['portfolio_history'].to_csv(f"{output_dir}/portfolio_history.csv", index=False)


def _create_simulated_prices(markets_df):
    """Create simulated price data for testing."""
    import pandas as pd
    import numpy as np

    all_prices = []

    for _, market in markets_df.iterrows():
        market_id = market['market_id']
        start = pd.to_datetime(market['start_time'])
        end = pd.to_datetime(market['end_time'])

        # Generate 15 price points
        timestamps = pd.date_range(start, end, periods=15)

        # Random walk around 0.50
        base_yes = 0.50
        base_no = 0.50

        for ts in timestamps:
            # Add some randomness
            price_yes = np.clip(base_yes + np.random.normal(0, 0.02), 0.40, 0.60)
            price_no = np.clip(base_no + np.random.normal(0, 0.02), 0.40, 0.60)

            # Ensure some spread opportunity
            total = price_yes + price_no
            if np.random.random() > 0.7:  # 30% chance of opportunity
                adjustment = np.random.uniform(0.01, 0.04)
                price_yes -= adjustment / 2
                price_no -= adjustment / 2

            all_prices.append({
                'timestamp': ts,
                'market_id': market_id,
                'price_yes': price_yes,
                'price_no': price_no,
                'spread': price_yes + price_no - 1.0,
            })

    return pd.DataFrame(all_prices)


def main():
    parser = argparse.ArgumentParser(
        description='AMM Delta-Neutral Strategy Backtest for Polymarket SOL 15-min Markets'
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Collect command
    collect_parser = subparsers.add_parser('collect', help='Collect market data')
    collect_parser.add_argument('--days', type=int, default=90, help='Days of history')
    collect_parser.add_argument('--fetch-prices', action='store_true', help='Also fetch price history')

    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Run analysis on data')
    analyze_parser.add_argument('--markets', type=str, help='Path to markets CSV')
    analyze_parser.add_argument('--prices', type=str, help='Path to prices file')

    # Backtest command
    backtest_parser = subparsers.add_parser('backtest', help='Run backtest')
    backtest_parser.add_argument('--markets', type=str, help='Path to markets CSV')
    backtest_parser.add_argument('--prices', type=str, help='Path to prices file')
    backtest_parser.add_argument('--capital', type=float, default=5000, help='Initial capital')
    backtest_parser.add_argument('--spread-threshold', type=float, help='Min spread to enter')
    backtest_parser.add_argument('--max-exposure', type=float, help='Max portfolio exposure')
    backtest_parser.add_argument('--output', type=str, help='Output directory')

    # Quick test command
    test_parser = subparsers.add_parser('test', help='Run quick test with simulated data')
    test_parser.add_argument('--capital', type=float, default=5000, help='Initial capital')

    args = parser.parse_args()

    if args.command == 'collect':
        collect_data(args)
    elif args.command == 'analyze':
        run_analysis(args)
    elif args.command == 'backtest':
        run_backtest_cmd(args)
    elif args.command == 'test':
        run_test(args)
    else:
        parser.print_help()


def run_test(args):
    """Run quick test with simulated data."""
    import pandas as pd
    import numpy as np

    logger.info("Running quick test with simulated data...")

    # Create simulated markets
    np.random.seed(42)
    n_markets = 100

    markets = []
    base_time = datetime.now() - timedelta(days=7)

    for i in range(n_markets):
        start = base_time + timedelta(minutes=15 * i)
        end = start + timedelta(minutes=15)

        markets.append({
            'market_id': f'market_{i}',
            'condition_id': f'cond_{i}',
            'question': f'Solana Up or Down - Test {i}',
            'start_time': start,
            'end_time': end,
            'outcome': 'Up' if np.random.random() > 0.5 else 'Down',
            'yes_token_id': f'yes_{i}',
            'no_token_id': f'no_{i}',
            'volume': np.random.uniform(500, 5000),
            'liquidity': np.random.uniform(1000, 10000),
        })

    markets_df = pd.DataFrame(markets)
    prices_df = _create_simulated_prices(markets_df)

    # Run backtest
    engine = BacktestEngine(initial_capital=args.capital)
    results = engine.run(markets_df, prices_df, verbose=True)

    # Print results
    metrics = PerformanceMetrics()
    report = metrics.generate_summary_report(results['metrics'])
    print(report)

    logger.info("Test complete!")


if __name__ == '__main__':
    main()
