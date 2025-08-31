# base_strategy.py
"""
Base Strategy Class

All trading strategies inherit from this base class to ensure consistency
and proper risk management across different approaches.
"""

import pandas as pd
import pandas_ta as ta
import numpy as np
from abc import ABC, abstractmethod

class BaseStrategy(ABC):
    """Base class for all trading strategies"""
    
    def __init__(self, name: str, description: str, risk_level: str = "medium"):
        self.name = name
        self.description = description
        self.risk_level = risk_level  # low, medium, high
        self.min_candles = 50  # Minimum candles needed
        
    @abstractmethod
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators for the strategy"""
        pass
    
    @abstractmethod
    def generate_signal(self, df: pd.DataFrame) -> str:
        """Generate BUY, SELL, or HOLD signal"""
        pass
    
    @abstractmethod
    def get_signal_strength(self, df: pd.DataFrame) -> int:
        """Get signal strength (0-10)"""
        pass
    
    def get_strategy_info(self) -> dict:
        """Get strategy information"""
        return {
            'name': self.name,
            'description': self.description,
            'risk_level': self.risk_level,
            'min_candles': self.min_candles
        }
    
    def validate_data(self, df: pd.DataFrame) -> bool:
        """Validate if we have enough data"""
        return len(df) >= self.min_candles
    
    def get_risk_multiplier(self) -> float:
        """Get risk multiplier based on strategy risk level"""
        multipliers = {
            'low': 0.5,
            'medium': 1.0,
            'high': 1.5
        }
        return multipliers.get(self.risk_level, 1.0)
