"""Options liquidity filter for identifying tradable options."""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from config.settings import get_settings
from src.data import get_client, get_cache
from src.utils.logger import get_logger
from src.utils.validators import validate_option_data, calculate_spread_pct


logger = get_logger(__name__)


class OptionsFilter:
    """Filter options chains for liquid, tradable contracts."""
    
    def __init__(self):
        """Initialize options filter."""
        self.settings = get_settings()
        self.client = get_client()
        self.cache = get_cache()
    
    def filter_options(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get and filter options chain for a symbol.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Dictionary with filtered calls and puts, or None if no liquid options
        """
        logger.info(f"📊 Filtering options for {symbol}...")
        
        # Get options chain
        chain = self._get_option_chain_with_cache(symbol)
        if not chain:
            logger.warning(f"No options chain data for {symbol}")
            return None
        
        # Filter calls and puts
        filtered_calls = self._filter_contracts(
            chain.get('callExpDateMap', {}),
            'CALL'
        )
        
        filtered_puts = self._filter_contracts(
            chain.get('putExpDateMap', {}),
            'PUT'
        )
        
        # Check if we have any liquid options
        if not filtered_calls and not filtered_puts:
            logger.warning(f"No liquid options found for {symbol}")
            return None
        
        logger.info(f"✓ {symbol}: {len(filtered_calls)} calls, {len(filtered_puts)} puts")
        
        return {
            'symbol': symbol,
            'underlying_price': chain.get('underlyingPrice', 0),
            'calls': filtered_calls,
            'puts': filtered_puts,
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_option_chain_with_cache(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get option chain with caching."""
        # Check cache first
        cached = self.cache.get_option_chain(symbol)
        if cached:
            return cached
        
        # Calculate date range for DTE filter
        from_date = datetime.now()
        to_date = from_date + timedelta(days=self.settings.max_dte)
        
        # Fetch from API
        chain = self.client.get_option_chain(symbol, from_date, to_date)
        
        if chain:
            self.cache.set_option_chain(symbol, chain)
        
        return chain
    
    def _filter_contracts(
        self,
        exp_date_map: Dict[str, Any],
        option_type: str
    ) -> List[Dict[str, Any]]:
        """
        Filter option contracts by liquidity criteria.
        
        Args:
            exp_date_map: Expiration date map from options chain
            option_type: 'CALL' or 'PUT'
            
        Returns:
            List of filtered option contracts
        """
        filtered = []
        
        for exp_date_str, strike_map in exp_date_map.items():
            # Parse expiration date and calculate DTE
            try:
                exp_date = datetime.strptime(exp_date_str.split(':')[0], '%Y-%m-%d')
                dte = (exp_date - datetime.now()).days
                
                # Filter by DTE
                if not (self.settings.min_dte <= dte <= self.settings.max_dte):
                    continue
                
            except Exception as e:
                logger.error(f"Error parsing expiration date {exp_date_str}: {e}")
                continue
            
            # Filter contracts at each strike
            for strike_str, contracts in strike_map.items():
                for contract in contracts:
                    if self._is_liquid_contract(contract, dte):
                        # Add metadata
                        contract['dte'] = dte
                        contract['expiration'] = exp_date.strftime('%Y-%m-%d')
                        contract['option_type'] = option_type
                        filtered.append(contract)
        
        return filtered
    
    def _is_liquid_contract(self, contract: Dict[str, Any], dte: int) -> bool:
        """
        Check if option contract meets liquidity requirements.
        
        Args:
            contract: Option contract data
            dte: Days to expiration
            
        Returns:
            True if liquid, False otherwise
        """
        # Validate basic data structure
        if not validate_option_data(contract):
            return False
        
        # Check open interest
        open_interest = contract.get('openInterest', 0)
        if open_interest < self.settings.min_open_interest:
            return False
        
        # Check volume
        volume = contract.get('totalVolume', 0)
        if volume < self.settings.min_option_volume:
            return False
        
        # Check bid-ask spread
        bid = contract.get('bid', 0)
        ask = contract.get('ask', 0)
        
        if bid <= 0 or ask <= 0:
            return False
        
        spread_pct = calculate_spread_pct(bid, ask)
        if spread_pct > self.settings.max_option_spread_pct:
            return False
        
        # Check Greeks are valid
        greeks = contract.get('greeks', {})
        if not greeks:
            return False
        
        # Must have valid delta at minimum
        delta = greeks.get('delta')
        if delta is None:
            return False
        
        return True
    
    def get_atm_strike(self, symbol: str, underlying_price: float) -> Optional[float]:
        """
        Find at-the-money strike price.
        
        Args:
            symbol: Stock ticker symbol
            underlying_price: Current stock price
            
        Returns:
            ATM strike price or None
        """
        chain = self._get_option_chain_with_cache(symbol)
        if not chain:
            return None
        
        # Get all available strikes from calls
        call_map = chain.get('callExpDateMap', {})
        if not call_map:
            return None
        
        # Get strikes from first expiration
        first_exp = next(iter(call_map.values()))
        strikes = [float(strike) for strike in first_exp.keys()]
        
        if not strikes:
            return None
        
        # Find closest strike to underlying price
        atm_strike = min(strikes, key=lambda x: abs(x - underlying_price))
        return atm_strike
    
    def get_contracts_by_delta(
        self,
        contracts: List[Dict[str, Any]],
        target_delta: float,
        tolerance: float = 0.1
    ) -> List[Dict[str, Any]]:
        """
        Filter contracts by target delta.
        
        Args:
            contracts: List of option contracts
            target_delta: Target delta value (absolute)
            tolerance: Delta tolerance range
            
        Returns:
            Filtered contracts matching delta criteria
        """
        filtered = []
        
        for contract in contracts:
            greeks = contract.get('greeks', {})
            delta = greeks.get('delta')
            
            if delta is None:
                continue
            
            # Use absolute delta for comparison
            abs_delta = abs(delta)
            
            if abs(abs_delta - target_delta) <= tolerance:
                filtered.append(contract)
        
        return filtered
