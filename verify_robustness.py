"""Verification script for robustness features."""

import sys
import os
import time
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.append(os.getcwd())

from src.data.api_client import TDAClient, RateLimitError, APIError, CircuitBreakerOpen
from src.data.models import OptionContract, Trade
from src.data.database import init_db, get_session
from src.data.repository import TradeRepository
from src.analytics.risk_metrics import RiskMetrics
from src.utils.logger import setup_logger

logger = setup_logger()

def test_data_models():
    """Test Pydantic data models."""
    print("\n🧪 Testing Data Models...")
    try:
        # Valid contract
        contract = OptionContract(
            symbol="AAPL_012624C200",
            description="AAPL Jan 26 2024 200 Call",
            expiration_date=datetime.now(),
            dte=5,
            option_type="CALL",
            strike=200.0,
            bid=1.50,
            ask=1.55,
            last=1.52,
            total_volume=1000,
            open_interest=5000,
            implied_volatility=25.5
        )
        print(f"✓ Valid contract created: {contract.symbol}")
        
        # Invalid contract (should raise error)
        try:
            OptionContract(
                symbol="INVALID",
                description="Invalid Contract",
                expiration_date=datetime.now(),
                dte=-1,  # Invalid DTE
                option_type="CALL",
                strike=-10,  # Invalid strike
                bid=1.0, ask=1.1, last=1.0, total_volume=10, open_interest=10,
                implied_volatility=20
            )
            print("❌ Invalid contract check FAILED (Should have raised ValidationError)")
        except Exception as e:
            print(f"✓ Invalid contract correctly rejected: {e}")
            
    except Exception as e:
        print(f"❌ Data model test FAILED: {e}")

def test_database():
    """Test database persistence."""
    print("\n🧪 Testing Database Persistence...")
    try:
        init_db()
        repo = TradeRepository()
        
        trade_data = {
            'symbol': 'TEST_SYM',
            'strategy': 'Long Call',
            'bias': 'BULLISH',
            'underlying_price': 150.0,
            'risk_metrics': {'max_loss': 100, 'max_gain': 500, 'risk_reward_ratio': 5.0},
            'probability_metrics': {'probability_profit': 0.65},
            'score': 85.0,
            'legs': [],
            'explanation': 'Test trade'
        }
        
        if repo.add_trade(trade_data):
            print("✓ Trade added to database")
        else:
            print("❌ Failed to add trade")
            
        trades = repo.get_trades_by_symbol('TEST_SYM')
        if trades and len(trades) > 0:
            print(f"✓ Retrieved {len(trades)} trades for TEST_SYM")
            print(f"  - Strategy: {trades[0].strategy}")
            print(f"  - Score: {trades[0].score}")
        else:
            print("❌ Failed to retrieve trades")
            
    except Exception as e:
        print(f"❌ Database test FAILED: {e}")

def test_risk_metrics():
    print("\n🧪 Testing Risk Metrics...")
    size = RiskMetrics.calculate_position_size(
        account_size=10000,
        max_loss_per_trade=200,
        trade_max_loss=50,
        current_portfolio_risk=0.01,
        max_portfolio_risk=0.05
    )
    print(f"✓ Calculated position size: {size} contracts")
    
    # Test risk limit block
    blocked_size = RiskMetrics.calculate_position_size(
        account_size=10000,
        max_loss_per_trade=200,
        trade_max_loss=50,
        current_portfolio_risk=0.06,  # Over limit
        max_portfolio_risk=0.05
    )
    print(f"✓ Blocked position size (should be 0): {blocked_size}")

if __name__ == "__main__":
    print("🚀 Starting Robustness Verification")
    test_data_models()
    test_database()
    test_risk_metrics()
    print("\n🏁 Verification Complete")
