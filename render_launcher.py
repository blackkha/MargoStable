#!/usr/bin/env python3
"""
Launcher script for Render.com deployment
This runs both the Flask web application and Telegram bot concurrently
"""
import os
import logging
import subprocess
import sys
import time
from threading import Thread
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Check for required environment variables
if not os.environ.get("PORT"):
    logger.warning("PORT environment variable not set, using default 5000")
    os.environ["PORT"] = "5000"

def run_flask_app():
    """Run the Flask web application using gunicorn"""
    port = os.environ.get("PORT", "5000")
    logger.info(f"Starting Flask application on port {port}")
    
    try:
        # Use gunicorn to run the Flask app
        subprocess.run([
            "gunicorn", 
            "--bind", f"0.0.0.0:{port}", 
            "--workers", "1",
            "--threads", "8",
            "--timeout", "120",
            "main:app"
        ], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Flask application failed with error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error running Flask app: {e}")
    
    logger.warning("Flask application has stopped")

def run_telegram_bot():
    """Run the Telegram bot"""
    if not os.environ.get("TELEGRAM_TOKEN"):
        logger.error("TELEGRAM_TOKEN environment variable not set. Bot will not work.")
        return
    
    logger.info("Starting Telegram bot")
    
    try:
        # Run the Telegram bot using the standalone workflow script
        subprocess.run(["python", "telegram_workflow.py"], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Telegram bot failed with error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error running Telegram bot: {e}")
    
    logger.warning("Telegram bot has stopped")

def main():
    """Run both the Flask app and Telegram bot in separate threads"""
    logger.info("Starting MargoBot launcher for Render.com")
    
    # Create thread for Flask app
    flask_thread = Thread(target=run_flask_app)
    flask_thread.daemon = True
    
    # Create thread for Telegram bot
    telegram_thread = Thread(target=run_telegram_bot)
    telegram_thread.daemon = True
    
    # Start both threads
    flask_thread.start()
    telegram_thread.start()
    
    # Keep the main thread running to allow both services to continue
    try:
        while True:
            time.sleep(60)
            # Log health check every minute
            logger.info("Health check: Services running")
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Main thread error: {e}")
    
    logger.info("MargoBot launcher shutting down")

if __name__ == "__main__":
    main()