"""Strategy selection engine based on market conditions."""

import numpy as np
from typing import Dict, Any, Optional, List, Tuple

from config.settings import get_settings
from src.utils.logger import get_logger
from .strategy_configs import (
    StrategyType,
    MarketCondition,
    StrategyConfig,
    get_strategy_config
)


logger = get_logger(__name__)


class StrategySelector:
    """Select optimal options strategy based on market conditions."""
    
    def __init__(self):
        """Initialize strategy selector."""
        self.settings = get_settings()
    
    def select_strategy(
        self,
        candidate: Dict[str, Any],
        options_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze market conditions and select optimal strategy.
        
        Args:
            candidate: Stock candidate from market scanner
            options_data: Filtered options data
            
        Returns:
            Strategy selection with details, or None if should skip
        """
        symbol = candidate['symbol']
        logger.info(f"🎯 Selecting strategy for {symbol}...")
        
        # Detect market condition
        condition = self._detect_market_condition(candidate, options_data)
        
        # Get strategy configuration
        config = get_strategy_config(condition)
        
        # Skip if too risky
        if config.strategy_type == StrategyType.SKIP:
            logger.warning(f"⚠️  {symbol}: Skipping - {config.description}")
            return None
        
        # Build trade structure
        trade = self._build_trade_structure(
            candidate,
            options_data,
            condition,
            config
        )
        
        if not trade:
            logger.warning(f"Could not build trade structure for {symbol}")
            return None
        
        logger.info(f"✓ {symbol}: {config.strategy_type.value} - {condition.value}")
        
        return trade
    
    def _detect_market_condition(
        self,
        candidate: Dict[str, Any],
        options_data: Dict[str, Any]
    ) -> MarketCondition:
        """
        Detect current market condition for the symbol.
        
        Args:
            candidate: Stock candidate data
            options_data: Options data
            
        Returns:
            Market condition classification
        """
        vwap_bias = candidate.get('vwap_bias', 'neutral')
        atr = candidate.get('atr', 0)
        volume = candidate.get('volume', 0)
        avg_volume = candidate.get('avg_volume', 1)
        
        # Calculate IV percentile (simplified - using ATM IV as proxy)
        iv_percentile = self._estimate_iv_percentile(options_data)
        
        # Volume ratio
        volume_ratio = volume / avg_volume if avg_volume > 0 else 1
        
        # Check for news/extreme IV spike
        if iv_percentile > self.settings.extreme_iv_threshold:
            return MarketCondition.NEWS_SPIKE
        
        # Strong momentum conditions
        if volume_ratio > 2.0 and atr > 2.5:
            if vwap_bias == 'bullish':
                return MarketCondition.STRONG_BULLISH
            elif vwap_bias == 'bearish':
                return MarketCondition.STRONG_BEARISH
        
        # Breakout conditions (high volume, low IV)
        if volume_ratio > 1.5 and iv_percentile < self.settings.low_iv_threshold:
            if vwap_bias == 'bullish':
                return MarketCondition.BULLISH_BREAKOUT
            elif vwap_bias == 'bearish':
                return MarketCondition.BEARISH_BREAKOUT
        
        # High IV range-bound
        if iv_percentile > self.settings.high_iv_threshold and vwap_bias == 'neutral':
            return MarketCondition.HIGH_IV_RANGE
        
        # Choppy market (neutral bias, low volume)
        if vwap_bias == 'neutral' and volume_ratio < 1.5:
            return MarketCondition.CHOPPY
        
        # Default to appropriate directional strategy
        if vwap_bias == 'bullish':
            return MarketCondition.BULLISH_BREAKOUT
        elif vwap_bias == 'bearish':
            return MarketCondition.BEARISH_BREAKOUT
        else:
            return MarketCondition.CHOPPY
    
    def _estimate_iv_percentile(self, options_data: Dict[str, Any]) -> float:
        """
        Estimate IV percentile using ATM options.
        
        Args:
            options_data: Options data
            
        Returns:
            Estimated IV percentile (0-100)
        """
        # Get ATM call IV as proxy
        calls = options_data.get('calls', [])
        
        if not calls:
            return 50.0  # Default to middle
        
        # Find ATM option (delta closest to 0.5)
        atm_call = min(
            calls,
            key=lambda x: abs(abs(x.get('greeks', {}).get('delta', 0)) - 0.5)
        )
        
        iv = atm_call.get('volatility', 0) * 100  # Convert to percentage
        
        # Simplified percentile estimation
        # In production, you'd compare to historical IV range
        if iv < 20:
            return 20.0
        elif iv < 30:
            return 35.0
        elif iv < 40:
            return 50.0
        elif iv < 60:
            return 70.0
        else:
            return 85.0
    
    def _build_trade_structure(
        self,
        candidate: Dict[str, Any],
        options_data: Dict[str, Any],
        condition: MarketCondition,
        config: StrategyConfig
    ) -> Optional[Dict[str, Any]]:
        """
        Build complete trade structure with strikes and contracts.
        
        Args:
            candidate: Stock candidate
            options_data: Options data
            condition: Market condition
            config: Strategy configuration
            
        Returns:
            Trade structure dictionary
        """
        symbol = candidate['symbol']
        underlying_price = options_data['underlying_price']
        
        # Determine if bullish or bearish
        is_bullish = condition in [
            MarketCondition.STRONG_BULLISH,
            MarketCondition.BULLISH_BREAKOUT
        ]
        
        is_bearish = condition in [
            MarketCondition.STRONG_BEARISH,
            MarketCondition.BEARISH_BREAKOUT
        ]
        
        # Select appropriate contracts
        if config.strategy_type in [StrategyType.LONG_CALL, StrategyType.CALL_DEBIT_SPREAD, StrategyType.CALL_CREDIT_SPREAD]:
            contracts = options_data.get('calls', [])
            option_type = 'CALL'
        elif config.strategy_type in [StrategyType.LONG_PUT, StrategyType.PUT_DEBIT_SPREAD, StrategyType.PUT_CREDIT_SPREAD]:
            contracts = options_data.get('puts', [])
            option_type = 'PUT'
        elif config.strategy_type == StrategyType.IRON_CONDOR:
            # Iron condor uses both
            return self._build_iron_condor(candidate, options_data, config)
        else:
            return None
        
        # Filter by DTE
        contracts = [c for c in contracts if c.get('dte', 999) <= config.max_dte]
        
        if not contracts:
            return None
        
        # Find contract closest to target delta
        long_contract = min(
            contracts,
            key=lambda x: abs(abs(x.get('greeks', {}).get('delta', 0)) - config.delta_target)
        )
        
        # Build trade based on strategy type
        if config.spread_width == 0:
            # Single option
            return {
                'symbol': symbol,
                'strategy': config.strategy_type.value,
                'condition': condition.value,
                'bias': 'bullish' if is_bullish else 'bearish' if is_bearish else 'neutral',
                'underlying_price': underlying_price,
                'expiration': long_contract.get('expiration'),
                'dte': long_contract.get('dte'),
                'legs': [
                    {
                        'action': 'BUY',
                        'option_type': option_type,
                        'strike': long_contract.get('strikePrice'),
                        'quantity': 1,
                        'price': (long_contract.get('bid', 0) + long_contract.get('ask', 0)) / 2,
                        'delta': long_contract.get('greeks', {}).get('delta'),
                        'theta': long_contract.get('greeks', {}).get('theta'),
                        'vega': long_contract.get('greeks', {}).get('vega'),
                    }
                ],
                'explanation': config.description
            }
        else:
            # Spread
            return self._build_spread(
                symbol,
                underlying_price,
                long_contract,
                contracts,
                config,
                condition,
                is_bullish,
                is_bearish,
                option_type
            )
    
    def _build_spread(
        self,
        symbol: str,
        underlying_price: float,
        long_contract: Dict[str, Any],
        contracts: List[Dict[str, Any]],
        config: StrategyConfig,
        condition: MarketCondition,
        is_bullish: bool,
        is_bearish: bool,
        option_type: str
    ) -> Optional[Dict[str, Any]]:
        """Build vertical spread trade structure."""
        long_strike = long_contract.get('strikePrice')
        
        # Find short strike (spread_width away)
        if config.strategy_type in [StrategyType.CALL_DEBIT_SPREAD, StrategyType.PUT_CREDIT_SPREAD]:
            # For call debit or put credit, short strike is higher
            target_short_strike = long_strike + config.spread_width
        else:
            # For put debit or call credit, short strike is lower
            target_short_strike = long_strike - config.spread_width
        
        # Find contract closest to target short strike
        short_contract = min(
            contracts,
            key=lambda x: abs(x.get('strikePrice', 0) - target_short_strike)
        )
        
        # Determine if debit or credit spread
        is_debit = config.strategy_type in [StrategyType.CALL_DEBIT_SPREAD, StrategyType.PUT_DEBIT_SPREAD]
        
        return {
            'symbol': symbol,
            'strategy': config.strategy_type.value,
            'condition': condition.value,
            'bias': 'bullish' if is_bullish else 'bearish' if is_bearish else 'neutral',
            'underlying_price': underlying_price,
            'expiration': long_contract.get('expiration'),
            'dte': long_contract.get('dte'),
            'legs': [
                {
                    'action': 'BUY' if is_debit else 'SELL',
                    'option_type': option_type,
                    'strike': long_strike,
                    'quantity': 1,
                    'price': (long_contract.get('bid', 0) + long_contract.get('ask', 0)) / 2,
                    'delta': long_contract.get('greeks', {}).get('delta'),
                    'theta': long_contract.get('greeks', {}).get('theta'),
                },
                {
                    'action': 'SELL' if is_debit else 'BUY',
                    'option_type': option_type,
                    'strike': short_contract.get('strikePrice'),
                    'quantity': 1,
                    'price': (short_contract.get('bid', 0) + short_contract.get('ask', 0)) / 2,
                    'delta': short_contract.get('greeks', {}).get('delta'),
                    'theta': short_contract.get('greeks', {}).get('theta'),
                }
            ],
            'explanation': config.description
        }
    
    def _build_iron_condor(
        self,
        candidate: Dict[str, Any],
        options_data: Dict[str, Any],
        config: StrategyConfig
    ) -> Optional[Dict[str, Any]]:
        """Build iron condor trade structure."""
        # Simplified iron condor - sell OTM call and put spreads
        symbol = candidate['symbol']
        underlying_price = options_data['underlying_price']
        
        calls = options_data.get('calls', [])
        puts = options_data.get('puts', [])
        
        # Filter by DTE
        calls = [c for c in calls if c.get('dte', 999) <= config.max_dte]
        puts = [c for c in puts if c.get('dte', 999) <= config.max_dte]
        
        if not calls or not puts:
            return None
        
        # Find OTM call (delta ~0.20)
        short_call = min(calls, key=lambda x: abs(abs(x.get('greeks', {}).get('delta', 0)) - 0.20))
        
        # Find OTM put (delta ~-0.20)
        short_put = min(puts, key=lambda x: abs(abs(x.get('greeks', {}).get('delta', 0)) - 0.20))
        
        # Find protection strikes
        long_call = min(
            calls,
            key=lambda x: abs(x.get('strikePrice', 0) - (short_call.get('strikePrice', 0) + config.spread_width))
        )
        
        long_put = min(
            puts,
            key=lambda x: abs(x.get('strikePrice', 0) - (short_put.get('strikePrice', 0) - config.spread_width))
        )
        
        return {
            'symbol': symbol,
            'strategy': StrategyType.IRON_CONDOR.value,
            'condition': MarketCondition.CHOPPY.value,
            'bias': 'neutral',
            'underlying_price': underlying_price,
            'expiration': short_call.get('expiration'),
            'dte': short_call.get('dte'),
            'legs': [
                {'action': 'SELL', 'option_type': 'CALL', 'strike': short_call.get('strikePrice'),
                 'quantity': 1, 'price': (short_call.get('bid', 0) + short_call.get('ask', 0)) / 2},
                {'action': 'BUY', 'option_type': 'CALL', 'strike': long_call.get('strikePrice'),
                 'quantity': 1, 'price': (long_call.get('bid', 0) + long_call.get('ask', 0)) / 2},
                {'action': 'SELL', 'option_type': 'PUT', 'strike': short_put.get('strikePrice'),
                 'quantity': 1, 'price': (short_put.get('bid', 0) + short_put.get('ask', 0)) / 2},
                {'action': 'BUY', 'option_type': 'PUT', 'strike': long_put.get('strikePrice'),
                 'quantity': 1, 'price': (long_put.get('bid', 0) + long_put.get('ask', 0)) / 2},
            ],
            'explanation': config.description
        }
