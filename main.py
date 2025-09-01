#!/usr/bin/env python3
"""
Advanced Crypto Trading Bot - Single Entry Point
Complete trading system with 10+ strategies and 30-second analysis
"""

import asyncio
import time
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import pandas as pd
import schedule
from concurrent.futures import ThreadPoolExecutor
import signal

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import organized modules
from core.database_schema import TradingDatabase
from indicators.technical_indicators_simple import TechnicalIndicators
from strategies.strategy_engine import (
    StrategyEngine, MultiIndicatorStrategy, MeanReversionStrategy,
    TrendFollowingStrategy, BreakoutStrategy
)
from strategies.advanced_strategies import (
    BbandRsiStrategy, EmaRsiStrategy, MacdRsiStrategy,
    AdxMomentumStrategy, VolatilityBreakoutStrategy, ScalpingStrategy,
    AdvancedStrategyFactory
)
from core.risk_management import RiskManager
from utils.logger import TradingLogger
from utils.enhanced_logger import EnhancedMarketLogger
from core.binance_client import BinanceClient
from utils.backtesting_engine import AdvancedBacktester
import config

class AdvancedTradingBot:
    """
    Complete cryptocurrency trading bot with advanced features:
    - 10+ sophisticated trading strategies
    - Real-time 30-second market analysis
    - Advanced risk management
    - MongoDB data persistence
    - Live Binance integration
    - Comprehensive backtesting
    """
    
    def __init__(self):
        print("🚀 ADVANCED CRYPTO TRADING BOT")
        print("🔥 10+ Strategies | 30s Analysis | Full Risk Management")
        print("=" * 70)
        
        # Initialize core components
        print("🔧 Initializing components...")
        
        self.database = TradingDatabase()
        print("   ✅ Database connected")
        
        self.exchange = BinanceClient()
        if not self.exchange.client:
            print("   ⚠️ Exchange connection failed - check API keys")
        else:
            print("   ✅ Exchange connected")
        
        self.strategy_engine = StrategyEngine(self.database)
        self.risk_manager = RiskManager(self.database, config.STRATEGY_CONFIG)
        self.indicators = TechnicalIndicators()
        
        self.logger = TradingLogger(self.database, {
            'log_level': 'INFO',
            'console_log_level': 'INFO',
            'log_file': 'trading_bot.log'
        })
        
        self.enhanced_logger = EnhancedMarketLogger(
            self.database, self.strategy_engine, self.risk_manager, self.exchange
        )
        
        print("   ✅ All components initialized")
        
        # Load all strategies
        self._load_all_strategies()
        
        # Bot state
        self.is_running = False
        self.is_paused = False
        
        # Performance tracking
        self.session_stats = {
            'start_time': datetime.utcnow(),
            'signals_generated': 0,
            'trades_executed': 0,
            'analyses_completed': 0
        }
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        print("🎯 Trading bot ready!")
    
    def _load_all_strategies(self):
        """Load and register all available strategies"""
        print("🎯 Loading trading strategies...")
        
        # Core strategies
        strategies = [
            MultiIndicatorStrategy(config.STRATEGY_CONFIG),
            MeanReversionStrategy(config.STRATEGY_CONFIG),
            TrendFollowingStrategy(config.STRATEGY_CONFIG),
            BreakoutStrategy(config.STRATEGY_CONFIG)
        ]
        
        # Advanced strategies
        factory = AdvancedStrategyFactory()
        advanced_strategies = factory.get_all_strategies(config.STRATEGY_CONFIG)
        strategies.extend(advanced_strategies)
        
        # Register all strategies
        for strategy in strategies:
            self.strategy_engine.register_strategy(strategy)
        
        print(f"   ✅ {len(strategies)} strategies loaded")
        
        # Activate default strategies
        default_active = ['MultiIndicator', 'BbandRsi', 'EmaRsi', 'MacdRsi', 'MeanReversion']
        for strategy_name in default_active:
            if strategy_name in self.strategy_engine.strategies:
                self.strategy_engine.activate_strategy(strategy_name)
        
        print(f"   🔥 {len(self.strategy_engine.active_strategies)} strategies activated")
    
    def start_trading(self):
        """Start the trading bot with 30-second analysis"""
        if self.is_running:
            print("Bot is already running!")
            return
        
        self.is_running = True
        print("\n🟢 STARTING ENHANCED TRADING BOT")
        print("📊 30-second analysis will begin shortly...")
        print("=" * 50)
        
        try:
            # Start enhanced logging
            self.enhanced_logger.start_logging()
            
            # Show current market status
            self._show_market_status()
            
            # Schedule tasks
            schedule.every(5).minutes.do(self._monitor_risk)
            schedule.every(10).minutes.do(self._update_portfolio)
            schedule.every(1).hours.do(self._hourly_report)
            
            # Main loop
            print("🔄 Bot running... Press Ctrl+C to stop")
            while self.is_running:
                schedule.run_pending()
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n🛑 Bot stopped by user")
        except Exception as e:
            self.logger.error(f"Critical error: {e}", exception=e)
            print(f"❌ Critical error: {e}")
        finally:
            self.stop_trading()
    
    def stop_trading(self):
        """Stop the trading bot gracefully"""
        if not self.is_running:
            return
        
        print("🛑 Stopping trading bot...")
        self.is_running = False
        
        # Stop enhanced logging
        self.enhanced_logger.stop_logging()
        
        # Generate session summary
        self._generate_session_summary()
        
        print("✅ Trading bot stopped successfully")
    
    def run_backtest(self, symbol: str = None, days: int = 30, strategy: str = None):
        """Run comprehensive backtesting"""
        symbol = symbol or config.TRADING_CONFIG['symbol'].replace('/', '')
        
        print(f"\n📈 BACKTESTING - {symbol} ({days} days)")
        print("=" * 50)
        
        try:
            # Fetch historical data
            market_data = self._fetch_market_data(symbol, '1h', days * 24)
            if market_data is None:
                print("❌ Could not fetch market data")
                return
            
            print(f"✅ Fetched {len(market_data)} data points")
            
            # Test specific strategy or all active ones
            strategies_to_test = []
            if strategy and strategy in self.strategy_engine.strategies:
                strategies_to_test = [self.strategy_engine.strategies[strategy]]
            else:
                strategies_to_test = [self.strategy_engine.strategies[name] 
                                    for name in self.strategy_engine.active_strategies[:5]]
            
            # Run backtests
            results = []
            backtester = AdvancedBacktester(initial_capital=10000)
            
            for strat in strategies_to_test:
                print(f"\n🧪 Testing {strat.name}...")
                try:
                    result = backtester.run_backtest(
                        strat, market_data.set_index('timestamp'), config.STRATEGY_CONFIG
                    )
                    
                    metrics = result['metrics']
                    results.append({
                        'strategy': strat.name,
                        'return_pct': metrics.total_return_pct,
                        'trades': metrics.total_trades,
                        'win_rate': metrics.win_rate,
                        'max_drawdown': metrics.max_drawdown_pct,
                        'sharpe_ratio': metrics.sharpe_ratio
                    })
                    
                    print(f"   📊 Return: {metrics.total_return_pct:+.2f}% | "
                          f"Trades: {metrics.total_trades} | "
                          f"Win Rate: {metrics.win_rate:.1f}%")
                    
                except Exception as e:
                    print(f"   ❌ Error testing {strat.name}: {e}")
            
            # Show summary
            if results:
                print(f"\n🏆 BACKTEST RESULTS SUMMARY")
                print("-" * 50)
                results.sort(key=lambda x: x['return_pct'], reverse=True)
                
                for i, r in enumerate(results, 1):
                    print(f"{i}. {r['strategy']:<15}: {r['return_pct']:+6.2f}% "
                          f"({r['trades']} trades, {r['win_rate']:.1f}% win rate)")
                
                best = results[0]
                print(f"\n🥇 Best performer: {best['strategy']} ({best['return_pct']:+.2f}%)")
        
        except Exception as e:
            print(f"❌ Backtesting error: {e}")
    
    def show_live_analysis(self):
        """Show current live market analysis"""
        print(f"\n📊 LIVE MARKET ANALYSIS")
        print("=" * 50)
        
        try:
            symbol = config.TRADING_CONFIG['symbol'].replace('/', '')
            market_data = self._fetch_market_data(symbol, config.TRADING_CONFIG['timeframe'])
            
            if market_data is None:
                print("❌ Could not fetch market data")
                return
            
            current_price = float(market_data['close'].iloc[-1])
            print(f"💰 {symbol}: ${current_price:,.2f}")
            
            # Calculate indicators
            indicators = self.indicators.calculate_all_indicators(market_data, config.STRATEGY_CONFIG)
            
            # Show key indicators
            if 'rsi' in indicators:
                rsi_status = "Overbought" if indicators['rsi'] > 70 else "Oversold" if indicators['rsi'] < 30 else "Neutral"
                print(f"📈 RSI: {indicators['rsi']:.1f} ({rsi_status})")
            
            if 'macd_bullish' in indicators:
                macd_status = "Bullish" if indicators['macd_bullish'] else "Bearish"
                print(f"📊 MACD: {macd_status}")
            
            # Generate signals
            signals = self.strategy_engine.analyze_market(symbol, market_data, config.STRATEGY_CONFIG)
            
            buy_signals = [s for s in signals if s['signal'] == 'BUY']
            sell_signals = [s for s in signals if s['signal'] == 'SELL']
            
            print(f"\n🎯 CURRENT SIGNALS:")
            print(f"   🟢 BUY: {len(buy_signals)} strategies")
            print(f"   🔴 SELL: {len(sell_signals)} strategies")
            print(f"   🟡 HOLD: {len(signals) - len(buy_signals) - len(sell_signals)} strategies")
            
            # Show top signals
            if buy_signals:
                best_buy = max(buy_signals, key=lambda x: x['confidence'])
                print(f"   🏆 Best BUY: {best_buy['strategy']} ({best_buy['confidence']:.1%} confidence)")
            
            if sell_signals:
                best_sell = max(sell_signals, key=lambda x: x['confidence'])
                print(f"   🏆 Best SELL: {best_sell['strategy']} ({best_sell['confidence']:.1%} confidence)")
        
        except Exception as e:
            print(f"❌ Analysis error: {e}")
    
    def manage_strategies(self):
        """Strategy management interface"""
        while True:
            print(f"\n🎯 STRATEGY MANAGEMENT")
            print("=" * 30)
            print("1. 📊 Show all strategies")
            print("2. 🔥 Show active strategies") 
            print("3. ➕ Activate strategy")
            print("4. ➖ Deactivate strategy")
            print("5. 🔙 Back to main menu")
            
            choice = input("\nEnter choice (1-5): ").strip()
            
            if choice == '1':
                print(f"\n📊 ALL STRATEGIES ({len(self.strategy_engine.strategies)}):")
                factory = AdvancedStrategyFactory()
                descriptions = factory.get_strategy_descriptions()
                
                for name in self.strategy_engine.strategies.keys():
                    status = "🔥 ACTIVE" if name in self.strategy_engine.active_strategies else "⚪ INACTIVE"
                    desc = descriptions.get(name, "Core trading strategy")
                    print(f"   {status} {name}: {desc}")
            
            elif choice == '2':
                print(f"\n🔥 ACTIVE STRATEGIES ({len(self.strategy_engine.active_strategies)}):")
                for name in self.strategy_engine.active_strategies:
                    print(f"   ✅ {name}")
            
            elif choice == '3':
                inactive = [name for name in self.strategy_engine.strategies.keys() 
                          if name not in self.strategy_engine.active_strategies]
                if not inactive:
                    print("All strategies are already active!")
                    continue
                
                print("Inactive strategies:")
                for i, name in enumerate(inactive, 1):
                    print(f"   {i}. {name}")
                
                try:
                    idx = int(input("Select strategy to activate: ")) - 1
                    if 0 <= idx < len(inactive):
                        self.strategy_engine.activate_strategy(inactive[idx])
                        print(f"✅ {inactive[idx]} activated")
                except (ValueError, IndexError):
                    print("Invalid selection!")
            
            elif choice == '4':
                if not self.strategy_engine.active_strategies:
                    print("No strategies are active!")
                    continue
                
                print("Active strategies:")
                for i, name in enumerate(self.strategy_engine.active_strategies, 1):
                    print(f"   {i}. {name}")
                
                try:
                    idx = int(input("Select strategy to deactivate: ")) - 1
                    if 0 <= idx < len(self.strategy_engine.active_strategies):
                        name = self.strategy_engine.active_strategies[idx]
                        self.strategy_engine.deactivate_strategy(name)
                        print(f"❌ {name} deactivated")
                except (ValueError, IndexError):
                    print("Invalid selection!")
            
            elif choice == '5':
                break
            else:
                print("Invalid choice!")
    
    def _fetch_market_data(self, symbol: str, timeframe: str = '1h', limit: int = 100):
        """Fetch market data from exchange"""
        try:
            if not self.exchange.client:
                return None
                
            binance_interval = self._map_timeframe(timeframe)
            klines = self.exchange.get_klines(symbol=symbol, interval=binance_interval, limit=limit)
            
            if not klines:
                return None
            
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col])
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            self.logger.error(f"Error fetching market data: {e}", exception=e)
            return None
    
    def _map_timeframe(self, timeframe: str) -> str:
        """Map timeframe to Binance format"""
        mapping = {'1m': '1m', '5m': '5m', '15m': '15m', '30m': '30m',
                  '1h': '1h', '4h': '4h', '1d': '1d'}
        return mapping.get(timeframe, '1h')
    
    def _show_market_status(self):
        """Show initial market status"""
        try:
            symbol = config.TRADING_CONFIG['symbol'].replace('/', '')
            market_data = self._fetch_market_data(symbol, config.TRADING_CONFIG['timeframe'])
            
            if market_data is not None:
                current_price = float(market_data['close'].iloc[-1])
                print(f"💰 {symbol}: ${current_price:,.2f}")
                print(f"📊 Timeframe: {config.TRADING_CONFIG['timeframe']}")
                print(f"🎯 Active strategies: {len(self.strategy_engine.active_strategies)}")
                print(f"⚖️ Risk per trade: {config.TRADING_CONFIG['risk_per_trade']*100:.1f}%")
        except Exception as e:
            print(f"⚠️ Could not fetch initial market status: {e}")
    
    def _monitor_risk(self):
        """Monitor risk metrics"""
        try:
            risk_report = self.risk_manager.get_risk_report(10000)
            if risk_report['daily_pnl']['status'] == 'WARNING':
                print(f"⚠️ RISK ALERT: Daily loss limit approaching")
        except Exception as e:
            self.logger.error(f"Risk monitoring error: {e}", exception=e)
    
    def _update_portfolio(self):
        """Update portfolio information"""
        try:
            portfolio_data = {
                'total_balance': 10000.0,
                'available_balance': 8000.0,
                'positions': [],
                'unrealized_pnl': 0.0,
                'realized_pnl': 0.0,
                'total_trades': self.session_stats['trades_executed']
            }
            self.database.update_portfolio(portfolio_data)
        except Exception as e:
            self.logger.error(f"Portfolio update error: {e}", exception=e)
    
    def _hourly_report(self):
        """Generate hourly report"""
        print(f"\n📈 HOURLY REPORT - {datetime.utcnow().strftime('%H:%M')}")
        print(f"   🎯 Signals: {self.session_stats['signals_generated']}")
        print(f"   💼 Trades: {self.session_stats['trades_executed']}")
        print(f"   📊 Analyses: {getattr(self.enhanced_logger, 'analysis_count', 0)}")
    
    def _generate_session_summary(self):
        """Generate session summary"""
        duration = datetime.utcnow() - self.session_stats['start_time']
        print(f"\n📋 SESSION SUMMARY:")
        print(f"   Duration: {duration}")
        print(f"   Analyses: {getattr(self.enhanced_logger, 'analysis_count', 0)}")
        print(f"   Signals: {self.session_stats['signals_generated']}")
        print(f"   Trades: {self.session_stats['trades_executed']}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n🔔 Received signal {signum}, shutting down...")
        self.stop_trading()
        sys.exit(0)

