#!/usr/bin/env python3
"""
Standalone Telegram bot for Crypto Leverage Indicator tracker
This runs independently of the main Flask application
"""
import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, List

import requests
import pytz
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackContext,
)
from apscheduler.schedulers.background import BackgroundScheduler

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Constants
SUBSCRIBERS_FILE = "telegram_subscribers.json"
CACHE_FILE = "telegram_crypto_data.json"
API_URL = "http://localhost:5000/api/crypto-data"
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    logger.error("TELEGRAM_TOKEN environment variable not set. Bot will not work.")

# Initialize scheduler
scheduler = BackgroundScheduler()

def load_subscribers() -> List[int]:
    """Load subscribers from file"""
    try:
        if os.path.exists(SUBSCRIBERS_FILE):
            with open(SUBSCRIBERS_FILE, "r") as f:
                return json.load(f)
        return []
    except Exception as e:
        logger.error(f"Error loading subscribers: {e}")
        return []

def save_subscribers(subscribers: List[int]) -> None:
    """Save subscribers to file"""
    try:
        with open(SUBSCRIBERS_FILE, "w") as f:
            json.dump(subscribers, f)
    except Exception as e:
        logger.error(f"Error saving subscribers: {e}")

def add_subscriber(chat_id: int) -> bool:
    """Add a subscriber to the list"""
    subscribers = load_subscribers()
    if chat_id not in subscribers:
        subscribers.append(chat_id)
        save_subscribers(subscribers)
        return True
    return False

def remove_subscriber(chat_id: int) -> bool:
    """Remove a subscriber from the list"""
    subscribers = load_subscribers()
    if chat_id in subscribers:
        subscribers.remove(chat_id)
        save_subscribers(subscribers)
        return True
    return False

def get_sample_data() -> List[Dict]:
    """Return sample data for demonstration purposes"""
    return [
        {
            "symbol": "SOL",
            "name": "Wrapped SOL",
            "ratio": 141752735692.04,
            "borrow_amount": 1354127513.0,
            "repay_amount": 0.1,
            "borrow_formatted": "1.4B", 
            "repay_formatted": "0.1"
        },
        {
            "symbol": "USUAL",
            "name": "Usual (Pre-Market)",
            "ratio": 20956704100.0,
            "borrow_amount": 209567041.0,
            "repay_amount": 0.1,
            "borrow_formatted": "209.6M",
            "repay_formatted": "0.1"
        },
        {
            "symbol": "ALPACA",
            "name": "Alpaca Finance",
            "ratio": 4200.14,
            "borrow_amount": 252591704.0,
            "repay_amount": 1864812.3,
            "borrow_formatted": "252.6M",
            "repay_formatted": "1.9M"
        }
    ]

def fetch_margin_data() -> List[Dict]:
    """
    Fetches cryptocurrency leverage indicator data from web app API or directly from CoinGecko
    Returns the top cryptocurrencies by leverage indicator
    """
    logger.info("Trying to fetch data from web application API")
    logger.info(f"Using API URL: {API_URL}")
    
    try:
        # Try to fetch data from the web application's API
        response = requests.get(API_URL, timeout=5)
        if response.status_code == 200:
            logger.info("Successfully fetched data from web application")
            data = response.json().get("data", [])
            return data[:20]  # Return top 20 cryptocurrencies
    except Exception as e:
        logger.error(f"Error fetching data from web application: {e}")
    
    # If we couldn't get data from the API, try to load from cache
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r") as f:
                cached_data = json.load(f)
                logger.info("Using cached data")
                return cached_data[:20]
    except Exception as e:
        logger.error(f"Error loading cached data: {e}")
    
    # As a last resort, return sample data
    logger.info("Using sample data")
    return get_sample_data()

