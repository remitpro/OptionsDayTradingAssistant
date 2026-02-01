"""Data models for type safety and validation."""

from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator

class Greeks(BaseModel):
    """Option Greeks."""
    delta: Optional[float] = Field(None, description="Delta value")
    gamma: Optional[float] = Field(None, description="Gamma value")
    theta: Optional[float] = Field(None, description="Theta value")
    vega: Optional[float] = Field(None, description="Vega value")
    rho: Optional[float] = Field(None, description="Rho value")

class Quote(BaseModel):
    """Stock quote data."""
    symbol: str
    price: float = Field(..., gt=0)
    bid: float = Field(..., ge=0)
    ask: float = Field(..., ge=0)
    volume: int = Field(..., ge=0)
    timestamp: datetime = Field(default_factory=datetime.now)

class OptionContract(BaseModel):
    """Option contract data."""
    symbol: str
    description: str
    expiration_date: datetime
    dte: int = Field(..., ge=0)
    option_type: Literal['CALL', 'PUT']
    strike: float = Field(..., gt=0)
    bid: float = Field(..., ge=0)
    ask: float = Field(..., ge=0)
    last: float = Field(..., ge=0)
    total_volume: int = Field(..., ge=0)
    open_interest: int = Field(..., ge=0)
    implied_volatility: float = Field(..., ge=0)
    greeks: Greeks = Field(default_factory=Greeks)
    in_the_money: bool = False
    multiplier: float = 100.0

class TradeLeg(BaseModel):
    """Single leg of a trade."""
    symbol: str
    option_type: Literal['CALL', 'PUT']
    action: Literal['BUY', 'SELL']
    quantity: int = Field(..., gt=0)
    strike: float = Field(..., gt=0)
    expiration: datetime
    price: float = Field(..., ge=0)  # Premium per share

class Trade(BaseModel):
    """Complete trade structure."""
    symbol: str
    strategy: str
    bias: Literal['BULLISH', 'BEARISH', 'NEUTRAL']
    status: Literal['OPEN', 'CLOSED', 'PENDING'] = 'OPEN'
    timestamp: datetime = Field(default_factory=datetime.now)
    underlying_price: float = Field(..., gt=0)
    legs: List[TradeLeg]
    max_loss: float = Field(..., ge=0)
    max_gain: float = Field(..., ge=0)
    risk_reward_ratio: float = Field(..., ge=0)
    probability_of_profit: Optional[float] = Field(None, ge=0, le=1)
    score: Optional[float] = Field(None, ge=0, le=100)
    explanation: str = ""
