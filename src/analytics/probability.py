"""Probability calculations using Black-Scholes and Monte Carlo."""

import numpy as np
from scipy.stats import norm
from typing import Dict, Any, Optional
import math

from src.utils.logger import get_logger
from .greeks import GreeksCalculator


logger = get_logger(__name__)


class ProbabilityCalculator:
    """Calculate probabilities for options trading."""
    
    @staticmethod
    def probability_itm(
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: str = 'call'
    ) -> float:
        """
        Calculate probability of finishing in-the-money.
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (years)
            r: Risk-free rate
            sigma: Implied volatility
            option_type: 'call' or 'put'
            
        Returns:
            Probability ITM (0-1)
        """
        if T <= 0:
            if option_type.lower() == 'call':
                return 1.0 if S > K else 0.0
            else:
                return 1.0 if S < K else 0.0
        
        _, d2 = GreeksCalculator.calculate_d1_d2(S, K, T, r, sigma)
        
        if option_type.lower() == 'call':
            return norm.cdf(d2)
        else:
            return norm.cdf(-d2)
    
    @staticmethod
    def probability_touch(
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: str = 'call'
    ) -> float:
        """
        Calculate probability of touching strike price before expiration.
        Approximation: P(touch) ≈ 2 × Delta
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (years)
            r: Risk-free rate
            sigma: Implied volatility
            option_type: 'call' or 'put'
            
        Returns:
            Probability of touch (0-1)
        """
        delta = GreeksCalculator.delta(S, K, T, r, sigma, option_type)
        prob_touch = min(2 * abs(delta), 1.0)
        return prob_touch
    
    @staticmethod
    def expected_move(
        S: float,
        sigma: float,
        T: float
    ) -> float:
        """
        Calculate expected move (1 standard deviation).
        
        Args:
            S: Current stock price
            sigma: Implied volatility (annualized)
            T: Time to expiration (years)
            
        Returns:
            Expected move in dollars
        """
        return S * sigma * math.sqrt(T)
    
    @staticmethod
    def monte_carlo_simulation(
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: str = 'call',
        num_simulations: int = 10000
    ) -> Dict[str, Any]:
        """
        Run Monte Carlo simulation for option pricing and probability.
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (years)
            r: Risk-free rate
            sigma: Implied volatility
            option_type: 'call' or 'put'
            num_simulations: Number of price paths to simulate
            
        Returns:
            Dictionary with simulation results
        """
        if T <= 0:
            return {
                'probability_profit': 1.0 if (S > K and option_type == 'call') or (S < K and option_type == 'put') else 0.0,
                'avg_profit': max(S - K, 0) if option_type == 'call' else max(K - S, 0),
                'max_profit': max(S - K, 0) if option_type == 'call' else max(K - S, 0),
                'max_loss': 0
            }
        
        # Generate random price paths using Geometric Brownian Motion
        dt = T
        drift = (r - 0.5 * sigma ** 2) * dt
        diffusion = sigma * math.sqrt(dt)
        
        # Random samples
        Z = np.random.standard_normal(num_simulations)
        
        # Final stock prices
        ST = S * np.exp(drift + diffusion * Z)
        
        # Calculate payoffs
        if option_type.lower() == 'call':
            payoffs = np.maximum(ST - K, 0)
        else:
            payoffs = np.maximum(K - ST, 0)
        
        # Discount payoffs
        discounted_payoffs = payoffs * np.exp(-r * T)
        
        # Calculate statistics
        profitable_paths = np.sum(payoffs > 0)
        probability_profit = profitable_paths / num_simulations
        
        avg_profit = np.mean(discounted_payoffs)
        max_profit = np.max(discounted_payoffs)
        
        return {
            'probability_profit': float(probability_profit),
            'avg_profit': float(avg_profit),
            'max_profit': float(max_profit),
            'expected_value': float(avg_profit),
            'final_prices': ST.tolist()[:100]  # Return first 100 for analysis
        }
    
    @staticmethod
    def calculate_probabilities(
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: str = 'call',
        run_monte_carlo: bool = True
    ) -> Dict[str, Any]:
        """
        Calculate all probabilities for an option.
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (years)
            r: Risk-free rate
            sigma: Implied volatility
            option_type: 'call' or 'put'
            run_monte_carlo: Whether to run Monte Carlo simulation
            
        Returns:
            Dictionary with all probability metrics
        """
        results = {
            'probability_itm': ProbabilityCalculator.probability_itm(S, K, T, r, sigma, option_type),
            'probability_touch': ProbabilityCalculator.probability_touch(S, K, T, r, sigma, option_type),
            'expected_move': ProbabilityCalculator.expected_move(S, sigma, T)
        }
        
        if run_monte_carlo:
            mc_results = ProbabilityCalculator.monte_carlo_simulation(
                S, K, T, r, sigma, option_type, num_simulations=10000
            )
            results['monte_carlo'] = mc_results
        
        return results
    
    @staticmethod
    def spread_probability_profit(
        S: float,
        K_long: float,
        K_short: float,
        T: float,
        r: float,
        sigma: float,
        debit_paid: float,
        option_type: str = 'call'
    ) -> float:
        """
        Calculate probability of profit for a vertical spread.
        
        Args:
            S: Current stock price
            K_long: Long strike
            K_short: Short strike
            T: Time to expiration (years)
            r: Risk-free rate
            sigma: Implied volatility
            debit_paid: Net debit paid (for debit spreads)
            option_type: 'call' or 'put'
            
        Returns:
            Probability of profit (0-1)
        """
        # Break-even point
        if option_type.lower() == 'call':
            breakeven = K_long + debit_paid
        else:
            breakeven = K_long - debit_paid
        
        # Probability of being above/below breakeven
        if T <= 0:
            if option_type.lower() == 'call':
                return 1.0 if S > breakeven else 0.0
            else:
                return 1.0 if S < breakeven else 0.0
        
        # Use normal distribution
        expected_price = S * math.exp(r * T)
        std_dev = S * sigma * math.sqrt(T)
        
        if option_type.lower() == 'call':
            z = (breakeven - expected_price) / std_dev
            return 1 - norm.cdf(z)
        else:
            z = (breakeven - expected_price) / std_dev
            return norm.cdf(z)
