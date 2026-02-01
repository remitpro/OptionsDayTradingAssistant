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
        """Filter option contracts by liquidity criteria."""
        filtered = []
        
        for exp_date_str, strike_map in exp_date_map.items():
            try:
                exp_date = datetime.strptime(exp_date_str.split(':')[0], '%Y-%m-%d')
                dte = (exp_date - datetime.now()).days
                
                if not (self.settings.min_dte <= dte <= self.settings.max_dte):
                    continue
                
            except Exception as e:
                logger.error(f"Error parsing expiration date {exp_date_str}: {e}")
                continue
            
            for strike_str, contracts in strike_map.items():
                for contract_data in contracts:
                    # Enrich data before validation
                    contract_data['dte'] = dte
                    contract_data['expiration_date'] = exp_date 
                    contract_data['option_type'] = option_type
                    
                    if self._is_liquid_contract(contract_data):
                        # Store essential data
                        filtered.append(contract_data)
        
        return filtered
    
    def _is_liquid_contract(self, contract: Dict[str, Any]) -> bool:
        """Check if option contract meets liquidity requirements."""
        # Validate basic data structure
        if not validate_option_data(contract):
            return False
            
        # Basic liquidity checks
        if contract.get('openInterest', 0) < self.settings.min_open_interest:
            return False
            
        if contract.get('totalVolume', 0) < self.settings.min_option_volume:
            return False
            
        # Spread check
        bid = contract.get('bid', 0)
        ask = contract.get('ask', 0)
        if bid <= 0 or ask <= 0:
            return False
            
        spread_pct = calculate_spread_pct(bid, ask)
        if spread_pct > self.settings.max_option_spread_pct:
            return False
            
        # Greeks check
        greeks = contract.get('greeks', {})
        if not greeks or greeks.get('delta') is None:
            return False
            
        # Implied Volatility check (New Robustness Feature)
        iv = contract.get('volatility', 0) 
        # Note: TDA returns volatility as a percentage (e.g. 25.0) or straight number? 
        # Usually 'volatility' field in TDA is IV.
        if iv <= 0 or iv == float('nan'):
            # Try to get from greeks if main field missing? 
            # Often it's top level. Let's assume strictness for now.
            return False
            
        return True

    def get_atm_strike(self, symbol: str, underlying_price: float) -> Optional[float]:
        """Find at-the-money strike price."""
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
        """Filter contracts by target delta."""
        filtered = []
        
        for contract in contracts:
            greeks = contract.get('greeks', {})
            delta = greeks.get('delta')
            
            if delta is None:
                continue
            
            if abs(abs(delta) - target_delta) <= tolerance:
                filtered.append(contract)
        
        return filtered
