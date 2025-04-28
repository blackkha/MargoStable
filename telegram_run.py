#!/usr/bin/env python3
"""
Main entry point for Telegram bot
This will run as a separate workflow without initializing the Flask app
"""
import os
import logging
import subprocess
import time

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def run_bot():
    """Run the Telegram bot continuously"""
    logger.info("Starting Telegram bot runner...")
    
    # Check for TELEGRAM_TOKEN
    if not os.environ.get("TELEGRAM_TOKEN"):
        logger.error("TELEGRAM_TOKEN environment variable not set. Bot will not work.")
        return
    
    while True:
        try:
            logger.info("Executing telegram_workflow.py")
            subprocess.run(["python", "telegram_workflow.py"])
        except Exception as e:
            logger.error(f"Error running Telegram bot: {e}")
        
        logger.info("Bot process exited, restarting in 5 seconds...")
        time.sleep(5)

if __name__ == "__main__":
    run_bot()