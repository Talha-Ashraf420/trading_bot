# exchange_handler.py
import ccxt
import pandas as pd
from config import EXCHANGE_CONFIG

class ExchangeHandler:
    def __init__(self):
        try:
            print('------------>>>',EXCHANGE_CONFIG['apiKey'])
            exchange_class = getattr(ccxt, EXCHANGE_CONFIG['id'])
            self.exchange = exchange_class({
                'apiKey': EXCHANGE_CONFIG['apiKey'],
                'secret': EXCHANGE_CONFIG['secret'],
                'options': EXCHANGE_CONFIG.get('options', {}),
            })
            self.exchange.set_sandbox_mode(True)
            self.exchange.load_markets()
            print(f"Successfully connected to {self.exchange.id}")
        except Exception as e:
            print(f"Error connecting to exchange: {e}")
            raise

    def fetch_ohlcv(self, symbol, timeframe, limit=100):
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            return df
        except Exception as e:
            print(f"Error fetching OHLCV data for {symbol}: {e}")
            return pd.DataFrame()

    def get_balance(self, currency='USDT'):
        try:
            balance = self.exchange.fetch_balance()
            return balance['free'][currency]
        except Exception as e:
            print(f"Error fetching balance for {currency}: {e}")
            return 0

    def create_market_order(self, symbol, side, amount):
        try:
            print(f"Placing market {side} order for {amount} of {symbol}")
            order = self.exchange.create_market_order(symbol, side, amount)
            return order
        except Exception as e:
            print(f"Error placing market order: {e}")
            return None