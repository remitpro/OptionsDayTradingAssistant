"""TD Ameritrade API client wrapper with rate limiting and caching."""

import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import tda
from tda import auth
from pathlib import Path

from config.settings import get_settings
from src.utils.logger import get_logger


logger = get_logger(__name__)


class TDAClient:
    """Wrapper for TD Ameritrade API with rate limiting and error handling."""
    
    def __init__(self):
        """Initialize TD Ameritrade client."""
        self.settings = get_settings()
        self.client: Optional[tda.client.Client] = None
        self._last_request_time = 0
        self._min_request_interval = 0.5  # 500ms between requests (120/min limit)
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize and authenticate TD Ameritrade client."""
        try:
            token_path = Path(self.settings.tda_token_path)
            token_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Try to load existing token or create new one
            try:
                self.client = auth.client_from_token_file(
                    str(token_path),
                    self.settings.tda_api_key
                )
                logger.info("✓ TD Ameritrade client authenticated from token file")
            except FileNotFoundError:
                logger.warning("Token file not found. Manual authentication required.")
                logger.info(f"Please run authentication: python -m tda.auth")
                logger.info(f"API Key: {self.settings.tda_api_key}")
                logger.info(f"Redirect URI: {self.settings.tda_redirect_uri}")
                logger.info(f"Token path: {token_path}")
                # For now, set client to None - will need manual auth
                self.client = None
        except Exception as e:
            logger.error(f"Failed to initialize TDA client: {e}")
            self.client = None
    
    def _rate_limit(self):
        """Enforce rate limiting between API requests."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self._min_request_interval:
            sleep_time = self._min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get real-time quote for a symbol.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Quote data dictionary or None if error
        """
        if not self.client:
            logger.error("TDA client not initialized")
            return None
        
        try:
            self._rate_limit()
            response = self.client.get_quote(symbol)
            
            if response.status_code == 200:
                data = response.json()
                return data.get(symbol, None)
            else:
                logger.error(f"Failed to get quote for {symbol}: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error getting quote for {symbol}: {e}")
            return None
    
    def get_quotes(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Get real-time quotes for multiple symbols.
        
        Args:
            symbols: List of stock ticker symbols
            
        Returns:
            Dictionary mapping symbols to quote data
        """
        if not self.client:
            logger.error("TDA client not initialized")
            return {}
        
        try:
            self._rate_limit()
            response = self.client.get_quotes(symbols)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get quotes: {response.status_code}")
                return {}
        except Exception as e:
            logger.error(f"Error getting quotes: {e}")
            return {}
    
    def get_price_history(
        self,
        symbol: str,
        period_type: str = 'day',
        period: int = 10,
        frequency_type: str = 'minute',
        frequency: int = 5
    ) -> Optional[Dict[str, Any]]:
        """
        Get historical price data for ATR and technical calculations.
        
        Args:
            symbol: Stock ticker symbol
            period_type: 'day', 'month', 'year', 'ytd'
            period: Number of periods
            frequency_type: 'minute', 'daily', 'weekly', 'monthly'
            frequency: Frequency value
            
        Returns:
            Price history data or None if error
        """
        if not self.client:
            logger.error("TDA client not initialized")
            return None
        
        try:
            self._rate_limit()
            response = self.client.get_price_history(
                symbol,
                period_type=tda.client.Client.PriceHistory.PeriodType[period_type.upper()],
                period=tda.client.Client.PriceHistory.Period[f'{period_type.upper()}S'](period),
                frequency_type=tda.client.Client.PriceHistory.FrequencyType[frequency_type.upper()],
                frequency=tda.client.Client.PriceHistory.Frequency[frequency_type.upper()](frequency)
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get price history for {symbol}: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error getting price history for {symbol}: {e}")
            return None
    
    def get_option_chain(
        self,
        symbol: str,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get options chain for a symbol.
        
        Args:
            symbol: Stock ticker symbol
            from_date: Start date for expiration range
            to_date: End date for expiration range
            
        Returns:
            Options chain data or None if error
        """
        if not self.client:
            logger.error("TDA client not initialized")
            return None
        
        try:
            self._rate_limit()
            
            # Build request
            request = self.client.get_option_chain(
                symbol,
                contract_type=tda.client.Client.Options.ContractType.ALL,
                include_quotes=True
            )
            
            # Add date range if specified
            if from_date:
                request = request.from_date(from_date)
            if to_date:
                request = request.to_date(to_date)
            
            response = request
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get option chain for {symbol}: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error getting option chain for {symbol}: {e}")
            return None
    
    def is_market_open(self) -> bool:
        """
        Check if market is currently open.
        
        Returns:
            True if market is open, False otherwise
        """
        if not self.client:
            logger.warning("TDA client not initialized, assuming market closed")
            return False
        
        try:
            self._rate_limit()
            response = self.client.get_hours_for_single_market(
                tda.client.Client.Markets.EQUITY,
                datetime.now()
            )
            
            if response.status_code == 200:
                data = response.json()
                equity_hours = data.get('equity', {}).get('EQ', {})
                return equity_hours.get('isOpen', False)
            else:
                logger.warning("Could not determine market hours")
                return False
        except Exception as e:
            logger.error(f"Error checking market hours: {e}")
            return False


# Global client instance
_client: Optional[TDAClient] = None


def get_client() -> TDAClient:
    """Get or create global TDA client instance."""
    global _client
    if _client is None:
        _client = TDAClient()
    return _client
