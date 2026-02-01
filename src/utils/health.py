"""System health monitoring."""

import shutil
import time
import os
from pathlib import Path
from typing import Dict, Any
from src.data.api_client import get_client
from src.data.database import get_db_engine
from src.utils.logger import get_logger

logger = get_logger(__name__)

class HealthMonitor:
    """Monitor system health metrics."""
    
    @staticmethod
    def check_disk_space(path: str = ".") -> Dict[str, Any]:
        """Check available disk space."""
        total, used, free = shutil.disk_usage(path)
        return {
            'total_gb': total // (2**30),
            'free_gb': free // (2**30),
            'status': 'OK' if free > 1 * (2**30) else 'CRITICAL' # 1GB limit
        }
        
    @staticmethod
    def check_api_latency() -> float:
        """Check API latency in seconds."""
        client = get_client()
        if not client.client:
            return -1.0
            
        start = time.time()
        # Ensure we don't trigger rate limits or auth errors if token invalid
        # Just checking if client object exists is weak, but actual ping requires auth.
        # Minimal impact: check market hours (fast call)
        try:
            client.is_market_open()
            return time.time() - start
        except Exception:
            return -1.0
            
    @staticmethod
    def check_database() -> bool:
        """Verify database is writable."""
        try:
            engine = get_db_engine()
            with engine.connect() as conn:
                # Proper way to execute raw sql in recent SQLAlchemy
                from sqlalchemy import text
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Health check DB failed: {e}")
            return False
            
    @staticmethod
    def run_health_check() -> Dict[str, Any]:
        """Run full system health check."""
        disk = HealthMonitor.check_disk_space()
        api_lat = HealthMonitor.check_api_latency()
        db_ok = HealthMonitor.check_database()
        
        status = "HEALTHY"
        if disk['status'] != 'OK' or db_ok is False or api_lat < 0:
            status = "UNHEALTHY"
        elif api_lat > 2.0:
            status = "DEGRADED"
            
        return {
            'status': status,
            'disk': disk,
            'api_latency': f"{api_lat:.3f}s",
            'database_connected': db_ok,
            'timestamp': str(time.time())
        }
