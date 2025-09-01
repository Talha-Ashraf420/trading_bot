import logging
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from core.database_schema import TradingDatabase
import json
import traceback

class TradingLogger:
    """Enhanced logging system for trading bot with database integration"""
    
    def __init__(self, database: TradingDatabase, config: Dict[str, Any]):
        self.database = database
        self.config = config
        
        # Setup file and console logging
        self.setup_logging()
        
        # Performance tracking
        self.performance_metrics = {
            'signals_generated': 0,
            'trades_executed': 0,
            'errors_encountered': 0,
            'session_start': datetime.utcnow()
        }
    
    def setup_logging(self):
        """Setup logging configuration"""
        
        # Create logger
        self.logger = logging.getLogger('TradingBot')
        self.logger.setLevel(getattr(logging, self.config.get('log_level', 'INFO')))
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        console_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # File handler for detailed logs
        log_file = self.config.get('log_file', 'trading_bot.log')
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler for important messages
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, self.config.get('console_log_level', 'INFO')))
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # Prevent duplicate logs
        self.logger.propagate = False
    
    def info(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Log info message"""
        self.logger.info(message)
        self.database.log_bot_activity('INFO', message, details or {})
    
    def warning(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Log warning message"""
        self.logger.warning(message)
        self.database.log_bot_activity('WARNING', message, details or {})
    
    def error(self, message: str, details: Optional[Dict[str, Any]] = None, exception: Optional[Exception] = None):
        """Log error message"""
        self.performance_metrics['errors_encountered'] += 1
        
        error_details = details or {}
        if exception:
            error_details['exception_type'] = type(exception).__name__
            error_details['exception_message'] = str(exception)
            error_details['traceback'] = traceback.format_exc()
        
        self.logger.error(message)
        if exception:
            self.logger.error(f"Exception details: {exception}")
        
        self.database.log_bot_activity('ERROR', message, error_details)
    
    def debug(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Log debug message"""
        self.logger.debug(message)
        if self.config.get('log_level') == 'DEBUG':
            self.database.log_bot_activity('DEBUG', message, details or {})
    
    def log_signal_generated(self, symbol: str, strategy: str, signal_data: Dict[str, Any]):
        """Log when a trading signal is generated"""
        self.performance_metrics['signals_generated'] += 1
        
        message = f"Signal generated for {symbol} by {strategy}: {signal_data.get('signal', 'UNKNOWN')}"
        details = {
            'symbol': symbol,
            'strategy': strategy,
            'signal': signal_data.get('signal'),
            'confidence': signal_data.get('confidence', 0),
            'price': signal_data.get('price', 0),
            'reasoning': signal_data.get('reasoning', [])
        }
        
        self.info(message, details)
    
    def log_trade_attempt(self, symbol: str, signal_data: Dict[str, Any], validation_result: Dict[str, Any]):
        """Log trade attempt and validation result"""
        
        if validation_result['allowed']:
            message = f"Trade attempt for {symbol}: {signal_data.get('signal')} - ALLOWED"
            level = 'INFO'
        else:
            message = f"Trade attempt for {symbol}: {signal_data.get('signal')} - BLOCKED"
            level = 'WARNING'
        
        details = {
            'symbol': symbol,
            'signal': signal_data.get('signal'),
            'price': signal_data.get('price'),
            'validation_result': validation_result
        }
        
        if level == 'INFO':
            self.info(message, details)
        else:
            self.warning(message, details)
    
    def log_trade_executed(self, symbol: str, trade_data: Dict[str, Any]):
        """Log successful trade execution"""
        self.performance_metrics['trades_executed'] += 1
        
        message = f"Trade executed for {symbol}: {trade_data.get('side')} {trade_data.get('quantity')} @ {trade_data.get('price')}"
        details = {
            'symbol': symbol,
            'side': trade_data.get('side'),
            'quantity': trade_data.get('quantity'),
            'price': trade_data.get('price'),
            'order_id': trade_data.get('order_id'),
            'strategy': trade_data.get('strategy')
        }
        
        self.info(message, details)
    
    def log_trade_failed(self, symbol: str, trade_data: Dict[str, Any], error: str):
        """Log failed trade execution"""
        message = f"Trade failed for {symbol}: {error}"
        details = {
            'symbol': symbol,
            'trade_data': trade_data,
            'error': error
        }
        
        self.error(message, details)
    
    def log_portfolio_update(self, portfolio_data: Dict[str, Any]):
        """Log portfolio updates"""
        message = f"Portfolio updated - Balance: ${portfolio_data.get('total_balance', 0):.2f}, P&L: ${portfolio_data.get('realized_pnl', 0):.2f}"
        details = {
            'total_balance': portfolio_data.get('total_balance'),
            'available_balance': portfolio_data.get('available_balance'),
            'unrealized_pnl': portfolio_data.get('unrealized_pnl'),
            'realized_pnl': portfolio_data.get('realized_pnl'),
            'total_trades': portfolio_data.get('total_trades')
        }
        
        self.info(message, details)
    
    def log_risk_warning(self, warning_type: str, details: Dict[str, Any]):
        """Log risk management warnings"""
        message = f"Risk Warning: {warning_type}"
        
        self.warning(message, details)
    
    def log_strategy_performance(self, strategy_name: str, performance_data: Dict[str, Any]):
        """Log strategy performance metrics"""
        message = f"Strategy performance update for {strategy_name}"
        details = {
            'strategy': strategy_name,
            'performance': performance_data
        }
        
        self.info(message, details)
    
    def log_market_data_update(self, symbol: str, timeframe: str, data_points: int):
        """Log market data updates"""
        message = f"Market data updated for {symbol} ({timeframe}): {data_points} data points"
        details = {
            'symbol': symbol,
            'timeframe': timeframe,
            'data_points': data_points,
            'timestamp': datetime.utcnow()
        }
        
        self.debug(message, details)
    
    def log_system_status(self, status: str, details: Optional[Dict[str, Any]] = None):
        """Log system status changes"""
        message = f"System status: {status}"
        
        if status in ['STARTING', 'RUNNING']:
            self.info(message, details)
        elif status in ['STOPPING', 'STOPPED']:
            self.info(message, details)
        elif status in ['ERROR', 'CRITICAL']:
            self.error(message, details)
        else:
            self.info(message, details)
    
    def log_bot_performance(self):
        """Log current bot performance metrics"""
        uptime = datetime.utcnow() - self.performance_metrics['session_start']
        uptime_hours = uptime.total_seconds() / 3600
        
        message = f"Bot performance update - Uptime: {uptime_hours:.2f}h"
        details = {
            'uptime_hours': uptime_hours,
            'signals_generated': self.performance_metrics['signals_generated'],
            'trades_executed': self.performance_metrics['trades_executed'],
            'errors_encountered': self.performance_metrics['errors_encountered'],
            'signals_per_hour': self.performance_metrics['signals_generated'] / uptime_hours if uptime_hours > 0 else 0,
            'trades_per_hour': self.performance_metrics['trades_executed'] / uptime_hours if uptime_hours > 0 else 0
        }
        
        self.info(message, details)
    
    def create_session_summary(self) -> Dict[str, Any]:
        """Create a comprehensive session summary"""
        uptime = datetime.utcnow() - self.performance_metrics['session_start']
        
        # Get recent performance from database
        recent_logs = list(self.database.logs.find({
            'timestamp': {'$gte': self.performance_metrics['session_start']}
        }).sort('timestamp', -1))
        
        log_counts = {
            'INFO': len([log for log in recent_logs if log['level'] == 'INFO']),
            'WARNING': len([log for log in recent_logs if log['level'] == 'WARNING']),
            'ERROR': len([log for log in recent_logs if log['level'] == 'ERROR']),
            'DEBUG': len([log for log in recent_logs if log['level'] == 'DEBUG'])
        }
        
        summary = {
            'session_start': self.performance_metrics['session_start'],
            'session_end': datetime.utcnow(),
            'uptime': str(uptime),
            'uptime_hours': uptime.total_seconds() / 3600,
            'performance_metrics': self.performance_metrics,
            'log_counts': log_counts,
            'total_logs': len(recent_logs)
        }
        
        return summary
    
    def export_logs_to_file(self, start_date: datetime, end_date: datetime, filename: str):
        """Export logs from database to file"""
        
        logs = list(self.database.logs.find({
            'timestamp': {
                '$gte': start_date,
                '$lte': end_date
            }
        }).sort('timestamp', 1))
        
        with open(filename, 'w') as f:
            f.write("Trading Bot Logs Export\n")
            f.write(f"Period: {start_date} to {end_date}\n")
            f.write(f"Total logs: {len(logs)}\n")
            f.write("="*50 + "\n\n")
            
            for log in logs:
                timestamp = log['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"[{timestamp}] {log['level']}: {log['message']}\n")
                
                if log.get('details'):
                    f.write(f"Details: {json.dumps(log['details'], indent=2, default=str)}\n")
                f.write("\n")
        
        message = f"Exported {len(logs)} logs to {filename}"
        self.info(message, {
            'filename': filename,
            'logs_count': len(logs),
            'start_date': start_date,
            'end_date': end_date
        })
    
    def get_error_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get summary of errors from the last N days"""
        from datetime import timedelta
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        error_logs = list(self.database.logs.find({
            'timestamp': {'$gte': start_date},
            'level': 'ERROR'
        }).sort('timestamp', -1))
        
        # Group errors by type
        error_types = {}
        for log in error_logs:
            error_type = log.get('details', {}).get('exception_type', 'Unknown')
            if error_type not in error_types:
                error_types[error_type] = []
            error_types[error_type].append(log)
        
        return {
            'period_days': days,
            'total_errors': len(error_logs),
            'error_types': {error_type: len(logs) for error_type, logs in error_types.items()},
            'recent_errors': error_logs[:10],  # Last 10 errors
            'most_common_error': max(error_types.keys(), key=lambda x: len(error_types[x])) if error_types else None
        }
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """Remove old logs from database to manage storage"""
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        result = self.database.logs.delete_many({
            'timestamp': {'$lt': cutoff_date}
        })
        
        message = f"Cleaned up {result.deleted_count} old log entries (older than {days_to_keep} days)"
        self.info(message, {
            'deleted_count': result.deleted_count,
            'cutoff_date': cutoff_date,
            'days_to_keep': days_to_keep
        })

# Global logger instance
trading_logger = None

def get_logger(database: TradingDatabase = None, config: Dict[str, Any] = None) -> TradingLogger:
    """Get or create the global trading logger instance"""
    global trading_logger
    
    if trading_logger is None and database is not None and config is not None:
        trading_logger = TradingLogger(database, config)
    
    return trading_logger

if __name__ == "__main__":
    # Example usage
    import config
    from core.database_schema import TradingDatabase
    
    # Initialize database and logger
    db = TradingDatabase()
    logger = TradingLogger(db, {
        'log_level': 'INFO',
        'console_log_level': 'INFO',
        'log_file': 'trading_bot.log'
    })
    
    # Test logging
    logger.info("Trading bot logging system initialized")
    logger.log_system_status("TESTING")
    
    # Test error logging
    try:
        raise ValueError("Test error")
    except Exception as e:
        logger.error("Test error occurred", exception=e)
    
    # Performance summary
    summary = logger.create_session_summary()
    print(f"Logger initialized successfully!")
    print(f"Session uptime: {summary['uptime_hours']:.2f} hours")