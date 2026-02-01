"""TD Ameritrade API client wrapper with rate limiting and caching."""

import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import tda
from tda import auth
from pathlib import Path
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, before_sleep_log

from config.settings import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Custom Exceptions
class TDAClientError(Exception):
    """Base exception for TDA client errors."""
    pass

class RateLimitError(TDAClientError):
    """Raised when rate limit is exceeded."""
    pass

class APIError(TDAClientError):
    """Raised when API returns error status."""
    pass

class CircuitBreakerOpen(TDAClientError):
    """Raised when circuit breaker is open."""
    pass

class CircuitBreaker:
    """Simple Circuit Breaker pattern implementation."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure_time = 0
        self.is_open = False
    
    def record_failure(self):
        """Record a failure and potentially open circuit."""
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.failure_threshold:
            self.is_open = True
            logger.error("🔴 Circuit Breaker OPENED due to repeated failures")
            
    def record_success(self):
        """Reset failure count on success."""
        if self.failures > 0:
            self.failures = 0
            if self.is_open:
                self.is_open = False
                logger.info("🟢 Circuit Breaker CLOSED (Recovered)")
            
    def check_state(self):
        """Check if circuit is open and potentially attempt recovery."""
        if self.is_open:
            time_since_failure = time.time() - self.last_failure_time
            if time_since_failure > self.recovery_timeout:
                logger.info("🟡 Circuit Breaker: Attempting recovery...")
                return  # Allow one request through to test
            raise CircuitBreakerOpen("API requests blocked by circuit breaker")

class TDAClient:
    """Wrapper for TD Ameritrade API with rate limiting, retries, and error handling."""
    
    def __init__(self):
        """Initialize TD Ameritrade client."""
        self.settings = get_settings()
        self.client: Optional[tda.client.Client] = None
        self._last_request_time = 0
        self._min_request_interval = 0.5  # 500ms between requests
        self.circuit_breaker = CircuitBreaker()
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
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((RateLimitError, APIError)),
        before_sleep=before_sleep_log(logger, 20)  # Log at INFO level
    )
    def _make_request(self, method, *args, **kwargs):
        """Make API request with retry logic and circuit breaker."""
        if not self.client:
            raise TDAClientError("TDA client not initialized")
            
        self.circuit_breaker.check_state()
        self._rate_limit()
        
        try:
            response = method(*args, **kwargs)
            
            if response.status_code == 200:
                self.circuit_breaker.record_success()
                return response
            elif response.status_code == 429:
                # Rate limit
                logger.warning("Rate limit hit, triggering retry...")
                raise RateLimitError("Rate limit exceeded")
            else:
                self.circuit_breaker.record_failure()
                raise APIError(f"API Error {response.status_code}")
                
        except Exception as e:
            # Don't record failure for rate limits (handled by retry)
            if not isinstance(e, RateLimitError):
                self.circuit_breaker.record_failure()
            raise e

    def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get real-time quote for a symbol."""
        try:
            response = self._make_request(self.client.get_quote, symbol)
            data = response.json()
            return data.get(symbol, None)
        except Exception as e:
            logger.error(f"Error getting quote for {symbol}: {e}")
            return None
    
    def get_quotes(self, symbols: List[str]) -> Dict[str, Any]:
        """Get real-time quotes for multiple symbols."""
        try:
            response = self._make_request(self.client.get_quotes, symbols)
            return response.json()
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
        """Get historical price data."""
        try:
            response = self._make_request(
                self.client.get_price_history,
                symbol,
                period_type=tda.client.Client.PriceHistory.PeriodType[period_type.upper()],
                period=tda.client.Client.PriceHistory.Period[f'{period_type.upper()}S'](period),
                frequency_type=tda.client.Client.PriceHistory.FrequencyType[frequency_type.upper()],
                frequency=tda.client.Client.PriceHistory.Frequency[frequency_type.upper()](frequency)
            )
            return response.json()
        except Exception as e:
            logger.error(f"Error getting price history for {symbol}: {e}")
            return None
    
    def get_option_chain(
        self,
        symbol: str,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        """Get options chain for a symbol."""
        try:
            # Build request wrapper
            def _fetch_chain():
                request = self.client.get_option_chain(
                    symbol,
                    contract_type=tda.client.Client.Options.ContractType.ALL,
                    include_quotes=True
                )
                if from_date:
                    request = request.from_date(from_date)
                if to_date:
                    request = request.to_date(to_date)
                return request
            
            response = self._make_request(_fetch_chain)
            return response.json()
        except Exception as e:
            logger.error(f"Error getting option chain for {symbol}: {e}")
            return None
    
    def is_market_open(self) -> bool:
        """Check if market is currently open."""
        if not self.client:
            logger.warning("TDA client not initialized, assuming market closed")
            return False
        
        try:
            response = self._make_request(
                self.client.get_hours_for_single_market,
                tda.client.Client.Markets.EQUITY,
                datetime.now()
            )
            
            data = response.json()
            equity_hours = data.get('equity', {}).get('EQ', {})
            return equity_hours.get('isOpen', False)
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
