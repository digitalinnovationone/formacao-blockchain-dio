"""
Risk Parameters for AMM Delta-Neutral Strategy
Profile: MODERATE
"""


class RiskParams:
    """Parametros de risco - Perfil MODERADO"""

    # === SPREAD ===
    MIN_SPREAD_TO_ENTER = -0.02    # So entra se YES + NO < 0.98
    TARGET_SPREAD = -0.03          # Spread ideal: YES + NO = 0.97

    # === POSICAO ===
    MAX_PER_MARKET_PCT = 0.15      # Maximo 15% do capital por mercado
    MAX_PER_MARKET_USD = 750       # Maximo $750 por mercado
    MIN_ORDER_SIZE = 10            # Minimo $10 por ordem

    # === EXPOSICAO TOTAL ===
    MAX_TOTAL_EXPOSURE = 0.70      # Maximo 70% do capital alocado
    MIN_CASH_RESERVE = 0.30        # Sempre manter 30% em caixa

    # === MERCADOS SIMULTANEOS ===
    MAX_ACTIVE_MARKETS = 5         # Maximo 5 mercados ao mesmo tempo

    # === EQUILIBRIO YES/NO ===
    TARGET_RATIO = 1.0             # Ideal: YES = NO
    MAX_RATIO = 1.3                # Maximo: YES pode ser 30% maior que NO
    MIN_RATIO = 0.7                # Minimo: YES pode ser 30% menor que NO

    # === TEMPO ===
    MIN_TIME_REMAINING = 120       # Minimo 2 minutos antes do settlement
    MAX_TIME_IN_MARKET = 900       # Maximo 15 minutos (vida do mercado)

    # === LIQUIDEZ ===
    MIN_VOLUME = 500               # Volume minimo do mercado
    MAX_SLIPPAGE = 0.005           # Slippage maximo aceitavel (0.5%)

    # === STOP LOSS ===
    STOP_LOSS_PCT = 0.10           # Stop loss de 10% da posicao

    # === REBALANCEAMENTO ===
    SPREAD_IMPROVEMENT_THRESHOLD = 0.01  # Adiciona se spread melhorar 1%

    @classmethod
    def to_dict(cls):
        """Retorna todos os parametros como dicionario."""
        return {
            key: value for key, value in vars(cls).items()
            if not key.startswith('_') and not callable(value)
        }
