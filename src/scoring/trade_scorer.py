"""Trade scoring and ranking system."""

from typing import List, Dict, Any
import math

from config.settings import get_settings
from src.utils.logger import get_logger
from src.analytics import ProbabilityCalculator, RiskMetrics


logger = get_logger(__name__)


class TradeScorer:
    """Score and rank trades based on multiple criteria."""
    
    def __init__(self):
        """Initialize trade scorer."""
        self.settings = get_settings()
    
    def score_trade(
        self,
        trade: Dict[str, Any],
        probability_metrics: Dict[str, Any],
        risk_metrics: Dict[str, Any],
        options_data: Dict[str, Any]
    ) -> float:
        """
        Calculate composite score for a trade (0-100).
        
        Args:
            trade: Trade structure
            probability_metrics: Probability calculations
            risk_metrics: Risk metrics
            options_data: Options data for liquidity scoring
            
        Returns:
            Score from 0-100
        """
        # Component scores
        prob_score = self._score_probability(probability_metrics)
        rr_score = self._score_risk_reward(risk_metrics)
        iv_score = self._score_iv_edge(trade, options_data)
        liquidity_score = self._score_liquidity(trade, options_data)
        trend_score = self._score_trend_alignment(trade)
        
        # Weighted composite score
        total_score = (
            self.settings.weight_probability * prob_score +
            self.settings.weight_risk_reward * rr_score +
            self.settings.weight_iv_edge * iv_score +
            self.settings.weight_liquidity * liquidity_score +
            self.settings.weight_trend * trend_score
        )
        
        logger.debug(f"{trade['symbol']}: P={prob_score:.1f} RR={rr_score:.1f} "
                    f"IV={iv_score:.1f} L={liquidity_score:.1f} T={trend_score:.1f} "
                    f"→ Total={total_score:.1f}")
        
        return round(total_score, 1)
    
    def _score_probability(self, prob_metrics: Dict[str, Any]) -> float:
        """
        Score based on probability of profit (0-100).
        
        Args:
            prob_metrics: Probability metrics
            
        Returns:
            Score 0-100
        """
        # Use Monte Carlo probability if available, otherwise ITM probability
        mc_results = prob_metrics.get('monte_carlo', {})
        if mc_results:
            prob_profit = mc_results.get('probability_profit', 0)
        else:
            prob_profit = prob_metrics.get('probability_itm', 0)
        
        # Convert to 0-100 scale
        return prob_profit * 100
    
    def _score_risk_reward(self, risk_metrics: Dict[str, Any]) -> float:
        """
        Score based on risk/reward ratio (0-100).
        
        Args:
            risk_metrics: Risk metrics
            
        Returns:
            Score 0-100
        """
        rr_ratio = risk_metrics.get('risk_reward_ratio', 0)
        
        # Normalize: 3:1 R/R = 100 points, linear scaling
        # Cap at 3:1 for scoring purposes
        normalized_rr = min(rr_ratio / 3.0, 1.0)
        
        return normalized_rr * 100
    
    def _score_iv_edge(self, trade: Dict[str, Any], options_data: Dict[str, Any]) -> float:
        """
        Score based on IV percentile advantage (0-100).
        
        Args:
            trade: Trade structure
            options_data: Options data
            
        Returns:
            Score 0-100
        """
        # Get IV from first leg
        legs = trade.get('legs', [])
        if not legs:
            return 50.0
        
        # Estimate IV percentile (simplified)
        # In production, you'd compare current IV to historical range
        strategy = trade.get('strategy', '')
        condition = trade.get('condition', '')
        
        # Favor low IV for debit strategies, high IV for credit strategies
        if 'Debit' in strategy or 'Long' in strategy:
            # Want low IV
            if 'breakout' in condition:
                return 80.0  # Low IV is good
            else:
                return 60.0
        elif 'Credit' in strategy or 'Condor' in strategy:
            # Want high IV
            if 'high_iv' in condition or 'choppy' in condition:
                return 80.0  # High IV is good
            else:
                return 60.0
        else:
            return 50.0
    
    def _score_liquidity(self, trade: Dict[str, Any], options_data: Dict[str, Any]) -> float:
        """
        Score based on options liquidity (0-100).
        
        Args:
            trade: Trade structure
            options_data: Options data
            
        Returns:
            Score 0-100
        """
        legs = trade.get('legs', [])
        if not legs:
            return 0
        
        # Get all contracts used in trade
        all_contracts = []
        if trade.get('bias') in ['bullish', 'neutral']:
            all_contracts.extend(options_data.get('calls', []))
        if trade.get('bias') in ['bearish', 'neutral']:
            all_contracts.extend(options_data.get('puts', []))
        
        if not all_contracts:
            return 50.0
        
        # Find contracts matching trade legs
        leg_scores = []
        for leg in legs:
            strike = leg.get('strike')
            option_type = leg.get('option_type')
            
            # Find matching contract
            matching = [
                c for c in all_contracts
                if c.get('strikePrice') == strike and c.get('option_type') == option_type
            ]
            
            if matching:
                contract = matching[0]
                
                # Score based on OI, volume, and spread
                oi = contract.get('openInterest', 0)
                volume = contract.get('totalVolume', 0)
                bid = contract.get('bid', 0)
                ask = contract.get('ask', 0)
                
                # OI score (>5000 = 100, linear from 1000-5000)
                oi_score = min((oi - 1000) / 4000 * 100, 100) if oi >= 1000 else 0
                
                # Volume score (>1000 = 100, linear from 300-1000)
                vol_score = min((volume - 300) / 700 * 100, 100) if volume >= 300 else 0
                
                # Spread score (tighter = better)
                if bid > 0 and ask > 0:
                    spread_pct = ((ask - bid) / ((ask + bid) / 2)) * 100
                    spread_score = max(100 - spread_pct * 20, 0)  # 5% spread = 0 points
                else:
                    spread_score = 0
                
                # Composite liquidity score for this leg
                leg_score = (oi_score * 0.4 + vol_score * 0.4 + spread_score * 0.2)
                leg_scores.append(leg_score)
        
        # Average across all legs
        return sum(leg_scores) / len(leg_scores) if leg_scores else 50.0
    
    def _score_trend_alignment(self, trade: Dict[str, Any]) -> float:
        """
        Score based on trend alignment with strategy (0-100).
        
        Args:
            trade: Trade structure
            
        Returns:
            Score 0-100
        """
        bias = trade.get('bias', 'neutral')
        condition = trade.get('condition', '')
        
        # Strong alignment gets high score
        if 'strong' in condition:
            return 90.0
        elif 'breakout' in condition:
            return 80.0
        elif 'high_iv' in condition:
            return 70.0
        elif 'choppy' in condition:
            # Neutral strategies in choppy markets
            if bias == 'neutral':
                return 75.0
            else:
                return 50.0
        else:
            return 60.0
    
    def rank_trades(
        self,
        scored_trades: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Rank trades by score and filter by minimum threshold.
        
        Args:
            scored_trades: List of trades with scores
            
        Returns:
            Filtered and sorted list of top trades
        """
        # Filter by minimum score
        filtered = [
            t for t in scored_trades
            if t.get('score', 0) >= self.settings.min_trade_score
        ]
        
        # Sort by score descending
        ranked = sorted(filtered, key=lambda x: x.get('score', 0), reverse=True)
        
        # Return top N trades
        top_trades = ranked[:self.settings.max_trades_output]
        
        logger.info(f"✓ Ranked {len(scored_trades)} trades → {len(top_trades)} above threshold")
        
        return top_trades
