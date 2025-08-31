# main.py
import time
import schedule
from exchange_handler import ExchangeHandler
from strategy import TradingStrategy
from risk_manager import RiskManager
from config import TRADING_CONFIG

class TradingBot:
    def __init__(self):
        self.exchange = ExchangeHandler()
        self.strategy = TradingStrategy()
        self.risk_manager = RiskManager()
        self.in_position = False

    def run_trade_cycle(self):
        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print("\n" + "="*70)
        print(f"🔄 Running Trade Cycle - {current_time}")
        print("="*70)

        if self.in_position:
            print("📍 Already in a position. Checking exit conditions...")
            # In a real bot, you would check exit conditions here.
            # For simplicity, this example only handles entries.
            return

        # 1. Fetch Data
        print("📊 Fetching market data...")
        df = self.exchange.fetch_ohlcv(TRADING_CONFIG['symbol'], TRADING_CONFIG['timeframe'])
        if df.empty:
            print("❌ Could not fetch data. Skipping cycle.")
            return

        # 2. Calculate Indicators
        print("🔢 Calculating technical indicators...")
        df = self.strategy.calculate_indicators(df)

        # 3. Show Current Market Info
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        
        price_change = ((latest['close'] - prev['close']) / prev['close']) * 100
        price_change_str = f"+{price_change:.2f}%" if price_change > 0 else f"{price_change:.2f}%"
        
        print(f"\n💰 CURRENT MARKET STATUS:")
        print(f"   Symbol: {TRADING_CONFIG['symbol']}")
        print(f"   Price: ${latest['close']:.2f} ({price_change_str})")
        print(f"   Volume: {latest['volume']:,.0f}")
        print(f"   RSI: {latest['RSI']:.1f}")
        print(f"   MACD: {latest['MACD']:.4f}")
        print(f"   ADX: {latest['ADX']:.1f} ({'Strong' if latest['ADX'] > 25 else 'Weak'} trend)")

        # 4. Generate Signal
        signal = self.strategy.generate_signal(df)
        signal_strength = self.strategy.get_signal_strength(df)
        
        print(f"\n🎯 SIGNAL ANALYSIS:")
        print(f"   Signal: {signal}")
        print(f"   Strength: {signal_strength}/10")
        
        # Show detailed signal breakdown
        trend = self.strategy.analyze_trend(df)
        momentum_signals = self.strategy.check_momentum_signals(df)
        volatility_signals = self.strategy.check_volatility_signals(df)
        
        print(f"   Trend: {trend.upper()}")
        
        # Show active momentum signals
        active_momentum = [key.replace('_', ' ').title() for key, value in momentum_signals.items() if value]
        if active_momentum:
            print(f"   Momentum Signals: {', '.join(active_momentum[:3])}{'...' if len(active_momentum) > 3 else ''}")
        
        # Show active volatility signals
        active_volatility = [key.replace('_', ' ').title() for key, value in volatility_signals.items() if value]
        if active_volatility:
            print(f"   Volatility Signals: {', '.join(active_volatility[:3])}{'...' if len(active_volatility) > 3 else ''}")

        if signal == 'HOLD':
            print(f"\n⏸️  HOLDING - Signal strength ({signal_strength}) below threshold or conflicting signals")
            self._show_buy_sell_conditions(df)
            return

        # 5. Get market conditions for risk management
        latest = df.iloc[-1]
        volatility_factor = latest['ATR'] / df['ATR'].rolling(20).mean().iloc[-1] if len(df) >= 20 else 1.0
        portfolio_metrics = self.risk_manager.get_portfolio_metrics()
        
        print(f"\n📊 RISK ASSESSMENT:")
        print(f"   Signal Strength: {signal_strength}/10")
        print(f"   Volatility Factor: {volatility_factor:.2f}x")
        print(f"   Portfolio Risk: {portfolio_metrics['total_portfolio_risk']:.2%}")
        
        # 6. Risk Management - Check if trade should be taken
        should_trade, reason = self.risk_manager.should_take_trade(
            signal_strength, volatility_factor, portfolio_metrics['total_portfolio_risk']
        )
        
        if not should_trade:
            print(f"\n❌ TRADE REJECTED: {reason}")
            self._show_buy_sell_conditions(df)
            return
        
        # 7. Calculate position details
        print(f"\n✅ TRADE APPROVED - Proceeding with {signal} order")
        side = 'buy' if signal == 'BUY' else 'sell'
        entry_price = latest['close']
        atr_value = latest['ATR']
        
        # Use adaptive stop-loss method for better results
        stop_loss_price = self.risk_manager.determine_stop_loss(
            entry_price, side, atr_value, df, method='adaptive'
        )
        
        if stop_loss_price is None:
            print("Could not determine stop-loss price. Skipping trade.")
            return
            
        balance = self.exchange.get_balance()
        position_size = self.risk_manager.calculate_position_size(
            balance, entry_price, stop_loss_price, signal_strength, volatility_factor
        )
        
        # Calculate take-profit level
        take_profit_price = self.risk_manager.calculate_take_profit(
            entry_price, stop_loss_price, side, risk_reward_ratio=2.0
        )
        
        print(f"\n💼 TRADE DETAILS:")
        print(f"   Account Balance: ${balance:.2f} USDT")
        print(f"   Entry Price: ${entry_price:.2f}")
        print(f"   Stop Loss: ${stop_loss_price:.2f}")
        print(f"   Take Profit: ${take_profit_price:.2f}")
        print(f"   Position Size: {position_size:.6f} {TRADING_CONFIG['symbol'].split('/')[0]}")
        print(f"   Trade Value: ${position_size * entry_price:.2f}")
        print(f"   Risk Amount: ${abs(entry_price - stop_loss_price) * position_size:.2f}")

        if position_size <= 0:
            print("\n❌ Position size is zero or negative. No trade will be placed.")
            return

        # 8. Execute Order
        order = self.exchange.create_market_order(TRADING_CONFIG['symbol'], side, position_size)
        
        if order:
            print(f"\n🎉 TRADE EXECUTED SUCCESSFULLY!")
            print(f"   Order ID: {order.get('id', 'N/A')}")
            print(f"   Side: {side.upper()}")
            print(f"   Amount: {position_size:.6f}")
            print(f"   Price: ${entry_price:.2f}")
            self.in_position = True
            # In a real bot, you would store order details and monitor for exit.
        else:
            print(f"\n❌ TRADE EXECUTION FAILED!")
    
    def _show_buy_sell_conditions(self, df):
        """Show what conditions need to be met for buy/sell signals"""
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        
        print(f"\n📋 BUY/SELL CONDITIONS STATUS:")
        print(f"   Current Signal Threshold: 4 points minimum")
        
        # Calculate current scores
        buy_score = 0
        sell_score = 0
        
        # Trend scoring
        trend = self.strategy.analyze_trend(df)
        if trend == 'bullish':
            buy_score += 2
            print(f"   ✅ Bullish Trend: +2 buy points")
        elif trend == 'bearish':
            sell_score += 2
            print(f"   ✅ Bearish Trend: +2 sell points")
        else:
            print(f"   ⚪ Neutral Trend: +0 points")
        
        # RSI scoring
        if latest['RSI'] < 30:
            buy_score += 2
            print(f"   ✅ RSI Oversold ({latest['RSI']:.1f}): +2 buy points")
        elif latest['RSI'] > 70:
            sell_score += 2
            print(f"   ✅ RSI Overbought ({latest['RSI']:.1f}): +2 sell points")
        else:
            print(f"   ⚪ RSI Neutral ({latest['RSI']:.1f}): +0 points")
        
        # MACD scoring
        if latest['MACD'] > latest['MACD_signal'] and prev['MACD'] <= prev['MACD_signal']:
            buy_score += 2
            print(f"   ✅ MACD Bullish Crossover: +2 buy points")
        elif latest['MACD'] < latest['MACD_signal'] and prev['MACD'] >= prev['MACD_signal']:
            sell_score += 2
            print(f"   ✅ MACD Bearish Crossover: +2 sell points")
        else:
            macd_status = "Above" if latest['MACD'] > latest['MACD_signal'] else "Below"
            print(f"   ⚪ MACD {macd_status} Signal: +0 points")
        
        # Volume scoring
        if latest['Volume_ratio'] > 1.5:
            if buy_score > sell_score:
                buy_score += 1
                print(f"   ✅ High Volume + Buy Bias: +1 buy point")
            elif sell_score > buy_score:
                sell_score += 1
                print(f"   ✅ High Volume + Sell Bias: +1 sell point")
            else:
                print(f"   ⚪ High Volume (no bias): +0 points")
        else:
            print(f"   ⚪ Normal Volume ({latest['Volume_ratio']:.2f}x): +0 points")
        
        print(f"\n📊 CURRENT SCORES:")
        print(f"   Buy Score: {buy_score}/4 {'✅ WOULD BUY' if buy_score >= 4 and buy_score > sell_score else '❌ Not enough'}")
        print(f"   Sell Score: {sell_score}/4 {'✅ WOULD SELL' if sell_score >= 4 and sell_score > buy_score else '❌ Not enough'}")
        
        # Show what's needed
        if buy_score < 4 and sell_score < 4:
            needed_buy = 4 - buy_score
            needed_sell = 4 - sell_score
            print(f"\n💡 TO TRIGGER SIGNALS:")
            print(f"   Need {needed_buy} more points for BUY")
            print(f"   Need {needed_sell} more points for SELL")
            print(f"   Watch for: RSI extremes, MACD crossovers, trend changes")

def job():
    bot = TradingBot()
    bot.run_trade_cycle()

if __name__ == '__main__':
    print("🚀 STARTING ADVANCED TRADING BOT")
    print("="*50)
    print("⚠️  Running in TEST MODE - No real money at risk")
    print("📊 Monitoring ETH/USDT every 30 seconds")
    print("🛑 Press Ctrl+C to stop")
    print("="*50)
    
    try:
        # Run the job immediately
        job() 
        
        # Schedule every 30 seconds for testing (change to 5 minutes for production)
        schedule.every(30).seconds.do(job)
        
        while True:
            schedule.run_pending()
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Bot stopped by user")
        print("👋 Thanks for using the Advanced Trading Bot!")
    except Exception as e:
        print(f"\n❌ Bot stopped due to error: {e}")
        import traceback
        traceback.print_exc()