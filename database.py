# database.py
"""
MongoDB Database Handler

Manages user accounts, trading history, and order tracking in MongoDB.
Stores all trading data with timestamps for analysis and reporting.
"""

import pymongo
from pymongo import MongoClient
from datetime import datetime, timezone
import uuid
from typing import Dict, List, Optional
import json

class TradingDatabase:
    """MongoDB handler for trading bot data"""
    
    def __init__(self, connection_string: str = "mongodb+srv://talha_db_user:52cOcZZwz8AxmQlu@cluster0.7fyyw6x.mongodb.net/", db_name: str = "TradingBot"):
        """Initialize database connection"""
        try:
            self.client = MongoClient(connection_string)
            self.db = self.client[db_name]
            
            # Collections
            self.users = self.db.users
            self.orders = self.db.orders
            self.trades = self.db.trades
            self.balances = self.db.balances
            self.strategies = self.db.strategies
            
            # Create indexes for better performance
            self._create_indexes()
            print(f"✅ Connected to MongoDB database: {db_name}")
            
        except Exception as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            raise

    def _create_indexes(self):
        """Create database indexes for better performance"""
        try:
            # User indexes
            self.users.create_index("user_id", unique=True)
            self.users.create_index("email", unique=True)
            
            # Order indexes
            self.orders.create_index([("user_id", 1), ("timestamp", -1)])
            self.orders.create_index("order_id", unique=True)
            self.orders.create_index("status")
            
            # Trade indexes
            self.trades.create_index([("user_id", 1), ("timestamp", -1)])
            self.trades.create_index("symbol")
            
            # Balance indexes
            self.balances.create_index([("user_id", 1), ("timestamp", -1)])
            
        except Exception as e:
            print(f"Warning: Could not create indexes: {e}")

    def create_user(self, email: str, name: str, initial_balance: float = 10000.0) -> str:
        """Create a new user account"""
        user_id = str(uuid.uuid4())
        
        user_data = {
            "user_id": user_id,
            "email": email,
            "name": name,
            "created_at": datetime.now(timezone.utc),
            "status": "active",
            "settings": {
                "default_risk_per_trade": 0.01,
                "max_open_positions": 5,
                "preferred_strategy": "conservative",
                "notifications": True
            }
        }
        
        try:
            # Create user
            self.users.insert_one(user_data)
            
            # Initialize balance
            self.update_balance(user_id, "USDT", initial_balance, "initial_deposit")
            
            print(f"✅ Created user: {name} ({email}) with ID: {user_id}")
            return user_id
            
        except pymongo.errors.DuplicateKeyError:
            print(f"❌ User with email {email} already exists")
            raise ValueError(f"User with email {email} already exists")

    def get_user(self, user_id: str) -> Optional[Dict]:
        """Get user information"""
        return self.users.find_one({"user_id": user_id})

    def update_balance(self, user_id: str, currency: str, amount: float, reason: str):
        """Update user balance"""
        balance_record = {
            "user_id": user_id,
            "currency": currency,
            "amount": amount,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc)
        }
        
        self.balances.insert_one(balance_record)

    def get_current_balance(self, user_id: str, currency: str = "USDT") -> float:
        """Get current balance for a currency"""
        pipeline = [
            {"$match": {"user_id": user_id, "currency": currency}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]
        
        result = list(self.balances.aggregate(pipeline))
        return result[0]["total"] if result else 0.0

    def create_order(self, user_id: str, symbol: str, side: str, amount: float, 
                    price: float, strategy: str, signal_strength: int) -> str:
        """Create a new order record"""
        order_id = str(uuid.uuid4())
        
        order_data = {
            "order_id": order_id,
            "user_id": user_id,
            "symbol": symbol,
            "side": side.upper(),
            "amount": amount,
            "price": price,
            "strategy": strategy,
            "signal_strength": signal_strength,
            "status": "pending",
            "timestamp": datetime.now(timezone.utc),
            "filled_amount": 0.0,
            "filled_price": 0.0,
            "fees": 0.0
        }
        
        self.orders.insert_one(order_data)
        return order_id

    def update_order_status(self, order_id: str, status: str, filled_amount: float = 0.0, 
                           filled_price: float = 0.0, fees: float = 0.0):
        """Update order status"""
        update_data = {
            "status": status,
            "updated_at": datetime.now(timezone.utc)
        }
        
        if filled_amount > 0:
            update_data["filled_amount"] = filled_amount
            update_data["filled_price"] = filled_price
            update_data["fees"] = fees
        
        self.orders.update_one(
            {"order_id": order_id},
            {"$set": update_data}
        )

    def create_trade(self, user_id: str, symbol: str, side: str, amount: float, 
                    entry_price: float, exit_price: float, strategy: str, 
                    pnl: float, fees: float):
        """Create a completed trade record"""
        trade_data = {
            "trade_id": str(uuid.uuid4()),
            "user_id": user_id,
            "symbol": symbol,
            "side": side.upper(),
            "amount": amount,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "strategy": strategy,
            "pnl": pnl,
            "fees": fees,
            "roi": (pnl / (amount * entry_price)) * 100,
            "timestamp": datetime.now(timezone.utc)
        }
        
        self.trades.insert_one(trade_data)
        
        # Update balance
        net_pnl = pnl - fees
        self.update_balance(user_id, "USDT", net_pnl, f"trade_pnl_{symbol}")

    def get_user_orders(self, user_id: str, status: str = None, limit: int = 100) -> List[Dict]:
        """Get user orders with optional status filter"""
        query = {"user_id": user_id}
        if status:
            query["status"] = status
        
        return list(self.orders.find(query).sort("timestamp", -1).limit(limit))

    def get_user_trades(self, user_id: str, symbol: str = None, limit: int = 100) -> List[Dict]:
        """Get user trades with optional symbol filter"""
        query = {"user_id": user_id}
        if symbol:
            query["symbol"] = symbol
        
        return list(self.trades.find(query).sort("timestamp", -1).limit(limit))

    def get_trading_stats(self, user_id: str) -> Dict:
        """Get comprehensive trading statistics"""
        # Total trades
        total_trades = self.trades.count_documents({"user_id": user_id})
        
        # Win/Loss stats
        winning_trades = self.trades.count_documents({"user_id": user_id, "pnl": {"$gt": 0}})
        losing_trades = self.trades.count_documents({"user_id": user_id, "pnl": {"$lt": 0}})
        
        # PnL aggregation
        pnl_pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {
                "_id": None,
                "total_pnl": {"$sum": "$pnl"},
                "total_fees": {"$sum": "$fees"},
                "avg_pnl": {"$avg": "$pnl"},
                "max_win": {"$max": "$pnl"},
                "max_loss": {"$min": "$pnl"}
            }}
        ]
        
        pnl_result = list(self.trades.aggregate(pnl_pipeline))
        pnl_data = pnl_result[0] if pnl_result else {}
        
        # Current balance
        current_balance = self.get_current_balance(user_id)
        
        return {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": (winning_trades / total_trades * 100) if total_trades > 0 else 0,
            "total_pnl": pnl_data.get("total_pnl", 0),
            "total_fees": pnl_data.get("total_fees", 0),
            "avg_pnl": pnl_data.get("avg_pnl", 0),
            "max_win": pnl_data.get("max_win", 0),
            "max_loss": pnl_data.get("max_loss", 0),
            "current_balance": current_balance
        }

    def get_open_positions(self, user_id: str) -> List[Dict]:
        """Get currently open positions"""
        return list(self.orders.find({
            "user_id": user_id,
            "status": {"$in": ["filled", "partially_filled"]}
        }))

    def log_strategy_performance(self, strategy_name: str, symbol: str, signal: str, 
                               signal_strength: int, success: bool):
        """Log strategy performance for analysis"""
        performance_data = {
            "strategy": strategy_name,
            "symbol": symbol,
            "signal": signal,
            "signal_strength": signal_strength,
            "success": success,
            "timestamp": datetime.now(timezone.utc)
        }
        
        self.strategies.insert_one(performance_data)

    def get_strategy_performance(self, strategy_name: str = None) -> Dict:
        """Get strategy performance statistics"""
        match_query = {}
        if strategy_name:
            match_query["strategy"] = strategy_name
        
        pipeline = [
            {"$match": match_query},
            {"$group": {
                "_id": "$strategy",
                "total_signals": {"$sum": 1},
                "successful_signals": {"$sum": {"$cond": ["$success", 1, 0]}},
                "avg_strength": {"$avg": "$signal_strength"}
            }},
            {"$addFields": {
                "success_rate": {
                    "$multiply": [
                        {"$divide": ["$successful_signals", "$total_signals"]},
                        100
                    ]
                }
            }}
        ]
        
        results = list(self.strategies.aggregate(pipeline))
        return {result["_id"]: result for result in results}

    def close_connection(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            print("📴 Database connection closed")

# Global database instance
db = None

def get_database() -> TradingDatabase:
    """Get database instance (singleton pattern)"""
    global db
    if db is None:
        db = TradingDatabase()
    return db

def initialize_database():
    """Initialize database connection"""
    global db
    db = TradingDatabase()
    return db
