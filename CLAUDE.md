# Advanced Crypto Trading Bot - Claude Code Context

## Project Overview
This is a sophisticated cryptocurrency trading bot built in Python with the following key features:
- 10+ advanced trading strategies
- Real-time 30-second market analysis  
- MongoDB data persistence
- Binance API integration
- Advanced risk management
- Comprehensive backtesting capabilities

## Project Structure
```
trading_bot/
├── main.py                    # Main entry point - AdvancedTradingBot class
├── enhanced_trading_bot.py    # Legacy enhanced bot implementation
├── config.py                  # Configuration settings (API keys, trading params)
├── requirements.txt           # Python dependencies
├── src/
│   ├── core/
│   │   ├── binance_client.py         # Binance API integration
│   │   ├── database_schema.py        # MongoDB schema and operations
│   │   └── risk_management.py        # Risk management utilities
│   ├── strategies/
│   │   ├── strategy_engine.py        # Base strategy classes
│   │   └── advanced_strategies.py    # Advanced trading strategies
│   ├── indicators/
│   │   └── technical_indicators_simple.py  # Technical analysis indicators
│   └── utils/
│       ├── logger.py                 # Basic logging utilities
│       ├── enhanced_logger.py        # Enhanced market logging
│       └── backtesting_engine.py     # Backtesting framework
└── freqtrade-strategies/            # External freqtrade strategies directory
```

## Key Components

### Main Trading Bot (`main.py`)
- Entry point class: `AdvancedTradingBot`
- Runs 30-second analysis cycles
- Manages multiple trading strategies simultaneously
- Handles live trading and paper trading modes

### Configuration (`config.py`)
- **Current Mode**: TEST_MODE = True (paper trading)
- **Trading Pair**: ETH/USDT
- **Timeframe**: 5m candles
- **Risk Settings**: 1% risk per trade, 10% capital allocation
- **API Keys**: Binance testnet credentials configured
- **Database**: MongoDB cluster connection

### Trading Strategies Available
1. Multi-Indicator Strategy
2. Mean Reversion Strategy  
3. Trend Following Strategy
4. Breakout Strategy
5. Bollinger Bands + RSI Strategy
6. EMA + RSI Strategy
7. MACD + RSI Strategy
8. ADX Momentum Strategy
9. Volatility Breakout Strategy
10. Scalping Strategy

### Technical Indicators Implemented
- RSI (Relative Strength Index)
- Bollinger Bands
- EMA/SMA (Moving Averages)
- MACD
- Stochastic Oscillator
- ADX (Average Directional Index)
- Volume indicators
- Support/Resistance levels

## Key Dependencies
- `python-binance`: Binance API integration
- `pandas`: Data manipulation and analysis
- `pandas-ta`: Technical analysis indicators
- `pymongo`: MongoDB database operations
- `schedule`: Task scheduling
- `matplotlib/plotly`: Data visualization
- `scikit-learn`: Machine learning capabilities

## Development Notes
- Currently in TEST_MODE for safe development
- MongoDB integration for trade history and analytics
- Comprehensive logging system with colored output
- Built-in backtesting engine for strategy validation
- Risk management with position sizing and stop losses

## Common Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Run the trading bot
python main.py

# Run tests (if available)
pytest

# Code formatting
black .
```

## Current Status
- Project is actively developed with recent commits
- Clean git status
- Paper trading mode enabled for safety
- Multiple strategies implemented and tested
- MongoDB integration completed

## Related Directories
- `/Users/talhaashraf/Documents/personal/freqtrade-strategies`: External freqtrade strategies for reference

## Safety Notes
- **IMPORTANT**: Currently in TEST_MODE - no real trades executed
- API credentials are for testnet/paper trading
- Risk management systems in place
- Comprehensive logging for monitoring

This context should help Claude Code understand the project structure, current implementation, and development approach for future assistance.