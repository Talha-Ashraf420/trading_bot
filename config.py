# config.py

# Replace with your actual Binance API key and secret
API_KEY="Lw67110MBMRcSQ05ip05JkIdgZd0FEv7NxrvA1HSApLrUiXVFBKhQbTVoTsVgbkP"
API_SECRET="5vY3D1wb94O9yOFMqdWHssZOtrXrcbtykIvYhZuvI5mjqVAcR3hHHtwL9XDT0zty"

# Set to False when you are ready for live trading
TEST_MODE = True


# config.py
EXCHANGE_CONFIG = {
    'id': 'binance',  # Exchange ID from CCXT, e.g., 'binance', 'kraken', 'coinbasepro'
    'apiKey': 'Lw67110MBMRcSQ05ip05JkIdgZd0FEv7NxrvA1HSApLrUiXVFBKhQbTVoTsVgbkP',
    'secret': '5vY3D1wb94O9yOFMqdWHssZOtrXrcbtykIvYhZuvI5mjqVAcR3hHHtwL9XDT0zty',
    # For sandbox/testnet trading, uncomment the following lines
    'options': {
        'defaultType': 'spot', # or 'spot'
        'adjustForTimeDifference': True,
        'test': True, # Use the testnet
    },
}

TRADING_CONFIG = {
    'symbol': 'ETH/USDT',      # Trading pair
    'timeframe': '5m',         # Timeframe for candles (e.g., '1m', '5m', '1h', '1d')
    'capital_allocation': 0.1, # Percentage of total capital to use per trade (e.g., 0.1 for 10%)
    'risk_per_trade': 0.01,    # Percentage of capital to risk per trade (e.g., 0.01 for 1%)
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