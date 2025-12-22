# AMM Delta-Neutral Strategy Backtest

Backtest framework for AMM Delta-Neutral Strategy on Polymarket SOL 15-min Markets.

## Strategy Overview

| Item | Description |
|------|-------------|
| **Strategy** | Market Making Delta-Neutral with bilateral hedge |
| **Market** | Solana Up/Down 15-minute markets |
| **Period** | 3 months (90 days) |
| **Objective** | Capture spread YES+NO < $1.00, maintaining balanced position |
| **Risk Profile** | Moderate |

## How It Works

The strategy exploits pricing inefficiencies in Polymarket's binary outcome markets:

1. **Entry**: When YES + NO prices sum to less than $1.00 (e.g., $0.48 + $0.49 = $0.97)
2. **Position**: Buy equal amounts of YES and NO tokens
3. **Settlement**: One side always pays $1.00, guaranteeing profit from the spread
4. **Example**: Buy 100 YES @ $0.48 + 100 NO @ $0.49 = $97 cost, receive $100 at settlement = $3 profit

## Project Structure

```
polymarket_sol_backtest/
├── config/
│   ├── settings.py          # Global parameters
│   └── risk_params.py       # Risk parameters
├── data/
│   ├── raw/                  # Raw API data
│   ├── processed/            # Processed data
│   ├── trades/               # Simulated trade history
│   └── results/              # Backtest results
├── src/
│   ├── data_collector.py     # Data collection from Polymarket API
│   ├── market_analyzer.py    # Market analysis
│   ├── spread_calculator.py  # Spread calculations
│   ├── position_manager.py   # Position management
│   ├── risk_manager.py       # Risk management
│   ├── backtest_engine.py    # Main backtest engine
│   ├── metrics.py            # Performance metrics
│   └── visualizer.py         # Charts and reports
├── notebooks/                # Jupyter notebooks for analysis
├── tests/                    # Unit tests
├── main.py                   # Entry point
└── requirements.txt          # Dependencies
```

## Installation

```bash
# Clone repository
git clone https://github.com/Leandrosmoreira/AMM-Polymarket-Backtest.git
cd AMM-Polymarket-Backtest/polymarket_sol_backtest

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Quick Test (with simulated data)

```bash
python main.py test --capital 5000
```

### Full Workflow

#### 1. Collect Data

```bash
# Collect market data (90 days)
python main.py collect --days 90

# Collect with price history
python main.py collect --days 90 --fetch-prices
```

#### 2. Analyze Data

```bash
python main.py analyze
```

#### 3. Run Backtest

```bash
# Basic backtest
python main.py backtest --capital 5000

# Custom parameters
python main.py backtest \
    --capital 10000 \
    --spread-threshold -0.03 \
    --max-exposure 0.60 \
    --output results/my_backtest
```

## Risk Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `MIN_SPREAD_TO_ENTER` | -0.02 | Only enter if YES + NO < 0.98 |
| `MAX_PER_MARKET_PCT` | 0.15 | Max 15% of capital per market |
| `MAX_PER_MARKET_USD` | $750 | Max $750 per market |
| `MAX_TOTAL_EXPOSURE` | 0.70 | Max 70% of capital allocated |
| `MAX_ACTIVE_MARKETS` | 5 | Max 5 simultaneous positions |
| `TARGET_RATIO` | 1.0 | Target YES/NO ratio |
| `MIN_VOLUME` | $500 | Minimum market volume |

## Expected Performance

### Optimistic Targets
- Monthly Return: 5%
- Win Rate: 85%
- Sharpe Ratio: > 2.0
- Max Drawdown: < 10%

### Realistic Expectations
- Monthly Return: 2%
- Win Rate: 70%
- Sharpe Ratio: ~1.0
- Max Drawdown: ~15%

## Output

The backtest generates:

1. **Performance Report** - Key metrics and statistics
2. **Equity Curve** - Portfolio value over time
3. **Drawdown Chart** - Drawdown visualization
4. **Returns Distribution** - Histogram of trade returns
5. **Monthly Returns** - Bar chart by month
6. **Trade Log** - CSV with all trades

## Decision Matrix

### Spread-Based Entry

| Spread (YES+NO) | Action |
|-----------------|--------|
| > 0.99 | NO ENTRY |
| 0.98 - 0.99 | CONSIDER |
| 0.97 - 0.98 | ENTER |
| < 0.97 | ENTER STRONG |

### Position Balance

| YES/NO Ratio | Action |
|--------------|--------|
| > 1.3 | BUY NO (rebalance) |
| 1.1 - 1.3 | Prefer NO |
| 0.9 - 1.1 | BALANCED |
| 0.7 - 0.9 | Prefer YES |
| < 0.7 | BUY YES (rebalance) |

## Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| No historical orderbook | Slippage may be underestimated | Conservative slippage model |
| Latency not simulated | Real bot will be slower | Add artificial delay |
| Competition not modeled | Others may take opportunities | Assume < 100% fill rate |
| Data gaps | Markets may be missing | Document gaps found |

## Next Steps After Backtest

**If positive** (Sharpe > 1, Win Rate > 60%):
1. Paper trading for 2 weeks
2. Real trading with 10% of capital
3. Scale gradually

**If negative**:
1. Analyze where strategy fails
2. Adjust parameters or logic
3. Re-test
4. If still negative, pivot strategy

## License

MIT License

## Author

Claude + Leandro - December 2024
