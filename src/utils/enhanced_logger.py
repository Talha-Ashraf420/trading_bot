"""
Enhanced logging system with 30-second detailed market analysis
Provides comprehensive real-time trading information
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import pandas as pd
from core.database_schema import TradingDatabase
from indicators.technical_indicators_simple import TechnicalIndicators
from strategies.strategy_engine import StrategyEngine
from core.risk_management import RiskManager
from core.binance_client import BinanceClient
import config

class EnhancedMarketLogger:
    """Enhanced logger with detailed 30-second market analysis"""
    
    def __init__(self, database: TradingDatabase, strategy_engine: StrategyEngine, 
                 risk_manager: RiskManager, exchange: BinanceClient):
        self.database = database
        self.strategy_engine = strategy_engine
        self.risk_manager = risk_manager
        self.exchange = exchange
        self.indicators_calc = TechnicalIndicators()
        
        self.is_running = False
        self.log_thread = None
        
        # Performance tracking
        self.session_start = datetime.utcnow()
        self.last_prices = {}
        self.price_alerts = []
        
        # Analysis counters
        self.analysis_count = 0
        self.signals_today = 0
        self.trades_today = 0
        
        print("📊 Enhanced 30-second logging system initialized")
    
    def start_logging(self):
        """Start the enhanced logging system"""
        if self.is_running:
            print("⚠️ Enhanced logging already running")
            return
        
        self.is_running = True
        self.log_thread = threading.Thread(target=self._logging_loop, daemon=True)
        self.log_thread.start()
        
        print("🟢 Enhanced 30-second logging started")
        print("📈 Detailed market analysis will appear every 30 seconds...")
        print("=" * 80)
    
    def stop_logging(self):
        """Stop the enhanced logging system"""
        self.is_running = False
        if self.log_thread:
            self.log_thread.join(timeout=5)
        print("🛑 Enhanced logging stopped")
    
    def _logging_loop(self):
        """Main logging loop - runs every 30 seconds"""
        while self.is_running:
            try:
                self._perform_detailed_analysis()
                time.sleep(30)  # Wait 30 seconds
            except Exception as e:
                print(f"❌ Enhanced logging error: {e}")
                time.sleep(30)
    
    def _perform_detailed_analysis(self):
        """Perform comprehensive 30-second market analysis"""
        self.analysis_count += 1
        current_time = datetime.utcnow()
        
        print(f"\n{'='*80}")
        print(f"📊 MARKET ANALYSIS #{self.analysis_count} | {current_time.strftime('%H:%M:%S')} UTC")
        print(f"{'='*80}")
        
        # Get market data for configured symbol
        symbol = config.TRADING_CONFIG['symbol'].replace('/', '')  # ETH/USDT -> ETHUSDT
        timeframe = config.TRADING_CONFIG['timeframe']
        
        # Fetch fresh market data
        market_data = self._fetch_market_data(symbol, timeframe)
        
        if market_data is None:
            print("❌ Unable to fetch market data - using cached data")
            return
        
        # Calculate all technical indicators
        indicators = self.indicators_calc.calculate_all_indicators(market_data, config.STRATEGY_CONFIG)
        
        if not indicators:
            print("⚠️ Insufficient data for technical analysis")
            return
        
        # Current price analysis
        current_price = float(market_data['close'].iloc[-1])
        self._analyze_price_movement(symbol, current_price)
        
        # Technical indicators summary
        self._analyze_technical_indicators(indicators, current_price)
        
        # Strategy signals analysis
        self._analyze_all_strategies(symbol, market_data, indicators)
        
        # Risk and portfolio analysis
        self._analyze_risk_and_portfolio()
        
        # Market sentiment and alerts
        self._analyze_market_sentiment(market_data, indicators)
        
        # Performance summary
        self._show_session_performance()
        
        # Store analysis in database
        self._store_analysis_data(symbol, timeframe, indicators, market_data)
        
        print(f"{'='*80}")
    
    def _fetch_market_data(self, symbol: str, timeframe: str, limit: int = 100) -> Optional[pd.DataFrame]:
        """Fetch fresh market data"""
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
            print(f"❌ Error fetching market data: {e}")
            return None
    
    def _map_timeframe(self, timeframe: str) -> str:
        """Map timeframe to Binance format"""
        mapping = {
            '1m': '1m', '5m': '5m', '15m': '15m', '30m': '30m',
            '1h': '1h', '4h': '4h', '1d': '1d'
        }
        return mapping.get(timeframe, '5m')
    
    def _analyze_price_movement(self, symbol: str, current_price: float):
        """Analyze price movement and changes"""
        print(f"💰 PRICE ANALYSIS - {symbol}")
        print(f"   Current Price: ${current_price:,.2f}")
        
        # Compare with last price
        if symbol in self.last_prices:
            last_price = self.last_prices[symbol]
            price_change = current_price - last_price
            price_change_pct = (price_change / last_price) * 100
            
            change_symbol = "📈" if price_change > 0 else "📉" if price_change < 0 else "➡️"
            print(f"   30s Change: {change_symbol} ${price_change:+,.2f} ({price_change_pct:+.3f}%)")
            
            # Price alerts
            if abs(price_change_pct) > 0.5:  # 0.5% move in 30 seconds
                alert = f"🚨 SIGNIFICANT MOVE: {price_change_pct:+.2f}% in 30 seconds!"
                print(f"   {alert}")
                self.price_alerts.append(alert)
        
        self.last_prices[symbol] = current_price
    
    def _analyze_technical_indicators(self, indicators: Dict[str, Any], current_price: float):
        """Analyze key technical indicators"""
        print(f"\n🔍 TECHNICAL INDICATORS")
        
        # Trend Analysis
        ema_12 = indicators.get('ema_12', current_price)
        ema_26 = indicators.get('ema_26', current_price)
        sma_20 = indicators.get('sma_20', current_price)
        sma_50 = indicators.get('sma_50', current_price)
        
        trend_status = "🟢 BULLISH" if current_price > ema_12 > ema_26 else "🔴 BEARISH" if current_price < ema_12 < ema_26 else "🟡 NEUTRAL"
        print(f"   Trend Status: {trend_status}")
        print(f"   EMA12: ${ema_12:,.2f} | EMA26: ${ema_26:,.2f}")
        print(f"   SMA20: ${sma_20:,.2f} | SMA50: ${sma_50:,.2f}")
        
        # Momentum Analysis
        rsi = indicators.get('rsi', 50)
        macd = indicators.get('macd', 0)
        macd_signal = indicators.get('macd_signal', 0)
        
        rsi_status = "🔴 OVERBOUGHT" if rsi > 70 else "🟢 OVERSOLD" if rsi < 30 else "🟡 NEUTRAL"
        macd_status = "🟢 BULLISH" if macd > macd_signal else "🔴 BEARISH"
        
        print(f"   RSI: {rsi:.1f} ({rsi_status})")
        print(f"   MACD: {macd:.2f} vs Signal: {macd_signal:.2f} ({macd_status})")
        
        # Volatility Analysis
        atr = indicators.get('atr', 0)
        bb_upper = indicators.get('bb_upper', current_price)
        bb_lower = indicators.get('bb_lower', current_price)
        bb_position = indicators.get('bb_position', 0.5)
        
        volatility_pct = (atr / current_price) * 100 if atr > 0 else 0
        volatility_status = "🔴 HIGH" if volatility_pct > 3 else "🟢 LOW" if volatility_pct < 1.5 else "🟡 NORMAL"
        
        print(f"   Volatility (ATR): {volatility_pct:.2f}% ({volatility_status})")
        print(f"   Bollinger Bands: ${bb_lower:,.2f} - ${bb_upper:,.2f}")
        print(f"   BB Position: {bb_position:.1%} {'(Lower)' if bb_position < 0.3 else '(Upper)' if bb_position > 0.7 else '(Middle)'}")
        
        # Volume Analysis
        volume_above_avg = indicators.get('volume_above_average', False)
        volume_spike = indicators.get('volume_spike', False)
        
        volume_status = "🟢 HIGH" if volume_spike else "🟡 ABOVE AVG" if volume_above_avg else "🔴 LOW"
        print(f"   Volume: {volume_status}")
    
    def _analyze_all_strategies(self, symbol: str, market_data: pd.DataFrame, indicators: Dict[str, Any]):
        """Analyze signals from all active strategies"""
        print(f"\n🎯 STRATEGY SIGNALS")
        
        # Get signals from strategy engine
        signals = self.strategy_engine.analyze_market(symbol, market_data, config.STRATEGY_CONFIG)
        
        if not signals:
            print("   ⚠️ No signals generated from active strategies")
            return
        
        buy_signals = [s for s in signals if s['signal'] == 'BUY']
        sell_signals = [s for s in signals if s['signal'] == 'SELL']
        hold_signals = [s for s in signals if s['signal'] == 'HOLD']
        
        print(f"   📊 Strategy Summary: {len(buy_signals)} BUY | {len(sell_signals)} SELL | {len(hold_signals)} HOLD")
        
        # Show individual strategy signals
        for signal in signals[:6]:  # Show up to 6 strategies
            confidence_bar = "█" * int(signal['confidence'] * 10) + "░" * (10 - int(signal['confidence'] * 10))
            signal_emoji = "🟢" if signal['signal'] == 'BUY' else "🔴" if signal['signal'] == 'SELL' else "🟡"
            
            print(f"   {signal_emoji} {signal['strategy']:<15}: {signal['signal']} ({confidence_bar} {signal['confidence']:.1%})")
            
            # Show top 2 reasons
            if signal['reasoning']:
                for reason in signal['reasoning'][:2]:
                    print(f"      └─ {reason}")
        
        # Consensus analysis
        consensus = self.strategy_engine.get_consensus_signal(signals)
        if consensus['signal'] != 'HOLD':
            consensus_emoji = "🟢" if consensus['signal'] == 'BUY' else "🔴"
            print(f"\n   🎯 CONSENSUS: {consensus_emoji} {consensus['signal']} (Confidence: {consensus['confidence']:.1%})")
            print(f"      Supporting strategies: {consensus['supporting_strategies']}/{consensus['total_strategies']}")
            
            if consensus['signal'] in ['BUY', 'SELL']:
                self.signals_today += 1
    
    def _analyze_risk_and_portfolio(self):
        """Analyze current risk metrics and portfolio status"""
        print(f"\n⚖️ RISK & PORTFOLIO")
        
        try:
            # Get account balance (simulated for now)
            account_balance = 10000.0  # This would be real balance in live trading
            
            risk_report = self.risk_manager.get_risk_report(account_balance)
            
            print(f"   💰 Account Balance: ${account_balance:,.2f}")
            print(f"   📊 Daily P&L: ${risk_report['daily_pnl']['amount']:+,.2f} ({risk_report['daily_pnl']['percentage']:+.2f}%)")
            
            # Risk utilization
            risk_status = risk_report['risk_utilization']['status']
            risk_emoji = "🟢" if risk_status == 'OK' else "🟡" if risk_status == 'WARNING' else "🔴"
            print(f"   ⚖️ Risk Utilization: {risk_emoji} {risk_report['risk_utilization']['percentage']:.2f}%")
            
            # Performance metrics
            performance = risk_report['performance']
            print(f"   🎯 Win Rate: {performance['win_rate']:.1f}% ({performance['winning_trades']}/{performance['total_trades']})")
            print(f"   💵 Total P&L: ${performance['total_pnl']:+,.2f}")
            
            if performance['total_trades'] > 0:
                print(f"   📈 Avg Win: ${performance['avg_win']:.2f} | 📉 Avg Loss: ${performance['avg_loss']:.2f}")
        
        except Exception as e:
            print(f"   ❌ Risk analysis error: {e}")
    
    def _analyze_market_sentiment(self, market_data: pd.DataFrame, indicators: Dict[str, Any]):
        """Analyze overall market sentiment and conditions"""
        print(f"\n🌡️ MARKET SENTIMENT")
        
        # Calculate sentiment score
        sentiment_score = 0
        sentiment_factors = []
        
        # Price trend (last 24 candles)
        if len(market_data) >= 24:
            price_24h_ago = float(market_data['close'].iloc[-24])
            current_price = float(market_data['close'].iloc[-1])
            price_change_24h = ((current_price - price_24h_ago) / price_24h_ago) * 100
            
            if price_change_24h > 2:
                sentiment_score += 2
                sentiment_factors.append(f"Strong 24h price gain (+{price_change_24h:.2f}%)")
            elif price_change_24h > 0:
                sentiment_score += 1
                sentiment_factors.append(f"Positive 24h trend (+{price_change_24h:.2f}%)")
            elif price_change_24h < -2:
                sentiment_score -= 2
                sentiment_factors.append(f"Strong 24h price decline ({price_change_24h:.2f}%)")
            else:
                sentiment_score -= 1
                sentiment_factors.append(f"Negative 24h trend ({price_change_24h:.2f}%)")
        
        # Technical sentiment
        rsi = indicators.get('rsi', 50)
        if 40 <= rsi <= 60:
            sentiment_score += 1
            sentiment_factors.append("RSI in healthy range")
        elif rsi > 70:
            sentiment_score -= 1
            sentiment_factors.append("RSI overbought")
        elif rsi < 30:
            sentiment_score += 1
            sentiment_factors.append("RSI oversold (potential bounce)")
        
        # Volume sentiment
        if indicators.get('volume_above_average', False):
            sentiment_score += 1
            sentiment_factors.append("Volume above average")
        
        # Trend sentiment
        if indicators.get('ema_crossover', False) and indicators.get('sma_trend', False):
            sentiment_score += 2
            sentiment_factors.append("Strong bullish trend alignment")
        elif indicators.get('ema_crossover', False):
            sentiment_score += 1
            sentiment_factors.append("EMA bullish crossover")
        
        # Overall sentiment
        if sentiment_score >= 3:
            sentiment_status = "🟢 VERY BULLISH"
        elif sentiment_score >= 1:
            sentiment_status = "🟡 BULLISH"
        elif sentiment_score <= -3:
            sentiment_status = "🔴 VERY BEARISH"
        elif sentiment_score <= -1:
            sentiment_status = "🟠 BEARISH"
        else:
            sentiment_status = "⚪ NEUTRAL"
        
        print(f"   Overall Sentiment: {sentiment_status} (Score: {sentiment_score:+d})")
        
        # Show top sentiment factors
        for factor in sentiment_factors[:3]:
            print(f"   └─ {factor}")
        
        # Market alerts
        if abs(sentiment_score) >= 3:
            alert_type = "STRONG BULLISH" if sentiment_score > 0 else "STRONG BEARISH"
            print(f"   🚨 ALERT: {alert_type} market sentiment detected!")
    
    def _show_session_performance(self):
        """Show current session performance"""
        session_duration = datetime.utcnow() - self.session_start
        hours_running = session_duration.total_seconds() / 3600
        
        print(f"\n📈 SESSION PERFORMANCE")
        print(f"   ⏱️ Running Time: {session_duration}")
        print(f"   📊 Analyses Completed: {self.analysis_count}")
        print(f"   🎯 Signals Generated: {self.signals_today}")
        print(f"   💼 Trades Executed: {self.trades_today}")
        print(f"   📈 Analysis Rate: {self.analysis_count/hours_running:.1f}/hour" if hours_running > 0 else "   📈 Analysis Rate: N/A")
        
        # Recent price alerts
        if self.price_alerts:
            print(f"   🚨 Recent Alerts: {len(self.price_alerts)}")
            for alert in self.price_alerts[-2:]:  # Show last 2 alerts
                print(f"      └─ {alert}")
    
    def _store_analysis_data(self, symbol: str, timeframe: str, indicators: Dict[str, Any], market_data: pd.DataFrame):
        """Store analysis data in database"""
        try:
            # Store latest market data
            latest = market_data.iloc[-1]
            self.database.insert_market_data(symbol, timeframe, {
                'timestamp': latest['timestamp'],
                'open': latest['open'],
                'high': latest['high'],
                'low': latest['low'],
                'close': latest['close'],
                'volume': latest['volume']
            })
            
            # Store indicators
            self.database.insert_indicators(
                symbol=symbol,
                timeframe=timeframe,
                timestamp=datetime.utcnow(),
                indicators_data=indicators
            )
            
            # Log activity
            self.database.log_bot_activity('INFO', f'Enhanced analysis #{self.analysis_count} completed', {
                'symbol': symbol,
                'indicators_count': len(indicators),
                'analysis_time': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            print(f"   ⚠️ Database storage error: {e}")

if __name__ == "__main__":
    # Test the enhanced logger
    from core.database_schema import TradingDatabase
    from strategies.strategy_engine import StrategyEngine, MultiIndicatorStrategy
    from core.risk_management import RiskManager
    from core.binance_client import BinanceClient
    
    print("🧪 Testing Enhanced Market Logger...")
    
    # Initialize components
    db = TradingDatabase()
    exchange = BinanceClient()
    strategy_engine = StrategyEngine(db)
    risk_manager = RiskManager(db, config.STRATEGY_CONFIG)
    
    # Add some strategies
    strategy_engine.register_strategy(MultiIndicatorStrategy(config.STRATEGY_CONFIG))
    strategy_engine.activate_strategy("MultiIndicator")
    
    # Create enhanced logger
    logger = EnhancedMarketLogger(db, strategy_engine, risk_manager, exchange)
    
    # Run a single analysis
    logger._perform_detailed_analysis()
    
    print("\n✅ Enhanced logger test completed!")