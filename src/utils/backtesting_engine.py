import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import matplotlib.pyplot as plt
import seaborn as sns
from indicators.technical_indicators_simple import TechnicalIndicators
from strategies.strategy_engine import BaseStrategy, StrategyEngine
from core.risk_management import RiskManager
from core.database_schema import TradingDatabase
import warnings
warnings.filterwarnings('ignore')

@dataclass
class BacktestTrade:
    """Represents a single trade in backtesting"""
    entry_time: datetime
    exit_time: Optional[datetime]
    symbol: str
    side: str  # 'BUY' or 'SELL'
    entry_price: float
    exit_price: Optional[float]
    quantity: float
    stop_loss: float
    take_profit: float
    pnl: Optional[float]
    pnl_pct: Optional[float]
    strategy: str
    status: str  # 'OPEN', 'CLOSED', 'STOPPED'
    exit_reason: str  # 'TAKE_PROFIT', 'STOP_LOSS', 'SIGNAL', 'END_OF_DATA'

@dataclass
class BacktestMetrics:
    """Comprehensive backtesting results"""
    total_return: float
    total_return_pct: float
    annual_return_pct: float
    max_drawdown: float
    max_drawdown_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    win_rate: float
    profit_factor: float
    avg_win: float
    avg_loss: float
    max_win: float
    max_loss: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_trade_duration: float
    avg_bars_in_trade: float
    consecutive_wins: int
    consecutive_losses: int
    recovery_factor: float
    payoff_ratio: float

