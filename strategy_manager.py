# strategy_manager.py
"""
Strategy Manager

Manages multiple trading strategies and handles portfolio allocation across them.
Ensures proper risk distribution and prevents over-allocation.
"""

from typing import Dict, List, Tuple, Optional
import pandas as pd
from strategies.conservative_strategy import ConservativeStrategy
from strategies.aggressive_strategy import AggressiveStrategy
from strategies.momentum_strategy import MomentumStrategy
from database import get_database

class StrategyManager:
    """Manages multiple trading strategies with portfolio allocation"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.db = get_database()
        
        # Initialize strategies
        self.strategies = {
            'conservative': ConservativeStrategy(),
            'aggressive': AggressiveStrategy(),
            'momentum': MomentumStrategy()
        }
        
        # Default portfolio allocation (can be customized)
        self.portfolio_allocation = {
            'conservative': 0.5,  # 50% conservative
            'momentum': 0.3,      # 30% momentum
            'aggressive': 0.2     # 20% aggressive
        }
        
        # Risk limits per strategy
        self.max_positions_per_strategy = {
            'conservative': 3,
            'momentum': 2,
            'aggressive': 1
        }
        
        self.total_max_positions = 5  # Maximum total open positions

    def get_available_strategies(self) -> Dict[str, Dict]:
        """Get information about all available strategies"""
        strategy_info = {}
        for name, strategy in self.strategies.items():
            info = strategy.get_strategy_info()
            info['allocation'] = self.portfolio_allocation.get(name, 0)
            info['max_positions'] = self.max_positions_per_strategy.get(name, 1)
            strategy_info[name] = info
        return strategy_info

    def analyze_all_strategies(self, df: pd.DataFrame, symbol: str) -> Dict[str, Dict]:
        """Analyze all strategies for the given data"""
        results = {}
        
        for name, strategy in self.strategies.items():
            try:
                # Validate data first
                if not strategy.validate_data(df):
                    results[name] = {
                        'signal': 'HOLD',
                        'strength': 0,
                        'risk_level': strategy.risk_level,
                        'allocation': 0,
                        'can_trade': False,
                        'error': 'Insufficient data'
                    }
                    continue
                
                # Calculate indicators for this strategy
                df_with_indicators = strategy.calculate_indicators(df.copy())
                
                # Ensure ATR is calculated
                if 'ATR' not in df_with_indicators.columns:
                    # Add a fallback ATR calculation
                    df_with_indicators['ATR'] = (df_with_indicators['high'] - df_with_indicators['low']).rolling(14).mean()
                
                # Generate signal and strength
                signal = strategy.generate_signal(df_with_indicators)
                strength = strategy.get_signal_strength(df_with_indicators)
                
                results[name] = {
                    'signal': signal,
                    'strength': strength,
                    'risk_level': strategy.risk_level,
                    'allocation': self.portfolio_allocation.get(name, 0),
                    'can_trade': self._can_strategy_trade(name, symbol)
                }
                
            except Exception as e:
                # Only print error in debug mode, not in normal operation
                # print(f"❌ Error analyzing {name} strategy: {e}")
                results[name] = {
                    'signal': 'HOLD',
                    'strength': 0,
                    'risk_level': strategy.risk_level if hasattr(strategy, 'risk_level') else 'unknown',
                    'allocation': 0,
                    'can_trade': False,
                    'error': str(e)
                }
        
        return results

    def get_best_signal(self, df: pd.DataFrame, symbol: str) -> Tuple[str, str, int, float]:
        """Get the best trading signal from all strategies"""
        strategy_results = self.analyze_all_strategies(df, symbol)
        
        best_strategy = None
        best_signal = 'HOLD'
        best_strength = 0
        best_allocation = 0
        
        # Find the strongest signal from strategies that can trade
        for name, result in strategy_results.items():
            if (result['can_trade'] and 
                result['signal'] != 'HOLD' and 
                result['strength'] > best_strength):
                
                best_strategy = name
                best_signal = result['signal']
                best_strength = result['strength']
                best_allocation = result['allocation']
        
        return best_strategy or 'none', best_signal, best_strength, best_allocation

    def _can_strategy_trade(self, strategy_name: str, symbol: str) -> bool:
        """Check if a strategy can open new positions"""
        # Check current open positions for this strategy
        open_orders = self.db.get_user_orders(self.user_id, status='filled')
        
        # Count positions by strategy
        strategy_positions = sum(1 for order in open_orders 
                               if order.get('strategy') == strategy_name)
        
        # Check strategy-specific limits
        max_for_strategy = self.max_positions_per_strategy.get(strategy_name, 1)
        if strategy_positions >= max_for_strategy:
            return False
        
        # Check total position limit
        total_positions = len(open_orders)
        if total_positions >= self.total_max_positions:
            return False
        
        return True

    def calculate_position_size(self, strategy_name: str, balance: float, 
                              entry_price: float, stop_loss_price: float) -> float:
        """Calculate position size based on strategy allocation"""
        if strategy_name not in self.strategies:
            return 0
        
        strategy = self.strategies[strategy_name]
        allocation = self.portfolio_allocation.get(strategy_name, 0)
        risk_multiplier = strategy.get_risk_multiplier()
        
        # Base position size calculation
        allocated_capital = balance * allocation
        risk_per_trade = 0.01  # 1% base risk
        
        # Adjust risk based on strategy
        adjusted_risk = risk_per_trade * risk_multiplier
        
        # Calculate position size
        risk_amount = allocated_capital * adjusted_risk
        price_difference = abs(entry_price - stop_loss_price)
        
        if price_difference == 0:
            return 0
        
        position_size = risk_amount / price_difference
        
        # Ensure we don't exceed allocation limits
        max_position_value = allocated_capital * 0.2  # Max 20% of allocated capital per trade
        max_position_size = max_position_value / entry_price
        
        return min(position_size, max_position_size)

    def update_portfolio_allocation(self, new_allocation: Dict[str, float]):
        """Update portfolio allocation across strategies"""
        # Validate allocation sums to 1.0
        total_allocation = sum(new_allocation.values())
        if abs(total_allocation - 1.0) > 0.01:
            raise ValueError(f"Portfolio allocation must sum to 1.0, got {total_allocation}")
        
        # Validate all strategies exist
        for strategy_name in new_allocation:
            if strategy_name not in self.strategies:
                raise ValueError(f"Unknown strategy: {strategy_name}")
        
        self.portfolio_allocation = new_allocation.copy()
        print(f"✅ Updated portfolio allocation: {self.portfolio_allocation}")

    def get_portfolio_status(self) -> Dict:
        """Get current portfolio status across all strategies"""
        open_orders = self.db.get_user_orders(self.user_id, status='filled')
        current_balance = self.db.get_current_balance(self.user_id)
        
        # Group positions by strategy
        strategy_positions = {}
        total_exposure = 0
        
        for order in open_orders:
            strategy = order.get('strategy', 'unknown')
            if strategy not in strategy_positions:
                strategy_positions[strategy] = {
                    'count': 0,
                    'total_value': 0,
                    'symbols': []
                }
            
            strategy_positions[strategy]['count'] += 1
            strategy_positions[strategy]['total_value'] += order['amount'] * order['price']
            strategy_positions[strategy]['symbols'].append(order['symbol'])
            total_exposure += order['amount'] * order['price']
        
        return {
            'current_balance': current_balance,
            'total_exposure': total_exposure,
            'exposure_ratio': total_exposure / current_balance if current_balance > 0 else 0,
            'strategy_positions': strategy_positions,
            'total_positions': len(open_orders),
            'max_positions': self.total_max_positions,
            'can_open_new': len(open_orders) < self.total_max_positions
        }

    def get_strategy_performance(self) -> Dict:
        """Get performance statistics for all strategies"""
        return self.db.get_strategy_performance()

    def log_trade_result(self, strategy_name: str, symbol: str, signal: str, 
                        signal_strength: int, success: bool):
        """Log trade result for strategy performance tracking"""
        self.db.log_strategy_performance(strategy_name, symbol, signal, signal_strength, success)

    def rebalance_portfolio(self, current_balance: float) -> Dict[str, float]:
        """Calculate how much capital each strategy should have"""
        rebalanced = {}
        
        for strategy_name, allocation in self.portfolio_allocation.items():
            allocated_amount = current_balance * allocation
            rebalanced[strategy_name] = allocated_amount
        
        return rebalanced

    def get_recommended_pairs(self) -> List[Dict[str, str]]:
        """Get recommended trading pairs based on strategy preferences"""
        # Conservative pairs (major cryptocurrencies)
        conservative_pairs = [
            {'symbol': 'BTC/USDT', 'description': 'Bitcoin - Most stable crypto'},
            {'symbol': 'ETH/USDT', 'description': 'Ethereum - Second largest crypto'},
            {'symbol': 'BNB/USDT', 'description': 'Binance Coin - Exchange token'},
        ]
        
        # Momentum pairs (trending altcoins)
        momentum_pairs = [
            {'symbol': 'ADA/USDT', 'description': 'Cardano - Smart contract platform'},
            {'symbol': 'SOL/USDT', 'description': 'Solana - High-speed blockchain'},
            {'symbol': 'MATIC/USDT', 'description': 'Polygon - Ethereum scaling'},
            {'symbol': 'DOT/USDT', 'description': 'Polkadot - Interoperability'},
        ]
        
        # Aggressive pairs (volatile altcoins)
        aggressive_pairs = [
            {'symbol': 'LINK/USDT', 'description': 'Chainlink - Oracle network'},
            {'symbol': 'UNI/USDT', 'description': 'Uniswap - DEX token'},
            {'symbol': 'AAVE/USDT', 'description': 'Aave - DeFi lending'},
            {'symbol': 'SUSHI/USDT', 'description': 'SushiSwap - DEX platform'},
        ]
        
        return {
            'conservative': conservative_pairs,
            'momentum': momentum_pairs,
            'aggressive': aggressive_pairs,
            'all': conservative_pairs + momentum_pairs + aggressive_pairs
        }
