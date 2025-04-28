"""
Standalone script to run the Telegram bot without port conflicts
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

# Make sure this script doesn't import the Flask app
if __name__ == "__main__":
    try:
        logger.info("Starting Telegram bot without web app dependencies...")
        # Import the standalone bot that doesn't depend on the Flask app
        # This ensures there are no port conflicts
        from standalone_bot import main as run_bot
        run_bot()
    except ImportError as e:
        logger.error(f"Import error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        sys.exit(1)