"""
Utility functions for the Binance Margin Stats Bot
"""

import logging
from datetime import datetime
import pytz

# Set up logging
logger = logging.getLogger(__name__)

def get_formatted_timestamp(timezone: str = "UTC") -> str:
    """
    Return a nicely formatted timestamp in the specified timezone.
    
    Args:
        timezone: The timezone to use (default: "UTC")
        
    Returns:
        A formatted timestamp string
    """
    try:
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        return now.strftime("%Y-%m-%d %H:%M:%S %Z")
    except Exception as e:
        logger.error(f"Error formatting timestamp: {e}")
        # Fall back to UTC timestamp without timezone info
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

def format_large_number(number: float, decimals: int = 1) -> str:
    """
    Format large numbers with K, M, B suffixes.
    
    Args:
        number: The number to format
        decimals: Number of decimal places to show
        
    Returns:
        Formatted string with appropriate suffix
    """
    if number is None:
        return "N/A"
        
    try:
        abs_number = abs(number)
        if abs_number < 1000:
            return f"{number:.{decimals}f}"
        elif abs_number < 1000000:
            return f"{number/1000:.{decimals}f}K"
        elif abs_number < 1000000000:
            return f"{number/1000000:.{decimals}f}M"
        else:
            return f"{number/1000000000:.{decimals}f}B"
    except Exception as e:
        logger.error(f"Error formatting large number: {e}")
        return str(number)

def safe_float(value, default=0.0):
    """
    Safely convert a value to float.
    
    Args:
        value: The value to convert
        default: Default value if conversion fails
        
    Returns:
        The float value or the default
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def validate_chat_id(chat_id):
    """
    Validate that a chat ID is in the correct format.
    
    Args:
        chat_id: The chat ID to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Ensure it's an integer
        chat_id = int(chat_id)
        # Telegram chat IDs are typically large integers
        return True
    except (ValueError, TypeError):
        return False
