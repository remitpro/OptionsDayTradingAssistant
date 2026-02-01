"""Risk metrics calculations for options trades."""

from typing import Dict, Any, List
import math

from src.utils.logger import get_logger


logger = get_logger(__name__)


class RiskMetrics:
    """Calculate risk metrics for options trades."""
    
    @staticmethod
    def calculate_trade_metrics(trade: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate comprehensive risk metrics for a trade.
        
        Args:
            trade: Trade structure with legs
            
        Returns:
            Dictionary with risk metrics
        """
        legs = trade.get('legs', [])
        
        if not legs:
            return {}
        
        # Calculate net debit/credit
        net_cost = 0
        for leg in legs:
            price = leg.get('price', 0)
            quantity = leg.get('quantity', 1)
            
            if leg.get('action') == 'BUY':
                net_cost += price * quantity * 100  # Options are per 100 shares
            else:  # SELL
                net_cost -= price * quantity * 100
        
        # Determine if debit or credit
        is_debit = net_cost > 0
        
        # Calculate max loss and max gain based on strategy
        strategy = trade.get('strategy', '')
        
        if 'Spread' in strategy:
            metrics = RiskMetrics._calculate_spread_metrics(trade, legs, net_cost, is_debit)
        elif 'Iron Condor' in strategy:
            metrics = RiskMetrics._calculate_iron_condor_metrics(trade, legs)
        else:
            # Single option
            metrics = RiskMetrics._calculate_single_option_metrics(trade, legs, net_cost)
        
        # Add common metrics
        metrics['net_cost'] = abs(net_cost)
        metrics['is_debit'] = is_debit
        
        # Calculate risk/reward ratio
        if metrics['max_loss'] > 0:
            metrics['risk_reward_ratio'] = metrics['max_gain'] / metrics['max_loss']
        else:
            metrics['risk_reward_ratio'] = 0
        
        # Calculate break-even points
        metrics['breakeven_points'] = RiskMetrics._calculate_breakeven(trade, legs, net_cost)
        
        return metrics
    
    @staticmethod
    def _calculate_single_option_metrics(
        trade: Dict[str, Any],
        legs: List[Dict[str, Any]],
        net_cost: float
    ) -> Dict[str, Any]:
        """Calculate metrics for single long option."""
        leg = legs[0]
        
        # For long options
        max_loss = abs(net_cost)
        
        # Max gain is theoretically unlimited for calls, strike - premium for puts
        if leg.get('option_type') == 'CALL':
            max_gain = float('inf')  # Unlimited
            # Use 2x current price as practical max for display
            underlying_price = trade.get('underlying_price', 0)
            practical_max_gain = (underlying_price * 2 - leg.get('strike', 0)) * 100 - max_loss
            max_gain = max(practical_max_gain, max_loss * 3)  # At least 3:1 for display
        else:  # PUT
            strike = leg.get('strike', 0)
            max_gain = (strike * 100) - max_loss
        
        return {
            'max_loss': max_loss,
            'max_gain': max_gain
        }
    
    @staticmethod
    def _calculate_spread_metrics(
        trade: Dict[str, Any],
        legs: List[Dict[str, Any]],
        net_cost: float,
        is_debit: bool
    ) -> Dict[str, Any]:
        """Calculate metrics for vertical spreads."""
        if len(legs) < 2:
            return {'max_loss': 0, 'max_gain': 0}
        
        # Get strikes
        strikes = [leg.get('strike', 0) for leg in legs]
        spread_width = abs(strikes[0] - strikes[1]) * 100  # Convert to dollars
        
        if is_debit:
            # Debit spread
            max_loss = abs(net_cost)
            max_gain = spread_width - max_loss
        else:
            # Credit spread
            max_gain = abs(net_cost)
            max_loss = spread_width - max_gain
        
        return {
            'max_loss': max_loss,
            'max_gain': max_gain,
            'spread_width': spread_width
        }
    
    @staticmethod
    def _calculate_iron_condor_metrics(
        trade: Dict[str, Any],
        legs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate metrics for iron condor."""
        if len(legs) < 4:
            return {'max_loss': 0, 'max_gain': 0}
        
        # Calculate net credit received
        net_credit = 0
        for leg in legs:
            price = leg.get('price', 0)
            if leg.get('action') == 'SELL':
                net_credit += price * 100
            else:
                net_credit -= price * 100
        
        # Get spread widths
        call_strikes = [leg.get('strike', 0) for leg in legs if leg.get('option_type') == 'CALL']
        put_strikes = [leg.get('strike', 0) for leg in legs if leg.get('option_type') == 'PUT']
        
        call_spread_width = abs(call_strikes[0] - call_strikes[1]) * 100 if len(call_strikes) == 2 else 0
        put_spread_width = abs(put_strikes[0] - put_strikes[1]) * 100 if len(put_strikes) == 2 else 0
        
        # Max gain is net credit, max loss is widest spread - credit
        max_gain = net_credit
        max_loss = max(call_spread_width, put_spread_width) - net_credit
        
        return {
            'max_loss': max_loss,
            'max_gain': max_gain,
            'net_credit': net_credit
        }
    
    @staticmethod
    def _calculate_breakeven(
        trade: Dict[str, Any],
        legs: List[Dict[str, Any]],
        net_cost: float
    ) -> List[float]:
        """Calculate break-even points."""
        strategy = trade.get('strategy', '')
        
        if len(legs) == 1:
            # Single option
            leg = legs[0]
            strike = leg.get('strike', 0)
            premium = abs(net_cost) / 100
            
            if leg.get('option_type') == 'CALL':
                return [strike + premium]
            else:
                return [strike - premium]
        
        elif 'Spread' in strategy:
            # Vertical spread
            strikes = sorted([leg.get('strike', 0) for leg in legs])
            premium = abs(net_cost) / 100
            
            if 'Call' in strategy:
                if net_cost > 0:  # Debit
                    return [strikes[0] + premium]
                else:  # Credit
                    return [strikes[1] - premium]
            else:  # Put spread
                if net_cost > 0:  # Debit
                    return [strikes[1] - premium]
                else:  # Credit
                    return [strikes[0] + premium]
        
        elif 'Iron Condor' in strategy:
            # Two break-even points
            call_strikes = sorted([leg.get('strike', 0) for leg in legs if leg.get('option_type') == 'CALL'])
            put_strikes = sorted([leg.get('strike', 0) for leg in legs if leg.get('option_type') == 'PUT'])
            
            net_credit = abs(net_cost) / 100
            
            upper_breakeven = call_strikes[0] + net_credit if call_strikes else 0
            lower_breakeven = put_strikes[1] - net_credit if put_strikes else 0
            
            return [lower_breakeven, upper_breakeven]
        
        return []
    
    @staticmethod
    def calculate_expected_value(
        probability_profit: float,
        max_gain: float,
        max_loss: float
    ) -> float:
        """
        Calculate expected value of a trade.
        
        Args:
            probability_profit: Probability of profit (0-1)
            max_gain: Maximum gain
            max_loss: Maximum loss
            
        Returns:
            Expected value
        """
        probability_loss = 1 - probability_profit
        ev = (probability_profit * max_gain) - (probability_loss * max_loss)
        return ev
    
    @staticmethod
    def calculate_position_size(
        account_size: float,
        max_loss_per_trade: float,
        trade_max_loss: float
    ) -> int:
        """
        Calculate appropriate position size based on risk limits.
        
        Args:
            account_size: Total account size
            max_loss_per_trade: Maximum loss per trade (dollars)
            trade_max_loss: Max loss for this trade (per contract)
            
        Returns:
            Number of contracts to trade
        """
        if trade_max_loss <= 0:
            return 0
        
        # Calculate max contracts based on risk limit
        max_contracts_by_risk = int(max_loss_per_trade / trade_max_loss)
        
        # Also limit to 2% of account per trade
        max_contracts_by_account = int((account_size * 0.02) / trade_max_loss)
        
        # Use the smaller of the two
        position_size = min(max_contracts_by_risk, max_contracts_by_account)
        
        return max(position_size, 1)  # At least 1 contract
