# backtest.py

import pandas as pd
from binance_client import BinanceClient
from strategy import bbands_entry_strategy # Updated import
import itertools

# --- Data Loading Function (no changes) ---
def get_historical_data(symbol='BTCUSDT', interval='4h', limit=2500):
    # ... (code is identical to before)
    client = BinanceClient()
    klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
    if not klines: return None
    klines_df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
    for col in ['open', 'high', 'low', 'close', 'volume']: klines_df[col] = pd.to_numeric(klines_df[col])
    return klines_df

# --- Simulation Engine with DYNAMIC EXITS ---
def run_simulation(klines_df, params):
    balance = 1000.0
    in_position = False
    buy_price = 0.0
    
    bbands_len, bbands_std, sl_pct = params

    # Pre-calculate indicators for the whole dataset once
    klines_df.ta.bbands(length=bbands_len, std=bbands_std, append=True)
    middle_band_col = f'BBM_{bbands_len}_{bbands_std}'

    for i in range(len(klines_df)):
        if i < bbands_len: continue
        
        current_price = klines_df['close'].iloc[i]
        
        if in_position:
            stop_loss_price = buy_price * (1 - sl_pct / 100)
            # DYNAMIC take profit target is the middle band
            take_profit_price = klines_df[middle_band_col].iloc[i]
            
            # Check for exit conditions
            if current_price <= stop_loss_price or current_price >= take_profit_price:
                balance *= (current_price / buy_price)
                in_position = False
        else:
            # Check for entry conditions
            historical_window = klines_df.iloc[:i+1] # Pass a view for the strategy function
            signal = bbands_entry_strategy(historical_window.copy(), bbands_length=bbands_len, bbands_std=bbands_std)
            if signal == 'BUY':
                in_position = True
                buy_price = current_price
                
    return balance

# --- Main Optimizer Function ---
def run_optimizer():
    print("Fetching historical data...")
    klines_df = get_historical_data()
    if klines_df is None: return

    split_index = int(len(klines_df) * 0.8)
    training_df, testing_df = klines_df.iloc[:split_index], klines_df.iloc[split_index:]
    print(f"Data split into {len(training_df)} training points and {len(testing_df)} testing points.")

    # --- Define Parameter Ranges (Take Profit % is removed) ---
    bbands_len_range = range(20, 41, 10)  # Test 20, 30, 40
    bbands_std_range = [2.0, 2.5]         # Test 2.0, 2.5 standard deviations
    sl_pct_range = [2.0, 3.0, 4.0]        # Test 2%, 3%, 4% stop loss
    
    param_combinations = list(itertools.product(bbands_len_range, bbands_std_range, sl_pct_range))
    print(f"\n--- Running Optimization on Training Data ({len(param_combinations)} sets) ---")

    best_params, best_balance = None, 0
    for params in param_combinations:
        final_balance = run_simulation(training_df.copy(), params)
        if final_balance > best_balance:
            best_balance, best_params = final_balance, params

    print("\n--- Optimization Finished ---")
    profit, profit_pct = best_balance - 1000, (best_balance - 1000) / 10
    print(f"Best Parameters Found: {best_params} (Length, Std Dev, SL %)")
    print(f"Training Set Performance: Final Balance = ${best_balance:.2f} ({profit_pct:.2f}%)")

    if not best_params: return
    print("\n--- Running Validation on Testing Data ---")
    testing_balance = run_simulation(testing_df.copy(), best_params)
    test_profit, test_profit_pct = testing_balance - 1000, (testing_balance - 1000) / 10
    
    print("\n--- FINAL REPORT ---")
    print(f"Optimized Parameters: {best_params}")
    print(f"Performance on Training Data (Seen): {profit_pct:.2f}%")
    print(f"Performance on Testing Data (Unseen): {test_profit_pct:.2f}%")

    if test_profit_pct > 0: print("\n✅ Strategy appears robust!")
    else: print("\n⚠️ Warning! Strategy was not profitable on unseen testing data.")

if __name__ == "__main__":
    run_optimizer()