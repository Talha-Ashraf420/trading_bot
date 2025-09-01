from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import pandas as pd
from datetime import datetime
from indicators.technical_indicators_simple import TechnicalIndicators
from core.database_schema import TradingDatabase

class BaseStrategy(ABC):
    """Abstract base class for trading strategies"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.indicators_calculator = TechnicalIndicators()
        
    @abstractmethod
    def generate_signal(self, df: pd.DataFrame, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading signal based on data and indicators"""
        pass
    
    @abstractmethod
    def get_parameters(self) -> Dict[str, Any]:
        """Get strategy parameters for optimization"""
        pass

class MultiIndicatorStrategy(BaseStrategy):
    """Strategy combining multiple technical indicators"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("MultiIndicator", config)
        
    def generate_signal(self, df: pd.DataFrame, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Generate signal based on multiple indicators"""
        
        signal_data = {
            'timestamp': datetime.utcnow(),
            'price': float(df['close'].iloc[-1]),
            'signal': 'HOLD',
            'confidence': 0.0,
            'reasoning': [],
            'indicators': indicators
        }
        
        score = 0
        max_score = 0
        reasoning = []
        
        # RSI Analysis (Weight: 2)
        if 'rsi' in indicators:
            max_score += 2
            if indicators.get('rsi_oversold', False):
                score += 2
                reasoning.append("RSI oversold (bullish)")
            elif indicators.get('rsi_overbought', False):
                score -= 2
                reasoning.append("RSI overbought (bearish)")
            elif indicators.get('rsi_bullish', False):
                score += 1
                reasoning.append("RSI bullish")
            else:
                score -= 1
                reasoning.append("RSI bearish")
        
        # MACD Analysis (Weight: 2)
        if 'macd_bullish' in indicators:
            max_score += 2
            if indicators['macd_bullish']:
                score += 2
                reasoning.append("MACD bullish crossover")
            else:
                score -= 2
                reasoning.append("MACD bearish crossover")
        
        # Bollinger Bands Analysis (Weight: 2)
        if 'near_bb_lower' in indicators and 'near_bb_upper' in indicators:
            max_score += 2
            if indicators['near_bb_lower']:
                score += 2
                reasoning.append("Near Bollinger lower band (bullish)")
            elif indicators['near_bb_upper']:
                score -= 2
                reasoning.append("Near Bollinger upper band (bearish)")
        
        # Moving Average Trend (Weight: 1)
        if 'ema_crossover' in indicators:
            max_score += 1
            if indicators['ema_crossover']:
                score += 1
                reasoning.append("EMA bullish trend")
            else:
                score -= 1
                reasoning.append("EMA bearish trend")
        
        # Volume Confirmation (Weight: 1)
        if 'volume_above_average' in indicators:
            max_score += 1
            if indicators['volume_above_average']:
                score += 1
                reasoning.append("Volume confirmation")
        
        # Stochastic Analysis (Weight: 1)
        if 'stoch_oversold' in indicators and 'stoch_overbought' in indicators:
            max_score += 1
            if indicators['stoch_oversold']:
                score += 1
                reasoning.append("Stochastic oversold")
            elif indicators['stoch_overbought']:
                score -= 1
                reasoning.append("Stochastic overbought")
        
        # Calculate confidence and signal
        if max_score > 0:
            confidence = abs(score) / max_score
            
            threshold = self.config.get('signal_threshold', 0.6)
            
            if score > 0 and confidence >= threshold:
                signal_data['signal'] = 'BUY'
                signal_data['confidence'] = confidence
            elif score < 0 and confidence >= threshold:
                signal_data['signal'] = 'SELL'
                signal_data['confidence'] = confidence
            else:
                signal_data['signal'] = 'HOLD'
                signal_data['confidence'] = confidence
        
        signal_data['reasoning'] = reasoning
        return signal_data
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            'signal_threshold': self.config.get('signal_threshold', 0.6),
            'rsi_period': self.config.get('rsi_period', 14),
            'bb_period': self.config.get('bb_period', 20),
            'ema_fast': self.config.get('ema_fast', 12),
            'ema_slow': self.config.get('ema_slow', 26)
        }

