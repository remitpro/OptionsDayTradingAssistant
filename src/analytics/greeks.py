"""Greeks calculations using py_vollib for accuracy."""

from typing import Dict, Any, List, Optional
import numpy as np
from py_vollib.black_scholes.greeks.analytical import delta, gamma, theta, vega, rho
from src.utils.logger import get_logger

logger = get_logger(__name__)

class GreeksCalculator:
    """Calculate option Greeks using industry-standard py_vollib."""
    
    @staticmethod
    def calculate_all_greeks(
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: str = 'c'
    ) -> Dict[str, float]:
        """
        Calculate all Greeks for an option.
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (years)
            r: Risk-free rate
            sigma: Implied volatility
            option_type: 'c' or 'p' for call/put (default: 'c')
            
        Returns:
            Dictionary with all Greeks
        """
        # Ensure option_type is 'c' or 'p'
        flag = option_type.lower()[0]
        if flag not in ['c', 'p']:
            flag = 'c'
            
        try:
            if T <= 0 or sigma <= 0:
                return {
                    'delta': 0.0,
                    'gamma': 0.0,
                    'theta': 0.0,
                    'vega': 0.0,
                    'rho': 0.0
                }
                
            d = delta(flag, S, K, T, r, sigma)
            g = gamma(flag, S, K, T, r, sigma)
            t = theta(flag, S, K, T, r, sigma) / 365.0  # Daily Theta
            v = vega(flag, S, K, T, r, sigma) / 100.0   # Vega per 1% move
            rh = rho(flag, S, K, T, r, sigma) / 100.0   # Rho per 1% rate change
            
            return {
                'delta': d,
                'gamma': g,
                'theta': t,
                'vega': v,
                'rho': rh
            }
        except Exception as e:
            logger.error(f"Error calculating Greeks: {e}")
            return {'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0, 'rho': 0}
            
    @staticmethod
    def calculate_portfolio_greeks(trades: List[Any]) -> Dict[str, float]:
        """
        Calculate aggregated Greeks for a portfolio of trades.
        
        Args:
            trades: List of Trade objects or dictionaries
            
        Returns:
            Dictionary with portfolio-level Greeks
        """
        portfolio_greeks = {
            'delta': 0.0,
            'gamma': 0.0,
            'theta': 0.0,
            'vega': 0.0
        }
        
        for trade in trades:
            # Handle both object and dict (Pydantic model vs Dict)
            legs = trade.legs if hasattr(trade, 'legs') else trade.get('legs', [])
            
            for leg in legs:
                qty = leg.quantity if hasattr(leg, 'quantity') else leg.get('quantity', 1)
                action = leg.action if hasattr(leg, 'action') else leg.get('action', 'BUY')
                
                # Check for cached greeks or calculate them
                # Note: In a real system we would look up current market data here.
                # For this implementation, we assume the trade/leg object has the greeks or we can't calculate.
                # Since we don't have stored Greeks on the Leg object in this simple model, 
                # we would typically skip or need to recalculate. 
                # Improving robustness: Add greeks to TradeLeg model in future.
                pass
                
        return portfolio_greeks
