# risk_manager.py
import numpy as np
from config import TRADING_CONFIG, STRATEGY_CONFIG

class AdvancedRiskManager:
    """
    Advanced Risk Management System
    
    This class implements sophisticated risk management techniques including:
    - Dynamic position sizing based on volatility
    - Multiple stop-loss methods
    - Portfolio heat management
    - Risk-adjusted position sizing
    """
    
    def __init__(self):
        self.max_portfolio_risk = TRADING_CONFIG.get('risk_per_trade', 0.01)
        self.max_position_size = STRATEGY_CONFIG.get('max_position_size', 0.1)
        self.atr_multiplier = STRATEGY_CONFIG.get('atr_multiplier', 2.0)
        self.capital_allocation = TRADING_CONFIG.get('capital_allocation', 0.1)
        
        # Track open positions for portfolio heat calculation
        self.open_positions = []
        self.total_portfolio_risk = 0.0

    def calculate_position_size(self, balance, entry_price, stop_loss_price, signal_strength=5, volatility_factor=1.0):
        """
        Calculate position size using multiple methods and return the most conservative
        
        Args:
            balance: Available trading balance
            entry_price: Entry price for the trade
            stop_loss_price: Stop loss price
            signal_strength: Signal strength (0-10)
            volatility_factor: Current market volatility factor
        """
        if entry_price == stop_loss_price or entry_price <= 0 or stop_loss_price <= 0:
            return 0
        
        # Method 1: Fixed Risk Position Sizing
        fixed_risk_size = self._calculate_fixed_risk_size(balance, entry_price, stop_loss_price)
        
        # Method 2: Volatility-Adjusted Position Sizing
        volatility_adjusted_size = self._calculate_volatility_adjusted_size(
            balance, entry_price, stop_loss_price, volatility_factor
        )
        
        # Method 3: Signal Strength Adjusted Position Sizing
        signal_adjusted_size = self._calculate_signal_adjusted_size(
            balance, entry_price, stop_loss_price, signal_strength
        )
        
        # Method 4: Portfolio Heat Adjusted Position Sizing
        portfolio_adjusted_size = self._calculate_portfolio_heat_adjusted_size(
            balance, entry_price, stop_loss_price
        )
        
        # Take the most conservative (smallest) position size
        position_sizes = [
            fixed_risk_size,
            volatility_adjusted_size,
            signal_adjusted_size,
            portfolio_adjusted_size
        ]
        
        final_position_size = min([size for size in position_sizes if size > 0])
        
        # Apply maximum position size limit
        max_allowed_size = balance * self.max_position_size / entry_price
        final_position_size = min(final_position_size, max_allowed_size)
        
        return max(0, final_position_size)
    
    def _calculate_fixed_risk_size(self, balance, entry_price, stop_loss_price):
        """Traditional fixed risk position sizing"""
        capital = balance * self.capital_allocation
        risk_amount = capital * self.max_portfolio_risk
        risk_per_unit = abs(entry_price - stop_loss_price)
        return risk_amount / risk_per_unit
    
    def _calculate_volatility_adjusted_size(self, balance, entry_price, stop_loss_price, volatility_factor):
        """Adjust position size based on market volatility"""
        base_size = self._calculate_fixed_risk_size(balance, entry_price, stop_loss_price)
        
        # Reduce position size in high volatility markets
        volatility_adjustment = 1.0 / max(volatility_factor, 0.5)
        return base_size * volatility_adjustment
    
    def _calculate_signal_adjusted_size(self, balance, entry_price, stop_loss_price, signal_strength):
        """Adjust position size based on signal strength"""
        base_size = self._calculate_fixed_risk_size(balance, entry_price, stop_loss_price)
        
        # Scale position size based on signal strength (0-10)
        strength_factor = signal_strength / 10.0
        return base_size * strength_factor
    
    def _calculate_portfolio_heat_adjusted_size(self, balance, entry_price, stop_loss_price):
        """Adjust position size based on current portfolio heat"""
        base_size = self._calculate_fixed_risk_size(balance, entry_price, stop_loss_price)
        
        # Calculate current portfolio risk
        current_risk = self.total_portfolio_risk
        max_total_risk = 0.05  # Maximum 5% total portfolio risk
        
        if current_risk >= max_total_risk:
            return 0  # Don't take new positions if portfolio risk is too high
        
        # Reduce position size as portfolio heat increases
        remaining_risk_capacity = max_total_risk - current_risk
        risk_adjustment = min(1.0, remaining_risk_capacity / self.max_portfolio_risk)
        
        return base_size * risk_adjustment

    def determine_stop_loss(self, entry_price, side, atr_value, df=None, method='atr'):
        """
        Determine stop loss using multiple methods
        
        Args:
            entry_price: Entry price
            side: 'buy' or 'sell'
            atr_value: Current ATR value
            df: Price dataframe for additional calculations
            method: Stop loss method ('atr', 'support_resistance', 'percentage', 'adaptive')
        """
        if method == 'atr':
            return self._atr_stop_loss(entry_price, side, atr_value)
        elif method == 'support_resistance' and df is not None:
            return self._support_resistance_stop_loss(entry_price, side, df)
        elif method == 'percentage':
            return self._percentage_stop_loss(entry_price, side)
        elif method == 'adaptive' and df is not None:
            return self._adaptive_stop_loss(entry_price, side, atr_value, df)
        else:
            return self._atr_stop_loss(entry_price, side, atr_value)
    
    def _atr_stop_loss(self, entry_price, side, atr_value):
        """ATR-based stop loss"""
        atr_offset = atr_value * self.atr_multiplier
        if side == 'buy':
            return entry_price - atr_offset
        elif side == 'sell':
            return entry_price + atr_offset
        return None
    
    def _support_resistance_stop_loss(self, entry_price, side, df):
        """Support/Resistance based stop loss"""
        if len(df) < 20:
            return self._atr_stop_loss(entry_price, side, df.iloc[-1]['ATR'])
        
        if side == 'buy':
            # Use recent support level
            support_level = df['Support'].iloc[-1]
            return min(support_level * 0.995, entry_price * 0.98)  # 0.5% below support or 2% below entry
        elif side == 'sell':
            # Use recent resistance level
            resistance_level = df['Resistance'].iloc[-1]
            return max(resistance_level * 1.005, entry_price * 1.02)  # 0.5% above resistance or 2% above entry
        return None
    
    def _percentage_stop_loss(self, entry_price, side, percentage=0.02):
        """Fixed percentage stop loss"""
        if side == 'buy':
            return entry_price * (1 - percentage)
        elif side == 'sell':
            return entry_price * (1 + percentage)
        return None
    
    def _adaptive_stop_loss(self, entry_price, side, atr_value, df):
        """Adaptive stop loss combining multiple methods"""
        atr_stop = self._atr_stop_loss(entry_price, side, atr_value)
        sr_stop = self._support_resistance_stop_loss(entry_price, side, df)
        pct_stop = self._percentage_stop_loss(entry_price, side)
        
        if side == 'buy':
            # Use the highest (least aggressive) stop loss for long positions
            stops = [stop for stop in [atr_stop, sr_stop, pct_stop] if stop is not None]
            return max(stops) if stops else None
        elif side == 'sell':
            # Use the lowest (least aggressive) stop loss for short positions
            stops = [stop for stop in [atr_stop, sr_stop, pct_stop] if stop is not None]
            return min(stops) if stops else None
        return None

    def calculate_take_profit(self, entry_price, stop_loss_price, side, risk_reward_ratio=2.0):
        """
        Calculate take profit level based on risk-reward ratio
        
        Args:
            entry_price: Entry price
            stop_loss_price: Stop loss price
            side: 'buy' or 'sell'
            risk_reward_ratio: Desired risk-reward ratio
        """
        if stop_loss_price is None:
            return None
        
        risk_amount = abs(entry_price - stop_loss_price)
        reward_amount = risk_amount * risk_reward_ratio
        
        if side == 'buy':
            return entry_price + reward_amount
        elif side == 'sell':
            return entry_price - reward_amount
        return None

    def should_take_trade(self, signal_strength, volatility_factor, portfolio_heat):
        """
        Determine if a trade should be taken based on risk factors
        
        Args:
            signal_strength: Signal strength (0-10)
            volatility_factor: Current volatility factor
            portfolio_heat: Current portfolio risk level
        """
        min_signal_strength = STRATEGY_CONFIG.get('min_signal_strength', 5)
        max_volatility = 2.0
        max_portfolio_heat = 0.05
        
        # Check minimum signal strength
        if signal_strength < min_signal_strength:
            return False, "Signal strength too low"
        
        # Check volatility
        if volatility_factor > max_volatility:
            return False, "Market volatility too high"
        
        # Check portfolio heat
        if portfolio_heat > max_portfolio_heat:
            return False, "Portfolio risk too high"
        
        return True, "Trade approved"

    def update_portfolio_risk(self, position_risk):
        """Update total portfolio risk when opening a position"""
        self.total_portfolio_risk += position_risk
    
    def remove_portfolio_risk(self, position_risk):
        """Remove position risk when closing a position"""
        self.total_portfolio_risk = max(0, self.total_portfolio_risk - position_risk)

    def get_portfolio_metrics(self):
        """Get current portfolio risk metrics"""
        return {
            'total_portfolio_risk': self.total_portfolio_risk,
            'open_positions': len(self.open_positions),
            'risk_utilization': self.total_portfolio_risk / 0.05,  # Percentage of max risk used
        }

# Maintain backward compatibility
RiskManager = AdvancedRiskManager