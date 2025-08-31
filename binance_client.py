# binance_client.py

from binance.client import Client
from binance.exceptions import BinanceAPIException
import config

class BinanceClient:
    def __init__(self):
        try:
            # Use testnet if in test mode
            self.client = Client(config.API_KEY, config.API_SECRET, tld='com', testnet=config.TEST_MODE)
            self.client.ping()
            print("Successfully connected to Binance API.")
        except BinanceAPIException as e:
            print(f"Error connecting to Binance API: {e}")
            self.client = None

    def get_klines(self, symbol, interval, limit=100):
        """Fetches historical kline (candlestick) data."""
        if not self.client:
            return None
        try:
            klines = self.client.get_klines(symbol=symbol, interval=interval, limit=limit)
            return klines
        except BinanceAPIException as e:
            print(f"Error fetching klines for {symbol}: {e}")
            return None

    def place_order(self, symbol, side, order_type, quantity):
        """Places an order."""
        if not self.client:
            return None
        try:
            print(f"Attempting to place a {side} order for {quantity} of {symbol}")
            if config.TEST_MODE:
                # Use create_test_order for testnet
                order = self.client.create_test_order(
                    symbol=symbol,
                    side=side,
                    type=order_type,
                    quantity=quantity
                )
                print("Test order placed successfully.")
            else:
                # Use create_order for live trading
                order = self.client.create_order(
                    symbol=symbol,
                    side=side,
                    type=order_type,
                    quantity=quantity
                )
                print("Live order placed successfully.")
            return order
        except BinanceAPIException as e:
            print(f"Error placing order: {e}")
            return None