#!/usr/bin/env python
"""
Dedicated script for running only the Telegram bot with no Flask dependencies
This script is intended to be used in a separate workflow
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

# Execute standalone_bot.py directly
try:
    logger.info("Starting standalone Telegram bot...")
    
    # Using exec to import and run the standalone_bot module
    # This avoids any potential Flask app initialization
    with open('standalone_bot.py', 'r') as f:
        bot_code = f.read()
        
    # Create a namespace for execution
    bot_namespace = {}
    
    # Execute the bot code in the namespace
    exec(bot_code, bot_namespace)
    
    # Call the main function
    bot_namespace['main']()
except Exception as e:
    logger.error(f"Error running Telegram bot: {e}")
    sys.exit(1)