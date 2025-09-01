from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from .database_schema import TradingDatabase
import math

class RiskManager:
    """Comprehensive risk management system for trading bot"""
    
    def __init__(self, database: TradingDatabase, config: Dict[str, Any]):
        self.database = database
        self.config = config
        self.max_daily_loss = config.get('max_daily_loss_pct', 5.0)  # 5%
        self.max_position_size = config.get('max_position_size', 0.1)  # 10%
        self.max_open_positions = config.get('max_open_positions', 3)
        self.risk_per_trade = config.get('risk_per_trade', 0.02)  # 2%
        self.stop_loss_pct = config.get('stop_loss_pct', 3.0)  # 3%
        self.take_profit_pct = config.get('take_profit_pct', 6.0)  # 6%
        self.min_reward_risk_ratio = config.get('min_reward_risk_ratio', 2.0)
        
    def calculate_position_size(self, 
                              symbol: str, 
                              entry_price: float, 
                              stop_loss_price: float, 
                              account_balance: float) -> Dict[str, Any]:
        """Calculate optimal position size based on risk management"""
        
        if entry_price <= 0 or stop_loss_price <= 0 or account_balance <= 0:
            return {'allowed': False, 'reason': 'Invalid price or balance data'}
        
        # Calculate risk per share
        risk_per_share = abs(entry_price - stop_loss_price)
        risk_per_share_pct = (risk_per_share / entry_price) * 100
        
        # Maximum amount to risk on this trade
        max_risk_amount = account_balance * (self.risk_per_trade / 100)
        
        # Calculate position size based on risk
        position_size_risk_based = max_risk_amount / risk_per_share
        
        # Calculate position size based on max position limit
        max_position_value = account_balance * (self.max_position_size / 100)
        position_size_max_based = max_position_value / entry_price
        
        # Take the smaller of the two
        recommended_position_size = min(position_size_risk_based, position_size_max_based)
        
        # Calculate position value and risk metrics
        position_value = recommended_position_size * entry_price
        total_risk = recommended_position_size * risk_per_share
        risk_pct = (total_risk / account_balance) * 100
        
        return {
            'allowed': True,
            'position_size': recommended_position_size,
            'position_value': position_value,
            'risk_amount': total_risk,
            'risk_percentage': risk_pct,
            'risk_per_share': risk_per_share,
            'risk_per_share_pct': risk_per_share_pct,
            'stop_loss_price': stop_loss_price,
            'reward_risk_ratio': self._calculate_reward_risk_ratio(entry_price, stop_loss_price)
        }
    
    def validate_trade(self, 
                      symbol: str, 
                      signal_data: Dict[str, Any], 
                      account_balance: float) -> Dict[str, Any]:
        """Validate if trade meets risk management criteria"""
        
        validation_result = {
            'allowed': True,
            'warnings': [],
            'blocking_issues': [],
            'risk_metrics': {}
        }
        
        # Check daily loss limit
        daily_pnl = self._get_daily_pnl()
        daily_loss_pct = abs(daily_pnl) / account_balance * 100 if daily_pnl < 0 else 0
        
        if daily_loss_pct >= self.max_daily_loss:
            validation_result['allowed'] = False
            validation_result['blocking_issues'].append(
                f"Daily loss limit exceeded: {daily_loss_pct:.2f}% >= {self.max_daily_loss}%"
            )
        
        # Check maximum open positions
        open_positions = self._count_open_positions()
        if open_positions >= self.max_open_positions:
            validation_result['allowed'] = False
            validation_result['blocking_issues'].append(
                f"Maximum open positions reached: {open_positions}/{self.max_open_positions}"
            )
        
        # Check signal confidence
        min_confidence = self.config.get('min_signal_confidence', 0.6)
        if signal_data.get('confidence', 0) < min_confidence:
            validation_result['allowed'] = False
            validation_result['blocking_issues'].append(
                f"Signal confidence too low: {signal_data.get('confidence', 0):.2f} < {min_confidence}"
            )
        
        # Calculate position sizing
        entry_price = signal_data.get('price', 0)
        stop_loss_price = self._calculate_stop_loss_price(entry_price, signal_data.get('signal', 'HOLD'))
        
        position_calc = self.calculate_position_size(symbol, entry_price, stop_loss_price, account_balance)
        
        if not position_calc['allowed']:
            validation_result['allowed'] = False
            validation_result['blocking_issues'].append(position_calc['reason'])
        else:
            validation_result['risk_metrics'] = position_calc
            
            # Check reward-to-risk ratio
            if position_calc['reward_risk_ratio'] < self.min_reward_risk_ratio:
                validation_result['warnings'].append(
                    f"Low reward-to-risk ratio: {position_calc['reward_risk_ratio']:.2f} < {self.min_reward_risk_ratio}"
                )
        
        # Check market volatility
        volatility_check = self._check_market_volatility(symbol)
        if volatility_check['high_volatility']:
            validation_result['warnings'].append(
                f"High market volatility detected: {volatility_check['atr_pct']:.2f}%"
            )
        
        return validation_result
    
    def calculate_stop_loss_take_profit(self, 
                                      entry_price: float, 
                                      signal: str, 
                                      atr: Optional[float] = None) -> Dict[str, float]:
        """Calculate stop loss and take profit levels"""
        
        if signal == 'BUY':
            if atr and atr > 0:
                # Use ATR-based stop loss (more dynamic)
                stop_loss = entry_price - (atr * self.config.get('atr_multiplier', 2.0))
                take_profit = entry_price + (atr * self.config.get('atr_multiplier', 2.0) * self.min_reward_risk_ratio)
            else:
                # Use percentage-based stop loss
                stop_loss = entry_price * (1 - self.stop_loss_pct / 100)
                take_profit = entry_price * (1 + self.take_profit_pct / 100)
        
        elif signal == 'SELL':
            if atr and atr > 0:
                stop_loss = entry_price + (atr * self.config.get('atr_multiplier', 2.0))
                take_profit = entry_price - (atr * self.config.get('atr_multiplier', 2.0) * self.min_reward_risk_ratio)
            else:
                stop_loss = entry_price * (1 + self.stop_loss_pct / 100)
                take_profit = entry_price * (1 - self.take_profit_pct / 100)
        else:
            return {'stop_loss': 0, 'take_profit': 0}
        
        return {
            'stop_loss': round(stop_loss, 8),
            'take_profit': round(take_profit, 8)
        }
    
    def update_position_risk(self, 
                           position_id: str, 
                           current_price: float, 
                           unrealized_pnl: float) -> Dict[str, Any]:
        """Update position risk metrics and suggest actions"""
        
        # Get position details from database
        position = self._get_position_details(position_id)
        if not position:
            return {'error': 'Position not found'}
        
        entry_price = position.get('entry_price', 0)
        stop_loss = position.get('stop_loss', 0)
        take_profit = position.get('take_profit', 0)
        
        # Calculate current risk metrics
        if entry_price > 0:
            unrealized_pnl_pct = (unrealized_pnl / (position.get('position_value', 1))) * 100
            
            # Trailing stop loss logic
            if position.get('side') == 'BUY':
                # For long positions, adjust stop loss upward
                price_move_pct = ((current_price - entry_price) / entry_price) * 100
                if price_move_pct > 5:  # If price moved up 5%
                    new_stop_loss = max(stop_loss, current_price * (1 - self.stop_loss_pct / 100))
                else:
                    new_stop_loss = stop_loss
            else:
                # For short positions, adjust stop loss downward
                price_move_pct = ((entry_price - current_price) / entry_price) * 100
                if price_move_pct > 5:
                    new_stop_loss = min(stop_loss, current_price * (1 + self.stop_loss_pct / 100))
                else:
                    new_stop_loss = stop_loss
            
            suggestions = []
            if new_stop_loss != stop_loss:
                suggestions.append(f"Update trailing stop loss to {new_stop_loss:.8f}")
            
            # Risk level assessment
            if unrealized_pnl_pct < -2:
                risk_level = 'HIGH'
                suggestions.append("Consider reducing position size or closing position")
            elif unrealized_pnl_pct > 3:
                risk_level = 'LOW'
                suggestions.append("Consider taking partial profits")
            else:
                risk_level = 'MEDIUM'
            
            return {
                'position_id': position_id,
                'current_price': current_price,
                'unrealized_pnl': unrealized_pnl,
                'unrealized_pnl_pct': unrealized_pnl_pct,
                'risk_level': risk_level,
                'new_stop_loss': new_stop_loss,
                'suggestions': suggestions
            }
    
    def get_risk_report(self, account_balance: float) -> Dict[str, Any]:
        """Generate comprehensive risk report"""
        
        # Daily P&L
        daily_pnl = self._get_daily_pnl()
        daily_pnl_pct = (daily_pnl / account_balance) * 100
        
        # Weekly P&L
        weekly_pnl = self._get_weekly_pnl()
        weekly_pnl_pct = (weekly_pnl / account_balance) * 100
        
        # Open positions analysis
        open_positions = self._get_open_positions_analysis()
        
        # Risk utilization
        total_risk_amount = sum([pos.get('risk_amount', 0) for pos in open_positions])
        risk_utilization_pct = (total_risk_amount / account_balance) * 100
        
        # Win rate calculation
        win_rate_data = self._calculate_win_rate()
        
        return {
            'timestamp': datetime.utcnow(),
            'account_balance': account_balance,
            'daily_pnl': {
                'amount': daily_pnl,
                'percentage': daily_pnl_pct,
                'limit': self.max_daily_loss,
                'status': 'OK' if abs(daily_pnl_pct) < self.max_daily_loss else 'WARNING'
            },
            'weekly_pnl': {
                'amount': weekly_pnl,
                'percentage': weekly_pnl_pct
            },
            'risk_utilization': {
                'amount': total_risk_amount,
                'percentage': risk_utilization_pct,
                'limit': self.risk_per_trade * self.max_open_positions * 100,
                'status': 'OK' if risk_utilization_pct < 10 else 'WARNING'
            },
            'open_positions': {
                'count': len(open_positions),
                'limit': self.max_open_positions,
                'details': open_positions
            },
            'performance': win_rate_data,
            'risk_limits': {
                'max_daily_loss_pct': self.max_daily_loss,
                'max_position_size_pct': self.max_position_size * 100,
                'risk_per_trade_pct': self.risk_per_trade * 100,
                'max_open_positions': self.max_open_positions
            }
        }
    
    def _calculate_stop_loss_price(self, entry_price: float, signal: str) -> float:
        """Calculate stop loss price"""
        if signal == 'BUY':
            return entry_price * (1 - self.stop_loss_pct / 100)
        elif signal == 'SELL':
            return entry_price * (1 + self.stop_loss_pct / 100)
        return entry_price
    
    def _calculate_reward_risk_ratio(self, entry_price: float, stop_loss_price: float) -> float:
        """Calculate reward to risk ratio"""
        risk = abs(entry_price - stop_loss_price)
        reward = risk * self.min_reward_risk_ratio
        return reward / risk if risk > 0 else 0
    
    def _get_daily_pnl(self) -> float:
        """Get today's P&L"""
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        pipeline = [
            {"$match": {
                "timestamp": {"$gte": today},
                "status": "FILLED"
            }},
            {"$group": {
                "_id": None,
                "total_pnl": {"$sum": "$pnl"}
            }}
        ]
        
        result = list(self.database.trades.aggregate(pipeline))
        return result[0]['total_pnl'] if result else 0.0
    
    def _get_weekly_pnl(self) -> float:
        """Get this week's P&L"""
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        pipeline = [
            {"$match": {
                "timestamp": {"$gte": week_ago},
                "status": "FILLED"
            }},
            {"$group": {
                "_id": None,
                "total_pnl": {"$sum": "$pnl"}
            }}
        ]
        
        result = list(self.database.trades.aggregate(pipeline))
        return result[0]['total_pnl'] if result else 0.0
    
    def _count_open_positions(self) -> int:
        """Count currently open positions"""
        open_positions = self.database.trades.count_documents({
            "status": "FILLED",
            "side": "BUY"  # Simplified - in real implementation, track position status
        })
        return open_positions
    
    def _get_open_positions_analysis(self) -> list:
        """Get detailed analysis of open positions"""
        # Simplified implementation - in real system, track position details
        return []
    
    def _get_position_details(self, position_id: str) -> Dict[str, Any]:
        """Get position details from database"""
        return {}
    
    def _check_market_volatility(self, symbol: str) -> Dict[str, Any]:
        """Check if market volatility is unusually high"""
        
        # Get recent ATR data from indicators
        recent_indicators = list(self.database.indicators.find({
            "symbol": symbol
        }).sort("timestamp", -1).limit(20))
        
        if not recent_indicators:
            return {'high_volatility': False, 'atr_pct': 0}
        
        # Get average ATR
        atr_values = [ind['indicators'].get('atr', 0) for ind in recent_indicators if 'atr' in ind.get('indicators', {})]
        
        if not atr_values:
            return {'high_volatility': False, 'atr_pct': 0}
        
        avg_atr = sum(atr_values) / len(atr_values)
        
        # Get current price for percentage calculation
        current_price = recent_indicators[0]['indicators'].get('current_price', 1)
        atr_pct = (avg_atr / current_price) * 100 if current_price > 0 else 0
        
        # Consider high volatility if ATR > 3% of price
        high_volatility = atr_pct > 3.0
        
        return {
            'high_volatility': high_volatility,
            'atr_pct': atr_pct,
            'avg_atr': avg_atr
        }
    
    def _calculate_win_rate(self) -> Dict[str, Any]:
        """Calculate win rate and other performance metrics"""
        
        # Get last 30 days of closed trades
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        pipeline = [
            {"$match": {
                "timestamp": {"$gte": thirty_days_ago},
                "status": "FILLED"
            }},
            {"$group": {
                "_id": None,
                "total_trades": {"$sum": 1},
                "winning_trades": {"$sum": {"$cond": [{"$gt": ["$pnl", 0]}, 1, 0]}},
                "losing_trades": {"$sum": {"$cond": [{"$lt": ["$pnl", 0]}, 1, 0]}},
                "total_pnl": {"$sum": "$pnl"},
                "avg_win": {"$avg": {"$cond": [{"$gt": ["$pnl", 0]}, "$pnl", None]}},
                "avg_loss": {"$avg": {"$cond": [{"$lt": ["$pnl", 0]}, "$pnl", None]}}
            }}
        ]
        
        result = list(self.database.trades.aggregate(pipeline))
        
        if not result:
            return {
                'win_rate': 0,
                'total_trades': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'profit_factor': 0
            }
        
        data = result[0]
        win_rate = (data['winning_trades'] / data['total_trades']) * 100 if data['total_trades'] > 0 else 0
        
        avg_win = data.get('avg_win', 0) or 0
        avg_loss = abs(data.get('avg_loss', 0)) if data.get('avg_loss') else 0
        
        profit_factor = avg_win / avg_loss if avg_loss > 0 else 0
        
        return {
            'win_rate': win_rate,
            'total_trades': data['total_trades'],
            'winning_trades': data['winning_trades'],
            'losing_trades': data['losing_trades'],
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'total_pnl': data['total_pnl']
        }

if __name__ == "__main__":
    # Example usage
    import config
    from .database_schema import TradingDatabase
    
    db = TradingDatabase()
    risk_manager = RiskManager(db, config.STRATEGY_CONFIG)
    
    # Example risk report
    risk_report = risk_manager.get_risk_report(1000.0)
    print("Risk Management initialized successfully!")
    print(f"Daily P&L status: {risk_report['daily_pnl']['status']}")
    print(f"Risk utilization: {risk_report['risk_utilization']['percentage']:.2f}%")