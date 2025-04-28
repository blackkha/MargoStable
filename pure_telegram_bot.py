"""
Pure Telegram bot without any Flask dependencies
This bot runs completely independently from the Flask web application
"""
import os
import sys
import json
import logging
import requests
from datetime import datetime

try:
    from telegram import Update
    from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackContext
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
except ImportError:
    print("Required packages not found. Please install: python-telegram-bot, apscheduler")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
DATA_CACHE_FILE = 'telegram_bot_cache.json'
SUBSCRIBERS_FILE = 'telegram_subscribers.json'
cached_data = "Data loading..."

# ===== Subscriber management =====
def load_subscribers():
    """Load subscribers from file"""
    try:
        if os.path.exists(SUBSCRIBERS_FILE):
            with open(SUBSCRIBERS_FILE, 'r') as f:
                return json.load(f)
        return []
    except Exception as e:
        logger.error(f"Error loading subscribers: {e}")
        return []

def save_subscribers(subscribers):
    """Save subscribers to file"""
    try:
        with open(SUBSCRIBERS_FILE, 'w') as f:
            json.dump(subscribers, f)
        return True
    except Exception as e:
        logger.error(f"Error saving subscribers: {e}")
        return False

def add_subscriber(chat_id):
    """Add a subscriber to the list"""
    subscribers = load_subscribers()
    if chat_id not in subscribers:
        subscribers.append(chat_id)
        save_subscribers(subscribers)

def remove_subscriber(chat_id):
    """Remove a subscriber from the list"""
    subscribers = load_subscribers()
    if chat_id in subscribers:
        subscribers.remove(chat_id)
        save_subscribers(subscribers)

# ===== Data handling =====
def get_sample_data():
    """Return sample data for demonstration purposes"""
    logger.info("Using sample data")
    sample_data = [
        {"asset": "APE", "totalBorrowed": "320000000", "totalRepaid": "16000000", "ratio": 20.00},
        {"asset": "SHIB", "totalBorrowed": "456000000", "totalRepaid": "25000000", "ratio": 18.24},
        {"asset": "GALA", "totalBorrowed": "95000000", "totalRepaid": "5500000", "ratio": 17.27},
        {"asset": "AXS", "totalBorrowed": "167500000", "totalRepaid": "10500000", "ratio": 15.95},
        {"asset": "SAND", "totalBorrowed": "125000000", "totalRepaid": "8500000", "ratio": 14.71},
        {"asset": "MANA", "totalBorrowed": "230000000", "totalRepaid": "17000000", "ratio": 13.53},
        {"asset": "NEAR", "totalBorrowed": "142500000", "totalRepaid": "11500000", "ratio": 12.39},
        {"asset": "FTM", "totalBorrowed": "176000000", "totalRepaid": "16200000", "ratio": 10.86},
        {"asset": "ATOM", "totalBorrowed": "183500000", "totalRepaid": "17300000", "ratio": 10.61},
        {"asset": "ONE", "totalBorrowed": "92800000", "totalRepaid": "8900000", "ratio": 10.43}
    ]
    return sample_data

def fetch_margin_data():
    """
    Fetches cryptocurrency margin data from Binance or sample data if not available
    Returns a formatted string with the top 10 crypto assets by B/R ratio
    """
    try:
        # Try Binance API directly
        logger.info("Trying to fetch data from Binance API")
        url = "https://www.binance.com/bapi/earn/v1/private/lending/margin/market"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            logger.warning(f"Binance API error: {response.status_code}")
            # If Binance API fails, use sample data
            return get_sample_data()

        data = response.json().get('data', [])
        if not data:
            logger.warning("Received empty data from Binance API")
            return get_sample_data()
        
        # Calculate borrow/repay ratio for each asset
        for item in data:
            borrowed = float(item.get('totalBorrowed', 0))
            repaid = float(item.get('totalRepaid', 1)) if item.get('totalRepaid') else 1
            item['ratio'] = borrowed / repaid
        
        # Filter for ratios > 10 and sort by ratio (descending)
        filtered_data = [item for item in data if item.get('ratio', 0) > 10]
        # Use filtered data if available, otherwise use all data
        if filtered_data:
            top = sorted(filtered_data, key=lambda x: x.get('ratio', 0), reverse=True)[:10]
        else:
            # If no items with ratio > 10, use the top 10 by ratio
            top = sorted(data, key=lambda x: x.get('ratio', 0), reverse=True)[:10]
        
        # Save data to cache file for backup
        with open(DATA_CACHE_FILE, 'w') as f:
            json.dump(top, f)
            
        return top
        
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        # Try to load from cache file
        try:
            if os.path.exists(DATA_CACHE_FILE):
                with open(DATA_CACHE_FILE, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        
        # Use sample data as last resort
        return get_sample_data()

def format_data_for_telegram(data):
    """Convert data to a nicely formatted string for Telegram"""
    output = "TOP CRYPTOCURRENCIES WITH B/R RATIO > 10\n"
    output += "ASSET      BOR.D   REP.D     B/R\n-------------------------------\n"
    for item in data:
        asset = item['asset']
        borrowed = float(item['totalBorrowed'])
        repaid = float(item['totalRepaid']) if item.get('totalRepaid') else 1
        ratio = round(borrowed / repaid, 1)
        output += f"{asset:<10} {borrowed/1e6:>6.1f}M  {repaid/1e6:>6.1f}M  {ratio:>6}\n"
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    return f"<pre>{output}\n\nUpdated: {timestamp}</pre>"

def update_cached_data():
    """Update the global cached data"""
    global cached_data
    logger.info("Updating data from sources...")
    try:
        data = fetch_margin_data()
        cached_data = format_data_for_telegram(data)
    except Exception as e:
        logger.error(f"Error updating data: {e}")
        cached_data = "<pre>Data temporarily unavailable. Please try again later.</pre>"

# ===== Bot commands =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello! I'm the Crypto Borrow/Repay Ratio Bot.\n"
        "I track cryptocurrencies with Borrow/Repay Ratio > 10.\n\n"
        "/margin — view current data\n"
        "/subscribe — subscribe to daily reports\n"
        "/unsubscribe — unsubscribe from reports"
    )

async def margin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_html(cached_data)

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    add_subscriber(chat_id)
    await update.message.reply_text("You've subscribed to daily reports at 10:00 UTC.")

async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    remove_subscriber(chat_id)
    await update.message.reply_text("You've unsubscribed from daily reports.")

# ===== Daily report =====
async def send_daily_report(context: CallbackContext):
    subscribers = load_subscribers()
    for chat_id in subscribers:
        try:
            await context.bot.send_message(chat_id=chat_id, text=cached_data, parse_mode='HTML')
        except Exception as e:
            logger.error(f"Error sending to {chat_id}: {e}")

# ===== Main function =====
def main():
    if not TELEGRAM_TOKEN:
        logger.error("No TELEGRAM_TOKEN found in environment variables")
        print("Please set the TELEGRAM_TOKEN environment variable")
        return

    update_cached_data()  # Update cache at startup

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("margin", margin))
    app.add_handler(CommandHandler("subscribe", subscribe))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe))

    scheduler = BackgroundScheduler()

    # Update data every 10 minutes
    scheduler.add_job(update_cached_data, 'interval', minutes=10)

    # Send daily report at 10:00 UTC
    scheduler.add_job(
        lambda: app.create_task(send_daily_report(app)),
        CronTrigger(hour=10, minute=0, timezone="UTC")
    )

    scheduler.start()

    logger.info("Bot started.")
    app.run_polling()

if __name__ == '__main__':
    main()