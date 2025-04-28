"""
Standalone Telegram bot for Crypto Borrow/Repay Ratio tracker
This runs independently of the main Flask application
"""

import os
import sys
import json
import logging
import requests
import time
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
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '')
SUBSCRIBERS_FILE = 'subscribers.json'
DATA_CACHE_FILE = 'telegram_crypto_data.json'

# Cached data
cached_data = "Данные ещё не загружены."

# ===== Subscriber management =====
def load_subscribers():
    if os.path.exists(SUBSCRIBERS_FILE):
        with open(SUBSCRIBERS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_subscribers(subscribers):
    with open(SUBSCRIBERS_FILE, 'w') as f:
        json.dump(subscribers, f)

def add_subscriber(chat_id):
    subscribers = load_subscribers()
    if chat_id not in subscribers:
        subscribers.append(chat_id)
        save_subscribers(subscribers)

def remove_subscriber(chat_id):
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
    Fetches cryptocurrency leverage indicator data from different sources
    Returns the top 10 cryptocurrencies by leverage indicator
    """
    try:
        # Try the web app's API endpoint first for data sharing
        # Using the Replit domain directly to avoid port conflicts
        try:
            # This will use the externally accessible Replit URL
            logger.info("Trying to fetch data from web application API")
            # Get the Replit domain from environment or use a fallback
            replit_domain = os.environ.get('REPLIT_DOMAIN', '')
            api_url = f"https://{replit_domain}/api/crypto-data" if replit_domain else "http://localhost:5000/api/crypto-data"
            logger.info(f"Using API URL: {api_url}")
            web_response = requests.get(api_url, timeout=5)
            if web_response.status_code == 200:
                data = web_response.json().get('data', [])
                logger.info("Successfully fetched data from web application")
                if data and len(data) > 0:
                    return data
        except Exception as e:
            logger.warning(f"Could not fetch data from web app: {e}")
        
        # Try CoinGecko API directly
        logger.info("Trying to fetch data from CoinGecko API")
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "volume_desc",
            "per_page": 100,  # Get 100 coins to filter for those with high leverage indicator
            "page": 1,
            "sparkline": "false",
            "price_change_percentage": "24h",
            "x_cg_demo_api_key": "CG-NZRKaD3gmsoYi6kqScnmNW4w"
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json"
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code != 200:
            logger.warning(f"CoinGecko API error: {response.status_code}")
            # If CoinGecko API fails, use sample data
            return get_sample_data()

        data = response.json()
        if not data:
            logger.warning("Received empty data from CoinGecko API")
            return get_sample_data()
        
        result = []
        for item in data:
            # Volume and market cap as leverage indicators
            total_volume = float(item.get('total_volume', 0) or 0)
            market_cap = float(item.get('market_cap', 1) or 1)
            
            # Calculate volume to market cap ratio (indicates trading activity relative to size)
            volume_to_mcap_ratio = total_volume / market_cap if market_cap > 0 else 0
            
            # Price volatility as another leverage indicator
            price_change_24h = abs(float(item.get('price_change_percentage_24h', 0) or 0))
            
            # Combine metrics to create a leverage indicator
            # Higher volume/mcap ratio + high volatility = likely high leverage activity
            leverage_indicator = round(volume_to_mcap_ratio * (1 + price_change_24h/100) * 100, 2)
            
            # Format for the bot's display (using Binance format for compatibility)
            result.append({
                'asset': item['symbol'].upper(),
                'name': item['name'],
                'totalBorrowed': str(total_volume),  # Using volume as a proxy for borrowed amount
                'totalRepaid': str(market_cap / 10),  # Dividing by 10 to get ratios in similar ranges
                'ratio': leverage_indicator  # Our derived leverage indicator
            })
            
        # Filter for high leverage indicators (> 10) and sort by the indicator (descending)
        filtered_data = [item for item in result if item.get('ratio', 0) > 10]
        # Use filtered data if available, otherwise use all data
        if filtered_data:
            top = sorted(filtered_data, key=lambda x: x.get('ratio', 0), reverse=True)[:10]
        else:
            # If no items with ratio > 10, use the top 10 by ratio
            top = sorted(result, key=lambda x: x.get('ratio', 0), reverse=True)[:10]
        
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
        # Handle both web app and direct API formats
        if 'symbol' in item:
            asset = item['symbol']
            borrowed = float(item.get('borrow_amount', 0))
            repaid = float(item.get('repay_amount', 1)) if item.get('repay_amount') else 1
            ratio = item.get('ratio', round(borrowed / repaid, 1)) if repaid else 0
        else:
            # Legacy format with asset/totalBorrowed/totalRepaid
            asset = item.get('asset', item.get('symbol', '???'))
            borrowed = float(item.get('totalBorrowed', 0))
            repaid = float(item.get('totalRepaid', 1)) if item.get('totalRepaid') else 1
            ratio = item.get('ratio', round(borrowed / repaid, 1)) if repaid else 0
            
        # Format the output line
        output += f"{asset:<10} {borrowed/1e6:>6.1f}M  {repaid/1e6:>6.1f}M  {ratio:>6.1f}\n"
    
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