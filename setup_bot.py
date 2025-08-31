#!/usr/bin/env python3
"""
Trading Bot Setup Script

This script helps you set up and configure your trading bot for the first time.
It will guide you through the configuration process and run initial tests.
"""

import os
import sys
import subprocess
from pathlib import Path

def print_header(title):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"🚀 {title}")
    print(f"{'='*60}")

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required!")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def install_requirements():
    """Install required packages"""
    print_header("INSTALLING REQUIREMENTS")
    
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print("❌ requirements.txt not found!")
        return False
    
    try:
        print("📦 Installing required packages...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ All packages installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing packages: {e}")
        return False

def test_imports():
    """Test if all required modules can be imported"""
    print_header("TESTING IMPORTS")
    
    required_modules = [
        'pandas',
        'numpy',
        'pandas_ta',
        'ccxt',
        'schedule',
        'matplotlib'
    ]
    
    failed_imports = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\n❌ Failed to import: {', '.join(failed_imports)}")
        print("Please install missing packages manually.")
        return False
    
    print("\n✅ All required modules imported successfully!")
    return True

def check_config():
    """Check configuration file"""
    print_header("CHECKING CONFIGURATION")
    
    try:
        from config import EXCHANGE_CONFIG, TRADING_CONFIG, STRATEGY_CONFIG
        
        print("✅ Configuration file loaded successfully!")
        print(f"Exchange: {EXCHANGE_CONFIG['id']}")
        print(f"Trading Pair: {TRADING_CONFIG['symbol']}")
        print(f"Timeframe: {TRADING_CONFIG['timeframe']}")
        print(f"Test Mode: {EXCHANGE_CONFIG.get('options', {}).get('test', False)}")
        
        # Check API keys
        if EXCHANGE_CONFIG['apiKey'] and EXCHANGE_CONFIG['secret']:
            print("✅ API credentials configured")
        else:
            print("⚠️  API credentials not configured")
            
        return True
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return False

def test_exchange_connection():
    """Test connection to exchange"""
    print_header("TESTING EXCHANGE CONNECTION")
    
    try:
        from exchange_handler import ExchangeHandler
        
        print("🔗 Connecting to exchange...")
        exchange = ExchangeHandler()
        
        # Test fetching data
        print("📊 Testing data fetch...")
        from config import TRADING_CONFIG
        df = exchange.fetch_ohlcv(TRADING_CONFIG['symbol'], TRADING_CONFIG['timeframe'], limit=10)
        
        if not df.empty:
            print(f"✅ Successfully fetched {len(df)} candles")
            print(f"Latest price: ${df.iloc[-1]['close']:.2f}")
        else:
            print("❌ No data received")
            return False
            
        # Test balance (if API keys are configured)
        try:
            balance = exchange.get_balance()
            print(f"✅ Account balance: {balance:.2f} USDT")
        except:
            print("⚠️  Could not fetch balance (API keys may not be configured)")
        
        return True
    except Exception as e:
        print(f"❌ Exchange connection failed: {e}")
        return False

def test_strategy():
    """Test strategy calculations"""
    print_header("TESTING STRATEGY")
    
    try:
        from strategy import AdvancedMultiIndicatorStrategy
        from exchange_handler import ExchangeHandler
        from config import TRADING_CONFIG
        
        print("🧠 Initializing strategy...")
        strategy = AdvancedMultiIndicatorStrategy()
        exchange = ExchangeHandler()
        
        print("📊 Fetching market data...")
        df = exchange.fetch_ohlcv(TRADING_CONFIG['symbol'], TRADING_CONFIG['timeframe'], limit=100)
        
        print("🔢 Calculating indicators...")
        df = strategy.calculate_indicators(df)
        
        print("🎯 Generating signal...")
        signal = strategy.generate_signal(df)
        strength = strategy.get_signal_strength(df)
        
        print(f"✅ Current signal: {signal}")
        print(f"✅ Signal strength: {strength}/10")
        
        return True
    except Exception as e:
        print(f"❌ Strategy test failed: {e}")
        return False

def run_sample_analysis():
    """Run a sample market analysis"""
    print_header("SAMPLE MARKET ANALYSIS")
    
    try:
        from strategy_analyzer import StrategyAnalyzer
        
        print("🔍 Running market analysis...")
        analyzer = StrategyAnalyzer()
        analyzer.analyze_current_market()
        
        return True
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 TRADING BOT SETUP WIZARD")
    print("============================")
    print("This script will help you set up your trading bot.")
    
    # Step 1: Check Python version
    if not check_python_version():
        return
    
    # Step 2: Install requirements
    install_choice = input("\n📦 Install required packages? (y/n): ").lower().strip()
    if install_choice == 'y':
        if not install_requirements():
            return
    
    # Step 3: Test imports
    if not test_imports():
        return
    
    # Step 4: Check configuration
    if not check_config():
        print("\n⚠️  Please configure your API keys in config.py before proceeding.")
        return
    
    # Step 5: Test exchange connection
    connection_choice = input("\n🔗 Test exchange connection? (y/n): ").lower().strip()
    if connection_choice == 'y':
        if not test_exchange_connection():
            print("\n⚠️  Exchange connection failed. Please check your configuration.")
            return
    
    # Step 6: Test strategy
    strategy_choice = input("\n🧠 Test strategy calculations? (y/n): ").lower().strip()
    if strategy_choice == 'y':
        if not test_strategy():
            return
    
    # Step 7: Run sample analysis
    analysis_choice = input("\n🔍 Run sample market analysis? (y/n): ").lower().strip()
    if analysis_choice == 'y':
        run_sample_analysis()
    
    # Final recommendations
    print_header("SETUP COMPLETE!")
    print("🎉 Your trading bot is ready to use!")
    print("\n📋 NEXT STEPS:")
    print("1. 📖 Read the TRADING_STRATEGY_GUIDE.md for detailed explanations")
    print("2. 🔧 Run strategy_analyzer.py to analyze current market conditions")
    print("3. 📊 Run backtesting.py to test the strategy on historical data")
    print("4. 🚀 Run main.py to start the trading bot (in test mode first!)")
    print("\n⚠️  IMPORTANT REMINDERS:")
    print("- Always start with paper trading (test mode)")
    print("- Never risk more than you can afford to lose")
    print("- Monitor the bot's performance regularly")
    print("- Keep learning and improving your strategy")
    
    print("\n💰 Good luck with your trading journey!")

if __name__ == "__main__":
    main()
