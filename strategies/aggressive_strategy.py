# aggressive_strategy.py
"""
Aggressive Scalping Strategy

A high-risk, high-reward strategy that looks for quick profits in volatile markets.
Uses shorter timeframes and more sensitive indicators for rapid entries and exits.
"""

import pandas as pd
import pandas_ta as ta
import numpy as np
from .base_strategy import BaseStrategy

class AggressiveStrategy(BaseStrategy):
    """Aggressive scalping strategy for experienced traders"""
    
    def __init__(self):
        super().__init__(
            name="Aggressive Scalping",
            description="High-risk strategy for quick profits in volatile markets",
            risk_level="high"
        )
        
        # Aggressive parameters - more sensitive
        self.rsi_period = 7
        self.rsi_oversold = 35
        self.rsi_overbought = 65
        
        self.ema_fast = 5
        self.ema_slow = 13
        self.sma_trend = 21
        
        self.macd_fast = 5
        self.macd_slow = 13
        self.macd_signal = 5
        
        self.bb_period = 10
        self.bb_std_dev = 1.5
        
        self.stoch_k = 5
        self.stoch_d = 3
        
        self.atr_period = 7
        self.volume_sma = 10
        
        self.min_candles = 30

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate fast-responding indicators"""
        df = df.copy()
        
        # Fast trend indicators
        df['EMA_fast'] = ta.ema(df['close'], length=self.ema_fast)
        df['EMA_slow'] = ta.ema(df['close'], length=self.ema_slow)
        df['SMA_trend'] = ta.sma(df['close'], length=self.sma_trend)
        
        # Fast MACD
        macd_data = ta.macd(df['close'], fast=self.macd_fast, slow=self.macd_slow, signal=self.macd_signal)
        df['MACD'] = macd_data.iloc[:, 0]
        df['MACD_signal'] = macd_data.iloc[:, 1]
        df['MACD_histogram'] = macd_data.iloc[:, 2]
        
        # Fast RSI
        df['RSI'] = ta.rsi(df['close'], length=self.rsi_period)
        
        # Tight Bollinger Bands
        bb_data = ta.bbands(df['close'], length=self.bb_period, std=self.bb_std_dev)
        df['BB_upper'] = bb_data.iloc[:, 0]
        df['BB_middle'] = bb_data.iloc[:, 1]
        df['BB_lower'] = bb_data.iloc[:, 2]
        
        # Fast Stochastic
        stoch_data = ta.stoch(df['high'], df['low'], df['close'], k=self.stoch_k, d=self.stoch_d)
        if stoch_data is not None and len(stoch_data.columns) >= 2:
            df['Stoch_K'] = stoch_data.iloc[:, 0]
            df['Stoch_D'] = stoch_data.iloc[:, 1]
        else:
            df['Stoch_K'] = 50
            df['Stoch_D'] = 50
        
        # Momentum indicators
        df['Price_change'] = df['close'].pct_change(periods=3) * 100
        df['Volume_SMA'] = ta.sma(df['volume'], length=self.volume_sma)
        df['Volume_ratio'] = df['volume'] / df['Volume_SMA']
        
        # ATR with fallback calculation
        try:
            atr_result = ta.atr(df['high'], df['low'], df['close'], length=self.atr_period)
            if atr_result is not None:
                df['ATR'] = atr_result
            else:
                raise ValueError("ATR calculation returned None")
        except:
            # Fallback ATR calculation
            df['ATR'] = (df['high'] - df['low']).rolling(window=self.atr_period).mean()
        
        # Williams %R for additional momentum
        df['Williams_R'] = ta.willr(df['high'], df['low'], df['close'], length=7)
        
        return df

    def generate_signal(self, df: pd.DataFrame) -> str:
        """Generate aggressive trading signals"""
        if not self.validate_data(df):
            return 'HOLD'
        
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Aggressive signal scoring (need 3+ points)
        buy_score = 0
        sell_score = 0
        
        # Fast EMA crossover (2 points)
        if latest['EMA_fast'] > latest['EMA_slow'] and prev['EMA_fast'] <= prev['EMA_slow']:
            buy_score += 2
        elif latest['EMA_fast'] < latest['EMA_slow'] and prev['EMA_fast'] >= prev['EMA_slow']:
            sell_score += 2
        
        # RSI momentum (2 points)
        if latest['RSI'] < self.rsi_oversold and latest['RSI'] > prev['RSI']:
            buy_score += 2
        elif latest['RSI'] > self.rsi_overbought and latest['RSI'] < prev['RSI']:
            sell_score += 2
        
        # MACD momentum (1 point)
        if latest['MACD_histogram'] > prev['MACD_histogram'] and latest['MACD_histogram'] > 0:
            buy_score += 1
        elif latest['MACD_histogram'] < prev['MACD_histogram'] and latest['MACD_histogram'] < 0:
            sell_score += 1
        
        # Stochastic crossover (1 point)
        if (latest['Stoch_K'] > latest['Stoch_D'] and prev['Stoch_K'] <= prev['Stoch_D'] and
            latest['Stoch_K'] < 50):
            buy_score += 1
        elif (latest['Stoch_K'] < latest['Stoch_D'] and prev['Stoch_K'] >= prev['Stoch_D'] and
              latest['Stoch_K'] > 50):
            sell_score += 1
        
        # Price momentum (1 point)
        if latest['Price_change'] > 0.5:
            buy_score += 1
        elif latest['Price_change'] < -0.5:
            sell_score += 1
        
        # Volume spike (1 point)
        if latest['Volume_ratio'] > 1.5:
            if buy_score > sell_score:
                buy_score += 1
            elif sell_score > buy_score:
                sell_score += 1
        
        # Williams %R confirmation (1 point)
        if latest['Williams_R'] > -20:  # Overbought
            sell_score += 1
        elif latest['Williams_R'] < -80:  # Oversold
            buy_score += 1
        
        # Aggressive threshold: need 3+ points
        if buy_score >= 3 and buy_score > sell_score:
            return 'BUY'
        elif sell_score >= 3 and sell_score > buy_score:
            return 'SELL'
        else:
            return 'HOLD'

    def get_signal_strength(self, df: pd.DataFrame) -> int:
        """Get signal strength (0-10)"""
        if not self.validate_data(df):
            return 0
        
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        strength = 0
        
        # Momentum strength
        if abs(latest['Price_change']) > 1.0:
            strength += 3
        
        # RSI momentum
        if (latest['RSI'] < self.rsi_oversold or latest['RSI'] > self.rsi_overbought):
            strength += 2
        
        # MACD strength
        if abs(latest['MACD_histogram']) > abs(prev['MACD_histogram']):
            strength += 2
        
        # Volume confirmation
        if latest['Volume_ratio'] > 1.5:
            strength += 2
        
        # Volatility (good for scalping)
        atr_avg = df['ATR'].rolling(10).mean().iloc[-1]
        if latest['ATR'] > atr_avg * 1.2:
            strength += 1
        
        return min(10, strength)
