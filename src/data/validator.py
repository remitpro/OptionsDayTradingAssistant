"""Data validation and freshness checks."""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from src.utils.logger import get_logger

logger = get_logger(__name__)

class DataValidator:
    """Validator for market data integrity and freshness."""
    
    def __init__(self, max_age_seconds: int = 60):
        self.max_age_seconds = max_age_seconds
        
    def check_freshness(self, timestamp: Any) -> bool:
        """
        Check if data is fresh enough to use.
        
        Args:
            timestamp: Unix timestamp (ms) or datetime object
            
        Returns:
            True if fresh, False if stale
        """
        now = datetime.now(timezone.utc)
        
        if isinstance(timestamp, (int, float)):
            # TDA sends timestamps in ms
            try:
                data_time = datetime.fromtimestamp(timestamp / 1000.0, tz=timezone.utc)
            except Exception:
                return False
        elif isinstance(timestamp, datetime):
            data_time = timestamp
            if data_time.tzinfo is None:
                # Assume UTC if naive, though dangerous
                data_time = data_time.replace(tzinfo=timezone.utc)
        else:
            return False
            
        age = (now - data_time).total_seconds()
        
        if age > self.max_age_seconds:
            logger.warning(f"Data stale: {age:.1f}s old (Limit: {self.max_age_seconds}s)")
            return False
            
        return True
        
    @staticmethod
    def validate_quote_integrity(quote: Dict[str, Any]) -> bool:
        """
        Check for malformed or suspicious negative prices.
        
        Args:
            quote: Quote dictionary
            
        Returns:
            True if valid
        """
        required = ['bidPrice', 'askPrice', 'lastPrice']
        for field in required:
            val = quote.get(field)
            if val is None or val < 0:
                logger.warning(f"Invalid quote data: {field}={val}")
                return False
                
        # Bid/Ask logic check
        if quote.get('bidPrice', 0) > quote.get('askPrice', 0):
            # Crossed market is possible but rare/suspicious for liquid stocks
            logger.debug(f"Crossed market validation warning: Bid > Ask for {quote.get('symbol')}")
            # We don't fail, but we note it.
            
        return True
