"""ThinkScript alert code generator for ThinkorSwim."""

from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

from src.utils.logger import get_logger


logger = get_logger(__name__)


class TOSAlertGenerator:
    """Generate ThinkScript alert code for ThinkorSwim."""
    
    @staticmethod
    def generate_alert(trade: Dict[str, Any], risk_metrics: Dict[str, Any]) -> str:
        """
        Generate ThinkScript alert code for a trade.
        
        Args:
            trade: Trade structure
            risk_metrics: Risk metrics with break-even points
            
        Returns:
            ThinkScript code as string
        """
        symbol = trade.get('symbol')
        strategy = trade.get('strategy')
        bias = trade.get('bias')
        underlying_price = trade.get('underlying_price', 0)
        
        # Get break-even points
        breakeven_points = risk_metrics.get('breakeven_points', [])
        
        # Determine entry, stop, and target levels
        if bias == 'bullish':
            entry_price = underlying_price
            stop_price = underlying_price * 0.97  # 3% stop
            target_price = underlying_price * 1.05  # 5% target
        elif bias == 'bearish':
            entry_price = underlying_price
            stop_price = underlying_price * 1.03  # 3% stop
            target_price = underlying_price * 0.95  # 5% target
        else:  # neutral
            entry_price = underlying_price
            stop_price = underlying_price * 0.95
            target_price = underlying_price * 1.05
        
        # Use break-even as entry if available
        if breakeven_points:
            if bias == 'bullish':
                entry_price = breakeven_points[0]
            elif bias == 'bearish':
                entry_price = breakeven_points[0]
            else:
                entry_price = sum(breakeven_points) / len(breakeven_points)
        
        # Generate ThinkScript code
        script = f"""# AI Trade Alert - {symbol} {strategy}
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Bias: {bias.upper()}
# Strategy: {strategy}

# Price Levels
def entryPrice = {entry_price:.2f};
def stopPrice = {stop_price:.2f};
def targetPrice = {target_price:.2f};

# Entry Alert
alert(close crosses above entryPrice, "{symbol} Entry Signal - {bias.upper()}", Alert.BAR, Sound.Ring);

# Stop Loss Alert
alert(close crosses below stopPrice, "{symbol} Stop Loss Hit", Alert.BAR, Sound.Bell);

# Take Profit Alert
alert(close crosses above targetPrice, "{symbol} Target Reached", Alert.BAR, Sound.Ding);

# Plot levels on chart (optional - comment out if not needed)
plot Entry = entryPrice;
plot Stop = stopPrice;
plot Target = targetPrice;

Entry.SetDefaultColor(Color.YELLOW);
Entry.SetStyle(Curve.SHORT_DASH);

Stop.SetDefaultColor(Color.RED);
Stop.SetStyle(Curve.SHORT_DASH);

Target.SetDefaultColor(Color.GREEN);
Target.SetStyle(Curve.SHORT_DASH);
"""
        
        return script
    
    @staticmethod
    def save_alert(trade: Dict[str, Any], risk_metrics: Dict[str, Any], output_dir: str = "outputs/alerts") -> str:
        """
        Generate and save ThinkScript alert to file.
        
        Args:
            trade: Trade structure
            risk_metrics: Risk metrics
            output_dir: Output directory path
            
        Returns:
            Path to saved file
        """
        # Generate script
        script = TOSAlertGenerator.generate_alert(trade, risk_metrics)
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        symbol = trade.get('symbol')
        timestamp = datetime.now().strftime('%Y%m%d')
        filename = f"alert_{symbol}_{timestamp}.txt"
        filepath = output_path / filename
        
        # Save to file
        with open(filepath, 'w') as f:
            f.write(script)
        
        logger.info(f"✓ Saved ThinkScript alert: {filepath}")
        
        return str(filepath)
    
    @staticmethod
    def generate_batch_alerts(trades: List[Dict[str, Any]], risk_metrics_list: List[Dict[str, Any]], output_dir: str = "outputs/alerts") -> List[str]:
        """
        Generate alerts for multiple trades.
        
        Args:
            trades: List of trade structures
            risk_metrics_list: List of risk metrics for each trade
            output_dir: Output directory path
            
        Returns:
            List of file paths
        """
        filepaths = []
        
        for trade, risk_metrics in zip(trades, risk_metrics_list):
            try:
                filepath = TOSAlertGenerator.save_alert(trade, risk_metrics, output_dir)
                filepaths.append(filepath)
            except Exception as e:
                logger.error(f"Error generating alert for {trade.get('symbol')}: {e}")
        
        return filepaths
