"""Portfolio risk management and aggregation."""

from typing import List, Dict, Any
from sqlalchemy.orm import Session
from src.data.database import TradeModel, get_session
from src.data.repository import TradeRepository
from src.analytics.greeks import GreeksCalculator
from src.utils.logger import get_logger

logger = get_logger(__name__)

class PortfolioManager:
    """Manage portfolio risk and open positions."""
    
    def __init__(self, session: Session = None):
        self.repo = TradeRepository(session)
        
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """
        Get summary of current portfolio risk.
        
        Returns:
            Dictionary with portfolio metrics
        """
        # Get all OPEN trades (In a real app, strict filtering by status='OPEN')
        # Since we just added status, older trades might be null, but default is OPEN in Python code? 
        # Actually SQL default only applies to new rows. Let's filter manually safely.
        
        all_trades = self.repo.get_recent_trades(limit=100)
        open_trades = [t for t in all_trades if t.status == 'OPEN']
        
        total_delta = 0.0
        total_theta = 0.0
        total_gamma = 0.0
        total_vega = 0.0
        total_max_loss = 0.0
        
        for trade in open_trades:
            # Aggregate Max Loss
            total_max_loss += trade.max_loss if trade.max_loss else 0
            
            # Aggregate Greeks (assuming stored in risk_metrics or calculated)
            # For now, we'll try to use stored values if available
            if trade.risk_metrics:
                # In a real dynamic system, Greeks change every second.
                # Here we are just summing the snapshot Greeks at entry for initial risk assessment.
                # To be robust in Phase 3, we would re-calculate current Greeks here.
                pass
                
            # TODO: Implement dynamic re-calculation of Greeks for open positions
            # This requires fetching current price of underlying which is expensive for many trades.
            
        return {
            'open_positions': len(open_trades),
            'total_max_loss': total_max_loss,
            'total_delta': total_delta,  # Placeholder until dynamic recalculation
            'timestamp': str(datetime.now())
        }
        
    def check_portfolio_risk(self, new_trade_risk: float, max_risk: float) -> bool:
        """
        Check if adding a new trade exceeds portfolio risk limits.
        
        Args:
            new_trade_risk: Max loss of the new trade
            max_risk: Maximum allowable total portfolio loss
            
        Returns:
            True if within limits, False if risk exceeded
        """
        summary = self.get_portfolio_summary()
        current_risk = summary['total_max_loss']
        
        if current_risk + new_trade_risk > max_risk:
            logger.warning(f"Risk rejected: New total {current_risk + new_trade_risk} > Limit {max_risk}")
            return False
            
        return True

from datetime import datetime
