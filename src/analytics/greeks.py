"""Greeks calculations for options."""

import numpy as np
from scipy.stats import norm
from typing import Dict, Any, Optional
import math

from src.utils.logger import get_logger


logger = get_logger(__name__)


class GreeksCalculator:
    """Calculate option Greeks using Black-Scholes model."""
    
    @staticmethod
    def calculate_d1_d2(
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float
    ) -> tuple[float, float]:
        """
        Calculate d1 and d2 for Black-Scholes.
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (years)
            r: Risk-free rate
            sigma: Implied volatility (annualized)
            
        Returns:
            Tuple of (d1, d2)
        """
        if T <= 0 or sigma <= 0:
            return (0, 0)
        
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        return (d1, d2)
    
    @staticmethod
    def delta(
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: str = 'call'
    ) -> float:
        """
        Calculate option delta.
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (years)
            r: Risk-free rate
            sigma: Implied volatility
            option_type: 'call' or 'put'
            
        Returns:
            Delta value
        """
        if T <= 0:
            # At expiration
            if option_type.lower() == 'call':
                return 1.0 if S > K else 0.0
            else:
                return -1.0 if S < K else 0.0
        
        d1, _ = GreeksCalculator.calculate_d1_d2(S, K, T, r, sigma)
        
        if option_type.lower() == 'call':
            return norm.cdf(d1)
        else:
            return norm.cdf(d1) - 1
    
    @staticmethod
    def gamma(
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float
    ) -> float:
        """
        Calculate option gamma (same for calls and puts).
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (years)
            r: Risk-free rate
            sigma: Implied volatility
            
        Returns:
            Gamma value
        """
        if T <= 0 or sigma <= 0:
            return 0.0
        
        d1, _ = GreeksCalculator.calculate_d1_d2(S, K, T, r, sigma)
        
        gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
        return gamma
    
    @staticmethod
    def theta(
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: str = 'call'
    ) -> float:
        """
        Calculate option theta (per day).
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (years)
            r: Risk-free rate
            sigma: Implied volatility
            option_type: 'call' or 'put'
            
        Returns:
            Theta value (per day)
        """
        if T <= 0:
            return 0.0
        
        d1, d2 = GreeksCalculator.calculate_d1_d2(S, K, T, r, sigma)
        
        if option_type.lower() == 'call':
            theta = (
                -S * norm.pdf(d1) * sigma / (2 * np.sqrt(T))
                - r * K * np.exp(-r * T) * norm.cdf(d2)
            )
        else:
            theta = (
                -S * norm.pdf(d1) * sigma / (2 * np.sqrt(T))
                + r * K * np.exp(-r * T) * norm.cdf(-d2)
            )
        
        # Convert to per-day theta
        return theta / 365
    
    @staticmethod
    def vega(
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float
    ) -> float:
        """
        Calculate option vega (same for calls and puts).
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (years)
            r: Risk-free rate
            sigma: Implied volatility
            
        Returns:
            Vega value (per 1% change in IV)
        """
        if T <= 0:
            return 0.0
        
        d1, _ = GreeksCalculator.calculate_d1_d2(S, K, T, r, sigma)
        
        vega = S * norm.pdf(d1) * np.sqrt(T)
        
        # Return vega per 1% change in IV
        return vega / 100
    
    @staticmethod
    def calculate_all_greeks(
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: str = 'call'
    ) -> Dict[str, float]:
        """
        Calculate all Greeks for an option.
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (years)
            r: Risk-free rate
            sigma: Implied volatility
            option_type: 'call' or 'put'
            
        Returns:
            Dictionary with all Greeks
        """
        return {
            'delta': GreeksCalculator.delta(S, K, T, r, sigma, option_type),
            'gamma': GreeksCalculator.gamma(S, K, T, r, sigma),
            'theta': GreeksCalculator.theta(S, K, T, r, sigma, option_type),
            'vega': GreeksCalculator.vega(S, K, T, r, sigma)
        }
    
    @staticmethod
    def theta_per_hour(theta_per_day: float, market_hours: float = 6.5) -> float:
        """
        Convert theta per day to theta per hour.
        
        Args:
            theta_per_day: Theta value per day
            market_hours: Trading hours per day (default: 6.5)
            
        Returns:
            Theta per hour
        """
        return theta_per_day / market_hours
