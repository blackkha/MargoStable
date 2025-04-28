"""
Configuration settings for the Binance Margin Stats Bot
"""

import os
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Telegram Bot Token
# Use environment variable if available, otherwise use hardcoded token
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '7971296486:AAHG34ZWKqGs4b9Oo_IMaB6X08UdJN9TmAg')

# File for storing subscribers
SUBSCRIBERS_FILE = 'subscribers.json'

# Binance API settings
BINANCE_API_BASE_URL = "https://www.binance.com/bapi/earn/v1/private/lending/margin/market"

# Scheduler settings
DATA_UPDATE_INTERVAL_MINUTES = 10
DAILY_REPORT_HOUR = 10
DAILY_REPORT_MINUTE = 0
DAILY_REPORT_TIMEZONE = "UTC"

# Initialize application settings
def init_app():
    """Initialize application settings and check for required resources."""
    logger.info("Initializing application settings...")
    
    # Check if token is available
    if not TELEGRAM_TOKEN:
        logger.critical("Telegram token not found!")
        raise ValueError("Telegram token not configured. Set the TELEGRAM_TOKEN environment variable.")
    
    # Log configuration
    logger.info(f"Bot configured with update interval: {DATA_UPDATE_INTERVAL_MINUTES} minutes")
    logger.info(f"Daily reports scheduled for: {DAILY_REPORT_HOUR}:{DAILY_REPORT_MINUTE} {DAILY_REPORT_TIMEZONE}")
    
    return True