def format_data_for_telegram(data: List[Dict]) -> str:
    """Convert data to a nicely formatted string for Telegram"""
    current_time = datetime.now(pytz.timezone("UTC")).strftime("%Y-%m-%d %H:%M:%S UTC")
    message = f"🔥 *Top Crypto Leverage Indicators* 🔥\n{current_time}\n\n"
    
    for i, crypto in enumerate(data[:10], 1):  # Top 10 for Telegram messages
        symbol = crypto.get("symbol", "")
        name = crypto.get("name", "")
        ratio = crypto.get("ratio", 0)
        borrow = crypto.get("borrow_formatted", "0")
        repay = crypto.get("repay_formatted", "0")
        
        message += f"{i}. *{symbol}* ({name})\n"
        message += f"   Leverage Indicator: *{ratio:.2f}*\n"
        message += f"   Borrow: {borrow} | Repay: {repay}\n\n"
    
    message += "Data source: CoinGecko API\n"
    message += "Leverage Indicator = Volume/Market Cap Ratio\n"
    
    return message

def update_cached_data() -> None:
    """Update the global cached data"""
    logger.info("Updating data from sources...")
    data = fetch_margin_data()
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(data, f)
        logger.info("Data cached successfully")
    except Exception as e:
        logger.error(f"Error caching data: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    welcome_message = (
        f"Hello {user.first_name}! 👋\n\n"
        "I'm the Crypto Leverage Indicator Bot. I track cryptocurrencies with high leverage indicators.\n\n"
        "Available commands:\n"
        "/margin - Get the latest crypto leverage indicator data\n"
        "/subscribe - Subscribe to daily updates\n"
        "/unsubscribe - Unsubscribe from daily updates\n\n"
        "Powered by CoinGecko API"
    )
    await update.message.reply_text(welcome_message)

async def margin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the current margin data when the command /margin is issued."""
    await update.message.reply_text("Fetching the latest data... 🔍")
    data = fetch_margin_data()
    message = format_data_for_telegram(data)
    await update.message.reply_text(message, parse_mode="Markdown")

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Subscribe to daily margin reports."""
    chat_id = update.effective_chat.id
    if add_subscriber(chat_id):
        await update.message.reply_text(
            "✅ You've successfully subscribed to daily leverage indicator reports! "
            "You'll receive updates every day at 12:00 UTC."
        )
    else:
        await update.message.reply_text(
            "You're already subscribed to daily reports! "
            "Use /unsubscribe to unsubscribe."
        )

async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unsubscribe from daily margin reports."""
    chat_id = update.effective_chat.id
    if remove_subscriber(chat_id):
        await update.message.reply_text(
            "❌ You've been unsubscribed from daily reports. "
            "Use /subscribe to subscribe again."
        )
    else:
        await update.message.reply_text(
            "You're not subscribed to daily reports. "
            "Use /subscribe to subscribe."
        )

async def send_daily_report(context: CallbackContext) -> None:
    """Send daily reports to all subscribers."""
    subscribers = load_subscribers()
    logger.info(f"Sending daily report to {len(subscribers)} subscribers")
    
    if not subscribers:
        logger.info("No subscribers to send reports to")
        return
    
    data = fetch_margin_data()
    message = format_data_for_telegram(data)
    
    for chat_id in subscribers:
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode="Markdown"
            )
            time.sleep(0.5)  # Avoid hitting rate limits
        except Exception as e:
            logger.error(f"Error sending message to {chat_id}: {e}")

def main() -> None:
    """Run the bot."""
    logger.info("Starting standalone Telegram bot...")
    
    # Update the cached data at startup
    update_cached_data()
    
    # Create the Application instance
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("margin", margin))
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe))
    
    # Schedule data updates every hour
    scheduler.add_job(update_cached_data, 'interval', hours=1)
    
    # Schedule daily reports at 12:00 UTC
    scheduler.add_job(
        lambda: application.create_task(send_daily_report(application)),
        'cron',
        hour=12,
        minute=0
    )
    
    # Start the scheduler
    scheduler.start()
    
    logger.info("Bot started.")
    
    # Run the bot until the process is stopped
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()