class MeanReversionStrategy(BaseStrategy):
    """Mean reversion strategy using Bollinger Bands and RSI"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("MeanReversion", config)
    
    def generate_signal(self, df: pd.DataFrame, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mean reversion signals"""
        
        signal_data = {
            'timestamp': datetime.utcnow(),
            'price': float(df['close'].iloc[-1]),
            'signal': 'HOLD',
            'confidence': 0.0,
            'reasoning': [],
            'indicators': indicators
        }
        
        reasoning = []
        
        # Mean reversion logic
        rsi_oversold = indicators.get('rsi_oversold', False)
        rsi_overbought = indicators.get('rsi_overbought', False)
        near_bb_lower = indicators.get('near_bb_lower', False)
        near_bb_upper = indicators.get('near_bb_upper', False)
        
        # Buy signals (oversold conditions)
        if (rsi_oversold and near_bb_lower) or (rsi_oversold and indicators.get('bb_position', 0.5) < 0.2):
            signal_data['signal'] = 'BUY'
            signal_data['confidence'] = 0.8
            reasoning.append("Strong oversold condition (RSI + BB)")
        elif rsi_oversold or near_bb_lower:
            signal_data['signal'] = 'BUY'
            signal_data['confidence'] = 0.6
            reasoning.append("Oversold condition detected")
        
        # Sell signals (overbought conditions)
        elif (rsi_overbought and near_bb_upper) or (rsi_overbought and indicators.get('bb_position', 0.5) > 0.8):
            signal_data['signal'] = 'SELL'
            signal_data['confidence'] = 0.8
            reasoning.append("Strong overbought condition (RSI + BB)")
        elif rsi_overbought or near_bb_upper:
            signal_data['signal'] = 'SELL'
            signal_data['confidence'] = 0.6
            reasoning.append("Overbought condition detected")
        
        signal_data['reasoning'] = reasoning
        return signal_data
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            'rsi_period': self.config.get('rsi_period', 14),
            'rsi_oversold': self.config.get('rsi_oversold', 30),
            'rsi_overbought': self.config.get('rsi_overbought', 70),
            'bb_period': self.config.get('bb_period', 20),
            'bb_std_dev': self.config.get('bb_std_dev', 2)
        }

class TrendFollowingStrategy(BaseStrategy):
    """Trend following strategy using moving averages and momentum"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("TrendFollowing", config)
    
    def generate_signal(self, df: pd.DataFrame, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trend following signals"""
        
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
        
        # Trend signals
        if indicators.get('ema_crossover', False):
            score += 2
            reasoning.append("EMA bullish crossover")
        
        if indicators.get('sma_trend', False):
            score += 1
            reasoning.append("Price above SMA trend")
        
        if indicators.get('macd_bullish', False):
            score += 2
            reasoning.append("MACD bullish")
        
        if indicators.get('adx', 0) > self.config.get('adx_threshold', 25):
            score += 1
            reasoning.append("Strong trend (ADX)")
        
        # Volume confirmation
        if indicators.get('volume_above_average', False):
            score += 1
            reasoning.append("Volume confirmation")
        
        # Generate signal
        if score >= 4:
            signal_data['signal'] = 'BUY'
            signal_data['confidence'] = min(score / 7, 1.0)
        elif score <= -4:
            signal_data['signal'] = 'SELL'
            signal_data['confidence'] = min(abs(score) / 7, 1.0)
        
        signal_data['reasoning'] = reasoning
        return signal_data
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            'ema_fast': self.config.get('ema_fast', 12),
            'ema_slow': self.config.get('ema_slow', 26),
            'sma_period': self.config.get('sma_period', 50),
            'adx_threshold': self.config.get('adx_threshold', 25)
        }

