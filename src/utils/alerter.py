"""Alert system for notifications."""

from datetime import datetime
from src.utils.logger import get_logger

logger = get_logger(__name__)

class AlertManager:
    """Manage high-priority system alerts."""
    
    @staticmethod
    def send_alert(title: str, message: str, level: str = 'INFO'):
        """
        Send an alert. 
        Currently logs to console/file. Can be extended to Email/SMS.
        
        Args:
            title: Short header
            message: Detailed message
            level: 'INFO', 'WARNING', 'CRITICAL'
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        full_msg = f"[{level}] {title}: {message}"
        
        if level == 'CRITICAL':
            logger.critical(full_msg)
            # TODO: Hook into Email/SMS API here
            # e.g. twilio_client.send_message(...)
        elif level == 'WARNING':
            logger.warning(full_msg)
        else:
            logger.info(full_msg)

    @staticmethod
    def notify_trade(trade: dict):
        """Notify user of a new high-quality trade setup."""
        symbol = trade.get('symbol')
        score = trade.get('score', 0)
        strategy = trade.get('strategy')
        
        AlertManager.send_alert(
            title=f"New Trade Found: {symbol}",
            message=f"Strategy: {strategy} | Score: {score}",
            level='INFO'
        )
