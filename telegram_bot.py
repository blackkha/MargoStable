"""
Telegram bot for Crypto Borrow/Repay Ratio tracker
This launches the standalone telegram bot independently from the main Flask application
"""

import sys
import os
import logging
from standalone_bot import main as run_bot

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting Telegram bot")
    try:
        run_bot()
    except Exception as e:
        logger.error(f"Error starting Telegram bot: {e}")
        sys.exit(1)