"""SQLite caching layer to reduce API calls."""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import contextmanager

from src.utils.logger import get_logger


logger = get_logger(__name__)


class Cache:
    """SQLite-based cache for market data."""
    
    def __init__(self, db_path: str = "data.db"):
        """
        Initialize cache database.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self._init_database()
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def _init_database(self):
        """Create database tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Quotes cache table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS quotes (
                    symbol TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    timestamp REAL NOT NULL
                )
            """)
            
            # Price history cache table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS price_history (
                    symbol TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    timestamp REAL NOT NULL
                )
            """)
            
            # Options chain cache table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS option_chains (
                    symbol TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    timestamp REAL NOT NULL
                )
            """)
            
            # Scan results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scan_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_date TEXT NOT NULL,
                    results TEXT NOT NULL,
                    timestamp REAL NOT NULL
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_quotes_timestamp ON quotes(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_price_history_timestamp ON price_history(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_option_chains_timestamp ON option_chains(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_scan_results_date ON scan_results(scan_date)")
            
            logger.info("✓ Cache database initialized")
    
    def _is_expired(self, timestamp: float, ttl_seconds: int) -> bool:
        """Check if cached data is expired."""
        age = datetime.now().timestamp() - timestamp
        return age > ttl_seconds
    
    def get_quote(self, symbol: str, ttl_seconds: int = 60) -> Optional[Dict[str, Any]]:
        """
        Get cached quote if available and not expired.
        
        Args:
            symbol: Stock ticker symbol
            ttl_seconds: Time to live in seconds (default: 60)
            
        Returns:
            Cached quote data or None
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT data, timestamp FROM quotes WHERE symbol = ?",
                (symbol,)
            )
            row = cursor.fetchone()
            
            if row:
                if not self._is_expired(row['timestamp'], ttl_seconds):
                    return json.loads(row['data'])
                else:
                    # Delete expired entry
                    cursor.execute("DELETE FROM quotes WHERE symbol = ?", (symbol,))
            
            return None
    
    def set_quote(self, symbol: str, data: Dict[str, Any]):
        """
        Cache quote data.
        
        Args:
            symbol: Stock ticker symbol
            data: Quote data to cache
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO quotes (symbol, data, timestamp) VALUES (?, ?, ?)",
                (symbol, json.dumps(data), datetime.now().timestamp())
            )
    
    def get_price_history(self, symbol: str, ttl_seconds: int = 3600) -> Optional[Dict[str, Any]]:
        """
        Get cached price history if available and not expired.
        
        Args:
            symbol: Stock ticker symbol
            ttl_seconds: Time to live in seconds (default: 3600 = 1 hour)
            
        Returns:
            Cached price history or None
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT data, timestamp FROM price_history WHERE symbol = ?",
                (symbol,)
            )
            row = cursor.fetchone()
            
            if row:
                if not self._is_expired(row['timestamp'], ttl_seconds):
                    return json.loads(row['data'])
                else:
                    cursor.execute("DELETE FROM price_history WHERE symbol = ?", (symbol,))
            
            return None
    
    def set_price_history(self, symbol: str, data: Dict[str, Any]):
        """
        Cache price history data.
        
        Args:
            symbol: Stock ticker symbol
            data: Price history data to cache
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO price_history (symbol, data, timestamp) VALUES (?, ?, ?)",
                (symbol, json.dumps(data), datetime.now().timestamp())
            )
    
    def get_option_chain(self, symbol: str, ttl_seconds: int = 300) -> Optional[Dict[str, Any]]:
        """
        Get cached option chain if available and not expired.
        
        Args:
            symbol: Stock ticker symbol
            ttl_seconds: Time to live in seconds (default: 300 = 5 minutes)
            
        Returns:
            Cached option chain or None
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT data, timestamp FROM option_chains WHERE symbol = ?",
                (symbol,)
            )
            row = cursor.fetchone()
            
            if row:
                if not self._is_expired(row['timestamp'], ttl_seconds):
                    return json.loads(row['data'])
                else:
                    cursor.execute("DELETE FROM option_chains WHERE symbol = ?", (symbol,))
            
            return None
    
    def set_option_chain(self, symbol: str, data: Dict[str, Any]):
        """
        Cache option chain data.
        
        Args:
            symbol: Stock ticker symbol
            data: Option chain data to cache
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO option_chains (symbol, data, timestamp) VALUES (?, ?, ?)",
                (symbol, json.dumps(data), datetime.now().timestamp())
            )
    
    def save_scan_results(self, results: List[Dict[str, Any]]):
        """
        Save scan results for historical tracking.
        
        Args:
            results: List of scan result dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            scan_date = datetime.now().strftime("%Y-%m-%d")
            cursor.execute(
                "INSERT INTO scan_results (scan_date, results, timestamp) VALUES (?, ?, ?)",
                (scan_date, json.dumps(results), datetime.now().timestamp())
            )
            logger.info(f"✓ Saved scan results for {scan_date}")
    
    def clear_expired(self):
        """Clear all expired cache entries."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            now = datetime.now().timestamp()
            
            # Clear expired quotes (> 1 minute)
            cursor.execute("DELETE FROM quotes WHERE timestamp < ?", (now - 60,))
            
            # Clear expired price history (> 1 hour)
            cursor.execute("DELETE FROM price_history WHERE timestamp < ?", (now - 3600,))
            
            # Clear expired option chains (> 5 minutes)
            cursor.execute("DELETE FROM option_chains WHERE timestamp < ?", (now - 300,))
            
            logger.info("✓ Cleared expired cache entries")


# Global cache instance
_cache: Optional[Cache] = None


def get_cache() -> Cache:
    """Get or create global cache instance."""
    global _cache
    if _cache is None:
        _cache = Cache()
    return _cache
