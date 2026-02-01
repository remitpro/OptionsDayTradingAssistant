"""Data validation utilities."""

from typing import Optional, Dict, Any
import math


def is_valid_price(price: Optional[float]) -> bool:
    """Check if price is valid (not None, NaN, or negative)."""
    if price is None:
        return False
    if math.isnan(price) or math.isinf(price):
        return False
    return price > 0


def is_valid_greek(value: Optional[float]) -> bool:
    """Check if Greek value is valid (not None, NaN, or Inf)."""
    if value is None:
        return False
    return not (math.isnan(value) or math.isinf(value))


def is_valid_volume(volume: Optional[int]) -> bool:
    """Check if volume is valid (not None and >= 0)."""
    if volume is None:
        return False
    return volume >= 0


def validate_option_data(option: Dict[str, Any]) -> bool:
    """
    Validate that option data has all required fields and valid values.
    
    Args:
        option: Option data dictionary
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ['bid', 'ask', 'openInterest', 'totalVolume']
    
    # Check required fields exist
    for field in required_fields:
        if field not in option:
            return False
    
    # Validate bid/ask
    if not is_valid_price(option.get('bid')) or not is_valid_price(option.get('ask')):
        return False
    
    # Validate volume and OI
    if not is_valid_volume(option.get('openInterest')) or not is_valid_volume(option.get('totalVolume')):
        return False
    
    # Validate Greeks if present
    greeks = option.get('greeks', {})
    if greeks:
        for greek in ['delta', 'gamma', 'theta', 'vega']:
            if greek in greeks and not is_valid_greek(greeks[greek]):
                return False
    
    return True


def calculate_spread_pct(bid: float, ask: float) -> float:
    """
    Calculate bid-ask spread as percentage of mid price.
    
    Args:
        bid: Bid price
        ask: Ask price
        
    Returns:
        Spread percentage
    """
    if bid <= 0 or ask <= 0 or ask < bid:
        return float('inf')
    
    mid = (bid + ask) / 2
    if mid == 0:
        return float('inf')
    
    return ((ask - bid) / mid) * 100
