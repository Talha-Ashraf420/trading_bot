import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
import warnings
warnings.filterwarnings('ignore')

class TechnicalIndicators:
    """
    Simplified technical indicators calculator without pandas-ta dependency
    Implements core indicators manually for better compatibility
    """
    
    def __init__(self):
        self.indicators = {}
    
    def calculate_all_indicators(self, df: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate all technical indicators for given OHLCV data"""
        
        # Ensure we have enough data
        if len(df) < 50:
            return {}
        
        indicators = {}
        
        # Price-based indicators
        indicators.update(self._calculate_price_indicators(df))
        
        # Trend indicators
        indicators.update(self._calculate_trend_indicators(df, config))
        
        # Momentum indicators
        indicators.update(self._calculate_momentum_indicators(df, config))
        
        # Volatility indicators
        indicators.update(self._calculate_volatility_indicators(df, config))
        
        # Volume indicators
        indicators.update(self._calculate_volume_indicators(df, config))
        
        # Support/Resistance indicators
        indicators.update(self._calculate_support_resistance(df))
        
        # Convert all numpy types to Python native types for MongoDB compatibility
        return self._convert_numpy_types(indicators)
    
    def _calculate_price_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Basic price indicators"""
        current_price = float(df['close'].iloc[-1])
        
        return {
            'current_price': current_price,
            'price_change_1h': float(((current_price - df['close'].iloc[-2]) / df['close'].iloc[-2]) * 100) if len(df) > 1 else 0,
            'price_change_24h': float(((current_price - df['close'].iloc[-24]) / df['close'].iloc[-24]) * 100) if len(df) > 24 else 0,
            'high_24h': float(df['high'].tail(24).max()) if len(df) > 24 else current_price,
            'low_24h': float(df['low'].tail(24).min()) if len(df) > 24 else current_price,
        }
    
    def _calculate_trend_indicators(self, df: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
        """Trend-following indicators"""
        indicators = {}
        
        # Simple Moving Averages
        sma_20 = df['close'].rolling(window=20).mean()
        sma_50 = df['close'].rolling(window=50).mean()
        
        if not sma_20.empty and not pd.isna(sma_20.iloc[-1]):
            indicators['sma_20'] = float(sma_20.iloc[-1])
            indicators['price_above_sma20'] = df['close'].iloc[-1] > sma_20.iloc[-1]
        
        if not sma_50.empty and not pd.isna(sma_50.iloc[-1]):
            indicators['sma_50'] = float(sma_50.iloc[-1])
            indicators['sma_trend'] = sma_20.iloc[-1] > sma_50.iloc[-1] if not pd.isna(sma_20.iloc[-1]) else False
        
        # Exponential Moving Averages
        ema_12 = df['close'].ewm(span=config.get('ema_fast', 12)).mean()
        ema_26 = df['close'].ewm(span=config.get('ema_slow', 26)).mean()
        
        if not ema_12.empty and not pd.isna(ema_12.iloc[-1]):
            indicators['ema_12'] = float(ema_12.iloc[-1])
        
        if not ema_26.empty and not pd.isna(ema_26.iloc[-1]):
            indicators['ema_26'] = float(ema_26.iloc[-1])
            indicators['ema_crossover'] = ema_12.iloc[-1] > ema_26.iloc[-1] if not pd.isna(ema_12.iloc[-1]) else False
        
        # MACD
        macd_line = ema_12 - ema_26
        signal_line = macd_line.ewm(span=config.get('macd_signal', 9)).mean()
        histogram = macd_line - signal_line
        
        if not pd.isna(macd_line.iloc[-1]) and not pd.isna(signal_line.iloc[-1]):
            indicators['macd'] = float(macd_line.iloc[-1])
            indicators['macd_signal'] = float(signal_line.iloc[-1])
            indicators['macd_histogram'] = float(histogram.iloc[-1])
            indicators['macd_bullish'] = macd_line.iloc[-1] > signal_line.iloc[-1]
        
        return indicators
    
    def _calculate_momentum_indicators(self, df: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
        """Momentum oscillators"""
        indicators = {}
        
        # RSI
        rsi = self._calculate_rsi(df['close'], config.get('rsi_period', 14))
        if not pd.isna(rsi):
            indicators['rsi'] = float(rsi)
            indicators['rsi_oversold'] = rsi < config.get('rsi_oversold', 30)
            indicators['rsi_overbought'] = rsi > config.get('rsi_overbought', 70)
            indicators['rsi_bullish'] = rsi > 50
        
        # Stochastic Oscillator
        stoch_k, stoch_d = self._calculate_stochastic(df, config.get('stoch_k', 14), config.get('stoch_d', 3))
        if not pd.isna(stoch_k) and not pd.isna(stoch_d):
            indicators['stoch_k'] = float(stoch_k)
            indicators['stoch_d'] = float(stoch_d)
            indicators['stoch_oversold'] = stoch_k < config.get('stoch_oversold', 20)
            indicators['stoch_overbought'] = stoch_k > config.get('stoch_overbought', 80)
        
        return indicators
    
    def _calculate_volatility_indicators(self, df: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
        """Volatility-based indicators"""
        indicators = {}
        
        # Bollinger Bands
        bb_period = config.get('bb_period', 20)
        bb_std = config.get('bb_std_dev', 2)
        
        sma = df['close'].rolling(window=bb_period).mean()
        std = df['close'].rolling(window=bb_period).std()
        
        if not pd.isna(sma.iloc[-1]) and not pd.isna(std.iloc[-1]):
            bb_upper = sma + (std * bb_std)
            bb_lower = sma - (std * bb_std)
            
            current_price = df['close'].iloc[-1]
            indicators['bb_upper'] = float(bb_upper.iloc[-1])
            indicators['bb_middle'] = float(sma.iloc[-1])
            indicators['bb_lower'] = float(bb_lower.iloc[-1])
            indicators['bb_width'] = indicators['bb_upper'] - indicators['bb_lower']
            indicators['bb_position'] = (current_price - indicators['bb_lower']) / indicators['bb_width']
            indicators['near_bb_lower'] = current_price <= indicators['bb_lower'] * 1.02
            indicators['near_bb_upper'] = current_price >= indicators['bb_upper'] * 0.98
        
        # Average True Range (ATR)
        atr = self._calculate_atr(df, config.get('atr_period', 14))
        if not pd.isna(atr):
            indicators['atr'] = float(atr)
            # Calculate volatility percentile
            atr_series = df.apply(lambda x: self._calculate_atr(df.loc[:x.name], 14), axis=1).dropna()
            if len(atr_series) > 20:
                indicators['volatility_high'] = atr > atr_series.quantile(0.8)
        
        return indicators
    
    def _calculate_volume_indicators(self, df: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
        """Volume-based indicators"""
        indicators = {}
        
        if 'volume' not in df.columns:
            return indicators
        
        # Volume moving average
        volume_sma = df['volume'].rolling(window=config.get('volume_sma', 20)).mean()
        if not pd.isna(volume_sma.iloc[-1]):
            current_volume = df['volume'].iloc[-1]
            indicators['volume_sma'] = float(volume_sma.iloc[-1])
            indicators['volume_above_average'] = current_volume > volume_sma.iloc[-1]
            indicators['volume_spike'] = current_volume > volume_sma.iloc[-1] * 1.5
        
        # On-Balance Volume (OBV)
        obv = self._calculate_obv(df)
        if not pd.isna(obv):
            indicators['obv'] = float(obv)
            obv_series = df.apply(lambda x: self._calculate_obv(df.loc[:x.name]), axis=1).dropna()
            if len(obv_series) > 5:
                indicators['obv_trend'] = obv > obv_series.iloc[-5]
        
        return indicators
    
    def _calculate_support_resistance(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Support and resistance levels"""
        indicators = {}
        
        # Pivot Points
        if len(df) >= 3:
            high = df['high'].iloc[-2]
            low = df['low'].iloc[-2]
            close = df['close'].iloc[-2]
            
            pivot = (high + low + close) / 3
            indicators['pivot_point'] = float(pivot)
            indicators['resistance_1'] = float(2 * pivot - low)
            indicators['support_1'] = float(2 * pivot - high)
            indicators['resistance_2'] = float(pivot + (high - low))
            indicators['support_2'] = float(pivot - (high - low))
        
        # Recent highs and lows
        if len(df) >= 20:
            recent_high = df['high'].tail(20).max()
            recent_low = df['low'].tail(20).min()
            current_price = df['close'].iloc[-1]
            
            indicators['recent_high'] = float(recent_high)
            indicators['recent_low'] = float(recent_low)
            indicators['near_resistance'] = current_price >= recent_high * 0.98
            indicators['near_support'] = current_price <= recent_low * 1.02
        
        return indicators
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        if pd.isna(gain.iloc[-1]) or pd.isna(loss.iloc[-1]) or loss.iloc[-1] == 0:
            return np.nan
        
        rs = gain.iloc[-1] / loss.iloc[-1]
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_stochastic(self, df: pd.DataFrame, k_period: int = 14, d_period: int = 3):
        """Calculate Stochastic Oscillator"""
        low_min = df['low'].rolling(window=k_period).min()
        high_max = df['high'].rolling(window=k_period).max()
        
        if pd.isna(low_min.iloc[-1]) or pd.isna(high_max.iloc[-1]):
            return np.nan, np.nan
        
        k_percent = 100 * ((df['close'].iloc[-1] - low_min.iloc[-1]) / (high_max.iloc[-1] - low_min.iloc[-1]))
        
        # Calculate D as moving average of K
        k_series = 100 * ((df['close'] - low_min) / (high_max - low_min))
        d_percent = k_series.rolling(window=d_period).mean().iloc[-1]
        
        return k_percent, d_percent if not pd.isna(d_percent) else k_percent
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range"""
        if len(df) < 2:
            return np.nan
        
        high = df['high']
        low = df['low']
        close = df['close'].shift(1)
        
        tr1 = high - low
        tr2 = abs(high - close)
        tr3 = abs(low - close)
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return atr.iloc[-1] if not pd.isna(atr.iloc[-1]) else np.nan
    
    def _calculate_obv(self, df: pd.DataFrame) -> float:
        """Calculate On-Balance Volume"""
        if 'volume' not in df.columns or len(df) < 2:
            return np.nan
        
        obv = 0
        for i in range(1, len(df)):
            if df['close'].iloc[i] > df['close'].iloc[i-1]:
                obv += df['volume'].iloc[i]
            elif df['close'].iloc[i] < df['close'].iloc[i-1]:
                obv -= df['volume'].iloc[i]
        
        return obv
    
    def _convert_numpy_types(self, obj):
        """Convert numpy types to Python native types for MongoDB compatibility"""
        if isinstance(obj, dict):
            return {key: self._convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_numpy_types(item) for item in obj]
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj
    
    def get_signal_strength(self, indicators: Dict[str, Any]) -> float:
        """Calculate overall signal strength (0-10)"""
        if not indicators:
            return 5.0
        
        bullish_signals = 0
        bearish_signals = 0
        total_signals = 0
        
        # Trend signals
        if 'ema_crossover' in indicators:
            total_signals += 1
            if indicators['ema_crossover']:
                bullish_signals += 1
            else:
                bearish_signals += 1
        
        if 'sma_trend' in indicators:
            total_signals += 1
            if indicators['sma_trend']:
                bullish_signals += 1
            else:
                bearish_signals += 1
        
        # Momentum signals
        if 'rsi_bullish' in indicators:
            total_signals += 1
            if indicators['rsi_bullish']:
                bullish_signals += 1
            else:
                bearish_signals += 1
        
        if 'macd_bullish' in indicators:
            total_signals += 1
            if indicators['macd_bullish']:
                bullish_signals += 1
            else:
                bearish_signals += 1
        
        # Volume confirmation
        if 'volume_above_average' in indicators:
            total_signals += 0.5
            if indicators['volume_above_average']:
                bullish_signals += 0.5
        
        if total_signals == 0:
            return 5.0  # Neutral
        
        # Calculate strength (5 = neutral, >5 = bullish, <5 = bearish)
        signal_ratio = bullish_signals / total_signals
        return signal_ratio * 10
    
    def get_trading_signal(self, indicators: Dict[str, Any], config: Dict[str, Any]) -> str:
        """Generate BUY/SELL/HOLD signal based on indicators"""
        signal_strength = self.get_signal_strength(indicators)
        min_strength = config.get('min_signal_strength', 6)
        
        # Strong bullish conditions
        bullish_conditions = [
            indicators.get('rsi_oversold', False),
            indicators.get('near_bb_lower', False),
            indicators.get('ema_crossover', False),
            indicators.get('macd_bullish', False),
            indicators.get('volume_above_average', False),
            indicators.get('stoch_oversold', False)
        ]
        
        # Strong bearish conditions  
        bearish_conditions = [
            indicators.get('rsi_overbought', False),
            indicators.get('near_bb_upper', False),
            not indicators.get('ema_crossover', True),
            not indicators.get('macd_bullish', True),
            indicators.get('stoch_overbought', False)
        ]
        
        bullish_score = sum(bullish_conditions)
        bearish_score = sum(bearish_conditions)
        
        if signal_strength >= min_strength and bullish_score >= 3:
            return 'BUY'
        elif signal_strength <= (10 - min_strength) and bearish_score >= 3:
            return 'SELL'
        else:
            return 'HOLD'

if __name__ == "__main__":
    # Example usage
    import pandas as pd
    
    # Create sample data for testing
    dates = pd.date_range('2024-01-01', periods=100, freq='H')
    sample_data = pd.DataFrame({
        'timestamp': dates,
        'open': np.random.randn(100).cumsum() + 100,
        'high': np.random.randn(100).cumsum() + 105,
        'low': np.random.randn(100).cumsum() + 95,
        'close': np.random.randn(100).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, 100)
    })
    
    # Initialize indicators calculator
    ti = TechnicalIndicators()
    
    # Sample configuration
    config = {
        'rsi_period': 14,
        'bb_period': 20,
        'bb_std_dev': 2,
        'min_signal_strength': 6
    }
    
    # Calculate indicators
    indicators = ti.calculate_all_indicators(sample_data, config)
    signal = ti.get_trading_signal(indicators, config)
    strength = ti.get_signal_strength(indicators)
    
    print(f"Sample indicators calculated: {len(indicators)} indicators")
    print(f"Signal: {signal}, Strength: {strength:.2f}")