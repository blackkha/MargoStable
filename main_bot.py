#!/usr/bin/env python
"""
Main entry point for Telegram Bot in Replit workflow
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

# Prevent app.py Flask initialization by setting environment variable
os.environ["SKIP_FLASK_INIT"] = "1"

if __name__ == "__main__":
    logger.info("Starting standalone Telegram bot...")
    
    # Try to run standalone_bot.py directly
    # This should avoid importing app.py and its Flask initialization
    try:
        # Import standalone_bot.py
        import standalone_bot
        
        # Run the bot
        standalone_bot.main()
    except Exception as e:
        logger.error(f"Error running Telegram bot: {e}")
        sys.exit(1)