def main():
    """Main entry point"""
    bot = AdvancedTradingBot()
    
    while True:
        print(f"\n🚀 ADVANCED TRADING BOT MENU")
        print("=" * 40)
        print("1. 🔥 Start Trading (30s analysis)")
        print("2. 📈 Run Backtesting")
        print("3. 📊 Live Market Analysis")
        print("4. 🎯 Manage Strategies")
        print("5. ⚙️ Show Configuration")
        print("6. 🛑 Exit")
        
        choice = input(f"\nEnter choice (1-6): ").strip()
        
        try:
            if choice == '1':
                bot.start_trading()
            
            elif choice == '2':
                symbol = input("Symbol (default ETHUSDT): ").strip() or 'ETHUSDT'
                days = int(input("Days (default 7): ").strip() or 7)
                strategy = input("Strategy (default all active): ").strip() or None
                bot.run_backtest(symbol, days, strategy)
            
            elif choice == '3':
                bot.show_live_analysis()
            
            elif choice == '4':
                bot.manage_strategies()
            
            elif choice == '5':
                print(f"\n⚙️ CONFIGURATION:")
                print(f"   Symbol: {config.TRADING_CONFIG['symbol']}")
                print(f"   Timeframe: {config.TRADING_CONFIG['timeframe']}")
                print(f"   Risk per trade: {config.TRADING_CONFIG['risk_per_trade']*100:.1f}%")
                print(f"   Test mode: {'✅ ON' if config.TEST_MODE else '❌ OFF'}")
                print(f"   Active strategies: {len(bot.strategy_engine.active_strategies)}")
            
            elif choice == '6':
                print("👋 Goodbye!")
                break
            
            else:
                print("❌ Invalid choice!")
        
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()