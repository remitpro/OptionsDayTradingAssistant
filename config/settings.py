"""Configuration management for the Options Trading Assistant."""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # TD Ameritrade API
    tda_api_key: str = Field(..., env='TDA_API_KEY')
    tda_redirect_uri: str = Field(default='https://localhost', env='TDA_REDIRECT_URI')
    tda_token_path: str = Field(default='./config/token.json', env='TDA_TOKEN_PATH')

    # Database
    database_url: str = Field(..., env='DATABASE_URL')
    
    # Stock Scanner Parameters
    min_stock_price: float = Field(default=20.0, env='MIN_STOCK_PRICE')
    max_stock_price: float = Field(default=300.0, env='MAX_STOCK_PRICE')
    min_avg_volume: int = Field(default=1_000_000, env='MIN_AVG_VOLUME')
    volume_multiplier: float = Field(default=1.3, env='VOLUME_MULTIPLIER')
    min_atr: float = Field(default=1.5, env='MIN_ATR')
    max_stock_spread_pct: float = Field(default=0.2, env='MAX_STOCK_SPREAD_PCT')
    
    # Options Filters
    min_dte: int = Field(default=0, env='MIN_DTE')
    max_dte: int = Field(default=7, env='MAX_DTE')
    min_open_interest: int = Field(default=1000, env='MIN_OPEN_INTEREST')
    min_option_volume: int = Field(default=300, env='MIN_OPTION_VOLUME')
    max_option_spread_pct: float = Field(default=5.0, env='MAX_OPTION_SPREAD_PCT')
    
    # Strategy Parameters
    low_iv_threshold: float = Field(default=30.0, env='LOW_IV_THRESHOLD')
    high_iv_threshold: float = Field(default=60.0, env='HIGH_IV_THRESHOLD')
    extreme_iv_threshold: float = Field(default=100.0, env='EXTREME_IV_THRESHOLD')
    
    # Scoring Weights
    weight_probability: float = Field(default=0.30, env='WEIGHT_PROBABILITY')
    weight_risk_reward: float = Field(default=0.25, env='WEIGHT_RISK_REWARD')
    weight_iv_edge: float = Field(default=0.20, env='WEIGHT_IV_EDGE')
    weight_liquidity: float = Field(default=0.15, env='WEIGHT_LIQUIDITY')
    weight_trend: float = Field(default=0.10, env='WEIGHT_TREND')
    
    # Output Settings
    min_trade_score: float = Field(default=70.0, env='MIN_TRADE_SCORE')
    max_trades_output: int = Field(default=5, env='MAX_TRADES_OUTPUT')
    output_dir: str = Field(default='outputs', env='OUTPUT_DIR')
    
    # Risk Limits
    max_position_size: int = Field(default=10, env='MAX_POSITION_SIZE')
    max_loss_per_trade: float = Field(default=1000.0, env='MAX_LOSS_PER_TRADE')
    
    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        case_sensitive = False


# Global settings instance
settings: Optional[Settings] = None


def load_settings() -> Settings:
    """Load and return application settings."""
    global settings
    if settings is None:
        settings = Settings()
    return settings


def get_settings() -> Settings:
    """Get current settings instance."""
    if settings is None:
        return load_settings()
    return settings
