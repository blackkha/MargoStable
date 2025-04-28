#!/usr/bin/env python
"""
Launcher script for Telegram Bot with no Flask dependencies
"""
import os
import sys
import logging
import subprocess

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Check for Telegram token
if not os.environ.get('TELEGRAM_TOKEN'):
    logger.error("TELEGRAM_TOKEN environment variable not set")
    print("Please set the TELEGRAM_TOKEN environment variable")
    sys.exit(1)

# This is the main entry point when the script is run
if __name__ == "__main__":
    logger.info("Starting Telegram bot launcher...")
    try:
        # Run standalone_bot.py using a separate process
        # This completely bypasses any Flask dependencies
        logger.info("Launching standalone_bot.py...")
        
        # Use execv to replace the current process with the bot process
        # This ensures no Flask app gets initialized
        os.execv(sys.executable, [sys.executable, 'standalone_bot.py'])
    except Exception as e:
        logger.error(f"Failed to start Telegram bot: {e}")
        sys.exit(1)