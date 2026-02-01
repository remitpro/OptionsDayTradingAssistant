"""Verification script for Phase 2 Analytics."""

import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.getcwd())

from src.analytics.greeks import GreeksCalculator
from src.analytics.portfolio import PortfolioManager
from src.utils.alerter import AlertManager
from src.data.database import init_db
from src.data.repository import TradeRepository

def test_greeks_calculation():
    print("[Test] Testing Real Greeks Code (py_vollib)...")
    # Test case: ATM Call
    # S=100, K=100, T=1yr, r=5%, sigma=20%
    # Expected: Delta ~ 0.63, Theta ~ -6.4
    
    greeks = GreeksCalculator.calculate_all_greeks(
        S=100.0, K=100.0, T=1.0, r=0.05, sigma=0.20, option_type='c'
    )
    
    print(f"Calculated Greeks: {greeks}")
    
    assert 0.60 < greeks['delta'] < 0.66, "Delta calculation looks off"
    assert greeks['theta'] < 0, "Theta should be negative for long call"
    print("[OK] Greeks calculation verified against expected range")

def test_portfolio_manager():
    print("\n[Test] Testing Portfolio Manager...")
    init_db()
    repo = TradeRepository()
    
    # Add a dummy open trade if none exist
    repo.add_trade({
        'symbol': 'TEST_PORTFOLIO',
        'strategy': 'Vertical',
        'bias': 'BULLISH',
        'status': 'OPEN',
        'underlying_price': 100,
        'risk_metrics': {'max_loss': 500},
        'score': 90
    })
    
    pm = PortfolioManager()
    summary = pm.get_portfolio_summary()
    
    print("Portfolio Summary:", summary)
    
    assert summary['open_positions'] > 0, "Should have at least 1 open position"
    assert summary['total_max_loss'] >= 500, "Max loss aggregation failed"
    print("[OK] Portfolio aggregation verified")

def test_alerts():
    print("\n[Test] Testing Alert System...")
    AlertManager.send_alert("Test Alert", "This is a verification test", "INFO")
    print("[OK] Alert sent (check logs)")

if __name__ == "__main__":
    print("Starting Phase 2 Verification")
    test_greeks_calculation()
    test_portfolio_manager()
    test_alerts()
    print("\nPhase 2 Verification Complete")
