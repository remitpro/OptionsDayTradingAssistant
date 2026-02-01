"""Strategy configuration parameters."""

from enum import Enum
from typing import Dict, Any
from dataclasses import dataclass


class StrategyType(Enum):
    """Available options strategies."""
    LONG_CALL = "Long Call"
    LONG_PUT = "Long Put"
    CALL_DEBIT_SPREAD = "Call Debit Spread"
    PUT_DEBIT_SPREAD = "Put Debit Spread"
    CALL_CREDIT_SPREAD = "Call Credit Spread"
    PUT_CREDIT_SPREAD = "Put Credit Spread"
    IRON_CONDOR = "Iron Condor"
    SKIP = "Skip - Too Risky"


class MarketCondition(Enum):
    """Market condition classifications."""
    STRONG_BULLISH = "strong_bullish"
    STRONG_BEARISH = "strong_bearish"
    BULLISH_BREAKOUT = "bullish_breakout"
    BEARISH_BREAKOUT = "bearish_breakout"
    HIGH_IV_RANGE = "high_iv_range"
    CHOPPY = "choppy"
    NEWS_SPIKE = "news_spike"


@dataclass
class StrategyConfig:
    """Configuration for a specific strategy."""
    strategy_type: StrategyType
    delta_target: float  # Target delta for option selection
    spread_width: int  # Number of strikes for spreads (0 for single options)
    max_dte: int  # Maximum days to expiration
    description: str


# Strategy configurations mapped to market conditions
STRATEGY_CONFIGS: Dict[MarketCondition, StrategyConfig] = {
    MarketCondition.STRONG_BULLISH: StrategyConfig(
        strategy_type=StrategyType.LONG_CALL,
        delta_target=0.60,  # Slightly ITM for momentum
        spread_width=0,
        max_dte=7,
        description="Strong bullish momentum with volume spike and trend confirmation"
    ),
    
    MarketCondition.STRONG_BEARISH: StrategyConfig(
        strategy_type=StrategyType.LONG_PUT,
        delta_target=0.60,
        spread_width=0,
        max_dte=7,
        description="Strong bearish momentum with volume spike and trend confirmation"
    ),
    
    MarketCondition.BULLISH_BREAKOUT: StrategyConfig(
        strategy_type=StrategyType.CALL_DEBIT_SPREAD,
        delta_target=0.50,  # ATM for breakout
        spread_width=5,  # $5 wide spread
        max_dte=7,
        description="Bullish breakout with low IV, using debit spread for defined risk"
    ),
    
    MarketCondition.BEARISH_BREAKOUT: StrategyConfig(
        strategy_type=StrategyType.PUT_DEBIT_SPREAD,
        delta_target=0.50,
        spread_width=5,
        max_dte=7,
        description="Bearish breakout with low IV, using debit spread for defined risk"
    ),
    
    MarketCondition.HIGH_IV_RANGE: StrategyConfig(
        strategy_type=StrategyType.CALL_CREDIT_SPREAD,  # or PUT_CREDIT_SPREAD based on bias
        delta_target=0.30,  # OTM for credit collection
        spread_width=5,
        max_dte=7,
        description="High IV range-bound market, selling premium with credit spread"
    ),
    
    MarketCondition.CHOPPY: StrategyConfig(
        strategy_type=StrategyType.IRON_CONDOR,
        delta_target=0.20,  # Far OTM
        spread_width=5,
        max_dte=2,  # 0-2 DTE for theta decay
        description="Choppy market with low directional conviction, collecting theta"
    ),
    
    MarketCondition.NEWS_SPIKE: StrategyConfig(
        strategy_type=StrategyType.SKIP,
        delta_target=0,
        spread_width=0,
        max_dte=0,
        description="Extreme IV spike (>100%), avoiding due to high risk"
    ),
}


def get_strategy_config(condition: MarketCondition) -> StrategyConfig:
    """
    Get strategy configuration for a market condition.
    
    Args:
        condition: Market condition
        
    Returns:
        Strategy configuration
    """
    return STRATEGY_CONFIGS.get(condition)
