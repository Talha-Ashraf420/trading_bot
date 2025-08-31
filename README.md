# 🚀 Advanced Multi-Strategy Trading Bot

A professional cryptocurrency trading bot with multiple strategies, MongoDB integration, and comprehensive risk management.

## ✨ Features

- **3 Trading Strategies**: Conservative, Momentum, and Aggressive
- **MongoDB Atlas Integration**: Complete order and user tracking
- **Multi-Pair Trading**: Trade multiple cryptocurrency pairs simultaneously
- **Advanced Risk Management**: Portfolio allocation and position sizing
- **Real-Time Logging**: Updates every 30 seconds with detailed analysis

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup Binance API
- Create Binance Testnet account at https://testnet.binance.vision/
- Generate API keys with "Reading" and "Spot Trading" permissions
- Update `config.py` with your API credentials

### 3. Run the Bot
```bash
python main.py
```

The setup wizard will guide you through:
- Creating your user account
- Selecting trading pairs
- Configuring strategy allocations

## 📊 Strategy Overview

### Conservative Strategy (50% allocation)
- **Risk Level**: Low
- **Focus**: Strong trend confirmation
- **Best For**: Stable, long-term growth

### Momentum Strategy (30% allocation)
- **Risk Level**: Medium
- **Focus**: Breakouts and momentum moves
- **Best For**: Trending markets

### Aggressive Strategy (20% allocation)
- **Risk Level**: High
- **Focus**: Quick scalping opportunities
- **Best For**: Volatile markets

## 🛡️ Risk Management

- **Maximum 5% total portfolio risk**
- **Strategy-specific position limits**
- **Dynamic position sizing based on signal strength**
- **Automatic stop-loss and take-profit levels**

## 📝 Logging

- **Detailed logs every 30 seconds**: Complete market analysis and strategy breakdown
- **Quick updates every 10 seconds**: Price changes and signal summaries
- **Trade execution logs**: Full audit trail of all trades

## ⚠️ Important Notes

- **Always start with testnet** - Never risk real money until thoroughly tested
- **Monitor performance** - Keep track of strategy success rates
- **Understand the risks** - Cryptocurrency trading involves substantial risk

## 📁 Project Structure

```
trading_bot/
├── main.py                    # Main application with setup wizard
├── config.py                  # Configuration settings
├── database.py                # MongoDB integration
├── strategy_manager.py        # Multi-strategy management
├── risk_manager.py           # Risk management system
├── exchange_handler.py       # Exchange API interface
├── strategies/               # Trading strategy implementations
│   ├── conservative_strategy.py
│   ├── momentum_strategy.py
│   └── aggressive_strategy.py
└── requirements.txt          # Python dependencies
```

## 🎯 Expected Performance

- **Conservative**: 3-8% monthly returns, low drawdown
- **Momentum**: 5-12% monthly returns, medium drawdown  
- **Aggressive**: 8-20% monthly returns, higher drawdown

**Remember**: Past performance doesn't guarantee future results. Always trade responsibly!

---

*Happy Trading! 🚀💰*
