#!/usr/bin/env python3
"""
Test Signal Generator

This script temporarily modifies strategy parameters to trigger buy/sell signals
for testing purposes. It shows you what the bot looks like when it finds trading opportunities.
"""

import sys
import time
from strategy import AdvancedMultiIndicatorStrategy
from risk_manager import AdvancedRiskManager
from exchange_handler import ExchangeHandler
from config import TRADING_CONFIG

class TestSignalGenerator:
    def __init__(self):
        self.exchange = ExchangeHandler()
        self.strategy = AdvancedMultiIndicatorStrategy()
        self.risk_manager = AdvancedRiskManager()
    
    def test_buy_signal(self):
        """Simulate conditions that would trigger a BUY signal"""
        print("🧪 TESTING BUY SIGNAL CONDITIONS")
        print("="*50)
        
        # Temporarily modify strategy to be more aggressive for testing
        original_rsi_oversold = self.strategy.rsi_oversold
        original_signal_threshold = 4
        
        # Make it easier to trigger signals
        self.strategy.rsi_oversold = 60  # Higher threshold
        
        df = self.exchange.fetch_ohlcv(TRADING_CONFIG['symbol'], TRADING_CONFIG['timeframe'])
        df = self.strategy.calculate_indicators(df)
        
        # Show what we're testing
        latest = df.iloc[-1]
        print(f"Current RSI: {latest['RSI']:.1f} (Modified threshold: {self.strategy.rsi_oversold})")
        
        signal = self.strategy.generate_signal(df)
        strength = self.strategy.get_signal_strength(df)
        
        print(f"Result: {signal} (Strength: {strength}/10)")
        
        if signal == 'BUY':
            self._simulate_trade_execution(df, signal, strength)
        else:
            print("❌ Still no BUY signal with modified parameters")
            self._show_detailed_analysis(df)
        
        # Restore original values
        self.strategy.rsi_oversold = original_rsi_oversold
    
    def test_sell_signal(self):
        """Simulate conditions that would trigger a SELL signal"""
        print("\n🧪 TESTING SELL SIGNAL CONDITIONS")
        print("="*50)
        
        # Temporarily modify strategy to be more aggressive for testing
        original_rsi_overbought = self.strategy.rsi_overbought
        
        # Make it easier to trigger signals
        self.strategy.rsi_overbought = 40  # Lower threshold
        
        df = self.exchange.fetch_ohlcv(TRADING_CONFIG['symbol'], TRADING_CONFIG['timeframe'])
        df = self.strategy.calculate_indicators(df)
        
        # Show what we're testing
        latest = df.iloc[-1]
        print(f"Current RSI: {latest['RSI']:.1f} (Modified threshold: {self.strategy.rsi_overbought})")
        
        signal = self.strategy.generate_signal(df)
        strength = self.strategy.get_signal_strength(df)
        
        print(f"Result: {signal} (Strength: {strength}/10)")
        
        if signal == 'SELL':
            self._simulate_trade_execution(df, signal, strength)
        else:
            print("❌ Still no SELL signal with modified parameters")
            self._show_detailed_analysis(df)
        
        # Restore original values
        self.strategy.rsi_overbought = original_rsi_overbought
    
    def _simulate_trade_execution(self, df, signal, strength):
        """Simulate what happens when a trade is executed"""
        latest = df.iloc[-1]
        
        print(f"\n✅ {signal} SIGNAL TRIGGERED!")
        print(f"Signal Strength: {strength}/10")
        
        # Calculate trade details
        side = 'buy' if signal == 'BUY' else 'sell'
        entry_price = latest['close']
        atr_value = latest['ATR']
        
        stop_loss = self.risk_manager.determine_stop_loss(entry_price, side, atr_value, df, method='adaptive')
        balance = self.exchange.get_balance()
        position_size = self.risk_manager.calculate_position_size(balance, entry_price, stop_loss, strength)
        take_profit = self.risk_manager.calculate_take_profit(entry_price, stop_loss, side, 2.0)
        
        print(f"\n💼 TRADE SIMULATION:")
        print(f"   Side: {side.upper()}")
        print(f"   Entry Price: ${entry_price:.2f}")
        print(f"   Stop Loss: ${stop_loss:.2f}")
        print(f"   Take Profit: ${take_profit:.2f}")
        print(f"   Position Size: {position_size:.6f} ETH")
        print(f"   Trade Value: ${position_size * entry_price:.2f}")
        print(f"   Risk Amount: ${abs(entry_price - stop_loss) * position_size:.2f}")
        print(f"   Potential Profit: ${abs(take_profit - entry_price) * position_size:.2f}")
        
        # Show risk/reward
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)
        ratio = reward / risk if risk > 0 else 0
        print(f"   Risk/Reward Ratio: 1:{ratio:.1f}")
        
        print(f"\n🎯 This is what you'd see when the bot finds a real trading opportunity!")
    
    def _show_detailed_analysis(self, df):
        """Show detailed analysis of why no signal was generated"""
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        
        print(f"\n📊 DETAILED ANALYSIS:")
        
        # Trend analysis
        trend = self.strategy.analyze_trend(df)
        print(f"   Trend: {trend.upper()}")
        
        # Key indicators
        print(f"   RSI: {latest['RSI']:.1f}")
        print(f"   MACD: {latest['MACD']:.4f} (Signal: {latest['MACD_signal']:.4f})")
        print(f"   ADX: {latest['ADX']:.1f}")
        print(f"   Volume Ratio: {latest['Volume_ratio']:.2f}x")
        
        # Signal breakdown
        momentum_signals = self.strategy.check_momentum_signals(df)
        volatility_signals = self.strategy.check_volatility_signals(df)
        
        active_momentum = [key for key, value in momentum_signals.items() if value]
        active_volatility = [key for key, value in volatility_signals.items() if value]
        
        print(f"   Active Momentum Signals: {len(active_momentum)}")
        print(f"   Active Volatility Signals: {len(active_volatility)}")
        
        print(f"\n💡 The market conditions aren't quite right for a strong signal yet.")
        print(f"   Keep monitoring - opportunities will come!")

def main():
    """Run signal tests"""
    print("🧪 TRADING SIGNAL TESTER")
    print("="*50)
    print("This tool simulates buy/sell signals by temporarily")
    print("modifying strategy parameters to show you what the")
    print("bot looks like when it finds trading opportunities.")
    print("="*50)
    
    try:
        tester = TestSignalGenerator()
        
        # Test buy signal
        tester.test_buy_signal()
        
        time.sleep(2)
        
        # Test sell signal
        tester.test_sell_signal()
        
        print(f"\n🎯 TESTING COMPLETE!")
        print(f"Now you know what to expect when the bot finds real signals.")
        print(f"Run 'python main.py' to start monitoring for actual opportunities.")
        
    except KeyboardInterrupt:
        print("\n🛑 Testing stopped by user")
    except Exception as e:
        print(f"\n❌ Testing failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
