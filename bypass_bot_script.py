"""
Script to run Telegram bot in a way that bypasses Flask dependency
"""
import os
import sys
import logging
import importlib
import importlib.util
from importlib.machinery import ModuleSpec

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

# Dynamically load standalone_bot and run it
try:
    logger.info("Starting Telegram bot without Flask...")
    
    # Import the module directly from the file
    spec = importlib.util.spec_from_file_location("standalone_bot", "standalone_bot.py")
    if spec is None:
        logger.error("Failed to find standalone_bot.py file")
        sys.exit(1)
    
    # Since we checked spec is not None, we can safely cast it to ModuleSpec
    typed_spec: ModuleSpec = spec  
    standalone_bot = importlib.util.module_from_spec(typed_spec)
    
    if typed_spec.loader is None:
        logger.error("Failed to load standalone_bot.py module: loader is None")
        sys.exit(1)
        
    typed_spec.loader.exec_module(standalone_bot)
    
    # Execute the main function
    standalone_bot.main()
except Exception as e:
    logger.error(f"Error running Telegram bot: {e}")
    sys.exit(1)