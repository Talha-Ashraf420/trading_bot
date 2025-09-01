"""
Advanced trading strategies inspired by popular freqtrade strategies
Implements proven algorithmic trading patterns with enhanced features
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime
from indicators.technical_indicators_simple import TechnicalIndicators
from strategies.strategy_engine import BaseStrategy

class BbandRsiStrategy(BaseStrategy):
    """
    BBand + RSI Strategy (Popular freqtrade pattern)
    Combines Bollinger Bands with RSI for entry/exit signals
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("BbandRsi", config)
        
    def generate_signal(self, df: pd.DataFrame, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Generate BBand + RSI signals"""
        
        signal_data = {
            'timestamp': datetime.utcnow(),
            'price': float(df['close'].iloc[-1]),
            'signal': 'HOLD',
            'confidence': 0.0,
            'reasoning': [],
            'indicators': indicators
        }
        
        reasoning = []
        score = 0
        
        # Entry conditions (BUY)
        rsi = indicators.get('rsi', 50)
        bb_position = indicators.get('bb_position', 0.5)
        volume_above_avg = indicators.get('volume_above_average', False)
        macd_bullish = indicators.get('macd_bullish', False)
        
        # Strong buy conditions
        if (rsi < 30 and bb_position < 0.2):  # RSI oversold + BB lower
            score += 4
            reasoning.append("RSI oversold + Bollinger lower band")
        elif (rsi < 35 and bb_position < 0.3):  # Moderate oversold
            score += 2
            reasoning.append("RSI approaching oversold + BB lower third")
        
        # Volume confirmation
        if volume_above_avg:
            score += 1
            reasoning.append("Volume confirmation")
        
        # MACD support
        if macd_bullish:
            score += 1
            reasoning.append("MACD bullish support")
        
        # Exit conditions (SELL)
        sell_score = 0
        if (rsi > 70 and bb_position > 0.8):  # RSI overbought + BB upper
            sell_score += 4
            reasoning.append("RSI overbought + Bollinger upper band")
        elif (rsi > 65 and bb_position > 0.7):  # Moderate overbought
            sell_score += 2
            reasoning.append("RSI approaching overbought + BB upper third")
        
        # Determine signal
        if score >= 4:
            signal_data['signal'] = 'BUY'
            signal_data['confidence'] = min(score / 6, 1.0)
        elif sell_score >= 4:
            signal_data['signal'] = 'SELL'
            signal_data['confidence'] = min(sell_score / 6, 1.0)
        elif score >= 2:
            signal_data['signal'] = 'BUY'
            signal_data['confidence'] = score / 6
        elif sell_score >= 2:
            signal_data['signal'] = 'SELL' 
            signal_data['confidence'] = sell_score / 6
        
        signal_data['reasoning'] = reasoning
        return signal_data
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'bb_lower_threshold': 0.2,
            'bb_upper_threshold': 0.8
        }

class EmaRsiStrategy(BaseStrategy):
    """
    EMA + RSI Strategy (Trend + Momentum)
    Uses multiple EMAs with RSI confirmation
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("EmaRsi", config)
        
    def generate_signal(self, df: pd.DataFrame, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Generate EMA + RSI signals"""
        
        signal_data = {
            'timestamp': datetime.utcnow(),
            'price': float(df['close'].iloc[-1]),
            'signal': 'HOLD',
            'confidence': 0.0,
            'reasoning': [],
            'indicators': indicators
        }
        
        reasoning = []
        score = 0
        
        # Get indicators
        ema_crossover = indicators.get('ema_crossover', False)
        sma_trend = indicators.get('sma_trend', False)
        rsi = indicators.get('rsi', 50)
        volume_above_avg = indicators.get('volume_above_average', False)
        atr = indicators.get('atr', 0)
        
        current_price = float(df['close'].iloc[-1])
        ema_12 = indicators.get('ema_12', current_price)
        ema_26 = indicators.get('ema_26', current_price)
        
        # Trend analysis
        if ema_crossover and sma_trend:  # Strong uptrend
            score += 3
            reasoning.append("EMA bullish crossover + SMA uptrend")
        elif ema_crossover:  # EMA crossover only
            score += 2
            reasoning.append("EMA bullish crossover")
        elif sma_trend:  # SMA uptrend only
            score += 1
            reasoning.append("SMA uptrend")
        
        # RSI momentum
        if 40 <= rsi <= 60:  # RSI neutral (good for trend following)
            score += 2
            reasoning.append("RSI neutral momentum")
        elif 30 <= rsi < 40:  # Oversold but not extreme
            score += 1
            reasoning.append("RSI moderately oversold")
        elif rsi > 70:  # Overbought - bearish
            score -= 2
            reasoning.append("RSI overbought (bearish)")
        
        # Volume confirmation
        if volume_above_avg:
            score += 1
            reasoning.append("Volume above average")
        
        # Price position relative to EMAs
        if current_price > ema_12 > ema_26:
            score += 2
            reasoning.append("Price above both EMAs")
        elif current_price > ema_12:
            score += 1
            reasoning.append("Price above fast EMA")
        
        # Volatility check
        if atr > 0:
            # Lower volatility preferred for EMA strategy
            recent_atr_pct = (atr / current_price) * 100
            if recent_atr_pct < 2:  # Low volatility
                score += 1
                reasoning.append("Low volatility environment")
        
        # Determine signal
        if score >= 5:
            signal_data['signal'] = 'BUY'
            signal_data['confidence'] = min(score / 8, 1.0)
        elif score >= 3:
            signal_data['signal'] = 'BUY'
            signal_data['confidence'] = score / 8
        elif score <= -2:
            signal_data['signal'] = 'SELL'
            signal_data['confidence'] = abs(score) / 8
        
        signal_data['reasoning'] = reasoning
        return signal_data
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            'ema_fast': 12,
            'ema_slow': 26,
            'rsi_neutral_min': 40,
            'rsi_neutral_max': 60,
            'volume_confirmation': True
        }

class MacdRsiStrategy(BaseStrategy):
    """
    MACD + RSI Strategy (Classic momentum combination)
    Uses MACD for trend direction and RSI for entry timing
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("MacdRsi", config)
        
    def generate_signal(self, df: pd.DataFrame, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Generate MACD + RSI signals"""
        
        signal_data = {
            'timestamp': datetime.utcnow(),
            'price': float(df['close'].iloc[-1]),
            'signal': 'HOLD',
            'confidence': 0.0,
            'reasoning': [],
            'indicators': indicators
        }
        
        reasoning = []
        score = 0
        
        # Get indicators
        macd_bullish = indicators.get('macd_bullish', False)
        macd_histogram = indicators.get('macd_histogram', 0)
        rsi = indicators.get('rsi', 50)
        volume_above_avg = indicators.get('volume_above_average', False)
        bb_position = indicators.get('bb_position', 0.5)
        
        # MACD analysis
        if macd_bullish and macd_histogram > 0:  # Strong MACD signal
            score += 3
            reasoning.append("MACD bullish with positive histogram")
        elif macd_bullish:  # MACD crossover only
            score += 2
            reasoning.append("MACD bullish crossover")
        elif macd_histogram > 0:  # Positive momentum
            score += 1
            reasoning.append("MACD positive momentum")
        
        # RSI timing
        if rsi < 35:  # Oversold - good buy timing
            score += 2
            reasoning.append("RSI oversold - good timing")
        elif 35 <= rsi <= 50:  # Neutral to slightly bearish
            score += 1
            reasoning.append("RSI neutral")
        elif rsi > 65:  # Overbought - bearish
            score -= 2
            reasoning.append("RSI overbought")
        
        # Bollinger Bands support
        if bb_position < 0.3:  # Lower third of BB
            score += 1
            reasoning.append("Price in lower Bollinger Band")
        elif bb_position > 0.7:  # Upper third of BB
            score -= 1
            reasoning.append("Price in upper Bollinger Band")
        
        # Volume confirmation
        if volume_above_avg:
            score += 1
            reasoning.append("Volume confirmation")
        
        # Look for divergence (simplified)
        if len(df) >= 5:
            recent_prices = df['close'].tail(5)
            price_trend = recent_prices.iloc[-1] > recent_prices.iloc[0]
            
            # If MACD bullish but price declining (bullish divergence)
            if macd_bullish and not price_trend and rsi < 40:
                score += 2
                reasoning.append("Possible bullish divergence")
        
        # Determine signal
        if score >= 5:
            signal_data['signal'] = 'BUY'
            signal_data['confidence'] = min(score / 8, 1.0)
        elif score >= 3:
            signal_data['signal'] = 'BUY'
            signal_data['confidence'] = score / 8
        elif score <= -2:
            signal_data['signal'] = 'SELL'
            signal_data['confidence'] = abs(score) / 8
        
        signal_data['reasoning'] = reasoning
        return signal_data
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'rsi_oversold': 35,
            'rsi_overbought': 65
        }

class AdxMomentumStrategy(BaseStrategy):
    """
    ADX + Momentum Strategy (Trend strength based)
    Uses ADX to identify strong trends and momentum for entries
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("AdxMomentum", config)
        
    def generate_signal(self, df: pd.DataFrame, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Generate ADX + Momentum signals"""
        
        signal_data = {
            'timestamp': datetime.utcnow(),
            'price': float(df['close'].iloc[-1]),
            'signal': 'HOLD',
            'confidence': 0.0,
            'reasoning': [],
            'indicators': indicators
        }
        
        reasoning = []
        score = 0
        
        # Get indicators
        adx = indicators.get('adx', 0)
        strong_trend = indicators.get('strong_trend', False)
        ema_crossover = indicators.get('ema_crossover', False)
        rsi = indicators.get('rsi', 50)
        volume_above_avg = indicators.get('volume_above_average', False)
        macd_bullish = indicators.get('macd_bullish', False)
        
        current_price = float(df['close'].iloc[-1])
        
        # ADX trend strength analysis
        if adx > 35:  # Very strong trend
            score += 3
            reasoning.append(f"Very strong trend (ADX: {adx:.1f})")
        elif adx > 25:  # Strong trend
            score += 2
            reasoning.append(f"Strong trend (ADX: {adx:.1f})")
        elif adx > 15:  # Moderate trend
            score += 1
            reasoning.append(f"Moderate trend (ADX: {adx:.1f})")
        else:  # Weak trend - avoid
            score -= 1
            reasoning.append(f"Weak trend (ADX: {adx:.1f}) - avoid")
        
        # Momentum confirmation
        if ema_crossover and macd_bullish:  # Strong momentum
            score += 3
            reasoning.append("EMA + MACD momentum alignment")
        elif ema_crossover or macd_bullish:  # Moderate momentum
            score += 2
            reasoning.append("EMA or MACD momentum")
        
        # RSI filter (avoid extremes in trending markets)
        if 45 <= rsi <= 65:  # Good range for trending
            score += 1
            reasoning.append("RSI in trending range")
        elif rsi < 30:  # Oversold in trend
            score += 2
            reasoning.append("RSI oversold in trend")
        elif rsi > 75:  # Overbought - caution
            score -= 1
            reasoning.append("RSI overbought - caution")
        
        # Volume confirmation (important for trend following)
        if volume_above_avg:
            score += 2
            reasoning.append("Volume supporting trend")
        
        # Price action confirmation
        if len(df) >= 3:
            recent_closes = df['close'].tail(3).values
            if recent_closes[-1] > recent_closes[-2] > recent_closes[-3]:
                score += 1
                reasoning.append("Consistent upward price action")
            elif recent_closes[-1] < recent_closes[-2] < recent_closes[-3]:
                score -= 1
                reasoning.append("Consistent downward price action")
        
        # Determine signal (higher threshold due to trend following nature)
        if score >= 6:
            signal_data['signal'] = 'BUY'
            signal_data['confidence'] = min(score / 10, 1.0)
        elif score >= 4:
            signal_data['signal'] = 'BUY'
            signal_data['confidence'] = score / 10
        elif score <= -2:
            signal_data['signal'] = 'SELL'
            signal_data['confidence'] = abs(score) / 10
        
        signal_data['reasoning'] = reasoning
        return signal_data
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            'adx_threshold': 25,
            'adx_strong': 35,
            'rsi_trend_min': 45,
            'rsi_trend_max': 65,
            'volume_importance': 'high'
        }

class VolatilityBreakoutStrategy(BaseStrategy):
    """
    Volatility Breakout Strategy (ATR-based)
    Identifies low volatility periods followed by breakouts
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("VolatilityBreakout", config)
        
    def generate_signal(self, df: pd.DataFrame, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Generate volatility breakout signals"""
        
        signal_data = {
            'timestamp': datetime.utcnow(),
            'price': float(df['close'].iloc[-1]),
            'signal': 'HOLD',
            'confidence': 0.0,
            'reasoning': [],
            'indicators': indicators
        }
        
        reasoning = []
        score = 0
        
        # Get indicators
        atr = indicators.get('atr', 0)
        bb_width = indicators.get('bb_width', 0)
        volume_spike = indicators.get('volume_spike', False)
        near_resistance = indicators.get('near_resistance', False)
        near_support = indicators.get('near_support', False)
        current_price = float(df['close'].iloc[-1])
        recent_high = indicators.get('recent_high', current_price)
        recent_low = indicators.get('recent_low', current_price)
        
        # Volatility analysis
        if atr > 0 and current_price > 0:
            atr_pct = (atr / current_price) * 100
            
            if atr_pct < 1.5:  # Low volatility (compression)
                score += 2
                reasoning.append(f"Low volatility (ATR: {atr_pct:.2f}%) - compression")
            elif atr_pct > 4:  # High volatility (expansion)
                score += 1
                reasoning.append(f"High volatility (ATR: {atr_pct:.2f}%) - expansion")
        
        # Bollinger Band compression/expansion
        if bb_width > 0:
            # Calculate BB width as percentage of price
            bb_width_pct = (bb_width / current_price) * 100
            
            if bb_width_pct < 3:  # Tight bands
                score += 1
                reasoning.append("Bollinger Bands compression")
            elif bb_width_pct > 8:  # Wide bands
                score += 1
                reasoning.append("Bollinger Bands expansion")
        
        # Breakout detection
        if near_resistance and volume_spike:
            score += 4
            reasoning.append("Resistance breakout with volume")
        elif near_support and volume_spike:
            score -= 3  # Support breakdown
            reasoning.append("Support breakdown with volume")
        elif near_resistance:
            score += 2
            reasoning.append("Approaching resistance")
        elif near_support:
            score += 1
            reasoning.append("Approaching support (bounce potential)")
        
        # Price position analysis
        if recent_high > 0 and recent_low > 0:
            price_position = (current_price - recent_low) / (recent_high - recent_low)
            
            if price_position > 0.9:  # Near recent high
                if volume_spike:
                    score += 3
                    reasoning.append("Breaking to new highs with volume")
                else:
                    score += 1
                    reasoning.append("Near recent highs")
            elif price_position < 0.1:  # Near recent low
                if volume_spike:
                    score += 2
                    reasoning.append("Bouncing from lows with volume")
                else:
                    score += 1
                    reasoning.append("Near recent lows - bounce potential")
        
        # Volume analysis (crucial for breakouts)
        if volume_spike:
            score += 2
            reasoning.append("Volume spike confirms move")
        
        # Range analysis
        if len(df) >= 10:
            recent_range = df['high'].tail(10).max() - df['low'].tail(10).min()
            if recent_range > 0:
                current_move = abs(current_price - df['close'].iloc[-2])
                move_pct = (current_move / recent_range) * 100
                
                if move_pct > 50:  # Significant move
                    score += 1
                    reasoning.append("Significant price move detected")
        
        # Determine signal
        if score >= 5:
            signal_data['signal'] = 'BUY'
            signal_data['confidence'] = min(score / 8, 1.0)
        elif score >= 3:
            signal_data['signal'] = 'BUY'
            signal_data['confidence'] = score / 8
        elif score <= -2:
            signal_data['signal'] = 'SELL'
            signal_data['confidence'] = abs(score) / 8
        
        signal_data['reasoning'] = reasoning
        return signal_data
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            'atr_low_threshold': 1.5,
            'atr_high_threshold': 4.0,
            'bb_compression_threshold': 3.0,
            'volume_spike_multiplier': 1.5,
            'breakout_confirmation': True
        }

class ScalpingStrategy(BaseStrategy):
    """
    Scalping Strategy (Short-term high frequency)
    Quick entries and exits on small price movements
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("Scalping", config)
        
    def generate_signal(self, df: pd.DataFrame, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Generate scalping signals"""
        
        signal_data = {
            'timestamp': datetime.utcnow(),
            'price': float(df['close'].iloc[-1]),
            'signal': 'HOLD',
            'confidence': 0.0,
            'reasoning': [],
            'indicators': indicators
        }
        
        reasoning = []
        score = 0
        
        # Get indicators (focus on fast-moving ones)
        rsi = indicators.get('rsi', 50)
        stoch_k = indicators.get('stoch_k', 50)
        bb_position = indicators.get('bb_position', 0.5)
        volume_above_avg = indicators.get('volume_above_average', False)
        ema_crossover = indicators.get('ema_crossover', False)
        current_price = float(df['close'].iloc[-1])
        
        # Fast RSI signals
        if rsi < 25:  # Very oversold
            score += 3
            reasoning.append("RSI very oversold")
        elif rsi < 35:  # Oversold
            score += 2
            reasoning.append("RSI oversold")
        elif rsi > 75:  # Very overbought
            score -= 3
            reasoning.append("RSI very overbought")
        elif rsi > 65:  # Overbought
            score -= 2
            reasoning.append("RSI overbought")
        
        # Stochastic for timing
        if stoch_k < 20:  # Stoch oversold
            score += 2
            reasoning.append("Stochastic oversold")
        elif stoch_k > 80:  # Stoch overbought
            score -= 2
            reasoning.append("Stochastic overbought")
        
        # Bollinger Band position (mean reversion)
        if bb_position < 0.15:  # Very low
            score += 3
            reasoning.append("Price at Bollinger lower band")
        elif bb_position < 0.3:  # Low
            score += 1
            reasoning.append("Price in lower Bollinger third")
        elif bb_position > 0.85:  # Very high
            score -= 3
            reasoning.append("Price at Bollinger upper band")
        elif bb_position > 0.7:  # High
            score -= 1
            reasoning.append("Price in upper Bollinger third")
        
        # Quick momentum check
        if len(df) >= 3:
            last_3_closes = df['close'].tail(3).values
            momentum = (last_3_closes[-1] - last_3_closes[0]) / last_3_closes[0] * 100
            
            if momentum > 0.5:  # Strong short-term momentum
                score += 1
                reasoning.append("Positive short-term momentum")
            elif momentum < -0.5:  # Strong negative momentum
                score -= 1
                reasoning.append("Negative short-term momentum")
        
        # Volume confirmation (important for scalping)
        if volume_above_avg:
            score += 1
            reasoning.append("Volume above average")
        
        # Price action patterns (simplified)
        if len(df) >= 5:
            recent_highs = df['high'].tail(5).values
            recent_lows = df['low'].tail(5).values
            
            # Look for double bottom pattern (bullish)
            if len(recent_lows) >= 3:
                if (recent_lows[-1] <= min(recent_lows[-3:-1]) * 1.002 and  # Near previous low
                    current_price > recent_lows[-1] * 1.005):  # Price moving up
                    score += 2
                    reasoning.append("Potential double bottom pattern")
            
            # Look for double top pattern (bearish)
            if len(recent_highs) >= 3:
                if (recent_highs[-1] >= max(recent_highs[-3:-1]) * 0.998 and  # Near previous high
                    current_price < recent_highs[-1] * 0.995):  # Price moving down
                    score -= 2
                    reasoning.append("Potential double top pattern")
        
        # Determine signal (scalping needs quick decisions)
        if score >= 4:
            signal_data['signal'] = 'BUY'
            signal_data['confidence'] = min(score / 7, 1.0)
        elif score >= 2:
            signal_data['signal'] = 'BUY'
            signal_data['confidence'] = score / 7
        elif score <= -4:
            signal_data['signal'] = 'SELL'
            signal_data['confidence'] = abs(score) / 7
        elif score <= -2:
            signal_data['signal'] = 'SELL'
            signal_data['confidence'] = abs(score) / 7
        
        signal_data['reasoning'] = reasoning
        return signal_data
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            'rsi_oversold': 25,
            'rsi_overbought': 75,
            'stoch_oversold': 20,
            'stoch_overbought': 80,
            'bb_lower_threshold': 0.15,
            'bb_upper_threshold': 0.85,
            'quick_exit': True
        }

# Strategy factory for easy instantiation
class AdvancedStrategyFactory:
    """Factory for creating advanced strategies"""
    
    @staticmethod
    def get_all_strategies(config: Dict[str, Any]) -> List[BaseStrategy]:
        """Get all available advanced strategies"""
        return [
            BbandRsiStrategy(config),
            EmaRsiStrategy(config),
            MacdRsiStrategy(config),
            AdxMomentumStrategy(config),
            VolatilityBreakoutStrategy(config),
            ScalpingStrategy(config)
        ]
    
    @staticmethod
    def get_strategy_by_name(name: str, config: Dict[str, Any]) -> Optional[BaseStrategy]:
        """Get specific strategy by name"""
        strategies = {
            'BbandRsi': BbandRsiStrategy,
            'EmaRsi': EmaRsiStrategy,
            'MacdRsi': MacdRsiStrategy,
            'AdxMomentum': AdxMomentumStrategy,
            'VolatilityBreakout': VolatilityBreakoutStrategy,
            'Scalping': ScalpingStrategy
        }
        
        strategy_class = strategies.get(name)
        return strategy_class(config) if strategy_class else None
    
    @staticmethod
    def get_strategy_descriptions() -> Dict[str, str]:
        """Get descriptions of all strategies"""
        return {
            'BbandRsi': 'Bollinger Bands + RSI for oversold/overbought signals',
            'EmaRsi': 'EMA crossovers with RSI momentum confirmation', 
            'MacdRsi': 'MACD trend with RSI timing for entries',
            'AdxMomentum': 'ADX trend strength with momentum indicators',
            'VolatilityBreakout': 'ATR-based volatility breakout detection',
            'Scalping': 'High-frequency short-term trading signals'
        }

if __name__ == "__main__":
    # Test the strategies
    import config
    
    print("🧪 Testing Advanced Strategies...")
    
    # Create sample data
    dates = pd.date_range('2024-01-01', periods=100, freq='H')
    np.random.seed(42)
    prices = 50000 + np.cumsum(np.random.randn(100) * 50)
    
    sample_data = pd.DataFrame({
        'timestamp': dates,
        'open': prices + np.random.randn(100) * 10,
        'high': prices + np.abs(np.random.randn(100) * 20),
        'low': prices - np.abs(np.random.randn(100) * 20),
        'close': prices,
        'volume': np.random.randint(100, 1000, 100)
    })
    
    # Test indicators
    indicators = TechnicalIndicators()
    results = indicators.calculate_all_indicators(sample_data, config.STRATEGY_CONFIG)
    
    # Test all strategies
    factory = AdvancedStrategyFactory()
    strategies = factory.get_all_strategies(config.STRATEGY_CONFIG)
    
    print(f"\n📊 Testing {len(strategies)} Advanced Strategies:")
    
    for strategy in strategies:
        signal = strategy.generate_signal(sample_data, results)
        print(f"\n✅ {strategy.name} Strategy:")
        print(f"   Signal: {signal['signal']}")
        print(f"   Confidence: {signal['confidence']:.2%}")
        print(f"   Top reasons: {', '.join(signal['reasoning'][:2])}")
    
    print(f"\n🎉 All advanced strategies tested successfully!")