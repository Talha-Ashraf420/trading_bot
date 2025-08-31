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
        print("\n" + "="*50)
        print(f" Running new trade cycle...")

        if self.in_position:
            print("Already in a position. Skipping this cycle.")
            # In a real bot, you would check exit conditions here.
            # For simplicity, this example only handles entries.
            return

        # 1. Fetch Data
        df = self.exchange.fetch_ohlcv(TRADING_CONFIG['symbol'], TRADING_CONFIG['timeframe'])
        if df.empty:
            print("Could not fetch data. Skipping cycle.")
            return

        # 2. Calculate Indicators
        df = self.strategy.calculate_indicators(df)

        # 3. Generate Signal
        signal = self.strategy.generate_signal(df)
        print(f"Signal for {TRADING_CONFIG['symbol']}: {signal}")

        if signal == 'HOLD':
            return

        # 4. Get signal strength and market conditions
        signal_strength = self.strategy.get_signal_strength(df)
        latest = df.iloc[-1]
        volatility_factor = latest['ATR'] / df['ATR'].rolling(20).mean().iloc[-1] if len(df) >= 20 else 1.0
        portfolio_metrics = self.risk_manager.get_portfolio_metrics()
        
        print(f"Signal Strength: {signal_strength}/10")
        print(f"Volatility Factor: {volatility_factor:.2f}")
        print(f"Portfolio Risk: {portfolio_metrics['total_portfolio_risk']:.2%}")
        
        # 5. Risk Management - Check if trade should be taken
        should_trade, reason = self.risk_manager.should_take_trade(
            signal_strength, volatility_factor, portfolio_metrics['total_portfolio_risk']
        )
        
        if not should_trade:
            print(f"Trade rejected: {reason}")
            return
        
        # 6. Calculate position details
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
        
        print(f"Account Balance: {balance:.2f} USDT")
        print(f"Entry Price: {entry_price:.2f}")
        print(f"Stop Loss: {stop_loss_price:.2f}")
        print(f"Take Profit: {take_profit_price:.2f}")
        print(f"Calculated Position Size: {position_size:.6f}")

        if position_size <= 0:
            print("Position size is zero or negative. No trade will be placed.")
            return

        # 7. Execute Order
        order = self.exchange.create_market_order(TRADING_CONFIG['symbol'], side, position_size)
        
        if order:
            print("Trade executed successfully.")
            self.in_position = True
            # In a real bot, you would store order details and monitor for exit.
        else:
            print("Trade execution failed.")

def job():
    bot = TradingBot()
    bot.run_trade_cycle()

if __name__ == '__main__':
    # Run the job immediately and then every 5 minutes
    job() 
    schedule.every(5).minutes.do(job)

    while True:
        schedule.run_pending()
        time.sleep(1)