class AdvancedBacktester:
    """Advanced backtesting engine with comprehensive analytics"""
    
    def __init__(self, initial_capital: float = 10000.0):
        self.initial_capital = initial_capital
        self.indicators_calculator = TechnicalIndicators()
        
        # Backtesting parameters
        self.commission = 0.001  # 0.1% per trade
        self.slippage = 0.0005   # 0.05% slippage
        
        # Results storage
        self.trades: List[BacktestTrade] = []
        self.equity_curve = []
        self.drawdown_curve = []
        self.daily_returns = []
        
    def run_backtest(self, 
                    strategy: BaseStrategy,
                    data: pd.DataFrame,
                    config: Dict[str, Any],
                    start_date: Optional[datetime] = None,
                    end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Run comprehensive backtest on historical data"""
        
        print(f"Starting backtest for strategy: {strategy.name}")
        
        # Filter data by date range if specified
        if start_date or end_date:
            data = self._filter_data_by_date(data, start_date, end_date)
        
        if len(data) < 100:
            raise ValueError("Insufficient data for backtesting (minimum 100 data points required)")
        
        # Initialize backtest state
        self._initialize_backtest(data)
        
        # Run simulation
        self._run_simulation(strategy, data, config)
        
        # Calculate metrics
        metrics = self._calculate_metrics(data)
        
        # Generate reports
        results = {
            'strategy_name': strategy.name,
            'backtest_period': {
                'start': data.index[0] if hasattr(data.index[0], 'strftime') else data.iloc[0]['timestamp'],
                'end': data.index[-1] if hasattr(data.index[-1], 'strftime') else data.iloc[-1]['timestamp'],
                'total_days': len(data)
            },
            'initial_capital': self.initial_capital,
            'final_capital': self.equity_curve[-1] if self.equity_curve else self.initial_capital,
            'metrics': metrics,
            'trades': [self._trade_to_dict(trade) for trade in self.trades],
            'equity_curve': self.equity_curve,
            'drawdown_curve': self.drawdown_curve,
            'daily_returns': self.daily_returns
        }
        
        print(f"Backtest completed: {len(self.trades)} trades, {metrics.total_return_pct:.2f}% return")
        
        return results
    
    def _initialize_backtest(self, data: pd.DataFrame):
        """Initialize backtest state"""
        self.trades = []
        self.equity_curve = [self.initial_capital]
        self.drawdown_curve = [0.0]
        self.daily_returns = []
        self.current_capital = self.initial_capital
        self.peak_capital = self.initial_capital
        self.open_positions = []
        
    def _run_simulation(self, strategy: BaseStrategy, data: pd.DataFrame, config: Dict[str, Any]):
        """Run the main simulation loop"""
        
        lookback_period = config.get('min_lookback_period', 50)
        
        for i in range(lookback_period, len(data)):
            current_time = data.index[i] if hasattr(data.index[i], 'strftime') else data.iloc[i]['timestamp']
            current_data = data.iloc[:i+1]
            current_price = float(data.iloc[i]['close'])
            
            # Calculate indicators for current window
            indicators = self.indicators_calculator.calculate_all_indicators(current_data, config)
            
            # Update open positions
            self._update_open_positions(current_time, current_price, data.iloc[i])
            
            # Generate new signals
            if len(current_data) >= lookback_period:
                signal_data = strategy.generate_signal(current_data, indicators)
                
                if signal_data['signal'] in ['BUY', 'SELL']:
                    self._process_signal(signal_data, current_time, current_price, indicators, config)
            
            # Update equity curve
            unrealized_pnl = self._calculate_unrealized_pnl(current_price)
            current_equity = self.current_capital + unrealized_pnl
            self.equity_curve.append(current_equity)
            
            # Update drawdown
            if current_equity > self.peak_capital:
                self.peak_capital = current_equity
            drawdown = (self.peak_capital - current_equity) / self.peak_capital
            self.drawdown_curve.append(drawdown)
            
            # Calculate daily returns
            if len(self.equity_curve) > 1:
                daily_return = (self.equity_curve[-1] - self.equity_curve[-2]) / self.equity_curve[-2]
                self.daily_returns.append(daily_return)
        
        # Close any remaining open positions
        self._close_all_positions(data.iloc[-1]['timestamp'], float(data.iloc[-1]['close']), 'END_OF_DATA')
    
    def _process_signal(self, 
                       signal_data: Dict[str, Any], 
                       current_time: datetime, 
                       current_price: float,
                       indicators: Dict[str, Any],
                       config: Dict[str, Any]):
        """Process a trading signal"""
        
        signal = signal_data['signal']
        confidence = signal_data.get('confidence', 0)
        
        # Simple position sizing (can be enhanced)
        max_position_size = config.get('max_position_size', 0.1)
        position_value = self.current_capital * max_position_size
        
        # Apply confidence-based sizing
        position_value *= confidence
        
        if position_value < 100:  # Minimum position size
            return
        
        # Calculate position size
        quantity = position_value / current_price
        
        # Apply commission and slippage
        effective_price = current_price * (1 + self.slippage) if signal == 'BUY' else current_price * (1 - self.slippage)
        commission_cost = position_value * self.commission
        
        # Check if we have enough capital
        total_cost = position_value + commission_cost
        if total_cost > self.current_capital:
            return  # Insufficient capital
        
        # Calculate stop loss and take profit
        atr = indicators.get('atr', current_price * 0.02)  # Default to 2% if no ATR
        
        if signal == 'BUY':
            stop_loss = current_price - (atr * config.get('atr_multiplier', 2.0))
            take_profit = current_price + (atr * config.get('atr_multiplier', 2.0) * config.get('reward_risk_ratio', 2.0))
        else:  # SELL
            stop_loss = current_price + (atr * config.get('atr_multiplier', 2.0))
            take_profit = current_price - (atr * config.get('atr_multiplier', 2.0) * config.get('reward_risk_ratio', 2.0))
        
        # Create trade
        trade = BacktestTrade(
            entry_time=current_time,
            exit_time=None,
            symbol=config.get('symbol', 'UNKNOWN'),
            side=signal,
            entry_price=effective_price,
            exit_price=None,
            quantity=quantity,
            stop_loss=stop_loss,
            take_profit=take_profit,
            pnl=None,
            pnl_pct=None,
            strategy=signal_data.get('strategy', 'Unknown'),
            status='OPEN',
            exit_reason=''
        )
        
        # Update capital
        self.current_capital -= total_cost
        
        # Add to open positions
        self.open_positions.append(trade)
        
    def _update_open_positions(self, current_time: datetime, current_price: float, current_bar: pd.Series):
        """Update all open positions and close if necessary"""
        
        positions_to_close = []
        
        for i, position in enumerate(self.open_positions):
            # Check stop loss and take profit
            should_close = False
            exit_reason = ''
            
            if position.side == 'BUY':
                if current_price <= position.stop_loss:
                    should_close = True
                    exit_reason = 'STOP_LOSS'
                elif current_price >= position.take_profit:
                    should_close = True
                    exit_reason = 'TAKE_PROFIT'
            else:  # SELL
                if current_price >= position.stop_loss:
                    should_close = True
                    exit_reason = 'STOP_LOSS'
                elif current_price <= position.take_profit:
                    should_close = True
                    exit_reason = 'TAKE_PROFIT'
            
            if should_close:
                positions_to_close.append((i, exit_reason))
        
        # Close positions (reverse order to maintain indices)
        for i, exit_reason in reversed(positions_to_close):
            self._close_position(i, current_time, current_price, exit_reason)
    
    def _close_position(self, position_index: int, exit_time: datetime, exit_price: float, exit_reason: str):
        """Close a specific position"""
        
        position = self.open_positions[position_index]
        
        # Apply slippage
        effective_exit_price = exit_price * (1 - self.slippage) if position.side == 'BUY' else exit_price * (1 + self.slippage)
        
        # Calculate P&L
        if position.side == 'BUY':
            pnl = (effective_exit_price - position.entry_price) * position.quantity
        else:  # SELL
            pnl = (position.entry_price - effective_exit_price) * position.quantity
        
        # Apply commission
        commission_cost = (position.quantity * effective_exit_price) * self.commission
        pnl -= commission_cost
        
        # Calculate percentage P&L
        pnl_pct = pnl / (position.entry_price * position.quantity) * 100
        
        # Update position
        position.exit_time = exit_time
        position.exit_price = effective_exit_price
        position.pnl = pnl
        position.pnl_pct = pnl_pct
        position.status = 'CLOSED'
        position.exit_reason = exit_reason
        
        # Update capital
        self.current_capital += (position.quantity * effective_exit_price) - commission_cost
        
        # Move to completed trades
        self.trades.append(position)
        
        # Remove from open positions
        del self.open_positions[position_index]
    
    def _close_all_positions(self, exit_time: datetime, exit_price: float, exit_reason: str):
        """Close all remaining open positions"""
        while self.open_positions:
            self._close_position(0, exit_time, exit_price, exit_reason)
    
    def _calculate_unrealized_pnl(self, current_price: float) -> float:
        """Calculate unrealized P&L for open positions"""
        unrealized_pnl = 0.0
        
        for position in self.open_positions:
            if position.side == 'BUY':
                pnl = (current_price - position.entry_price) * position.quantity
            else:  # SELL
                pnl = (position.entry_price - current_price) * position.quantity
            
            unrealized_pnl += pnl
        
        return unrealized_pnl
    
    def _calculate_metrics(self, data: pd.DataFrame) -> BacktestMetrics:
        """Calculate comprehensive backtest metrics"""
        
        if not self.trades:
            return self._empty_metrics()
        
        # Basic metrics
        total_return = self.equity_curve[-1] - self.initial_capital
        total_return_pct = (total_return / self.initial_capital) * 100
        
        # Time-based metrics
        days = len(data)
        years = days / 365.25
        annual_return_pct = ((self.equity_curve[-1] / self.initial_capital) ** (1/years) - 1) * 100 if years > 0 else 0
        
        # Drawdown metrics
        max_drawdown = max(self.drawdown_curve)
        max_drawdown_pct = max_drawdown * 100
        
        # Trade statistics
        winning_trades = [t for t in self.trades if t.pnl > 0]
        losing_trades = [t for t in self.trades if t.pnl < 0]
        
        win_rate = len(winning_trades) / len(self.trades) * 100 if self.trades else 0
        
        avg_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.pnl for t in losing_trades]) if losing_trades else 0
        max_win = max([t.pnl for t in winning_trades]) if winning_trades else 0
        max_loss = min([t.pnl for t in losing_trades]) if losing_trades else 0
        
        profit_factor = abs(sum([t.pnl for t in winning_trades])) / abs(sum([t.pnl for t in losing_trades])) if losing_trades else float('inf')
        payoff_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
        
        # Risk-adjusted metrics
        if self.daily_returns:
            daily_returns_array = np.array(self.daily_returns)
            sharpe_ratio = np.mean(daily_returns_array) / np.std(daily_returns_array) * np.sqrt(252) if np.std(daily_returns_array) != 0 else 0
            
            # Sortino ratio (downside deviation)
            downside_returns = [r for r in daily_returns_array if r < 0]
            downside_std = np.std(downside_returns) if downside_returns else 0
            sortino_ratio = np.mean(daily_returns_array) / downside_std * np.sqrt(252) if downside_std != 0 else 0
        else:
            sharpe_ratio = 0
            sortino_ratio = 0
        
        # Calmar ratio
        calmar_ratio = annual_return_pct / max_drawdown_pct if max_drawdown_pct != 0 else 0
        
        # Trade duration
        trade_durations = []
        for trade in self.trades:
            if trade.exit_time:
                duration = (trade.exit_time - trade.entry_time).total_seconds() / 3600  # hours
                trade_durations.append(duration)
        
        avg_trade_duration = np.mean(trade_durations) if trade_durations else 0
        avg_bars_in_trade = avg_trade_duration / 1  # Assuming 1-hour bars
        
        # Consecutive wins/losses
        consecutive_wins = self._calculate_consecutive_wins()
        consecutive_losses = self._calculate_consecutive_losses()
        
        # Recovery factor
        recovery_factor = total_return_pct / max_drawdown_pct if max_drawdown_pct != 0 else 0
        
        return BacktestMetrics(
            total_return=total_return,
            total_return_pct=total_return_pct,
            annual_return_pct=annual_return_pct,
            max_drawdown=max_drawdown * self.initial_capital,
            max_drawdown_pct=max_drawdown_pct,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            win_rate=win_rate,
            profit_factor=profit_factor,
            avg_win=avg_win,
            avg_loss=avg_loss,
            max_win=max_win,
            max_loss=max_loss,
            total_trades=len(self.trades),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            avg_trade_duration=avg_trade_duration,
            avg_bars_in_trade=avg_bars_in_trade,
            consecutive_wins=consecutive_wins,
            consecutive_losses=consecutive_losses,
            recovery_factor=recovery_factor,
            payoff_ratio=payoff_ratio
        )
    
    def _empty_metrics(self) -> BacktestMetrics:
        """Return empty metrics when no trades were made"""
        return BacktestMetrics(
            total_return=0, total_return_pct=0, annual_return_pct=0,
            max_drawdown=0, max_drawdown_pct=0, sharpe_ratio=0,
            sortino_ratio=0, calmar_ratio=0, win_rate=0, profit_factor=0,
            avg_win=0, avg_loss=0, max_win=0, max_loss=0,
            total_trades=0, winning_trades=0, losing_trades=0,
            avg_trade_duration=0, avg_bars_in_trade=0,
            consecutive_wins=0, consecutive_losses=0,
            recovery_factor=0, payoff_ratio=0
        )
    
    def _calculate_consecutive_wins(self) -> int:
        """Calculate maximum consecutive wins"""
        max_consecutive = 0
        current_consecutive = 0
        
        for trade in self.trades:
            if trade.pnl > 0:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
        
        return max_consecutive
    
    def _calculate_consecutive_losses(self) -> int:
        """Calculate maximum consecutive losses"""
        max_consecutive = 0
        current_consecutive = 0
        
        for trade in self.trades:
            if trade.pnl < 0:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
        
        return max_consecutive
    
    def _filter_data_by_date(self, data: pd.DataFrame, start_date: Optional[datetime], end_date: Optional[datetime]) -> pd.DataFrame:
        """Filter data by date range"""
        if 'timestamp' in data.columns:
            if start_date:
                data = data[data['timestamp'] >= start_date]
            if end_date:
                data = data[data['timestamp'] <= end_date]
        return data
    
    def _trade_to_dict(self, trade: BacktestTrade) -> Dict[str, Any]:
        """Convert trade object to dictionary"""
        return {
            'entry_time': trade.entry_time,
            'exit_time': trade.exit_time,
            'symbol': trade.symbol,
            'side': trade.side,
            'entry_price': trade.entry_price,
            'exit_price': trade.exit_price,
            'quantity': trade.quantity,
            'pnl': trade.pnl,
            'pnl_pct': trade.pnl_pct,
            'strategy': trade.strategy,
            'exit_reason': trade.exit_reason,
            'duration_hours': (trade.exit_time - trade.entry_time).total_seconds() / 3600 if trade.exit_time else None
        }
    
    def generate_report(self, results: Dict[str, Any], filename: Optional[str] = None) -> str:
        """Generate detailed backtest report"""
        
        metrics = results['metrics']
        
        report = f"""
=== BACKTEST REPORT ===
Strategy: {results['strategy_name']}
Period: {results['backtest_period']['start']} to {results['backtest_period']['end']}
Initial Capital: ${results['initial_capital']:,.2f}
Final Capital: ${results['final_capital']:,.2f}

=== PERFORMANCE METRICS ===
Total Return: ${metrics.total_return:,.2f} ({metrics.total_return_pct:.2f}%)
Annual Return: {metrics.annual_return_pct:.2f}%
Max Drawdown: ${metrics.max_drawdown:,.2f} ({metrics.max_drawdown_pct:.2f}%)

=== RISK METRICS ===
Sharpe Ratio: {metrics.sharpe_ratio:.3f}
Sortino Ratio: {metrics.sortino_ratio:.3f}
Calmar Ratio: {metrics.calmar_ratio:.3f}
Recovery Factor: {metrics.recovery_factor:.3f}

=== TRADE STATISTICS ===
Total Trades: {metrics.total_trades}
Winning Trades: {metrics.winning_trades} ({metrics.win_rate:.1f}%)
Losing Trades: {metrics.losing_trades} ({100-metrics.win_rate:.1f}%)
Profit Factor: {metrics.profit_factor:.3f}
Payoff Ratio: {metrics.payoff_ratio:.3f}

Average Win: ${metrics.avg_win:.2f}
Average Loss: ${metrics.avg_loss:.2f}
Max Win: ${metrics.max_win:.2f}
Max Loss: ${metrics.max_loss:.2f}

Consecutive Wins: {metrics.consecutive_wins}
Consecutive Losses: {metrics.consecutive_losses}
Average Trade Duration: {metrics.avg_trade_duration:.1f} hours
"""
        
        if filename:
            with open(filename, 'w') as f:
                f.write(report)
            print(f"Report saved to {filename}")
        
        return report
    
    def plot_results(self, results: Dict[str, Any], save_path: Optional[str] = None):
        """Generate comprehensive backtest plots"""
        
        fig, axes = plt.subplots(3, 2, figsize=(15, 12))
        fig.suptitle(f"Backtest Results: {results['strategy_name']}", fontsize=16)
        
        # Equity curve
        axes[0, 0].plot(results['equity_curve'])
        axes[0, 0].set_title('Equity Curve')
        axes[0, 0].set_ylabel('Portfolio Value ($)')
        axes[0, 0].grid(True)
        
        # Drawdown curve
        axes[0, 1].fill_between(range(len(results['drawdown_curve'])), 
                               results['drawdown_curve'], alpha=0.3, color='red')
        axes[0, 1].set_title('Drawdown')
        axes[0, 1].set_ylabel('Drawdown (%)')
        axes[0, 1].grid(True)
        
        # Daily returns histogram
        if results['daily_returns']:
            axes[1, 0].hist(results['daily_returns'], bins=50, alpha=0.7)
            axes[1, 0].set_title('Daily Returns Distribution')
            axes[1, 0].set_xlabel('Daily Return')
            axes[1, 0].set_ylabel('Frequency')
            axes[1, 0].grid(True)
        
        # Monthly returns heatmap (if enough data)
        if len(results['daily_returns']) > 30:
            # Create monthly returns matrix
            monthly_returns = pd.Series(results['daily_returns']).resample('M').apply(lambda x: (1 + x).prod() - 1)
            if len(monthly_returns) > 12:
                monthly_matrix = monthly_returns.values.reshape(-1, 12)
                sns.heatmap(monthly_matrix, annot=True, fmt='.2f', ax=axes[1, 1], cmap='RdYlGn', center=0)
                axes[1, 1].set_title('Monthly Returns Heatmap')
        
        # Trade analysis
        if results['trades']:
            trade_pnl = [trade['pnl'] for trade in results['trades']]
            axes[2, 0].scatter(range(len(trade_pnl)), trade_pnl, alpha=0.6)
            axes[2, 0].axhline(y=0, color='black', linestyle='--', alpha=0.5)
            axes[2, 0].set_title('Trade P&L')
            axes[2, 0].set_xlabel('Trade Number')
            axes[2, 0].set_ylabel('P&L ($)')
            axes[2, 0].grid(True)
            
            # Cumulative P&L
            cumulative_pnl = np.cumsum(trade_pnl)
            axes[2, 1].plot(cumulative_pnl)
            axes[2, 1].set_title('Cumulative Trade P&L')
            axes[2, 1].set_xlabel('Trade Number')
            axes[2, 1].set_ylabel('Cumulative P&L ($)')
            axes[2, 1].grid(True)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Plots saved to {save_path}")
        
        plt.show()

if __name__ == "__main__":
    # Example usage
    import pandas as pd
    from strategies.strategy_engine import MultiIndicatorStrategy
    import config
    
    # Create sample data
    dates = pd.date_range('2023-01-01', periods=1000, freq='H')
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.randn(1000) * 0.5)
    
    sample_data = pd.DataFrame({
        'timestamp': dates,
        'open': prices + np.random.randn(1000) * 0.1,
        'high': prices + np.abs(np.random.randn(1000) * 0.2),
        'low': prices - np.abs(np.random.randn(1000) * 0.2),
        'close': prices,
        'volume': np.random.randint(1000, 10000, 1000)
    })
    
    sample_data.set_index('timestamp', inplace=True)
    
    # Run backtest
    backtester = AdvancedBacktester(initial_capital=10000)
    strategy = MultiIndicatorStrategy(config.STRATEGY_CONFIG)
    
    results = backtester.run_backtest(strategy, sample_data, config.STRATEGY_CONFIG)
    
    # Generate report
    report = backtester.generate_report(results)
    print(report)