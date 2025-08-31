# main.py
"""
Advanced Multi-Strategy Trading Bot

Features:
- Multiple trading strategies with portfolio allocation
- MongoDB Atlas integration for order and user tracking
- Trading pair selection with risk management
- User account management with comprehensive logging
- Real-time updates every 30 seconds
"""

import time
import schedule
from datetime import datetime
from typing import Dict, List
from exchange_handler import ExchangeHandler
from strategy_manager import StrategyManager
from risk_manager import AdvancedRiskManager
from database import initialize_database, get_database
from config import TRADING_CONFIG

class AdvancedTradingBot:
    """Enhanced trading bot with multiple strategies and database integration"""
    
    def __init__(self, user_id: str, selected_pairs: List[str]):
        self.user_id = user_id
        self.selected_pairs = selected_pairs
        self.db = get_database()
        
        # Initialize components
        self.exchange = ExchangeHandler()
        self.strategy_manager = StrategyManager(user_id)
        self.risk_manager = AdvancedRiskManager()
        
        # Track positions per pair
        self.pair_positions = {pair: False for pair in selected_pairs}
        
        print(f"🚀 Advanced Trading Bot initialized for user: {user_id}")
        print(f"📊 Monitoring pairs: {', '.join(selected_pairs)}")
        
        # Add logging for 30-second updates
        self.last_log_time = time.time()
        self.log_interval = 30  # 30 seconds

    def run_trading_cycle(self):
        """Run trading cycle for all selected pairs"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        current_timestamp = time.time()
        
        # Check if we should show detailed logs (every 30 seconds)
        show_detailed_logs = (current_timestamp - self.last_log_time) >= self.log_interval
        
        if show_detailed_logs:
            print("\n" + "="*80)
            print(f"🔄 Advanced Trading Cycle - {current_time}")
            print("="*80)
            self.last_log_time = current_timestamp
        else:
            print(f"⏱️  {current_time} - Quick market scan...")
        
        # Get portfolio status
        portfolio_status = self.strategy_manager.get_portfolio_status()
        
        if show_detailed_logs:
            print(f"\n💼 PORTFOLIO STATUS:")
            print(f"   Balance: ${portfolio_status['current_balance']:.2f}")
            print(f"   Exposure: ${portfolio_status['total_exposure']:.2f} ({portfolio_status['exposure_ratio']:.1%})")
            print(f"   Positions: {portfolio_status['total_positions']}/{portfolio_status['max_positions']}")
        else:
            print(f"💼 Balance: ${portfolio_status['current_balance']:.2f} | Positions: {portfolio_status['total_positions']}/{portfolio_status['max_positions']}")
        
        if not portfolio_status['can_open_new']:
            if show_detailed_logs:
                print("⚠️  Maximum positions reached. Monitoring existing positions...")
            return
        
        # Analyze each trading pair
        for pair in self.selected_pairs:
            try:
                self._analyze_pair(pair, show_detailed_logs)
            except Exception as e:
                if show_detailed_logs:
                    print(f"❌ Error analyzing {pair}: {e}")
        
        # Show strategy performance (only in detailed logs)
        if show_detailed_logs:
            self._show_strategy_performance()

    def _analyze_pair(self, symbol: str, show_detailed_logs: bool = True):
        """Analyze a specific trading pair"""
        if show_detailed_logs:
            print(f"\n📊 ANALYZING {symbol}")
            print("-" * 40)
        
        # Fetch market data
        df = self.exchange.fetch_ohlcv(symbol, TRADING_CONFIG['timeframe'])
        if df.empty:
            if show_detailed_logs:
                print(f"❌ Could not fetch data for {symbol}")
            return
        
        # Get current price info
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        price_change = ((latest['close'] - prev['close']) / prev['close']) * 100
        price_change_str = f"+{price_change:.2f}%" if price_change > 0 else f"{price_change:.2f}%"
        
        # Analyze all strategies
        strategy_results = self.strategy_manager.analyze_all_strategies(df, symbol)
        
        # Get best signal
        best_strategy, best_signal, best_strength, allocation = self.strategy_manager.get_best_signal(df, symbol)
        
        if show_detailed_logs:
            print(f"   Price: ${latest['close']:.4f} ({price_change_str})")
            print(f"   Volume: {latest['volume']:,.0f}")
            
            print(f"   Strategy Analysis:")
            for strategy_name, result in strategy_results.items():
                status = "✅" if result['can_trade'] else "⏸️"
                print(f"     {status} {strategy_name.title()}: {result['signal']} (Strength: {result['strength']}/10)")
            
            if best_signal == 'HOLD' or best_strategy == 'none':
                print(f"   🔍 Result: HOLD - No strong signals detected")
                return
            
            print(f"   🎯 Best Signal: {best_signal} from {best_strategy} strategy")
            print(f"   💪 Signal Strength: {best_strength}/10")
        else:
            # Quick summary for non-detailed logs
            print(f"📊 {symbol}: ${latest['close']:.4f} ({price_change_str}) | Best: {best_signal if best_signal != 'HOLD' else 'HOLD'} ({best_strength}/10)")
            
            if best_signal == 'HOLD' or best_strategy == 'none':
                return
        
        # Execute trade if conditions are met
        self._execute_trade(symbol, best_strategy, best_signal, best_strength, allocation, df, show_detailed_logs)

    def _execute_trade(self, symbol: str, strategy_name: str, signal: str, 
                      strength: int, allocation: float, df, show_detailed_logs: bool = True):
        """Execute a trade based on strategy signal"""
        
        # Risk management checks
        balance = self.db.get_current_balance(self.user_id)
        latest = df.iloc[-1]
        entry_price = latest['close']
        atr_value = latest['ATR']
        
        # Calculate stop loss using the selected strategy
        strategy = self.strategy_manager.strategies[strategy_name]
        df_with_indicators = strategy.calculate_indicators(df)
        
        side = 'buy' if signal == 'BUY' else 'sell'
        stop_loss_price = self.risk_manager.determine_stop_loss(
            entry_price, side, atr_value, df_with_indicators, method='adaptive'
        )
        
        if stop_loss_price is None:
            if show_detailed_logs:
                print(f"   ❌ Could not determine stop loss for {symbol}")
            return
        
        # Calculate position size using strategy allocation
        position_size = self.strategy_manager.calculate_position_size(
            strategy_name, balance, entry_price, stop_loss_price
        )
        
        if position_size <= 0:
            if show_detailed_logs:
                print(f"   ❌ Position size too small for {symbol}")
            return
        
        # Calculate trade details
        take_profit_price = self.risk_manager.calculate_take_profit(
            entry_price, stop_loss_price, side, risk_reward_ratio=2.0
        )
        
        trade_value = position_size * entry_price
        risk_amount = abs(entry_price - stop_loss_price) * position_size
        
        if show_detailed_logs:
            print(f"\n   💼 TRADE EXECUTION PLAN:")
            print(f"      Strategy: {strategy_name.title()}")
            print(f"      Side: {side.upper()}")
            print(f"      Entry: ${entry_price:.4f}")
            print(f"      Stop Loss: ${stop_loss_price:.4f}")
            print(f"      Take Profit: ${take_profit_price:.4f}")
            print(f"      Position Size: {position_size:.6f}")
            print(f"      Trade Value: ${trade_value:.2f}")
            print(f"      Risk Amount: ${risk_amount:.2f}")
        else:
            print(f"🚀 EXECUTING {side.upper()} {symbol}: ${trade_value:.2f} ({strategy_name})")
        
        # Create order in database
        order_id = self.db.create_order(
            self.user_id, symbol, side, position_size, 
            entry_price, strategy_name, strength
        )
        
        # Execute order on exchange
        try:
            order = self.exchange.create_market_order(symbol, side, position_size)
            
            if order:
                # Update order status in database
                self.db.update_order_status(
                    order_id, 'filled', position_size, entry_price, 0.0
                )
                
                # Update balance
                if side == 'buy':
                    self.db.update_balance(self.user_id, 'USDT', -trade_value, f'buy_{symbol}')
                else:
                    self.db.update_balance(self.user_id, 'USDT', trade_value, f'sell_{symbol}')
                
                if show_detailed_logs:
                    print(f"   ✅ TRADE EXECUTED SUCCESSFULLY!")
                    print(f"      Order ID: {order_id}")
                else:
                    print(f"✅ SUCCESS: {side.upper()} {symbol} executed!")
                
                # Log strategy performance
                self.strategy_manager.log_trade_result(
                    strategy_name, symbol, signal, strength, True
                )
                
            else:
                # Update order status as failed
                self.db.update_order_status(order_id, 'failed')
                if show_detailed_logs:
                    print(f"   ❌ TRADE EXECUTION FAILED!")
                else:
                    print(f"❌ FAILED: {side.upper()} {symbol} execution failed!")
                
                # Log strategy performance
                self.strategy_manager.log_trade_result(
                    strategy_name, symbol, signal, strength, False
                )
                
        except Exception as e:
            if show_detailed_logs:
                print(f"   ❌ Trade execution error: {e}")
            else:
                print(f"❌ ERROR: {symbol} execution error: {e}")
            self.db.update_order_status(order_id, 'failed')

    def _show_strategy_performance(self):
        """Show strategy performance statistics"""
        performance = self.strategy_manager.get_strategy_performance()
        
        if performance:
            print(f"\n📈 STRATEGY PERFORMANCE:")
            for strategy_name, stats in performance.items():
                success_rate = stats.get('success_rate', 0)
                total_signals = stats.get('total_signals', 0)
                avg_strength = stats.get('avg_strength', 0)
                
                print(f"   {strategy_name.title()}: {success_rate:.1f}% success ({total_signals} signals, avg strength: {avg_strength:.1f})")

    def get_user_dashboard(self) -> Dict:
        """Get comprehensive user dashboard data"""
        stats = self.db.get_trading_stats(self.user_id)
        portfolio = self.strategy_manager.get_portfolio_status()
        recent_trades = self.db.get_user_trades(self.user_id, limit=10)
        open_orders = self.db.get_user_orders(self.user_id, status='filled', limit=10)
        
        return {
            'user_stats': stats,
            'portfolio': portfolio,
            'recent_trades': recent_trades,
            'open_orders': open_orders,
            'strategy_performance': self.strategy_manager.get_strategy_performance()
        }

def setup_user_account():
    """Setup user account and trading preferences"""
    print("🚀 ENHANCED TRADING BOT SETUP")
    print("="*50)
    
    # Initialize database
    db = initialize_database()
    
    # Get user information
    print("\n👤 USER ACCOUNT SETUP:")
    name = input("Enter your name: ").strip()
    email = input("Enter your email: ").strip()
    
    if not name or not email:
        print("❌ Name and email are required!")
        return None, []
    
    try:
        # Create user account
        user_id = db.create_user(email, name, initial_balance=10000.0)
        print(f"✅ Created user account: {user_id}")
        
    except ValueError as e:
        print(f"❌ {e}")
        # Try to find existing user
        existing_users = list(db.users.find({"email": email}))
        if existing_users:
            user_id = existing_users[0]['user_id']
            print(f"✅ Using existing account: {user_id}")
        else:
            return None, []
    
    # Select trading pairs
    print(f"\n📊 TRADING PAIR SELECTION:")
    strategy_manager = StrategyManager(user_id)
    recommended_pairs = strategy_manager.get_recommended_pairs()
    
    print("Available trading pairs:")
    print("\n🛡️  CONSERVATIVE (Low Risk):")
    for i, pair in enumerate(recommended_pairs['conservative'], 1):
        print(f"   {i}. {pair['symbol']} - {pair['description']}")
    
    print("\n⚡ MOMENTUM (Medium Risk):")
    for i, pair in enumerate(recommended_pairs['momentum'], len(recommended_pairs['conservative']) + 1):
        print(f"   {i}. {pair['symbol']} - {pair['description']}")
    
    print("\n🔥 AGGRESSIVE (High Risk):")
    for i, pair in enumerate(recommended_pairs['aggressive'], len(recommended_pairs['conservative']) + len(recommended_pairs['momentum']) + 1):
        print(f"   {i}. {pair['symbol']} - {pair['description']}")
    
    # Get user selection
    all_pairs = recommended_pairs['all']
    selected_pairs = []
    
    while True:
        try:
            selection = input(f"\nSelect pairs (1-{len(all_pairs)}, comma-separated) or 'done': ").strip()
            
            if selection.lower() == 'done':
                break
            
            indices = [int(x.strip()) - 1 for x in selection.split(',')]
            for idx in indices:
                if 0 <= idx < len(all_pairs):
                    pair_symbol = all_pairs[idx]['symbol']
                    if pair_symbol not in selected_pairs:
                        selected_pairs.append(pair_symbol)
                        print(f"✅ Added {pair_symbol}")
                    else:
                        print(f"⚠️  {pair_symbol} already selected")
                else:
                    print(f"❌ Invalid selection: {idx + 1}")
        
        except ValueError:
            print("❌ Please enter valid numbers separated by commas")
    
    if not selected_pairs:
        print("⚠️  No pairs selected, using default: ETH/USDT")
        selected_pairs = ['ETH/USDT']
    
    print(f"\n✅ Selected pairs: {', '.join(selected_pairs)}")
    
    # Strategy allocation
    print(f"\n⚙️  STRATEGY ALLOCATION:")
    strategies = strategy_manager.get_available_strategies()
    for name, info in strategies.items():
        print(f"   {name.title()}: {info['allocation']:.0%} ({info['description']})")
    
    return user_id, selected_pairs

def main():
    """Main function to run the enhanced trading bot"""
    try:
        # Setup user account and preferences
        user_id, selected_pairs = setup_user_account()
        
        if not user_id:
            print("❌ Failed to setup user account")
            return
        
        # Initialize advanced trading bot
        bot = AdvancedTradingBot(user_id, selected_pairs)
        
        print(f"\n🚀 STARTING ADVANCED TRADING BOT")
        print("="*50)
        print("⚠️  Running in TEST MODE - No real money at risk")
        print(f"📊 Monitoring {len(selected_pairs)} pairs with multiple strategies")
        print("📝 Detailed logs every 30 seconds, quick updates every 10 seconds")
        print("🛑 Press Ctrl+C to stop")
        print("="*50)
        
        # Run initial cycle
        bot.run_trading_cycle()
        
        # Schedule regular cycles (every 10 seconds for quick updates)
        schedule.every(10).seconds.do(bot.run_trading_cycle)
        
        while True:
            schedule.run_pending()
            time.sleep(5)  # Check every 5 seconds for responsiveness
            
    except KeyboardInterrupt:
        print("\n\n🛑 Advanced Trading Bot stopped by user")
        print("👋 Thanks for using the Advanced Trading Bot!")
        
        # Show final dashboard
        if 'bot' in locals():
            dashboard = bot.get_user_dashboard()
            print(f"\n📊 FINAL DASHBOARD:")
            print(f"   Total Trades: {dashboard['user_stats']['total_trades']}")
            print(f"   Win Rate: {dashboard['user_stats']['win_rate']:.1f}%")
            print(f"   Total PnL: ${dashboard['user_stats']['total_pnl']:.2f}")
            print(f"   Current Balance: ${dashboard['user_stats']['current_balance']:.2f}")
        
    except Exception as e:
        print(f"\n❌ Advanced Trading Bot stopped due to error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