class BreakoutStrategy(BaseStrategy):
    """Breakout strategy using support/resistance and volume"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("Breakout", config)
    
    def generate_signal(self, df: pd.DataFrame, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Generate breakout signals"""
        
        signal_data = {
            'timestamp': datetime.utcnow(),
            'price': float(df['close'].iloc[-1]),
            'signal': 'HOLD',
            'confidence': 0.0,
            'reasoning': [],
            'indicators': indicators
        }
        
        reasoning = []
        current_price = float(df['close'].iloc[-1])
        
        # Volume spike confirmation
        volume_spike = indicators.get('volume_spike', False)
        
        # Resistance breakout
        if indicators.get('near_resistance', False) and volume_spike:
            if current_price > indicators.get('recent_high', current_price):
                signal_data['signal'] = 'BUY'
                signal_data['confidence'] = 0.8
                reasoning.append("Resistance breakout with volume")
        
        # Support breakdown
        elif indicators.get('near_support', False) and volume_spike:
            if current_price < indicators.get('recent_low', current_price):
                signal_data['signal'] = 'SELL'
                signal_data['confidence'] = 0.8
                reasoning.append("Support breakdown with volume")
        
        # Bollinger Band breakout
        elif indicators.get('near_bb_upper', False) and volume_spike:
            signal_data['signal'] = 'BUY'
            signal_data['confidence'] = 0.7
            reasoning.append("Bollinger upper band breakout")
        
        signal_data['reasoning'] = reasoning
        return signal_data
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            'volume_threshold': self.config.get('volume_threshold', 1.5),
            'bb_period': self.config.get('bb_period', 20),
            'lookback_period': self.config.get('lookback_period', 20)
        }

