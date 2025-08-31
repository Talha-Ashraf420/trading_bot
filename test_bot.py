#!/usr/bin/env python3
"""
Simple test script to verify the trading bot is working correctly
"""

from strategy import AdvancedMultiIndicatorStrategy
from risk_manager import AdvancedRiskManager
from exchange_handler import ExchangeHandler
from config import TRADING_CONFIG

def test_bot():
    """Test all components of the trading bot"""
    print("🚀 TESTING TRADING BOT COMPONENTS")
    print("="*50)
    
    try:
        # Test 1: Exchange Connection
        print("\n1. Testing Exchange Connection...")
        exchange = ExchangeHandler()
        print("✅ Exchange connected successfully")
        
        # Test 2: Data Fetching
        print("\n2. Testing Data Fetching...")
        df = exchange.fetch_ohlcv(TRADING_CONFIG['symbol'], TRADING_CONFIG['timeframe'], limit=100)
        print(f"✅ Fetched {len(df)} candles")
        print(f"   Latest price: ${df.iloc[-1]['close']:.2f}")
        
        # Test 3: Strategy Initialization
        print("\n3. Testing Strategy...")
        strategy = AdvancedMultiIndicatorStrategy()
        print("✅ Strategy initialized")
        
        # Test 4: Indicator Calculations
        print("\n4. Testing Indicator Calculations...")
        df = strategy.calculate_indicators(df)
        print("✅ All indicators calculated")
        
        # Show some indicator values
        latest = df.iloc[-1]
        print(f"   RSI: {latest['RSI']:.1f}")
        print(f"   MACD: {latest['MACD']:.4f}")
        print(f"   ATR: {latest['ATR']:.4f}")
        print(f"   ADX: {latest['ADX']:.1f}")
        
        # Test 5: Signal Generation
        print("\n5. Testing Signal Generation...")
        signal = strategy.generate_signal(df)
        strength = strategy.get_signal_strength(df)
        print(f"✅ Signal: {signal} (Strength: {strength}/10)")
        
        # Test 6: Risk Management
        print("\n6. Testing Risk Management...")
        risk_manager = AdvancedRiskManager()
        
        if signal != 'HOLD':
            side = 'buy' if signal == 'BUY' else 'sell'
            entry_price = latest['close']
            atr_value = latest['ATR']
            
            stop_loss = risk_manager.determine_stop_loss(entry_price, side, atr_value, df, method='adaptive')
            balance = exchange.get_balance()
            position_size = risk_manager.calculate_position_size(balance, entry_price, stop_loss, strength)
            
            print(f"✅ Risk management calculated")
            print(f"   Entry: ${entry_price:.2f}")
            print(f"   Stop Loss: ${stop_loss:.2f}")
            print(f"   Position Size: {position_size:.6f}")
        else:
            print("✅ Risk management ready (no active signal)")
        
        # Test 7: Portfolio Metrics
        print("\n7. Testing Portfolio Metrics...")
        metrics = risk_manager.get_portfolio_metrics()
        print(f"✅ Portfolio metrics calculated")
        print(f"   Total Risk: {metrics['total_portfolio_risk']:.2%}")
        print(f"   Open Positions: {metrics['open_positions']}")
        
        print("\n🎉 ALL TESTS PASSED!")
        print("Your trading bot is ready to use!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_bot()
    if success:
        print("\n📋 NEXT STEPS:")
        print("1. Run 'python strategy_analyzer.py' for detailed market analysis")
        print("2. Run 'python backtesting.py' to test on historical data")
        print("3. Run 'python main.py' to start the trading bot (test mode)")
        print("\n⚠️  Remember: Always start with paper trading!")
    else:
        print("\n🔧 Please fix the issues above before proceeding.")
