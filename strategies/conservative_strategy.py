# conservative_strategy.py
"""
Conservative Multi-Indicator Strategy

A low-risk strategy that focuses on strong trend confirmation and conservative entries.
Based on proven indicators with strict filtering to minimize losses.
"""

import pandas as pd
import pandas_ta as ta
import numpy as np
from .base_strategy import BaseStrategy

class ConservativeStrategy(BaseStrategy):
    """Conservative strategy with strict entry conditions"""
    
    def __init__(self):
        super().__init__(
            name="Conservative Multi-Indicator",
            description="Low-risk strategy with strict trend confirmation and conservative entries",
            risk_level="low"
        )
        
        # Conservative parameters
        self.rsi_period = 21
        self.rsi_oversold = 25
        self.rsi_overbought = 75
        
        self.ema_fast = 21
        self.ema_slow = 50
        self.sma_trend = 100
        
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        
        self.bb_period = 20
        self.bb_std_dev = 2.5
        
        self.adx_period = 14
        self.adx_threshold = 30  # Higher threshold for stronger trends
        
        self.atr_period = 14
        self.volume_sma = 20
        
        self.min_candles = 100

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators"""
        df = df.copy()
        
        # Trend indicators
        df['EMA_fast'] = ta.ema(df['close'], length=self.ema_fast)
        df['EMA_slow'] = ta.ema(df['close'], length=self.ema_slow)
        df['SMA_trend'] = ta.sma(df['close'], length=self.sma_trend)
        
        # MACD
        macd_data = ta.macd(df['close'], fast=self.macd_fast, slow=self.macd_slow, signal=self.macd_signal)
        df['MACD'] = macd_data.iloc[:, 0]
        df['MACD_signal'] = macd_data.iloc[:, 1]
        df['MACD_histogram'] = macd_data.iloc[:, 2]
        
        # RSI
        df['RSI'] = ta.rsi(df['close'], length=self.rsi_period)
        
        # Bollinger Bands
        bb_data = ta.bbands(df['close'], length=self.bb_period, std=self.bb_std_dev)
        df['BB_upper'] = bb_data.iloc[:, 0]
        df['BB_middle'] = bb_data.iloc[:, 1]
        df['BB_lower'] = bb_data.iloc[:, 2]
        
        # ADX for trend strength
        adx_data = ta.adx(df['high'], df['low'], df['close'], length=self.adx_period)
        if adx_data is not None and len(adx_data.columns) >= 3:
            df['DI_plus'] = adx_data.iloc[:, 0]
            df['DI_minus'] = adx_data.iloc[:, 1]
            df['ADX'] = adx_data.iloc[:, 2]
        else:
            df['ADX'] = 25
            df['DI_plus'] = 50
            df['DI_minus'] = 50
        
        # Volume and volatility
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
        
        return df

    def generate_signal(self, df: pd.DataFrame) -> str:
        """Generate conservative trading signals"""
        if not self.validate_data(df):
            return 'HOLD'
        
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Conservative signal scoring (need 6+ points)
        buy_score = 0
        sell_score = 0
        
        # Strong trend requirement (ADX > 30)
        if latest['ADX'] < self.adx_threshold:
            return 'HOLD'  # No trading in weak trends
        
        # Trend alignment (3 points)
        if (latest['EMA_fast'] > latest['EMA_slow'] > latest['SMA_trend'] and
            latest['close'] > latest['SMA_trend']):
            buy_score += 3
        elif (latest['EMA_fast'] < latest['EMA_slow'] < latest['SMA_trend'] and
              latest['close'] < latest['SMA_trend']):
            sell_score += 3
        
        # RSI confirmation (2 points)
        if latest['RSI'] < self.rsi_oversold:
            buy_score += 2
        elif latest['RSI'] > self.rsi_overbought:
            sell_score += 2
        
        # MACD confirmation (2 points)
        if (latest['MACD'] > latest['MACD_signal'] and 
            prev['MACD'] <= prev['MACD_signal']):
            buy_score += 2
        elif (latest['MACD'] < latest['MACD_signal'] and 
              prev['MACD'] >= prev['MACD_signal']):
            sell_score += 2
        
        # Bollinger Bands position (1 point)
        if latest['close'] < latest['BB_lower']:
            buy_score += 1
        elif latest['close'] > latest['BB_upper']:
            sell_score += 1
        
        # Volume confirmation (1 point)
        if latest['Volume_ratio'] > 1.2:
            if buy_score > sell_score:
                buy_score += 1
            elif sell_score > buy_score:
                sell_score += 1
        
        # Conservative threshold: need 6+ points
        if buy_score >= 6 and buy_score > sell_score:
            return 'BUY'
        elif sell_score >= 6 and sell_score > buy_score:
            return 'SELL'
        else:
            return 'HOLD'

    def get_signal_strength(self, df: pd.DataFrame) -> int:
        """Get signal strength (0-10)"""
        if not self.validate_data(df):
            return 0
        
        latest = df.iloc[-1]
        strength = 0
        
        # ADX strength
        if latest['ADX'] > self.adx_threshold:
            strength += 3
        
        # Trend alignment
        if (latest['EMA_fast'] > latest['EMA_slow'] > latest['SMA_trend'] or
            latest['EMA_fast'] < latest['EMA_slow'] < latest['SMA_trend']):
            strength += 3
        
        # RSI extremes
        if latest['RSI'] < self.rsi_oversold or latest['RSI'] > self.rsi_overbought:
            strength += 2
        
        # Volume confirmation
        if latest['Volume_ratio'] > 1.2:
            strength += 2
        
        return min(10, strength)