class StrategyEngine:
    """Main strategy engine to manage and execute multiple strategies"""
    
    def __init__(self, database: TradingDatabase):
        self.database = database
        self.strategies = {}
        self.active_strategies = []
        self.indicators_calculator = TechnicalIndicators()
        
    def register_strategy(self, strategy: BaseStrategy):
        """Register a strategy with the engine"""
        self.strategies[strategy.name] = strategy
        print(f"Strategy '{strategy.name}' registered")
    
    def activate_strategy(self, strategy_name: str):
        """Activate a strategy for signal generation"""
        if strategy_name in self.strategies:
            if strategy_name not in self.active_strategies:
                self.active_strategies.append(strategy_name)
                print(f"Strategy '{strategy_name}' activated")
        else:
            print(f"Strategy '{strategy_name}' not found")
    
    def deactivate_strategy(self, strategy_name: str):
        """Deactivate a strategy"""
        if strategy_name in self.active_strategies:
            self.active_strategies.remove(strategy_name)
            print(f"Strategy '{strategy_name}' deactivated")
    
    def analyze_market(self, symbol: str, df: pd.DataFrame, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze market data and generate signals from all active strategies"""
        
        if df is None or len(df) < 50:
            return []
        
        # Calculate technical indicators
        indicators = self.indicators_calculator.calculate_all_indicators(df, config)
        
        # Store indicators in database
        self.database.insert_indicators(
            symbol=symbol,
            timeframe=config.get('timeframe', '1h'),
            timestamp=datetime.utcnow(),
            indicators_data=indicators
        )
        
        signals = []
        
        # Generate signals from all active strategies
        for strategy_name in self.active_strategies:
            if strategy_name in self.strategies:
                try:
                    strategy = self.strategies[strategy_name]
                    signal_data = strategy.generate_signal(df, indicators)
                    
                    signal_data['strategy'] = strategy_name
                    signal_data['symbol'] = symbol
                    
                    # Store signal in database
                    self.database.insert_signal(symbol, strategy_name, signal_data)
                    
                    signals.append(signal_data)
                    
                except Exception as e:
                    print(f"Error generating signal from {strategy_name}: {e}")
        
        return signals
    
    def get_consensus_signal(self, signals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate consensus signal from multiple strategies"""
        
        if not signals:
            return {'signal': 'HOLD', 'confidence': 0.0, 'reasoning': ['No signals generated']}
        
        buy_signals = [s for s in signals if s['signal'] == 'BUY']
        sell_signals = [s for s in signals if s['signal'] == 'SELL']
        hold_signals = [s for s in signals if s['signal'] == 'HOLD']
        
        buy_confidence = sum([s['confidence'] for s in buy_signals]) / len(signals) if buy_signals else 0
        sell_confidence = sum([s['confidence'] for s in sell_signals]) / len(signals) if sell_signals else 0
        
        reasoning = []
        for signal in signals:
            reasoning.extend([f"{signal['strategy']}: {r}" for r in signal['reasoning']])
        
        # Consensus logic
        if len(buy_signals) > len(sell_signals) and buy_confidence > 0.5:
            return {
                'signal': 'BUY',
                'confidence': buy_confidence,
                'reasoning': reasoning,
                'supporting_strategies': len(buy_signals),
                'total_strategies': len(signals)
            }
        elif len(sell_signals) > len(buy_signals) and sell_confidence > 0.5:
            return {
                'signal': 'SELL',
                'confidence': sell_confidence,
                'reasoning': reasoning,
                'supporting_strategies': len(sell_signals),
                'total_strategies': len(signals)
            }
        else:
            return {
                'signal': 'HOLD',
                'confidence': 0.5,
                'reasoning': reasoning,
                'supporting_strategies': len(hold_signals),
                'total_strategies': len(signals)
            }
    
    def backtest_strategy(self, strategy_name: str, df: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
        """Backtest a single strategy"""
        if strategy_name not in self.strategies:
            return {}
        
        strategy = self.strategies[strategy_name]
        
        # Simple backtest implementation
        balance = config.get('initial_balance', 1000.0)
        position = 0
        trades = []
        
        for i in range(50, len(df)):
            window_df = df.iloc[:i+1]
            indicators = self.indicators_calculator.calculate_all_indicators(window_df, config)
            signal_data = strategy.generate_signal(window_df, indicators)
            
            if signal_data['signal'] == 'BUY' and position <= 0:
                position = balance / df['close'].iloc[i]
                balance = 0
                trades.append({
                    'type': 'BUY',
                    'price': df['close'].iloc[i],
                    'timestamp': i,
                    'position': position
                })
            elif signal_data['signal'] == 'SELL' and position > 0:
                balance = position * df['close'].iloc[i]
                position = 0
                trades.append({
                    'type': 'SELL',
                    'price': df['close'].iloc[i],
                    'timestamp': i,
                    'balance': balance
                })
        
        # Calculate final performance
        final_value = balance + (position * df['close'].iloc[-1] if position > 0 else 0)
        return_pct = ((final_value - config.get('initial_balance', 1000.0)) / config.get('initial_balance', 1000.0)) * 100
        
        return {
            'strategy': strategy_name,
            'initial_balance': config.get('initial_balance', 1000.0),
            'final_value': final_value,
            'return_pct': return_pct,
            'total_trades': len(trades),
            'trades': trades
        }

if __name__ == "__main__":
    # Example usage
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    import config
    from src.core.database_schema import TradingDatabase
    
    # Initialize database and strategy engine
    db = TradingDatabase()
    engine = StrategyEngine(db)
    
    # Register strategies
    engine.register_strategy(MultiIndicatorStrategy(config.STRATEGY_CONFIG))
    engine.register_strategy(MeanReversionStrategy(config.STRATEGY_CONFIG))
    engine.register_strategy(TrendFollowingStrategy(config.STRATEGY_CONFIG))
    engine.register_strategy(BreakoutStrategy(config.STRATEGY_CONFIG))
    
    # Activate strategies
    engine.activate_strategy("MultiIndicator")
    engine.activate_strategy("MeanReversion")
    
    print(f"Strategy engine initialized with {len(engine.active_strategies)} active strategies")