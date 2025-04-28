"""
Standalone script to run the Telegram bot independently from the Flask application
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

if __name__ == "__main__":
    try:
        logger.info("Starting standalone Telegram bot...")
        # Import standalone_bot which doesn't have Flask dependencies
        from standalone_bot import main as run_bot
        run_bot()
    except Exception as e:
        logger.error(f"Error running Telegram bot: {e}")
        sys.exit(1)