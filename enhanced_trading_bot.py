#!/usr/bin/env python3
"""
Enhanced Trading Bot with Advanced Strategies and 30-second Logging
Includes 10 sophisticated trading strategies and comprehensive market analysis
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import pandas as pd
import schedule
from concurrent.futures import ThreadPoolExecutor
import signal
import sys

# Import our modules
from database_schema import TradingDatabase
from technical_indicators_simple import TechnicalIndicators
from strategy_engine import (
    StrategyEngine, MultiIndicatorStrategy, MeanReversionStrategy,
    TrendFollowingStrategy, BreakoutStrategy
)
from advanced_strategies import (
    BbandRsiStrategy, EmaRsiStrategy, MacdRsiStrategy,
    AdxMomentumStrategy, VolatilityBreakoutStrategy, ScalpingStrategy,
    AdvancedStrategyFactory
)
from risk_management import RiskManager
from logger import TradingLogger, get_logger
from enhanced_logger import EnhancedMarketLogger
from binance_client import BinanceClient
from backtesting_engine import AdvancedBacktester
import config

class EnhancedTradingBot:
    """
    Enhanced trading bot with advanced strategies and comprehensive logging
    Features 10+ strategies and detailed 30-second market analysis
    """
    
    def __init__(self, config_dict: Dict[str, Any]):
        self.config = config_dict
        self.is_running = False
        self.is_paused = False
        
        # Initialize core components
        print("🤖 Initializing Enhanced Trading Bot...")
        print("🔥 With Advanced Strategies & 30-Second Logging")
        print("=" * 60)
        
        # Database
        self.database = TradingDatabase()
        print("✅ Database connected")
        
        # Logger
        self.logger = TradingLogger(self.database, {
            'log_level': 'INFO',
            'console_log_level': 'INFO',
            'log_file': 'enhanced_trading_bot.log'
        })
        
        # Exchange client
        self.exchange = BinanceClient()
        if not self.exchange.client:
            self.logger.error("Failed to connect to exchange")
            raise Exception("Exchange connection failed")
        print("✅ Exchange connected")
        
        # Strategy engine with ALL strategies
        self.strategy_engine = StrategyEngine(self.database)
        self._setup_all_strategies()
        print("✅ All strategies loaded")
        
        # Risk manager
        self.risk_manager = RiskManager(self.database, config.STRATEGY_CONFIG)
        print("✅ Risk management initialized")
        
        # Enhanced logger for 30-second analysis
        self.enhanced_logger = EnhancedMarketLogger(
            self.database, self.strategy_engine, self.risk_manager, self.exchange
        )
        print("✅ Enhanced 30-second logger ready")
        
        # Technical indicators
        self.indicators = TechnicalIndicators()
        
        # Performance tracking
        self.session_stats = {
            'start_time': datetime.utcnow(),
            'signals_generated': 0,
            'trades_attempted': 0,
            'trades_executed': 0,
            'trades_rejected': 0,
            'total_pnl': 0.0,
            'strategies_active': len(self.strategy_engine.active_strategies)
        }
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.log_system_status("INITIALIZED")
        print("🚀 Enhanced Trading Bot initialized successfully!")
        print(f"📊 Active Strategies: {self.session_stats['strategies_active']}")
    
    def _setup_all_strategies(self):
        """Initialize and register ALL trading strategies"""
        
        print("🎯 Loading Trading Strategies...")
        
        # Original strategies
        self.strategy_engine.register_strategy(MultiIndicatorStrategy(config.STRATEGY_CONFIG))
        self.strategy_engine.register_strategy(MeanReversionStrategy(config.STRATEGY_CONFIG))
        self.strategy_engine.register_strategy(TrendFollowingStrategy(config.STRATEGY_CONFIG))
        self.strategy_engine.register_strategy(BreakoutStrategy(config.STRATEGY_CONFIG))
        
        # Advanced strategies
        factory = AdvancedStrategyFactory()
        advanced_strategies = factory.get_all_strategies(config.STRATEGY_CONFIG)
        
        for strategy in advanced_strategies:
            self.strategy_engine.register_strategy(strategy)
        
        print(f"   📈 Registered {len(self.strategy_engine.strategies)} strategies:")
        
        # Show all available strategies
        descriptions = factory.get_strategy_descriptions()
        for name, strategy in self.strategy_engine.strategies.items():
            description = descriptions.get(name, "Original core strategy")
            print(f"      • {name}: {description}")
        
        # Activate strategies based on config
        active_strategies = self.config.get('active_strategies', [
            'MultiIndicator', 'MeanReversion', 'BbandRsi', 'EmaRsi', 'MacdRsi'
        ])
        
        print(f"\n   🔄 Activating strategies:")
        for strategy_name in active_strategies:
            if strategy_name in self.strategy_engine.strategies:
                self.strategy_engine.activate_strategy(strategy_name)
                print(f"      ✅ {strategy_name} activated")
            else:
                print(f"      ❌ {strategy_name} not found")
        
        print(f"   🎯 Total active strategies: {len(self.strategy_engine.active_strategies)}")
    
    def start(self):
        """Start the enhanced trading bot"""
        if self.is_running:
            print("Bot is already running!")
            return
        
        self.is_running = True
        self.logger.log_system_status("STARTING")
        
        print("🟢 Starting Enhanced Trading Bot...")
        print("📊 30-second detailed analysis will begin shortly...")
        
        try:
            # Start enhanced logging first
            self.enhanced_logger.start_logging()
            
            # Schedule tasks
            self._schedule_tasks()
            
            # Show initial status
            self._show_startup_status()
            
            # Start main loop
            self._run_main_loop()
            
        except KeyboardInterrupt:
            print("\n🛑 Bot stopped by user")
        except Exception as e:
            self.logger.error(f"Critical error in main loop: {e}", exception=e)
        finally:
            self.stop()
    
    def stop(self):
        """Stop the trading bot gracefully"""
        if not self.is_running:
            return
        
        print("🛑 Stopping Enhanced Trading Bot...")
        self.is_running = False
        
        # Stop enhanced logging
        self.enhanced_logger.stop_logging()
        
        self.logger.log_system_status("STOPPING")
        
        # Close any open positions (if needed)
        self._emergency_close_positions()
        
        # Generate session summary
        self._generate_session_summary()
        
        self.logger.log_system_status("STOPPED")
        print("✅ Enhanced Trading Bot stopped successfully")
    
    def pause(self):
        """Pause trading (stop generating new signals)"""
        self.is_paused = True
        self.logger.info("Enhanced trading bot paused")
        print("⏸️ Trading paused (30-second analysis continues)")
    
    def resume(self):
        """Resume trading"""
        self.is_paused = False
        self.logger.info("Enhanced trading bot resumed")
        print("▶️ Trading resumed")
    
    def _show_startup_status(self):
        """Show detailed startup status"""
        print(f"\n📋 ENHANCED TRADING BOT STATUS")
        print(f"=" * 60)
        print(f"🔗 Exchange: Binance ({'Testnet' if config.TEST_MODE else 'Live'})")
        print(f"💱 Symbol: {config.TRADING_CONFIG['symbol']}")
        print(f"⏱️ Timeframe: {config.TRADING_CONFIG['timeframe']}")
        print(f"💰 Risk per trade: {config.TRADING_CONFIG['risk_per_trade']*100:.1f}%")
        print(f"📊 Active strategies: {len(self.strategy_engine.active_strategies)}")
        
        strategy_list = ", ".join(self.strategy_engine.active_strategies)
        print(f"🎯 Strategies: {strategy_list}")
        
        print(f"🔄 Analysis frequency: Every 30 seconds")
        print(f"⚖️ Risk management: {'✅ Active' if self.risk_manager else '❌ Disabled'}")
        print(f"💾 Database logging: ✅ Active")
        print(f"=" * 60)
        
        # Show current market snapshot
        self._show_initial_market_snapshot()
    
    def _show_initial_market_snapshot(self):
        """Show initial market conditions"""
        try:
            symbol = config.TRADING_CONFIG['symbol'].replace('/', '')
            market_data = self._fetch_market_data(symbol, config.TRADING_CONFIG['timeframe'])
            
            if market_data is not None:
                current_price = float(market_data['close'].iloc[-1])
                indicators = self.indicators.calculate_all_indicators(market_data, config.STRATEGY_CONFIG)
                
                print(f"📈 INITIAL MARKET STATUS")
                print(f"   {symbol}: ${current_price:,.2f}")
                
                if 'rsi' in indicators:
                    rsi_status = "Overbought" if indicators['rsi'] > 70 else "Oversold" if indicators['rsi'] < 30 else "Neutral"
                    print(f"   RSI: {indicators['rsi']:.1f} ({rsi_status})")
                
                if 'bb_position' in indicators:
                    bb_pos = indicators['bb_position']
                    bb_status = "Upper band" if bb_pos > 0.8 else "Lower band" if bb_pos < 0.2 else "Middle range"
                    print(f"   Bollinger Position: {bb_pos:.1%} ({bb_status})")
                
                if 'volume_above_average' in indicators:
                    vol_status = "Above average" if indicators['volume_above_average'] else "Below average"
                    print(f"   Volume: {vol_status}")
                
        except Exception as e:
            print(f"   ⚠️ Could not fetch initial market data: {e}")
    
    def _schedule_tasks(self):
        """Schedule periodic tasks"""
        
        # Enhanced analysis already runs every 30 seconds via enhanced_logger
        
        # Strategy performance review every 10 minutes
        schedule.every(10).minutes.do(self._review_strategy_performance)
        
        # Risk monitoring every 5 minutes
        schedule.every(5).minutes.do(self._monitor_risk)
        
        # Portfolio update every 15 minutes  
        schedule.every(15).minutes.do(self._update_portfolio)
        
        # Hourly performance report
        schedule.every(1).hours.do(self._generate_hourly_report)
        
        # Daily comprehensive report
        schedule.every().day.at("09:00").do(self._generate_daily_report)
        
        # Weekly cleanup and optimization
        schedule.every().sunday.at("02:00").do(self._weekly_maintenance)
    
    def _run_main_loop(self):
        """Enhanced main event loop"""
        self.logger.log_system_status("RUNNING")
        
        loop_count = 0
        last_major_analysis = time.time()
        
        while self.is_running:
            try:
                # Run scheduled tasks
                schedule.run_pending()
                
                # Every minute, check for high-priority signals
                if loop_count % 60 == 0:  # Every minute (since we sleep 1 second)
                    if not self.is_paused:
                        self._check_urgent_signals()
                
                # Every 5 minutes, ensure we're still connected
                if loop_count % 300 == 0:  # Every 5 minutes
                    self._health_check()
                
                loop_count += 1
                time.sleep(1)  # 1 second loop
                
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}", exception=e)
                time.sleep(5)  # Wait before retrying
    
    def _check_urgent_signals(self):
        """Check for urgent trading signals between 30-second analyses"""
        try:
            symbol = config.TRADING_CONFIG['symbol'].replace('/', '')
            timeframe = config.TRADING_CONFIG['timeframe']
            
            # Quick data fetch
            market_data = self._fetch_market_data(symbol, timeframe, limit=50)
            if market_data is None:
                return
            
            # Quick indicator calculation
            indicators = self.indicators.calculate_all_indicators(market_data, config.STRATEGY_CONFIG)
            
            # Check only high-confidence strategies for urgent signals
            urgent_strategies = ['BbandRsi', 'MacdRsi', 'VolatilityBreakout']
            urgent_signals = []
            
            for strategy_name in urgent_strategies:
                if strategy_name in self.strategy_engine.active_strategies:
                    strategy = self.strategy_engine.strategies[strategy_name]
                    signal_data = strategy.generate_signal(market_data, indicators)
                    
                    # Only consider high-confidence signals as urgent
                    if signal_data['signal'] in ['BUY', 'SELL'] and signal_data['confidence'] > 0.8:
                        urgent_signals.append(signal_data)
            
            # Process urgent signals
            if urgent_signals:
                print(f"\n🚨 URGENT SIGNAL DETECTED - {datetime.utcnow().strftime('%H:%M:%S')}")
                for signal in urgent_signals:
                    print(f"   🎯 {signal.get('strategy', 'Unknown')}: {signal['signal']} (Confidence: {signal['confidence']:.1%})")
                
                # Process the highest confidence signal
                best_signal = max(urgent_signals, key=lambda x: x['confidence'])
                self._process_trading_signal(symbol, best_signal)
                
        except Exception as e:
            self.logger.error(f"Error checking urgent signals: {e}", exception=e)
    
    def _health_check(self):
        """Perform system health check"""
        try:
            # Check exchange connection
            if not self.exchange.client:
                print("⚠️ Exchange connection lost - attempting reconnection...")
                self.exchange = BinanceClient()
            
            # Check database connection
            try:
                self.database.logs.find_one()
            except Exception as e:
                print(f"⚠️ Database connection issue: {e}")
            
            # Check strategy engine
            if len(self.strategy_engine.active_strategies) == 0:
                print("⚠️ No active strategies - reactivating default strategies...")
                self.strategy_engine.activate_strategy("MultiIndicator")
                self.strategy_engine.activate_strategy("BbandRsi")
                
        except Exception as e:
            self.logger.error(f"Health check failed: {e}", exception=e)
    
    def _review_strategy_performance(self):
        """Review and compare strategy performance"""
        print(f"\n📊 STRATEGY PERFORMANCE REVIEW - {datetime.utcnow().strftime('%H:%M:%S')}")
        print("=" * 50)
        
        # This would analyze strategy performance from database
        # For now, show active strategies
        print(f"🎯 Active Strategies ({len(self.strategy_engine.active_strategies)}):")
        for strategy_name in self.strategy_engine.active_strategies:
            print(f"   ✅ {strategy_name}")
        
        print(f"📈 Session Stats:")
        print(f"   Signals Generated: {self.session_stats['signals_generated']}")
        print(f"   Trades Attempted: {self.session_stats['trades_attempted']}")
        print(f"   Trades Executed: {self.session_stats['trades_executed']}")
        
        success_rate = (self.session_stats['trades_executed'] / max(self.session_stats['trades_attempted'], 1)) * 100
        print(f"   Success Rate: {success_rate:.1f}%")
    
    def _fetch_market_data(self, symbol: str, timeframe: str, limit: int = 100) -> Optional[pd.DataFrame]:
        """Fetch market data from exchange"""
        try:
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
        """Map timeframe to Binance interval format"""
        mapping = {
            '1m': '1m', '5m': '5m', '15m': '15m', '30m': '30m',
            '1h': '1h', '4h': '4h', '1d': '1d'
        }
        return mapping.get(timeframe, '5m')
    
    def _process_trading_signal(self, symbol: str, signal_data: Dict[str, Any]):
        """Process a trading signal and execute if valid"""
        try:
            self.session_stats['trades_attempted'] += 1
            
            account_info = self._get_account_balance()
            if not account_info:
                self.logger.error("Failed to get account information")
                return
            
            balance = account_info['available_balance']
            validation_result = self.risk_manager.validate_trade(symbol, signal_data, balance)
            
            self.logger.log_trade_attempt(symbol, signal_data, validation_result)
            
            if not validation_result['allowed']:
                self.session_stats['trades_rejected'] += 1
                print(f"❌ Trade rejected: {', '.join(validation_result['blocking_issues'])}")
                return
            
            risk_metrics = validation_result['risk_metrics']
            success = self._execute_trade(symbol, signal_data, risk_metrics)
            
            if success:
                self.session_stats['trades_executed'] += 1
                print(f"✅ Trade executed: {signal_data['signal']} {symbol}")
            else:
                self.session_stats['trades_rejected'] += 1
                
        except Exception as e:
            self.logger.error(f"Error processing trading signal: {e}", exception=e)
    
    def _execute_trade(self, symbol: str, signal_data: Dict[str, Any], risk_metrics: Dict[str, Any]) -> bool:
        """Execute the actual trade"""
        try:
            if config.TEST_MODE:
                # Simulate trade execution
                print(f"📝 SIMULATED TRADE (TEST MODE):")
                print(f"   Symbol: {symbol}")
                print(f"   Signal: {signal_data['signal']}")
                print(f"   Quantity: {risk_metrics['position_size']:.6f}")
                print(f"   Price: ${signal_data['price']:,.2f}")
                print(f"   Risk: ${risk_metrics['risk_amount']:.2f}")
                
                # Record simulated trade
                trade_data = {
                    'symbol': symbol,
                    'side': signal_data['signal'],
                    'quantity': risk_metrics['position_size'],
                    'price': signal_data['price'],
                    'order_id': f"SIM_{int(time.time())}",
                    'status': 'SIMULATED',
                    'timestamp': datetime.utcnow(),
                    'strategy': signal_data.get('strategy', 'Unknown'),
                    'fees': risk_metrics.get('position_value', 0) * 0.001,
                    'pnl': 0.0
                }
                
                self.database.insert_trade(trade_data)
                self.logger.log_trade_executed(symbol, trade_data)
                return True
            else:
                # Real trade execution would go here
                print("⚠️ Live trading not implemented yet - use TEST_MODE")
                return False
                
        except Exception as e:
            self.logger.error(f"Error executing trade: {e}", exception=e)
            return False
    
    def _get_account_balance(self) -> Optional[Dict[str, float]]:
        """Get account balance information"""
        try:
            # Return simulated balance for now
            return {
                'total_balance': 10000.0,
                'available_balance': 8000.0
            }
        except Exception as e:
            self.logger.error(f"Error getting account balance: {e}", exception=e)
            return None
    
    def _monitor_risk(self):
        """Monitor risk metrics"""
        try:
            account_info = self._get_account_balance()
            if not account_info:
                return
            
            risk_report = self.risk_manager.get_risk_report(account_info['total_balance'])
            
            if risk_report['daily_pnl']['status'] == 'WARNING':
                print(f"⚠️ RISK ALERT: Daily loss limit approaching ({risk_report['daily_pnl']['percentage']:.2f}%)")
                self.logger.log_risk_warning('DAILY_LOSS_LIMIT', risk_report['daily_pnl'])
            
            if risk_report['risk_utilization']['status'] == 'WARNING':
                print(f"⚠️ RISK ALERT: High risk utilization ({risk_report['risk_utilization']['percentage']:.2f}%)")
                self.logger.log_risk_warning('HIGH_RISK_UTILIZATION', risk_report['risk_utilization'])
            
        except Exception as e:
            self.logger.error(f"Error monitoring risk: {e}", exception=e)
    
    def _update_portfolio(self):
        """Update portfolio information"""
        try:
            account_info = self._get_account_balance()
            if not account_info:
                return
            
            portfolio_data = {
                'total_balance': account_info['total_balance'],
                'available_balance': account_info['available_balance'],
                'positions': [],
                'unrealized_pnl': 0.0,
                'realized_pnl': self.session_stats['total_pnl'],
                'total_trades': self.session_stats['trades_executed']
            }
            
            self.database.update_portfolio(portfolio_data)
            
        except Exception as e:
            self.logger.error(f"Error updating portfolio: {e}", exception=e)
    
    def _generate_hourly_report(self):
        """Generate hourly performance report"""
        print(f"\n📈 HOURLY PERFORMANCE REPORT - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}")
        print("=" * 60)
        
        uptime = datetime.utcnow() - self.session_stats['start_time']
        print(f"⏱️ Session Duration: {uptime}")
        print(f"📊 Analyses Completed: {self.enhanced_logger.analysis_count}")
        print(f"🎯 Signals Generated: {self.session_stats['signals_generated']}")
        print(f"💼 Trades Executed: {self.session_stats['trades_executed']}")
        print(f"📈 Active Strategies: {len(self.strategy_engine.active_strategies)}")
        
        # Show recent alerts
        if hasattr(self.enhanced_logger, 'price_alerts') and self.enhanced_logger.price_alerts:
            print(f"🚨 Recent Price Alerts: {len(self.enhanced_logger.price_alerts)}")
        
        self.logger.log_bot_performance()
    
    def _generate_daily_report(self):
        """Generate daily performance report"""
        print(f"\n📊 DAILY PERFORMANCE REPORT - {datetime.utcnow().strftime('%Y-%m-%d')}")
        print("=" * 60)
        
        account_info = self._get_account_balance()
        if account_info:
            risk_report = self.risk_manager.get_risk_report(account_info['total_balance'])
            
            print(f"💰 Account Status:")
            print(f"   Balance: ${account_info['total_balance']:,.2f}")
            print(f"   Daily P&L: ${risk_report['daily_pnl']['amount']:+.2f} ({risk_report['daily_pnl']['percentage']:+.2f}%)")
            print(f"   Total Trades: {risk_report['performance']['total_trades']}")
            print(f"   Win Rate: {risk_report['performance']['win_rate']:.1f}%")
            
            self.logger.info("Daily report generated", {
                'date': datetime.utcnow().strftime('%Y-%m-%d'),
                'performance': risk_report['performance'],
                'risk_metrics': risk_report
            })
    
    def _weekly_maintenance(self):
        """Perform weekly maintenance tasks"""
        try:
            print(f"\n🔧 WEEKLY MAINTENANCE - {datetime.utcnow().strftime('%Y-%m-%d')}")
            
            # Cleanup old logs
            self.logger.cleanup_old_logs(30)
            
            # Database optimization could go here
            print("✅ Weekly maintenance completed")
            
        except Exception as e:
            self.logger.error(f"Error in weekly maintenance: {e}", exception=e)
    
    def _emergency_close_positions(self):
        """Close all open positions in case of emergency"""
        try:
            print("🚨 Emergency position closure initiated")
            self.logger.info("Emergency position closure initiated")
            
        except Exception as e:
            self.logger.error(f"Error in emergency position closure: {e}", exception=e)
    
    def _generate_session_summary(self):
        """Generate summary of the trading session"""
        try:
            session_duration = datetime.utcnow() - self.session_stats['start_time']
            
            summary = {
                'session_duration': str(session_duration),
                'analyses_completed': getattr(self.enhanced_logger, 'analysis_count', 0),
                'signals_generated': self.session_stats['signals_generated'],
                'trades_attempted': self.session_stats['trades_attempted'],
                'trades_executed': self.session_stats['trades_executed'],
                'trades_rejected': self.session_stats['trades_rejected'],
                'success_rate': (self.session_stats['trades_executed'] / max(self.session_stats['trades_attempted'], 1)) * 100,
                'strategies_active': len(self.strategy_engine.active_strategies)
            }
            
            self.logger.info("Enhanced session summary", summary)
            
            print("📋 ENHANCED SESSION SUMMARY:")
            for key, value in summary.items():
                print(f"   {key.replace('_', ' ').title()}: {value}")
                
        except Exception as e:
            self.logger.error(f"Error generating session summary: {e}", exception=e)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n🔔 Received signal {signum}, shutting down gracefully...")
        self.stop()
        sys.exit(0)
    
    def run_backtest(self, symbol: str, days: int = 30, strategy_name: Optional[str] = None):
        """Run backtest on recent data"""
        try:
            print(f"🔄 Running enhanced backtest for {symbol} over {days} days...")
            
            market_data = self._fetch_market_data(symbol, '1h', days * 24)
            if market_data is None:
                print("❌ Failed to fetch market data for backtest")
                return
            
            backtester = AdvancedBacktester(initial_capital=10000)
            
            # Test specific strategy or all active strategies
            strategies_to_test = [strategy_name] if strategy_name else self.strategy_engine.active_strategies
            
            for strategy_name in strategies_to_test[:3]:  # Limit to 3 for performance
                if strategy_name in self.strategy_engine.strategies:
                    strategy = self.strategy_engine.strategies[strategy_name]
                    
                    print(f"\n🧪 Testing {strategy_name}...")
                    results = backtester.run_backtest(strategy, market_data, config.STRATEGY_CONFIG)
                    
                    # Show key results
                    print(f"   📊 Results:")
                    print(f"      Total Return: {results['metrics'].total_return_pct:+.2f}%")
                    print(f"      Total Trades: {results['metrics'].total_trades}")
                    print(f"      Win Rate: {results['metrics'].win_rate:.1f}%")
                    print(f"      Max Drawdown: {results['metrics'].max_drawdown_pct:.2f}%")
                    
                    if results['metrics'].total_trades > 0:
                        print(f"      Avg Win: ${results['metrics'].avg_win:.2f}")
                        print(f"      Avg Loss: ${results['metrics'].avg_loss:.2f}")
        
        except Exception as e:
            self.logger.error(f"Error running backtest: {e}", exception=e)

def main():
    """Main entry point for enhanced trading bot"""
    print("🤖 Welcome to Enhanced Crypto Trading Bot")
    print("🔥 Featuring Advanced Strategies & 30-Second Analysis")
    print("=" * 60)
    
    try:
        # Create enhanced trading bot
        bot_config = {
            'active_strategies': [
                'MultiIndicator', 'MeanReversion', 'BbandRsi', 
                'EmaRsi', 'MacdRsi', 'VolatilityBreakout'
            ],
            'enhanced_logging': True,
            'analysis_frequency': 30,  # seconds
            'risk_management': True,
            'auto_trading': config.TEST_MODE
        }
        
        bot = EnhancedTradingBot(bot_config)
        
        # Interactive menu
        while True:
            print(f"\n📋 ENHANCED TRADING BOT MENU:")
            print("1. 🚀 Start Enhanced Trading (with 30s analysis)")
            print("2. 📈 Run Strategy Backtest")
            print("3. 📊 View Risk & Performance Report") 
            print("4. ⏸️ Pause/Resume Trading")
            print("5. 🎯 Show Active Strategies")
            print("6. 🧪 Test Single Strategy")
            print("7. 🛑 Exit")
            
            choice = input(f"\nEnter your choice (1-7): ").strip()
            
            if choice == '1':
                if not bot.is_running:
                    print("🚀 Starting enhanced trading with 30-second analysis...")
                    bot.start()
                else:
                    print("Bot is already running!")
            
            elif choice == '2':
                symbol = input("Enter symbol (default ETHUSDT): ").strip() or 'ETHUSDT'
                days = int(input("Enter days for backtest (default 7): ").strip() or 7)
                bot.run_backtest(symbol, days)
            
            elif choice == '3':
                account_info = bot._get_account_balance()
                if account_info:
                    risk_report = bot.risk_manager.get_risk_report(account_info['total_balance'])
                    print(f"\n📊 RISK & PERFORMANCE REPORT:")
                    print(f"   💰 Balance: ${account_info['total_balance']:,.2f}")
                    print(f"   📈 Daily P&L: ${risk_report['daily_pnl']['amount']:+.2f} ({risk_report['daily_pnl']['percentage']:+.2f}%)")
                    print(f"   🎯 Win Rate: {risk_report['performance']['win_rate']:.1f}%")
                    print(f"   💼 Total Trades: {risk_report['performance']['total_trades']}")
                    print(f"   ⚖️ Risk Utilization: {risk_report['risk_utilization']['percentage']:.2f}%")
            
            elif choice == '4':
                if bot.is_running:
                    if bot.is_paused:
                        bot.resume()
                    else:
                        bot.pause()
                else:
                    print("Bot is not running!")
            
            elif choice == '5':
                print(f"\n🎯 ACTIVE STRATEGIES ({len(bot.strategy_engine.active_strategies)}):")
                factory = AdvancedStrategyFactory()
                descriptions = factory.get_strategy_descriptions()
                
                for strategy_name in bot.strategy_engine.active_strategies:
                    description = descriptions.get(strategy_name, "Core trading strategy")
                    print(f"   ✅ {strategy_name}: {description}")
            
            elif choice == '6':
                print(f"\n🧪 Available strategies:")
                strategies = list(bot.strategy_engine.strategies.keys())
                for i, name in enumerate(strategies, 1):
                    print(f"   {i}. {name}")
                
                try:
                    choice_idx = int(input("Select strategy number: ")) - 1
                    if 0 <= choice_idx < len(strategies):
                        strategy_name = strategies[choice_idx]
                        symbol = input("Enter symbol (default ETHUSDT): ").strip() or 'ETHUSDT'
                        bot.run_backtest(symbol, 7, strategy_name)
                except (ValueError, IndexError):
                    print("Invalid selection!")
            
            elif choice == '7':
                if bot.is_running:
                    bot.stop()
                print("👋 Goodbye!")
                break
            
            else:
                print("❌ Invalid choice!")
                
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()