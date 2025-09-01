# config.py

# Binance API Configuration - RESET FOR FRESH START
API_KEY = "Pr4oufbwYVOO8SIhS8e096Am9iZ2GOWwortfyNWq9KgSpnZ6wGUA6QvfvA3HiF83"
API_SECRET = "RuhmvsuTJIQLxySoMJCADsIO4IQLkrTAk1ioWgTJWiBK7ozzYiexnCpBAN9GtlPH"

# Set to True for paper trading (recommended for learning)
TEST_MODE = True

# Database Configuration
DATABASE_CONFIG = {
    'host': 'cluster0.7fyyw6x.mongodb.net',
    'database': 'trading_bot',
    'connection_string': 'mongodb+srv://talha_db_user:52cOcZZwz8AxmQlu@cluster0.7fyyw6x.mongodb.net/'
}

TRADING_CONFIG = {
    'symbol': 'ETH/USDT',      # Trading pair
    'timeframe': '5m',         # Timeframe for candles (e.g., '1m', '5m', '1h', '1d')
    'capital_allocation': 0.1, # Percentage of total capital to use per trade (e.g., 0.1 for 10%)
    'risk_per_trade': 0.01,    # Percentage of capital to risk per trade (e.g., 0.01 for 1%)
    'buy_only_mode': True,     # Only execute BUY orders (good for beginners with USDT balance)
}

STRATEGY_CONFIG = {
    # RSI Parameters
    'rsi_period': 14,
    'rsi_oversold': 30,
    'rsi_overbought': 70,
    
    # Bollinger Bands Parameters
    'bb_period': 20,
    'bb_std_dev': 2,
    
    # Moving Average Parameters
    'ema_fast': 12,
    'ema_slow': 26,
    'sma_trend': 50,
    
    # MACD Parameters
    'macd_fast': 12,
    'macd_slow': 26,
    'macd_signal': 9,
    
    # Stochastic Parameters
    'stoch_k': 14,
    'stoch_d': 3,
    'stoch_oversold': 20,
    'stoch_overbought': 80,
    
    # Volume Parameters
    'volume_sma': 20,
    
    # ATR Parameters
    'atr_period': 14,
    'atr_multiplier': 2.0,  # Multiplier for stop-loss calculation
    
    # ADX Parameters
    'adx_period': 14,
    'adx_threshold': 25,  # Minimum ADX value to consider trend strong
    
    # Signal Threshold
    'signal_threshold': 4,  # Minimum score needed for a signal
    
    # Risk Management
    'max_position_size': 0.1,  # Maximum 10% of portfolio per trade
    'min_signal_strength': 5,  # Minimum signal strength (0-10) to trade
}