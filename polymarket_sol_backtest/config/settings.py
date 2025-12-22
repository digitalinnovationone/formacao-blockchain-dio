"""
Global settings for AMM Delta-Neutral Strategy Backtest
Polymarket SOL 15-min Markets
"""

# === MERCADO ===
ASSET = "SOL"
MARKET_TYPE = "up_or_down"
TIMEFRAME_MINUTES = 15

# === PERIODO DO BACKTEST ===
BACKTEST_START = "2024-09-13"  # 3 meses atras
BACKTEST_END = "2024-12-13"    # Hoje
BACKTEST_DAYS = 90

# === CAPITAL ===
INITIAL_CAPITAL = 5000  # USD
CURRENCY = "USDC"

# === API ===
GAMMA_API_BASE = "https://gamma-api.polymarket.com"
CLOB_API_BASE = "https://clob.polymarket.com"

# === RATE LIMITING ===
MAX_REQUESTS_PER_SECOND = 10
REQUEST_TIMEOUT = 30  # seconds

# === DATA PATHS ===
DATA_RAW_PATH = "data/raw"
DATA_PROCESSED_PATH = "data/processed"
DATA_TRADES_PATH = "data/trades"
DATA_RESULTS_PATH = "data/results"

# === LOGGING ===
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
