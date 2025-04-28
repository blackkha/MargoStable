#!/usr/bin/env python3
"""
Dedicated entry point for Telegram bot workflow
"""
import os
import logging
import subprocess

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Run the Telegram bot in a separate process to avoid conflicts with Flask app"""
    logger.info("Starting Telegram bot workflow...")
    
    # Check for TELEGRAM_TOKEN
    if not os.environ.get("TELEGRAM_TOKEN"):
        logger.error("TELEGRAM_TOKEN environment variable not set. Bot will not work.")
        return
    
    # Run the standalone telegram bot script
    try:
        logger.info("Executing telegram_workflow.py")
        result = subprocess.run(["python", "telegram_workflow.py"], check=True)
        logger.info(f"Telegram bot exited with code {result.returncode}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running Telegram bot: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()