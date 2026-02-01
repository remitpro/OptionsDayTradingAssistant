"""ThinkorSwim watchlist generator."""

import csv
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path

from src.utils.logger import get_logger


logger = get_logger(__name__)


class WatchlistGenerator:
    """Generate ThinkorSwim-compatible watchlist files."""
    
    @staticmethod
    def generate_watchlist(trades: List[Dict[str, Any]], output_dir: str = "outputs/watchlists") -> str:
        """
        Generate watchlist CSV file for ThinkorSwim.
        
        Args:
            trades: List of trade structures
            output_dir: Output directory path
            
        Returns:
            Path to saved watchlist file
        """
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d')
        filename = f"watchlist_{timestamp}.csv"
        filepath = output_path / filename
        
        # Prepare watchlist data
        watchlist_data = []
        for trade in trades:
            symbol = trade.get('symbol')
            strategy = trade.get('strategy')
            bias = trade.get('bias', '').capitalize()
            entry_price = trade.get('underlying_price', 0)
            score = trade.get('score', 0)
            
            description = f"{strategy} - {bias}"
            
            watchlist_data.append({
                'Symbol': symbol,
                'Description': description,
                'Entry': f"{entry_price:.2f}",
                'Score': f"{score:.0f}"
            })
        
        # Write to CSV
        with open(filepath, 'w', newline='') as f:
            if watchlist_data:
                fieldnames = ['Symbol', 'Description', 'Entry', 'Score']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                writer.writeheader()
                writer.writerows(watchlist_data)
        
        logger.info(f"✓ Saved watchlist: {filepath} ({len(watchlist_data)} symbols)")
        
        return str(filepath)
    
    @staticmethod
    def generate_detailed_watchlist(
        trades: List[Dict[str, Any]],
        risk_metrics_list: List[Dict[str, Any]],
        output_dir: str = "outputs/watchlists"
    ) -> str:
        """
        Generate detailed watchlist with additional columns.
        
        Args:
            trades: List of trade structures
            risk_metrics_list: List of risk metrics
            output_dir: Output directory path
            
        Returns:
            Path to saved watchlist file
        """
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d')
        filename = f"watchlist_detailed_{timestamp}.csv"
        filepath = output_path / filename
        
        # Prepare detailed watchlist data
        watchlist_data = []
        for trade, risk_metrics in zip(trades, risk_metrics_list):
            symbol = trade.get('symbol')
            strategy = trade.get('strategy')
            bias = trade.get('bias', '').capitalize()
            entry_price = trade.get('underlying_price', 0)
            score = trade.get('score', 0)
            expiration = trade.get('expiration', '')
            dte = trade.get('dte', 0)
            
            max_loss = risk_metrics.get('max_loss', 0)
            max_gain = risk_metrics.get('max_gain', 0)
            rr_ratio = risk_metrics.get('risk_reward_ratio', 0)
            
            # Get strikes
            legs = trade.get('legs', [])
            strikes_str = ' / '.join([f"{leg.get('strike', 0):.0f}" for leg in legs])
            
            watchlist_data.append({
                'Symbol': symbol,
                'Strategy': strategy,
                'Bias': bias,
                'Strikes': strikes_str,
                'Expiration': expiration,
                'DTE': dte,
                'Entry': f"{entry_price:.2f}",
                'MaxLoss': f"${max_loss:.0f}",
                'MaxGain': f"${max_gain:.0f}",
                'R/R': f"{rr_ratio:.2f}",
                'Score': f"{score:.0f}"
            })
        
        # Write to CSV
        with open(filepath, 'w', newline='') as f:
            if watchlist_data:
                fieldnames = ['Symbol', 'Strategy', 'Bias', 'Strikes', 'Expiration', 
                            'DTE', 'Entry', 'MaxLoss', 'MaxGain', 'R/R', 'Score']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                writer.writeheader()
                writer.writerows(watchlist_data)
        
        logger.info(f"✓ Saved detailed watchlist: {filepath}")
        
        return str(filepath)
    
    @staticmethod
    def generate_import_instructions() -> str:
        """
        Generate instructions for importing watchlist into ThinkorSwim.
        
        Returns:
            Instructions as string
        """
        instructions = """
=== ThinkorSwim Watchlist Import Instructions ===

1. Open ThinkorSwim platform

2. Go to Setup menu → Open Shared Item → Import

3. Select the watchlist CSV file generated by this system

4. Choose "Watchlist" as the item type

5. Click "Import"

6. The watchlist will appear in your ThinkorSwim watchlists

7. You can customize columns by right-clicking the watchlist header

Note: The basic watchlist CSV contains Symbol, Description, Entry, and Score columns.
The detailed watchlist includes additional trading information.

For ThinkScript alerts:
1. Open a chart for the symbol
2. Go to Studies → Edit Studies → New
3. Copy and paste the ThinkScript code from the alert file
4. Click OK to apply
5. Alerts will trigger based on the defined conditions
"""
        return instructions
