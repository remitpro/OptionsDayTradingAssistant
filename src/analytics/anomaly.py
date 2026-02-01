"""Market data anomaly detection."""

from typing import List, Dict, Any
import numpy as np
from src.utils.logger import get_logger

logger = get_logger(__name__)

class AnomalyDetector:
    """Detect anomalies in market data."""
    
    def __init__(self, price_deviation_threshold: float = 0.05, volume_multiplier: float = 10.0):
        self.price_threshold = price_deviation_threshold
        self.volume_multiplier = volume_multiplier
        
    def is_price_anomaly(self, current_price: float, history: List[float]) -> bool:
        """
        Check if current price is a statistical outlier vs history.
        
        Args:
            current_price: Latest price
            history: List of historical prices (last N periods)
            
        Returns:
            True if anomaly
        """
        if not history or len(history) < 5:
            return False
            
        avg = np.mean(history)
        std = np.std(history)
        
        if std == 0:
            return abs(current_price - avg) > (avg * self.price_threshold)
            
        z_score = abs(current_price - avg) / std
        
        # Z-score > 4 is highly unlikely (99.99% confidence)
        if z_score > 4.0:
            logger.warning(f"Price anomaly detected: {current_price} (Z-Score: {z_score:.2f})")
            return True
            
        return False
        
    def detect_bad_tick(self, quote: Dict[str, Any], prev_close: float) -> bool:
        """
        Simple check for massive % moves that indicate bad data.
        
        Args:
            quote: Current quote
            prev_close: Previous close price
            
        Returns:
            True if bad tick suspected
        """
        current = quote.get('lastPrice', 0)
        if current <= 0 or prev_close <= 0:
            return True
            
        pct_change = abs(current - prev_close) / prev_close
        
        # If stock moved > 50% in a day (rare for large caps, possible for penny stocks)
        # We assume for this system's target (liquid options) 50% is an error or halt.
        if pct_change > 0.50:
            logger.warning(f"Bad tick suspected: {pct_change:.1%} move")
            return True
            
        return False
