"""Market scanner for filtering stock candidates."""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from config.settings import get_settings
from src.data import get_client, get_cache
from src.utils.logger import get_logger
from src.utils.validators import is_valid_price, calculate_spread_pct

# New Components
from src.data.validator import DataValidator
from src.analytics.anomaly import AnomalyDetector
from src.analytics.indicators import TechnicalIndicators

logger = get_logger(__name__)


class MarketScanner:
    """Scan and filter stocks based on trading criteria."""
    
    def __init__(self):
        """Initialize market scanner."""
        self.settings = get_settings()
        self.client = get_client()
        self.cache = get_cache()
        
        # Initialize robust components
        self.validator = DataValidator()
        self.anomaly_detector = AnomalyDetector()
    
    def scan_market(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """
        Scan market and return filtered candidates.
        
        Args:
            symbols: List of symbols to scan
            
        Returns:
            List of candidate dictionaries with analysis
        """
        logger.info(f"🔍 Scanning {len(symbols)} symbols...")
        
        candidates = []
        
        for symbol in symbols:
            try:
                # Get quote data
                quote = self._get_quote_with_cache(symbol)
                if not quote:
                    continue
                
                # 1. New: Data Freshness Check
                if not self.validator.check_freshness(quote.get('quoteTimeInLong', 0)):
                    continue
                    
                # Apply filters
                if not self._apply_price_filter(quote):
                    continue
                
                if not self._apply_spread_filter(quote):
                    continue
                
                # Get price history
                history = self._get_price_history_with_cache(symbol)
                if not history:
                    continue
                
                # 2. New: Anomaly Check
                candles = history.get('candles', [])
                if candles:
                    prices = [c.get('close') for c in candles]
                    if self.anomaly_detector.is_price_anomaly(quote.get('lastPrice', 0), prices):
                        logger.warning(f"Rejecting {symbol}: Price anomaly detected")
                        continue
                
                # Calculate ATR (Legacy method preserved for stability or can switch to library)
                atr = self._calculate_atr(history)
                if atr is None or atr < self.settings.min_atr:
                    continue
                
                # Check volume
                avg_volume = self._calculate_avg_volume(history)
                if not self._apply_volume_filter(quote, avg_volume):
                    continue
                
                # 3. New: RSI Check
                item_rsi = 50.0  # Default
                if len(candles) > 15:
                    closes = pd.Series([c.get('close') for c in candles])
                    rsi_series = TechnicalIndicators.calculate_rsi(closes)
                    item_rsi = rsi_series.iloc[-1]
                
                # Analyze VWAP
                vwap_bias = self._analyze_vwap(quote, history)
                
                # Filter by RSI (Basic logic: Don't buy if overbought > 70)
                if item_rsi > 75 and vwap_bias == 'bullish':
                     logger.debug(f"Skipping {symbol}: RSI {item_rsi:.1f} (Overbought)")
                     continue
                if item_rsi < 25 and vwap_bias == 'bearish':
                     continue
                
                # Candidate passed all filters
                candidate = {
                    'symbol': symbol,
                    'price': quote.get('lastPrice', 0),
                    'bid': quote.get('bidPrice', 0),
                    'ask': quote.get('askPrice', 0),
                    'volume': quote.get('totalVolume', 0),
                    'avg_volume': avg_volume,
                    'atr': atr,
                    'rsi': item_rsi,
                    'vwap_bias': vwap_bias,
                    'timestamp': datetime.now().isoformat()
                }
                
                candidates.append(candidate)
                logger.info(f"✓ {symbol}: ${quote.get('lastPrice', 0):.2f} | "
                          f"ATR: {atr:.2f} | RSI: {item_rsi:.1f} | Bias: {vwap_bias}")
                
            except Exception as e:
                logger.error(f"Error scanning {symbol}: {e}")
                continue
        
        logger.info(f"✓ Found {len(candidates)} candidates")
        return candidates
    
    def _get_quote_with_cache(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get quote with caching."""
        # Check cache first
        cached = self.cache.get_quote(symbol)
        if cached:
            return cached
        
        # Fetch from API
        quote = self.client.get_quote(symbol)
        if quote:
            self.cache.set_quote(symbol, quote)
        
        return quote
    
    def _get_price_history_with_cache(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get price history with caching."""
        # Check cache first
        cached = self.cache.get_price_history(symbol)
        if cached:
            return cached
        
        # Fetch from API (last 20 days for ATR calculation)
        history = self.client.get_price_history(
            symbol,
            period_type='day',
            period=20,
            frequency_type='daily',
            frequency=1
        )
        
        if history:
            self.cache.set_price_history(symbol, history)
        
        return history
    
    def _apply_price_filter(self, quote: Dict[str, Any]) -> bool:
        """Filter by price range."""
        price = quote.get('lastPrice', 0)
        
        if not is_valid_price(price):
            return False
        
        return self.settings.min_stock_price <= price <= self.settings.max_stock_price
    
    def _apply_spread_filter(self, quote: Dict[str, Any]) -> bool:
        """Filter by bid-ask spread."""
        bid = quote.get('bidPrice', 0)
        ask = quote.get('askPrice', 0)
        
        if not is_valid_price(bid) or not is_valid_price(ask):
            return False
        
        spread_pct = calculate_spread_pct(bid, ask)
        return spread_pct <= self.settings.max_stock_spread_pct
    
    def _apply_volume_filter(self, quote: Dict[str, Any], avg_volume: float) -> bool:
        """Filter by volume criteria."""
        current_volume = quote.get('totalVolume', 0)
        
        # Check average volume
        if avg_volume < self.settings.min_avg_volume:
            return False
        
        # Check today's volume vs average
        if current_volume < avg_volume * self.settings.volume_multiplier:
            return False
        
        return True
    
    def _calculate_atr(self, history: Dict[str, Any], period: int = 14) -> Optional[float]:
        """
        Calculate Average True Range (ATR).
        
        Args:
            history: Price history data
            period: ATR period (default: 14)
            
        Returns:
            ATR value or None if insufficient data
        """
        candles = history.get('candles', [])
        
        if len(candles) < period + 1:
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(candles)
        
        # Calculate True Range
        df['high_low'] = df['high'] - df['low']
        df['high_close'] = abs(df['high'] - df['close'].shift())
        df['low_close'] = abs(df['low'] - df['close'].shift())
        
        df['true_range'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
        
        # Calculate ATR
        atr = df['true_range'].rolling(window=period).mean().iloc[-1]
        
        return float(atr) if not pd.isna(atr) else None
    
    def _calculate_avg_volume(self, history: Dict[str, Any], period: int = 20) -> float:
        """
        Calculate average volume.
        
        Args:
            history: Price history data
            period: Averaging period
            
        Returns:
            Average volume
        """
        candles = history.get('candles', [])
        
        if not candles:
            return 0
        
        volumes = [c.get('volume', 0) for c in candles[-period:]]
        return np.mean(volumes) if volumes else 0
    
    def _analyze_vwap(self, quote: Dict[str, Any], history: Dict[str, Any]) -> str:
        """
        Analyze price relationship to VWAP.
        
        Args:
            quote: Current quote data
            history: Price history data
            
        Returns:
            'bullish', 'bearish', or 'neutral'
        """
        current_price = quote.get('lastPrice', 0)
        
        # Calculate VWAP from today's data
        candles = history.get('candles', [])
        if not candles:
            return 'neutral'
        
        # Use last candle as proxy for intraday VWAP
        # In production, you'd want intraday minute data
        recent_candles = candles[-5:]  # Last 5 days
        
        total_volume = sum(c.get('volume', 0) for c in recent_candles)
        if total_volume == 0:
            return 'neutral'
        
        # Weighted average price
        vwap = sum(
            ((c.get('high', 0) + c.get('low', 0) + c.get('close', 0)) / 3) * c.get('volume', 0)
            for c in recent_candles
        ) / total_volume
        
        # Determine bias
        threshold = 0.005  # 0.5% threshold
        diff_pct = (current_price - vwap) / vwap
        
        if diff_pct > threshold:
            return 'bullish'
        elif diff_pct < -threshold:
            return 'bearish'
        else:
            return 'neutral'


def get_default_symbols() -> List[str]:
    """
    Get default list of liquid symbols to scan.
    
    Returns:
        List of ticker symbols
    """
    # Popular liquid stocks across sectors
    return [
        # Tech
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'AMD', 'INTC', 'NFLX',
        # Finance
        'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C',
        # Healthcare
        'JNJ', 'UNH', 'PFE', 'ABBV', 'TMO', 'MRK',
        # Consumer
        'WMT', 'HD', 'DIS', 'NKE', 'SBUX', 'MCD',
        # Energy
        'XOM', 'CVX', 'COP', 'SLB',
        # Industrial
        'BA', 'CAT', 'GE', 'UPS',
        # Communication
        'T', 'VZ', 'CMCSA',
        # Retail
        'TGT', 'COST', 'LOW',
        # Semiconductor
        'AVGO', 'QCOM', 'TXN', 'AMAT',
        # Software
        'CRM', 'ORCL', 'ADBE', 'NOW',
        # Auto
        'F', 'GM',
        # Biotech
        'GILD', 'AMGN', 'BIIB',
        # ETFs (high volume)
        'SPY', 'QQQ', 'IWM', 'DIA'
    ]
