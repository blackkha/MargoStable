"""
Module for fetching and processing Binance margin data
"""

import requests
import logging
from typing import Dict, List, Any

# Set up logging
logger = logging.getLogger(__name__)

# Cached data
_cached_data = "Данные ещё не загружены."

def get_cached_data() -> str:
    """Return the currently cached margin data."""
    global _cached_data
    return _cached_data

def fetch_margin_data() -> str:
    """
    Fetch margin trading data from Binance API.
    Returns formatted string with top 10 assets by borrowed amount.
    """
    url = "https://www.binance.com/bapi/earn/v1/private/lending/margin/market"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        logger.info("Fetching margin data from Binance API")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
        
        data = response.json().get('data', [])
        
        if not data:
            logger.warning("Received empty data from Binance API")
            return "<pre>❌ Получены пустые данные от Binance API</pre>"
            
        # Sort by total borrowed amount (descending) and take top 10
        top_assets = sorted(data, key=lambda x: float(x.get('totalBorrowed', 0)), reverse=True)[:10]
        
        # Format the data into a readable table
        output = "📊 TOP 10 ASSETS BY BORROWED AMOUNT\n"
        output += "ASSET      BOR.D   REP.D     B/R\n"
        output += "-------------------------------\n"
        
        for item in top_assets:
            asset = item['asset']
            borrowed = float(item.get('totalBorrowed', 0))
            repaid = float(item.get('totalRepaid', 1)) if item.get('totalRepaid') else 1
            ratio = round(borrowed / repaid, 1)
            
            output += f"{asset:<10} {borrowed/1e6:>6.1f}M  {repaid/1e6:>6.1f}M  {ratio:>6}\n"
        
        # Add timestamp and footer
        output += "\nBOR.D = Borrowed (Daily), REP.D = Repaid (Daily), B/R = Borrowed/Repaid Ratio"
        
        return f"<pre>{output}</pre>"
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching data from Binance API: {e}")
        return f"<pre>❌ Ошибка при получении данных с Binance API: {str(e)}</pre>"
    except Exception as e:
        logger.error(f"Unexpected error processing margin data: {e}")
        return f"<pre>❌ Неожиданная ошибка: {str(e)}</pre>"

def update_cached_data() -> None:
    """Update the cached margin data."""
    global _cached_data
    logger.info("Updating cached margin data...")
    _cached_data = fetch_margin_data()
    logger.info("Margin data cache updated successfully")
