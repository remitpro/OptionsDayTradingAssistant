"""Verification script for Phase 3 Health & Data Quality."""

import sys
import os
import time
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.getcwd())

from src.data.validator import DataValidator
from src.analytics.anomaly import AnomalyDetector
from src.utils.health import HealthMonitor

def test_data_validator():
    print("[Test] Testing Data Validator...")
    validator = DataValidator(max_age_seconds=60)
    
    # Fresh data
    now_ms = time.time() * 1000
    assert validator.check_freshness(now_ms) is True, "Fresh data valid check failed"
    
    # Stale data (2 mins old)
    old_ms = (time.time() - 120) * 1000
    assert validator.check_freshness(old_ms) is False, "Stale data invalid check failed"
    
    print("[OK] Data freshness logic verified")

def test_anomaly_detector():
    print("\n[Test] Testing Anomaly Detector...")
    detector = AnomalyDetector()
    
    # Normal price history
    history = [100.0, 100.1, 99.9, 100.2, 100.0]
    is_anomaly = detector.is_price_anomaly(100.1, history)
    assert is_anomaly is False, "Normal price flagged as anomaly"
    
    # Spike (Flash crash scenario)
    is_anomaly = detector.is_price_anomaly(50.0, history)
    assert is_anomaly is True, "Price spike NOT flagged as anomaly"
    
    print("[OK] Anomaly detection logic verified")

def test_health_monitor():
    print("\n[Test] Testing System Health Monitor...")
    report = HealthMonitor.run_health_check()
    
    print(f"Health Report: {report}")
    
    assert 'status' in report
    # We expect HEALTHY or UNHEALTHY depending on env, but structure must match
    assert isinstance(report['disk'], dict)
    
    print("[OK] Health monitor ran successfully")

if __name__ == "__main__":
    print("Starting Phase 3 Verification")
    test_data_validator()
    test_anomaly_detector()
    test_health_monitor()
    print("\nPhase 3 Verification Complete")
