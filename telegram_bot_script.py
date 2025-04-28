"""
Standalone script to run the Telegram bot without importing the Flask app
"""
import os
import sys
import logging

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

# Import the standalone bot implementation
try:
    from standalone_bot import main as run_bot
    logger.info("Starting standalone Telegram bot...")
    run_bot()
except ImportError as e:
    logger.error(f"Import error: {e}")
    sys.exit(1)
except Exception as e:
    logger.error(f"Error running Telegram bot: {e}")
    sys.exit(1)