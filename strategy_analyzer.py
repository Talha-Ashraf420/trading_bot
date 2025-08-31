# strategy_analyzer.py
"""
Strategy Analysis Tool

This script helps you analyze and compare different trading strategies,
understand signal generation, and optimize parameters.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from strategy import AdvancedMultiIndicatorStrategy
from exchange_handler import ExchangeHandler
from config import TRADING_CONFIG, STRATEGY_CONFIG

class StrategyAnalyzer:
    def __init__(self):
        self.strategy = AdvancedMultiIndicatorStrategy()
        self.exchange = ExchangeHandler()
    
    def analyze_current_market(self, symbol=None, timeframe=None):
        """Analyze current market conditions and signals"""
        symbol = symbol or TRADING_CONFIG['symbol']
        timeframe = timeframe or TRADING_CONFIG['timeframe']
        
        print(f"\n{'='*60}")
        print(f"📊 MARKET ANALYSIS FOR {symbol} ({timeframe})")
        print(f"{'='*60}")
        
        # Fetch data
        df = self.exchange.fetch_ohlcv(symbol, timeframe, limit=200)
        if df.empty:
            print("❌ Could not fetch market data")
            return
        
        # Calculate indicators
        df = self.strategy.calculate_indicators(df)
        
        # Get latest values
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Current price info
        print(f"\n💰 PRICE INFORMATION:")
        print(f"Current Price: ${latest['close']:.2f}")
        print(f"24h Change: {((latest['close'] - df.iloc[-24]['close']) / df.iloc[-24]['close'] * 100):+.2f}%")
        print(f"Volume Ratio: {latest['Volume_ratio']:.2f}x average")
        
        # Trend analysis
        trend = self.strategy.analyze_trend(df)
        print(f"\n📈 TREND ANALYSIS:")
        print(f"Overall Trend: {trend.upper()}")
        print(f"EMA Fast (12): ${latest['EMA_fast']:.2f}")
        print(f"EMA Slow (26): ${latest['EMA_slow']:.2f}")
        print(f"SMA Trend (50): ${latest['SMA_trend']:.2f}")
        print(f"ADX Strength: {latest['ADX']:.1f} ({'Strong' if latest['ADX'] > 25 else 'Weak'} trend)")
        
        # Momentum indicators
        print(f"\n⚡ MOMENTUM INDICATORS:")
        print(f"RSI: {latest['RSI']:.1f} ({'Oversold' if latest['RSI'] < 30 else 'Overbought' if latest['RSI'] > 70 else 'Neutral'})")
        print(f"MACD: {latest['MACD']:.4f} (Signal: {latest['MACD_signal']:.4f})")
        print(f"Stochastic %K: {latest['Stoch_K']:.1f} ({'Oversold' if latest['Stoch_K'] < 20 else 'Overbought' if latest['Stoch_K'] > 80 else 'Neutral'})")
        
        # Volatility analysis
        print(f"\n🌊 VOLATILITY ANALYSIS:")
        print(f"ATR: {latest['ATR']:.4f}")
        print(f"BB Position: {latest['BB_position']:.2f} (0=lower band, 1=upper band)")
        print(f"BB Width: {latest['BB_width']:.4f} ({'Squeeze' if latest['BB_width'] < 0.02 else 'Normal'})")
        
        # Signal analysis
        signal = self.strategy.generate_signal(df)
        signal_strength = self.strategy.get_signal_strength(df)
        
        print(f"\n🎯 SIGNAL ANALYSIS:")
        print(f"Current Signal: {signal}")
        print(f"Signal Strength: {signal_strength}/10")
        
        # Get detailed signal breakdown
        momentum_signals = self.strategy.check_momentum_signals(df)
        volatility_signals = self.strategy.check_volatility_signals(df)
        
        print(f"\n📋 SIGNAL BREAKDOWN:")
        print("Momentum Signals:")
        for key, value in momentum_signals.items():
            if value:
                print(f"  ✅ {key.replace('_', ' ').title()}")
        
        print("Volatility Signals:")
        for key, value in volatility_signals.items():
            if value:
                print(f"  ✅ {key.replace('_', ' ').title()}")
        
        return df
    
    def backtest_simple(self, symbol=None, days=30):
        """Simple backtest to show strategy performance"""
        symbol = symbol or TRADING_CONFIG['symbol']
        
        print(f"\n{'='*60}")
        print(f"📊 SIMPLE BACKTEST - {symbol} (Last {days} days)")
        print(f"{'='*60}")
        
        # Fetch more data for backtest
        df = self.exchange.fetch_ohlcv(symbol, TRADING_CONFIG['timeframe'], limit=days*288)  # 5min * 288 = 1 day
        if df.empty:
            print("❌ Could not fetch historical data")
            return
        
        df = self.strategy.calculate_indicators(df)
        
        # Simple signal tracking
        signals = []
        prices = []
        strengths = []
        
        for i in range(50, len(df)):  # Start after indicators are calculated
            current_df = df.iloc[:i+1]
            signal = self.strategy.generate_signal(current_df)
            strength = self.strategy.get_signal_strength(current_df)
            
            signals.append(signal)
            prices.append(df.iloc[i]['close'])
            strengths.append(strength)
        
        # Count signals
        buy_signals = signals.count('BUY')
        sell_signals = signals.count('SELL')
        hold_signals = signals.count('HOLD')
        
        print(f"Total Signals Generated: {len(signals)}")
        print(f"  📈 BUY signals: {buy_signals}")
        print(f"  📉 SELL signals: {sell_signals}")
        print(f"  ⏸️  HOLD signals: {hold_signals}")
        
        # Calculate average signal strength
        buy_strengths = [strengths[i] for i, s in enumerate(signals) if s == 'BUY']
        sell_strengths = [strengths[i] for i, s in enumerate(signals) if s == 'SELL']
        
        if buy_strengths:
            print(f"Average BUY signal strength: {np.mean(buy_strengths):.1f}/10")
        if sell_strengths:
            print(f"Average SELL signal strength: {np.mean(sell_strengths):.1f}/10")
        
        return signals, prices, strengths
    
    def compare_timeframes(self, symbol=None):
        """Compare signals across different timeframes"""
        symbol = symbol or TRADING_CONFIG['symbol']
        timeframes = ['5m', '15m', '1h', '4h']
        
        print(f"\n{'='*60}")
        print(f"🕐 MULTI-TIMEFRAME ANALYSIS - {symbol}")
        print(f"{'='*60}")
        
        for tf in timeframes:
            try:
                df = self.exchange.fetch_ohlcv(symbol, tf, limit=100)
                if df.empty:
                    continue
                
                df = self.strategy.calculate_indicators(df)
                signal = self.strategy.generate_signal(df)
                strength = self.strategy.get_signal_strength(df)
                trend = self.strategy.analyze_trend(df)
                
                print(f"{tf:>4}: {signal:>4} (Strength: {strength}/10, Trend: {trend})")
                
            except Exception as e:
                print(f"{tf:>4}: Error - {str(e)}")
    
    def plot_indicators(self, symbol=None, save_plot=True):
        """Create a comprehensive chart with all indicators"""
        try:
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
            from matplotlib.patches import Rectangle
        except ImportError:
            print("❌ Matplotlib not installed. Run: pip install matplotlib")
            return
        
        symbol = symbol or TRADING_CONFIG['symbol']
        df = self.exchange.fetch_ohlcv(symbol, TRADING_CONFIG['timeframe'], limit=200)
        if df.empty:
            print("❌ Could not fetch data for plotting")
            return
        
        df = self.strategy.calculate_indicators(df)
        
        # Create subplots
        fig, axes = plt.subplots(4, 1, figsize=(15, 12))
        fig.suptitle(f'{symbol} - Advanced Multi-Indicator Analysis', fontsize=16, fontweight='bold')
        
        # Plot 1: Price and Moving Averages
        ax1 = axes[0]
        ax1.plot(df.index, df['close'], label='Close Price', linewidth=2, color='black')
        ax1.plot(df.index, df['EMA_fast'], label='EMA Fast (12)', alpha=0.7, color='blue')
        ax1.plot(df.index, df['EMA_slow'], label='EMA Slow (26)', alpha=0.7, color='red')
        ax1.plot(df.index, df['SMA_trend'], label='SMA Trend (50)', alpha=0.7, color='green')
        ax1.fill_between(df.index, df['BB_lower'], df['BB_upper'], alpha=0.1, color='gray', label='Bollinger Bands')
        ax1.set_title('Price Action & Moving Averages')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: RSI and Stochastic
        ax2 = axes[1]
        ax2.plot(df.index, df['RSI'], label='RSI', color='purple', linewidth=2)
        ax2.axhline(y=70, color='r', linestyle='--', alpha=0.5, label='Overbought (70)')
        ax2.axhline(y=30, color='g', linestyle='--', alpha=0.5, label='Oversold (30)')
        ax2.plot(df.index, df['Stoch_K'], label='Stochastic %K', color='orange', alpha=0.7)
        ax2.set_title('Momentum Oscillators')
        ax2.set_ylim(0, 100)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: MACD
        ax3 = axes[2]
        ax3.plot(df.index, df['MACD'], label='MACD', color='blue', linewidth=2)
        ax3.plot(df.index, df['MACD_signal'], label='Signal Line', color='red', linewidth=2)
        ax3.bar(df.index, df['MACD_histogram'], label='Histogram', alpha=0.3, color='green')
        ax3.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        ax3.set_title('MACD')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Plot 4: Volume and ATR
        ax4 = axes[3]
        ax4_twin = ax4.twinx()
        ax4.bar(df.index, df['volume'], alpha=0.3, color='blue', label='Volume')
        ax4_twin.plot(df.index, df['ATR'], color='red', linewidth=2, label='ATR')
        ax4.set_title('Volume & Volatility (ATR)')
        ax4.legend(loc='upper left')
        ax4_twin.legend(loc='upper right')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_plot:
            filename = f"{symbol.replace('/', '_')}_analysis.png"
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            print(f"📊 Chart saved as: {filename}")
        
        plt.show()

def main():
    """Main function to run strategy analysis"""
    analyzer = StrategyAnalyzer()
    
    print("🚀 ADVANCED TRADING STRATEGY ANALYZER")
    print("=====================================")
    
    while True:
        print("\nChoose an analysis option:")
        print("1. 📊 Current Market Analysis")
        print("2. 📈 Simple Backtest")
        print("3. 🕐 Multi-Timeframe Analysis")
        print("4. 📊 Plot Indicators Chart")
        print("5. 🔧 Strategy Configuration")
        print("6. ❌ Exit")
        
        choice = input("\nEnter your choice (1-6): ").strip()
        
        if choice == '1':
            analyzer.analyze_current_market()
        elif choice == '2':
            days = input("Enter number of days to backtest (default 30): ").strip()
            days = int(days) if days.isdigit() else 30
            analyzer.backtest_simple(days=days)
        elif choice == '3':
            analyzer.compare_timeframes()
        elif choice == '4':
            analyzer.plot_indicators()
        elif choice == '5':
            print(f"\n📋 CURRENT STRATEGY CONFIGURATION:")
            print(f"{'='*50}")
            for key, value in STRATEGY_CONFIG.items():
                print(f"{key:20}: {value}")
        elif choice == '6':
            print("👋 Goodbye! Happy trading!")
            break
        else:
            print("❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
