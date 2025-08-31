# strategy.py
import pandas as pd
import pandas_ta as ta
import numpy as np
from config import STRATEGY_CONFIG

class AdvancedMultiIndicatorStrategy:
    """
    Advanced Multi-Indicator Trading Strategy
    
    This strategy combines multiple technical indicators to generate high-probability
    trading signals. It uses trend-following, momentum, and volatility indicators
    to create a comprehensive trading system.
    """
    
    def __init__(self):
        # RSI Parameters
        self.rsi_period = STRATEGY_CONFIG.get('rsi_period', 14)
        self.rsi_oversold = STRATEGY_CONFIG.get('rsi_oversold', 30)
        self.rsi_overbought = STRATEGY_CONFIG.get('rsi_overbought', 70)
        
        # Bollinger Bands Parameters
        self.bb_period = STRATEGY_CONFIG.get('bb_period', 20)
        self.bb_std_dev = STRATEGY_CONFIG.get('bb_std_dev', 2)
        
        # Moving Average Parameters
        self.ema_fast = STRATEGY_CONFIG.get('ema_fast', 12)
        self.ema_slow = STRATEGY_CONFIG.get('ema_slow', 26)
        self.sma_trend = STRATEGY_CONFIG.get('sma_trend', 50)
        
        # MACD Parameters
        self.macd_fast = STRATEGY_CONFIG.get('macd_fast', 12)
        self.macd_slow = STRATEGY_CONFIG.get('macd_slow', 26)
        self.macd_signal = STRATEGY_CONFIG.get('macd_signal', 9)
        
        # Stochastic Parameters
        self.stoch_k = STRATEGY_CONFIG.get('stoch_k', 14)
        self.stoch_d = STRATEGY_CONFIG.get('stoch_d', 3)
        self.stoch_oversold = STRATEGY_CONFIG.get('stoch_oversold', 20)
        self.stoch_overbought = STRATEGY_CONFIG.get('stoch_overbought', 80)
        
        # Volume Parameters
        self.volume_sma = STRATEGY_CONFIG.get('volume_sma', 20)
        
        # ATR for volatility
        self.atr_period = STRATEGY_CONFIG.get('atr_period', 14)
        
        # ADX for trend strength
        self.adx_period = STRATEGY_CONFIG.get('adx_period', 14)
        self.adx_threshold = STRATEGY_CONFIG.get('adx_threshold', 25)

    def calculate_indicators(self, df):
        """Calculate all technical indicators"""
        df = df.copy()
        
        # Trend Indicators
        df['EMA_fast'] = ta.ema(df['close'], length=self.ema_fast)
        df['EMA_slow'] = ta.ema(df['close'], length=self.ema_slow)
        df['SMA_trend'] = ta.sma(df['close'], length=self.sma_trend)
        
        # MACD
        macd_data = ta.macd(df['close'], fast=self.macd_fast, slow=self.macd_slow, signal=self.macd_signal)
        df['MACD'] = macd_data[f'MACD_{self.macd_fast}_{self.macd_slow}_{self.macd_signal}']
        df['MACD_signal'] = macd_data[f'MACDs_{self.macd_fast}_{self.macd_slow}_{self.macd_signal}']
        df['MACD_histogram'] = macd_data[f'MACDh_{self.macd_fast}_{self.macd_slow}_{self.macd_signal}']
        
        # RSI
        df['RSI'] = ta.rsi(df['close'], length=self.rsi_period)
        
        # Bollinger Bands
        bb_data = ta.bbands(df['close'], length=self.bb_period, std=self.bb_std_dev)
        # Handle different pandas_ta versions
        bb_cols = bb_data.columns
        df['BB_upper'] = bb_data.iloc[:, 0]  # Upper band
        df['BB_middle'] = bb_data.iloc[:, 1]  # Middle band (SMA)
        df['BB_lower'] = bb_data.iloc[:, 2]  # Lower band
        df['BB_width'] = (df['BB_upper'] - df['BB_lower']) / df['BB_middle']
        df['BB_position'] = (df['close'] - df['BB_lower']) / (df['BB_upper'] - df['BB_lower'])
        
        # Stochastic Oscillator
        stoch_data = ta.stoch(df['high'], df['low'], df['close'], k=self.stoch_k, d=self.stoch_d)
        # Handle different pandas_ta versions
        if stoch_data is not None and len(stoch_data.columns) >= 2:
            df['Stoch_K'] = stoch_data.iloc[:, 0]  # %K
            df['Stoch_D'] = stoch_data.iloc[:, 1]  # %D
        else:
            # Fallback calculation
            df['Stoch_K'] = ta.stoch(df['high'], df['low'], df['close'], k=self.stoch_k)
            df['Stoch_D'] = df['Stoch_K'].rolling(window=self.stoch_d).mean()
        
        # Volume indicators
        df['Volume_SMA'] = ta.sma(df['volume'], length=self.volume_sma)
        df['Volume_ratio'] = df['volume'] / df['Volume_SMA']
        
        # Volatility
        df['ATR'] = ta.atr(df['high'], df['low'], df['close'], length=self.atr_period)
        
        # Trend Strength (ADX)
        adx_data = ta.adx(df['high'], df['low'], df['close'], length=self.adx_period)
        # Handle different pandas_ta versions
        if adx_data is not None and len(adx_data.columns) >= 3:
            df['DI_plus'] = adx_data.iloc[:, 0]   # DI+
            df['DI_minus'] = adx_data.iloc[:, 1]  # DI-
            df['ADX'] = adx_data.iloc[:, 2]       # ADX
        else:
            # Fallback - use simple calculation
            df['ADX'] = ta.adx(df['high'], df['low'], df['close'], length=self.adx_period)
            df['DI_plus'] = 50  # Default neutral values
            df['DI_minus'] = 50
        
        # Support and Resistance levels
        df['Resistance'] = df['high'].rolling(window=20).max()
        df['Support'] = df['low'].rolling(window=20).min()
        
        # Price momentum
        df['Price_momentum'] = df['close'].pct_change(periods=5)
        
        return df

    def analyze_trend(self, df):
        """Analyze overall market trend"""
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        trend_signals = []
        
        # EMA Trend
        if latest['EMA_fast'] > latest['EMA_slow']:
            trend_signals.append('bullish')
        else:
            trend_signals.append('bearish')
            
        # Price vs SMA
        if latest['close'] > latest['SMA_trend']:
            trend_signals.append('bullish')
        else:
            trend_signals.append('bearish')
            
        # ADX Trend Strength
        if latest['ADX'] > self.adx_threshold:
            if latest['DI_plus'] > latest['DI_minus']:
                trend_signals.append('strong_bullish')
            else:
                trend_signals.append('strong_bearish')
        
        bullish_count = sum(1 for signal in trend_signals if 'bullish' in signal)
        bearish_count = len(trend_signals) - bullish_count
        
        if bullish_count > bearish_count:
            return 'bullish'
        elif bearish_count > bullish_count:
            return 'bearish'
        else:
            return 'neutral'

    def check_momentum_signals(self, df):
        """Check momentum-based signals"""
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        signals = {
            'rsi_oversold': latest['RSI'] < self.rsi_oversold,
            'rsi_overbought': latest['RSI'] > self.rsi_overbought,
            'rsi_bullish_divergence': latest['RSI'] > prev['RSI'] and latest['close'] < prev['close'],
            'rsi_bearish_divergence': latest['RSI'] < prev['RSI'] and latest['close'] > prev['close'],
            'macd_bullish_crossover': latest['MACD'] > latest['MACD_signal'] and prev['MACD'] <= prev['MACD_signal'],
            'macd_bearish_crossover': latest['MACD'] < latest['MACD_signal'] and prev['MACD'] >= prev['MACD_signal'],
            'macd_histogram_increasing': latest['MACD_histogram'] > prev['MACD_histogram'],
            'stoch_oversold': latest['Stoch_K'] < self.stoch_oversold and latest['Stoch_D'] < self.stoch_oversold,
            'stoch_overbought': latest['Stoch_K'] > self.stoch_overbought and latest['Stoch_D'] > self.stoch_overbought,
            'stoch_bullish_crossover': latest['Stoch_K'] > latest['Stoch_D'] and prev['Stoch_K'] <= prev['Stoch_D'],
            'stoch_bearish_crossover': latest['Stoch_K'] < latest['Stoch_D'] and prev['Stoch_K'] >= prev['Stoch_D']
        }
        
        return signals

    def check_volatility_signals(self, df):
        """Check volatility and volume signals"""
        latest = df.iloc[-1]
        
        # Calculate rolling means safely
        bb_width_mean = df['BB_width'].rolling(20).mean().iloc[-1] if len(df) >= 20 else latest['BB_width']
        atr_mean = df['ATR'].rolling(20).mean().iloc[-1] if len(df) >= 20 else latest['ATR']
        
        signals = {
            'bb_squeeze': latest['BB_width'] < bb_width_mean * 0.8,
            'bb_expansion': latest['BB_width'] > bb_width_mean * 1.2,
            'price_near_bb_lower': latest['BB_position'] < 0.2,
            'price_near_bb_upper': latest['BB_position'] > 0.8,
            'high_volume': latest['Volume_ratio'] > 1.5,
            'low_volume': latest['Volume_ratio'] < 0.7,
            'high_volatility': latest['ATR'] > atr_mean * 1.2
        }
        
        return signals

    def generate_signal(self, df):
        """Generate trading signal based on multiple indicators"""
        if len(df) < max(self.ema_slow, self.sma_trend, self.bb_period, self.adx_period):
            return 'HOLD'
        
        trend = self.analyze_trend(df)
        momentum_signals = self.check_momentum_signals(df)
        volatility_signals = self.check_volatility_signals(df)
        
        latest = df.iloc[-1]
        
        # Calculate signal strength
        buy_score = 0
        sell_score = 0
        
        # Trend-based scoring
        if trend == 'bullish':
            buy_score += 2
        elif trend == 'bearish':
            sell_score += 2
        
        # Momentum-based scoring
        if momentum_signals['rsi_oversold'] and not momentum_signals['rsi_overbought']:
            buy_score += 2
        if momentum_signals['rsi_overbought'] and not momentum_signals['rsi_oversold']:
            sell_score += 2
            
        if momentum_signals['macd_bullish_crossover']:
            buy_score += 2
        if momentum_signals['macd_bearish_crossover']:
            sell_score += 2
            
        if momentum_signals['stoch_oversold'] and momentum_signals['stoch_bullish_crossover']:
            buy_score += 2
        if momentum_signals['stoch_overbought'] and momentum_signals['stoch_bearish_crossover']:
            sell_score += 2
        
        # Volatility-based scoring
        if volatility_signals['price_near_bb_lower'] and volatility_signals['bb_squeeze']:
            buy_score += 1
        if volatility_signals['price_near_bb_upper'] and volatility_signals['bb_squeeze']:
            sell_score += 1
            
        if volatility_signals['high_volume']:
            if buy_score > sell_score:
                buy_score += 1
            elif sell_score > buy_score:
                sell_score += 1
        
        # Additional confirmation signals
        if latest['close'] > latest['EMA_fast'] > latest['EMA_slow']:
            buy_score += 1
        if latest['close'] < latest['EMA_fast'] < latest['EMA_slow']:
            sell_score += 1
        
        # Risk management filters
        if volatility_signals['high_volatility'] and latest['ADX'] < self.adx_threshold:
            # High volatility with weak trend - reduce signal strength
            buy_score = max(0, buy_score - 2)
            sell_score = max(0, sell_score - 2)
        
        # Generate final signal
        signal_threshold = 4  # Minimum score needed for a signal
        
        if buy_score >= signal_threshold and buy_score > sell_score:
            return 'BUY'
        elif sell_score >= signal_threshold and sell_score > buy_score:
            return 'SELL'
        else:
            return 'HOLD'
    
    def get_signal_strength(self, df):
        """Get the strength of the current signal (0-10)"""
        if len(df) < max(self.ema_slow, self.sma_trend, self.bb_period, self.adx_period):
            return 0
        
        trend = self.analyze_trend(df)
        momentum_signals = self.check_momentum_signals(df)
        volatility_signals = self.check_volatility_signals(df)
        
        strength = 0
        
        # Trend strength
        if trend in ['bullish', 'bearish']:
            strength += 3
        
        # Momentum alignment
        momentum_count = sum([
            momentum_signals['macd_bullish_crossover'] or momentum_signals['macd_bearish_crossover'],
            momentum_signals['rsi_oversold'] or momentum_signals['rsi_overbought'],
            momentum_signals['stoch_bullish_crossover'] or momentum_signals['stoch_bearish_crossover']
        ])
        strength += momentum_count * 2
        
        # Volume confirmation
        if volatility_signals['high_volume']:
            strength += 2
        
        return min(10, strength)

# Maintain backward compatibility
TradingStrategy = AdvancedMultiIndicatorStrategy