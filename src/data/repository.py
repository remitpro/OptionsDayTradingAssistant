"""Repository pattern for database operations."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from src.data.database import TradeModel, get_session
from src.utils.logger import get_logger

logger = get_logger(__name__)

class TradeRepository:
    """Repository for managing trade data persistence."""
    
    def __init__(self, session: Session = None):
        self.session = session or get_session()
        
    def add_trade(self, trade_data: Dict[str, Any]) -> bool:
        """
        Add a trade to the database.
        
        Args:
            trade_data: Dictionary containing trade information
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Extract fields that map directly to columns
            db_trade = TradeModel(
                symbol=trade_data.get('symbol'),
                strategy=trade_data.get('strategy'),
                bias=trade_data.get('bias'),
                status=trade_data.get('status', 'OPEN'),
                timestamp=datetime.now(),
                underlying_price=trade_data.get('underlying_price'),
                max_loss=trade_data.get('risk_metrics', {}).get('max_loss', 0),
                max_gain=trade_data.get('risk_metrics', {}).get('max_gain', 0),
                risk_reward_ratio=trade_data.get('risk_metrics', {}).get('risk_reward_ratio', 0),
                probability_of_profit=trade_data.get('probability_metrics', {}).get('probability_profit'),
                score=trade_data.get('score'),
                legs=trade_data.get('legs', []),
                risk_metrics=trade_data.get('risk_metrics', {}),
                explanation=trade_data.get('explanation', '')
            )
            
            self.session.add(db_trade)
            self.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to add trade to database: {e}")
            self.session.rollback()
            return False
            
    def get_recent_trades(self, limit: int = 50) -> List[TradeModel]:
        """Get most recent trades."""
        return self.session.query(TradeModel)\
            .order_by(TradeModel.timestamp.desc())\
            .limit(limit)\
            .all()
            
    def get_trades_by_symbol(self, symbol: str) -> List[TradeModel]:
        """Get trades for a specific symbol."""
        return self.session.query(TradeModel)\
            .filter(TradeModel.symbol == symbol)\
            .order_by(TradeModel.timestamp.desc())\
            .all()
