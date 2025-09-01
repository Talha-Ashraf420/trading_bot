from pymongo import MongoClient, ASCENDING, DESCENDING
from datetime import datetime
import config

class TradingDatabase:
    def __init__(self):
        self.client = MongoClient(config.DATABASE_CONFIG['connection_string'])
        self.db = self.client[config.DATABASE_CONFIG['database']]
        self.setup_collections()
    
    def setup_collections(self):
        """Initialize all collections with proper indexes"""
        
        # Market Data Collection
        self.market_data = self.db.market_data
        self.market_data.create_index([("symbol", ASCENDING), ("timestamp", ASCENDING)], unique=True)
        self.market_data.create_index([("timestamp", DESCENDING)])
        
        # Technical Indicators Collection
        self.indicators = self.db.indicators
        self.indicators.create_index([("symbol", ASCENDING), ("timestamp", ASCENDING), ("timeframe", ASCENDING)], unique=True)
        
        # Trading Signals Collection
        self.signals = self.db.signals
        self.signals.create_index([("symbol", ASCENDING), ("timestamp", DESCENDING)])
        self.signals.create_index([("strategy", ASCENDING), ("timestamp", DESCENDING)])
        
        # Trades Collection
        self.trades = self.db.trades
        self.trades.create_index([("symbol", ASCENDING), ("timestamp", DESCENDING)])
        self.trades.create_index([("status", ASCENDING)])
        
        # Portfolio Collection
        self.portfolio = self.db.portfolio
        self.portfolio.create_index([("timestamp", DESCENDING)])
        
        # Performance Metrics Collection
        self.performance = self.db.performance
        self.performance.create_index([("date", DESCENDING)])
        
        # Strategy Performance Collection
        self.strategy_performance = self.db.strategy_performance
        self.strategy_performance.create_index([("strategy_name", ASCENDING), ("date", DESCENDING)])
        
        # Risk Metrics Collection
        self.risk_metrics = self.db.risk_metrics
        self.risk_metrics.create_index([("timestamp", DESCENDING)])
        
        # Bot Logs Collection
        self.logs = self.db.bot_logs
        self.logs.create_index([("timestamp", DESCENDING)])
        self.logs.create_index([("level", ASCENDING), ("timestamp", DESCENDING)])
    
    def insert_market_data(self, symbol, timeframe, data):
        """Insert OHLCV market data"""
        document = {
            "symbol": symbol,
            "timeframe": timeframe,
            "timestamp": data['timestamp'],
            "open": float(data['open']),
            "high": float(data['high']),
            "low": float(data['low']),
            "close": float(data['close']),
            "volume": float(data['volume']),
            "created_at": datetime.utcnow()
        }
        return self.market_data.update_one(
            {"symbol": symbol, "timestamp": data['timestamp']},
            {"$set": document},
            upsert=True
        )
    
    def insert_indicators(self, symbol, timeframe, timestamp, indicators_data):
        """Insert technical indicators data"""
        document = {
            "symbol": symbol,
            "timeframe": timeframe,
            "timestamp": timestamp,
            "indicators": indicators_data,
            "created_at": datetime.utcnow()
        }
        return self.indicators.update_one(
            {"symbol": symbol, "timestamp": timestamp, "timeframe": timeframe},
            {"$set": document},
            upsert=True
        )
    
    def insert_signal(self, symbol, strategy, signal_data):
        """Insert trading signal"""
        document = {
            "symbol": symbol,
            "strategy": strategy,
            "timestamp": signal_data['timestamp'],
            "signal": signal_data['signal'],  # BUY, SELL, HOLD
            "confidence": signal_data.get('confidence', 0),
            "price": float(signal_data['price']),
            "indicators_snapshot": signal_data.get('indicators', {}),
            "reasoning": signal_data.get('reasoning', ''),
            "created_at": datetime.utcnow()
        }
        return self.signals.insert_one(document)
    
    def insert_trade(self, trade_data):
        """Insert trade execution data"""
        document = {
            "symbol": trade_data['symbol'],
            "side": trade_data['side'],  # BUY, SELL
            "quantity": float(trade_data['quantity']),
            "price": float(trade_data['price']),
            "order_id": trade_data.get('order_id'),
            "status": trade_data['status'],  # PENDING, FILLED, CANCELLED, FAILED
            "timestamp": trade_data['timestamp'],
            "strategy": trade_data.get('strategy'),
            "fees": float(trade_data.get('fees', 0)),
            "pnl": float(trade_data.get('pnl', 0)),
            "created_at": datetime.utcnow()
        }
        return self.trades.insert_one(document)
    
    def update_portfolio(self, portfolio_data):
        """Update portfolio snapshot"""
        document = {
            "timestamp": datetime.utcnow(),
            "total_balance": float(portfolio_data['total_balance']),
            "available_balance": float(portfolio_data['available_balance']),
            "positions": portfolio_data['positions'],
            "unrealized_pnl": float(portfolio_data.get('unrealized_pnl', 0)),
            "realized_pnl": float(portfolio_data.get('realized_pnl', 0)),
            "total_trades": portfolio_data.get('total_trades', 0)
        }
        return self.portfolio.insert_one(document)
    
    def log_bot_activity(self, level, message, details=None):
        """Log bot activities"""
        document = {
            "timestamp": datetime.utcnow(),
            "level": level,  # INFO, WARNING, ERROR, DEBUG
            "message": message,
            "details": details or {}
        }
        return self.logs.insert_one(document)
    
    def get_latest_market_data(self, symbol, timeframe, limit=100):
        """Get latest market data"""
        return list(self.market_data.find(
            {"symbol": symbol},
            sort=[("timestamp", DESCENDING)],
            limit=limit
        ))
    
    def get_performance_summary(self, days=30):
        """Get performance summary for specified days"""
        from datetime import timedelta
        start_date = datetime.utcnow() - timedelta(days=days)
        
        pipeline = [
            {"$match": {"timestamp": {"$gte": start_date}}},
            {"$group": {
                "_id": None,
                "total_trades": {"$sum": 1},
                "total_pnl": {"$sum": "$pnl"},
                "avg_pnl": {"$avg": "$pnl"},
                "winning_trades": {"$sum": {"$cond": [{"$gt": ["$pnl", 0]}, 1, 0]}},
                "losing_trades": {"$sum": {"$cond": [{"$lt": ["$pnl", 0]}, 1, 0]}}
            }}
        ]
        
        result = list(self.trades.aggregate(pipeline))
        return result[0] if result else None
    
    def clear_all_data(self):
        """Clear all trading data for fresh start - USE WITH CAUTION"""
        collections = [
            self.market_data, self.indicators, self.signals, 
            self.trades, self.portfolio, self.performance,
            self.strategy_performance, self.risk_metrics, self.logs
        ]
        
        for collection in collections:
            collection.delete_many({})
        
        print("All trading data cleared. Fresh start initiated!")
    
    def close_connection(self):
        """Close database connection"""
        self.client.close()

if __name__ == "__main__":
    # Initialize database and clear for fresh start
    db = TradingDatabase()
    print("Database schema initialized successfully!")
    
    # Uncomment the line below if you want to clear all existing data
    # db.clear_all_data()