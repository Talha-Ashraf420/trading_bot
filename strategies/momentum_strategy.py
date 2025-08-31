# momentum_strategy.py
"""
Momentum Breakout Strategy

A medium-risk strategy that focuses on catching strong momentum moves and breakouts.
Combines trend-following with momentum indicators for balanced risk-reward.
"""

import pandas as pd
import pandas_ta as ta
import numpy as np
from .base_strategy import BaseStrategy

class MomentumStrategy(BaseStrategy):
    """Momentum breakout strategy for trending markets"""
    
    def __init__(self):
        super().__init__(
            name="Momentum Breakout",
            description="Medium-risk strategy focusing on momentum and breakouts",
            risk_level="medium"
        )
        
        # Momentum parameters
        self.rsi_period = 14
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        
        self.ema_fast = 8
        self.ema_slow = 21
        self.sma_trend = 50
        
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        
        self.bb_period = 20
        self.bb_std_dev = 2
        
        self.atr_period = 14
        self.volume_sma = 20
        
        # Momentum specific
        self.momentum_period = 10
        self.breakout_period = 20
        
        self.min_candles = 50

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate momentum and breakout indicators"""
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
        df['BB_width'] = (df['BB_upper'] - df['BB_lower']) / df['BB_middle']
        
        # Momentum indicators
        df['Momentum'] = ta.mom(df['close'], length=self.momentum_period)
        df['ROC'] = ta.roc(df['close'], length=self.momentum_period)  # Rate of Change
        
        # Breakout levels
        df['Resistance'] = df['high'].rolling(window=self.breakout_period).max()
        df['Support'] = df['low'].rolling(window=self.breakout_period).min()
        
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
        
        # Average True Range Percent
        df['ATR_percent'] = (df['ATR'] / df['close']) * 100
        
        # Commodity Channel Index for momentum
        df['CCI'] = ta.cci(df['high'], df['low'], df['close'], length=14)
        
        return df

    def generate_signal(self, df: pd.DataFrame) -> str:
        """Generate momentum-based trading signals"""
        if not self.validate_data(df):
            return 'HOLD'
        
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Momentum signal scoring (need 4+ points)
        buy_score = 0
        sell_score = 0
        
        # Breakout detection (3 points)
        if latest['close'] > latest['Resistance'] and latest['volume'] > latest['Volume_SMA'] * 1.5:
            buy_score += 3
        elif latest['close'] < latest['Support'] and latest['volume'] > latest['Volume_SMA'] * 1.5:
            sell_score += 3
        
        # Momentum confirmation (2 points)
        if latest['Momentum'] > 0 and latest['ROC'] > 2:
            buy_score += 2
        elif latest['Momentum'] < 0 and latest['ROC'] < -2:
            sell_score += 2
        
        # EMA trend (2 points)
        if latest['EMA_fast'] > latest['EMA_slow'] and latest['close'] > latest['SMA_trend']:
            buy_score += 2
        elif latest['EMA_fast'] < latest['EMA_slow'] and latest['close'] < latest['SMA_trend']:
            sell_score += 2
        
        # MACD momentum (1 point)
        if latest['MACD'] > latest['MACD_signal'] and latest['MACD_histogram'] > prev['MACD_histogram']:
            buy_score += 1
        elif latest['MACD'] < latest['MACD_signal'] and latest['MACD_histogram'] < prev['MACD_histogram']:
            sell_score += 1
        
        # RSI momentum (1 point)
        if 40 < latest['RSI'] < 60 and latest['RSI'] > prev['RSI']:  # Building momentum
            buy_score += 1
        elif 40 < latest['RSI'] < 60 and latest['RSI'] < prev['RSI']:
            sell_score += 1
        
        # CCI momentum (1 point)
        if latest['CCI'] > 100:  # Strong upward momentum
            buy_score += 1
        elif latest['CCI'] < -100:  # Strong downward momentum
            sell_score += 1
        
        # Bollinger Band expansion (1 point) - good for momentum
        bb_width_avg = df['BB_width'].rolling(10).mean().iloc[-1]
        if latest['BB_width'] > bb_width_avg * 1.2:
            if buy_score > sell_score:
                buy_score += 1
            elif sell_score > buy_score:
                sell_score += 1
        
        # Momentum threshold: need 4+ points
        if buy_score >= 4 and buy_score > sell_score:
            return 'BUY'
        elif sell_score >= 4 and sell_score > buy_score:
            return 'SELL'
        else:
            return 'HOLD'

    def get_signal_strength(self, df: pd.DataFrame) -> int:
        """Get signal strength (0-10)"""
        if not self.validate_data(df):
            return 0
        
        latest = df.iloc[-1]
        strength = 0
        
        # Momentum strength
        if abs(latest['ROC']) > 3:
            strength += 3
        
        # Breakout strength
        if (latest['close'] > latest['Resistance'] or latest['close'] < latest['Support']):
            strength += 3
        
        # Volume confirmation
        if latest['Volume_ratio'] > 1.5:
            strength += 2
        
        # Trend alignment
        if ((latest['EMA_fast'] > latest['EMA_slow'] > latest['SMA_trend']) or
            (latest['EMA_fast'] < latest['EMA_slow'] < latest['SMA_trend'])):
            strength += 2
        
        return min(10, strength)
