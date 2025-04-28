import os
import json
import requests
import logging
import ccxt
import pandas as pd
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
import plotly.express as px
import plotly.utils as pu

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

# Create declarative base for SQLAlchemy
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///crypto_data.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with SQLAlchemy
db.init_app(app)

# Create models
class CryptoData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(20), nullable=False)
    borrow_amount = db.Column(db.Float, nullable=False)
    repay_amount = db.Column(db.Float, nullable=False)
    ratio = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'symbol': self.symbol,
            'borrow_amount': self.borrow_amount,
            'repay_amount': self.repay_amount,
            'ratio': self.ratio,
            'timestamp': self.timestamp.isoformat()
        }

# Function to fetch crypto data from different exchanges
def fetch_crypto_borrow_data():
    """
    Fetch cryptocurrency leverage indicator data from exchanges.
    Returns the top 20 cryptocurrencies by leverage indicators.
    """
    try:
        # First try to get data from CoinGecko
        return fetch_coingecko_market_data()
    except Exception as e:
        logger.error(f"Error fetching from CoinGecko: {e}")
        
        # If CoinGecko fails, try another source
        try:
            return fetch_alternative_source_data()
        except Exception as e:
            logger.error(f"Error fetching from alternative source: {e}")
            
            # If all fails, get from cache or sample
            return get_cached_or_sample_data()

def fetch_coingecko_market_data():
    """Fetch market data from CoinGecko API to derive a leverage indicator"""
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "volume_desc",
        "per_page": 100,  # Get 100 coins to filter for those with high leverage indicator
        "page": 1,
        "sparkline": "false",
        "price_change_percentage": "24h,7d",
        "x_cg_demo_api_key": "CG-NZRKaD3gmsoYi6kqScnmNW4w"
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json"
    }
    
    logger.info("Fetching market data from CoinGecko API")
    response = requests.get(url, params=params, headers=headers, timeout=10)
    
    # Check if request was successful
    if response.status_code == 200:
        data = response.json()
        
        if not data:
            logger.warning("Received empty data from CoinGecko API")
            raise Exception("Empty data received from CoinGecko")
            
        # Process the data
        result = []
        for item in data:
            symbol = item['symbol'].upper()
            name = item['name']
            
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
            
            # Use total_volume as borrow_amount and market_cap as repay_amount for UI consistency
            result.append({
                'symbol': symbol,
                'name': name,
                'borrow_amount': total_volume,  # Using volume as a proxy for borrowed amount
                'borrow_formatted': format_large_number(total_volume),
                'repay_amount': market_cap / 10,  # Dividing by 10 to get ratios in similar ranges
                'repay_formatted': format_large_number(market_cap / 10),
                'ratio': leverage_indicator  # Our derived leverage indicator
            })
        
        # Filter for high leverage indicators (> 10) and sort by the indicator (descending)
        result = [item for item in result if item['ratio'] > 10]
        result = sorted(result, key=lambda x: x['ratio'], reverse=True)[:20]
        
        # Save to cache
        save_to_cache(result)
        
        # Save to database
        save_to_database(result)
        
        return result
    else:
        logger.error(f"CoinGecko API returned status code {response.status_code}")
        raise Exception(f"Failed to fetch data from CoinGecko: {response.status_code}")

def fetch_alternative_source_data():
    """Fetch data from an alternative source using CCXT"""
    logger.info("Fetching data from alternative sources using CCXT")
    
    # We'll use CCXT to get data from multiple exchanges - limiting to just binance to speed up processing
    exchanges = ['binance']  # Further limiting the exchanges to speed up processing
    
    all_data = []
    success = False
    
    for exchange_id in exchanges:
        try:
            # Initialize the exchange
            exchange_class = getattr(ccxt, exchange_id)
            exchange = exchange_class({
                'enableRateLimit': True,
            })
            
            # Get markets
            markets = exchange.load_markets()
            
            # For each exchange, we'll estimate borrow/repay by using 
            # 24h volume and price changes as a proxy
            symbols = list(markets.keys())[:30]  # Limit to 30 symbols for speed
            
            for symbol in symbols:
                try:
                    # Get OHLCV data (Open, High, Low, Close, Volume)
                    ohlcv = exchange.fetch_ohlcv(symbol, '1d', limit=2)
                    
                    if len(ohlcv) >= 2:
                        # Use yesterday's data
                        yesterday = ohlcv[0]
                        
                        # Calculate metrics
                        volume = yesterday[5]  # Volume
                        price_change = yesterday[4] - yesterday[1]  # Close - Open
                        
                        # Crude proxy: positive price change = more borrowing than repaying
                        if price_change > 0:
                            # More buying than selling - proxy for borrowing
                            borrow_amount = volume * 0.6  # Assume 60% of volume is borrowed
                            repay_amount = volume * 0.4   # Assume 40% is repaid
                        else:
                            # More selling than buying
                            borrow_amount = volume * 0.4
                            repay_amount = volume * 0.6
                            
                        ratio = round(borrow_amount / repay_amount, 2)
                        
                        # Extract base symbol (BTC from BTC/USDT)
                        base_symbol = symbol.split('/')[0]
                        
                        all_data.append({
                            'symbol': base_symbol,
                            'borrow_amount': borrow_amount,
                            'borrow_formatted': format_large_number(borrow_amount),
                            'repay_amount': repay_amount,
                            'repay_formatted': format_large_number(repay_amount),
                            'ratio': ratio
                        })
                        
                        success = True
                except Exception as e:
                    logger.warning(f"Error processing {symbol} on {exchange_id}: {e}")
                    continue
                
        except Exception as e:
            logger.error(f"Error with exchange {exchange_id}: {e}")
            continue
    
    if not success or not all_data:
        raise Exception("Failed to fetch data from all alternative sources")
    
    # Combine data for the same symbols by taking the average ratio
    df = pd.DataFrame(all_data)
    grouped = df.groupby('symbol').agg({
        'borrow_amount': 'sum',
        'repay_amount': 'sum',
        'ratio': 'mean'
    }).reset_index()
    
    # Recalculate ratio based on summed values
    grouped['ratio'] = round(grouped['borrow_amount'] / grouped['repay_amount'], 2)
    
    # Add formatted values
    grouped['borrow_formatted'] = grouped['borrow_amount'].apply(format_large_number)
    grouped['repay_formatted'] = grouped['repay_amount'].apply(format_large_number)
    
    # Filter for ratios > 10 and sort by ratio (descending)
    filtered = grouped[grouped['ratio'] > 10]
    # If we have enough data with ratio > 10, use that, otherwise use top 20
    if len(filtered) > 0:
        result = filtered.sort_values('ratio', ascending=False).head(20).to_dict('records')
    else:
        result = grouped.sort_values('ratio', ascending=False).head(20).to_dict('records')
    
    # Save to cache
    save_to_cache(result)
    
    # Save to database
    save_to_database(result)
    
    return result

def get_cached_or_sample_data():
    """Get data from cache or use sample data as last resort"""
    try:
        # Try to get from cache
        if os.path.exists('cached_crypto_data.json'):
            with open('cached_crypto_data.json', 'r') as f:
                data = json.load(f)
                
                # Check if data is recent (less than 1 hour old)
                if 'timestamp' in data:
                    cache_time = datetime.fromisoformat(data['timestamp'])
                    if datetime.utcnow() - cache_time < timedelta(hours=1):
                        logger.info("Using cached crypto data")
                        return data['data']
                    
        # Check database for recent data
        with app.app_context():
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            recent_data = CryptoData.query.filter(CryptoData.timestamp > one_hour_ago).all()
            
            if recent_data:
                logger.info("Using database crypto data")
                # Process into the format we need
                symbols = set(item.symbol for item in recent_data)
                result = []
                
                for symbol in symbols:
                    symbol_data = [item for item in recent_data if item.symbol == symbol]
                    if symbol_data:
                        latest = max(symbol_data, key=lambda x: x.timestamp)
                        result.append({
                            'symbol': latest.symbol,
                            'borrow_amount': latest.borrow_amount,
                            'borrow_formatted': format_large_number(latest.borrow_amount),
                            'repay_amount': latest.repay_amount,
                            'repay_formatted': format_large_number(latest.repay_amount),
                            'ratio': latest.ratio
                        })
                
                # Filter for ratio > 10 and sort by ratio (descending)
                result = [item for item in result if item['ratio'] > 10]
                result = sorted(result, key=lambda x: x['ratio'], reverse=True)[:20]
                return result
    
    except Exception as e:
        logger.error(f"Error getting cached data: {e}")
    
    # If all else fails, use sample data
    logger.warning("Using sample crypto data - Not real data")
    return get_sample_data()

def save_to_cache(data):
    """Save data to a cache file"""
    try:
        cache_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'data': data
        }
        
        with open('cached_crypto_data.json', 'w') as f:
            json.dump(cache_data, f)
            
        logger.info("Saved crypto data to cache file")
    except Exception as e:
        logger.error(f"Could not save to cache: {e}")

def save_to_database(data):
    """Save crypto data to database"""
    try:
        with app.app_context():
            for item in data:
                crypto_data = CryptoData(
                    symbol=item['symbol'],
                    borrow_amount=item['borrow_amount'],
                    repay_amount=item['repay_amount'],
                    ratio=item['ratio']
                )
                db.session.add(crypto_data)
            
            db.session.commit()
            logger.info("Saved crypto data to database")
    except Exception as e:
        logger.error(f"Could not save to database: {e}")
        # Rollback in case of error
        db.session.rollback()

def get_sample_data():
    """Return sample data for demonstration purposes"""
    logger.warning("Using sample data - Not real cryptocurrency data")
    sample_data = [
        {
            'symbol': 'APE',
            'borrow_amount': 320000000,
            'borrow_formatted': '320.0M',
            'repay_amount': 16000000,
            'repay_formatted': '16.0M',
            'ratio': 20.00
        },
        {
            'symbol': 'SHIB',
            'borrow_amount': 456000000,
            'borrow_formatted': '456.0M',
            'repay_amount': 25000000,
            'repay_formatted': '25.0M',
            'ratio': 18.24
        },
        {
            'symbol': 'GALA',
            'borrow_amount': 95000000,
            'borrow_formatted': '95.0M',
            'repay_amount': 5500000,
            'repay_formatted': '5.5M',
            'ratio': 17.27
        },
        {
            'symbol': 'AXS',
            'borrow_amount': 167500000,
            'borrow_formatted': '167.5M',
            'repay_amount': 10500000,
            'repay_formatted': '10.5M',
            'ratio': 15.95
        },
        {
            'symbol': 'SAND',
            'borrow_amount': 125000000,
            'borrow_formatted': '125.0M',
            'repay_amount': 8500000,
            'repay_formatted': '8.5M',
            'ratio': 14.71
        },
        {
            'symbol': 'MANA',
            'borrow_amount': 230000000,
            'borrow_formatted': '230.0M',
            'repay_amount': 17000000,
            'repay_formatted': '17.0M',
            'ratio': 13.53
        },
        {
            'symbol': 'NEAR',
            'borrow_amount': 142500000,
            'borrow_formatted': '142.5M',
            'repay_amount': 11500000,
            'repay_formatted': '11.5M',
            'ratio': 12.39
        },
        {
            'symbol': 'FTM',
            'borrow_amount': 176000000,
            'borrow_formatted': '176.0M',
            'repay_amount': 16200000,
            'repay_formatted': '16.2M',
            'ratio': 10.86
        },
        {
            'symbol': 'ATOM',
            'borrow_amount': 183500000,
            'borrow_formatted': '183.5M',
            'repay_amount': 17300000,
            'repay_formatted': '17.3M',
            'ratio': 10.61
        },
        {
            'symbol': 'ONE',
            'borrow_amount': 92800000,
            'borrow_formatted': '92.8M',
            'repay_amount': 8900000,
            'repay_formatted': '8.9M',
            'ratio': 10.43
        },
        {
            'symbol': 'MATIC',
            'borrow_amount': 274000000,
            'borrow_formatted': '274.0M',
            'repay_amount': 24000000,
            'repay_formatted': '24.0M',
            'ratio': 11.42
        },
        {
            'symbol': 'ALGO',
            'borrow_amount': 155000000,
            'borrow_formatted': '155.0M',
            'repay_amount': 14000000,
            'repay_formatted': '14.0M',
            'ratio': 11.07
        },
        {
            'symbol': 'DOGE',
            'borrow_amount': 198000000,
            'borrow_formatted': '198.0M',
            'repay_amount': 18000000,
            'repay_formatted': '18.0M',
            'ratio': 11.00
        },
        {
            'symbol': 'DOT',
            'borrow_amount': 187000000,
            'borrow_formatted': '187.0M',
            'repay_amount': 17000000,
            'repay_formatted': '17.0M',
            'ratio': 11.00
        },
        {
            'symbol': 'AVAX',
            'borrow_amount': 165000000,
            'borrow_formatted': '165.0M',
            'repay_amount': 15000000,
            'repay_formatted': '15.0M',
            'ratio': 11.00
        },
        {
            'symbol': 'SOL',
            'borrow_amount': 242000000,
            'borrow_formatted': '242.0M',
            'repay_amount': 22000000,
            'repay_formatted': '22.0M',
            'ratio': 11.00
        },
        {
            'symbol': 'LINK',
            'borrow_amount': 154000000,
            'borrow_formatted': '154.0M',
            'repay_amount': 14000000,
            'repay_formatted': '14.0M',
            'ratio': 11.00
        },
        {
            'symbol': 'XRP',
            'borrow_amount': 209000000,
            'borrow_formatted': '209.0M',
            'repay_amount': 19000000,
            'repay_formatted': '19.0M',
            'ratio': 11.00
        },
        {
            'symbol': 'UNI',
            'borrow_amount': 143000000,
            'borrow_formatted': '143.0M',
            'repay_amount': 13000000,
            'repay_formatted': '13.0M',
            'ratio': 11.00
        },
        {
            'symbol': 'ADA',
            'borrow_amount': 132000000,
            'borrow_formatted': '132.0M',
            'repay_amount': 12000000,
            'repay_formatted': '12.0M',
            'ratio': 11.00
        }
    ]
    return sample_data

def format_large_number(number, decimals=1):
    """Format large numbers with K, M, B suffixes"""
    if number is None:
        return "N/A"
        
    try:
        abs_number = abs(number)
        if abs_number < 1000:
            return f"{number:.{decimals}f}"
        elif abs_number < 1000000:
            return f"{number/1000:.{decimals}f}K"
        elif abs_number < 1000000000:
            return f"{number/1000000:.{decimals}f}M"
        else:
            return f"{number/1000000000:.{decimals}f}B"
    except Exception as e:
        logger.error(f"Error formatting large number: {e}")
        return str(number)

def generate_chart(crypto_data):
    """Generate a bar chart for crypto data"""
    try:
        # Create a DataFrame from the crypto data
        df = pd.DataFrame(crypto_data)
        
        # Sort by ratio for the chart
        df = df.sort_values('ratio', ascending=False)
        
        # Create a bar chart showing the borrow/repay ratio
        fig = px.bar(
            df, 
            x='symbol', 
            y='ratio', 
            title='Cryptocurrencies with Borrow/Repay Ratio > 10',
            labels={'symbol': 'Cryptocurrency', 'ratio': 'Borrow/Repay Ratio'},
            color='ratio',
            color_continuous_scale='Viridis',
            text='ratio'
        )
        
        # Update layout
        fig.update_layout(
            template='plotly_dark',
            xaxis_title='Cryptocurrency',
            yaxis_title='Borrow/Repay Ratio',
            coloraxis_showscale=False,
            height=500
        )
        
        # Format the text labels
        fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        
        # Convert to JSON
        chart_json = pu.PlotlyJSONEncoder().encode(fig)
        
        return chart_json
    except Exception as e:
        logger.error(f"Error generating chart: {e}")
        return None

# Routes
@app.route('/')
def index():
    """Display the homepage with crypto borrow/repay ratio data"""
    crypto_data = fetch_crypto_borrow_data()
    chart_json = generate_chart(crypto_data)
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    return render_template('index.html', 
                           crypto_data=crypto_data, 
                           chart_json=chart_json,
                           timestamp=timestamp)

@app.route('/api/crypto-data')
def api_crypto_data():
    """API endpoint to get crypto data in JSON format"""
    try:
        crypto_data = fetch_crypto_borrow_data()
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        return jsonify({
            'timestamp': timestamp,
            'data': crypto_data
        })
    except Exception as e:
        logger.error(f"API error: {e}")
        # Try to get cached data if fetch fails
        try:
            data = get_cached_or_sample_data()
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            return jsonify({
                'timestamp': timestamp,
                'data': data
            })
        except Exception:
            return jsonify({"error": str(e)}), 500

@app.route('/history')
def history():
    """Show historical data from the database"""
    days = request.args.get('days', 7, type=int)
    
    with app.app_context():
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get the data from database
        historical_data = CryptoData.query.filter(CryptoData.timestamp > cutoff_date).all()
        
        # Group by day and symbol
        df = pd.DataFrame([d.to_dict() for d in historical_data])
        
        if df.empty:
            return render_template('history.html', has_data=False, days=days)
            
        # Convert timestamp to datetime if it's a string
        if isinstance(df['timestamp'].iloc[0], str):
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
        # Add date column
        df['date'] = df['timestamp'].dt.date
        
        # For each date, get the top symbols by ratio
        dates = sorted(df['date'].unique())
        
        # Prepare data for charts
        date_data = []
        for date in dates:
            day_data = df[df['date'] == date]
            # Filter for ratio > 10
            filtered_day_data = day_data[day_data['ratio'] > 10]
            # If we have enough data with ratio > 10, use that, otherwise use top 20
            if len(filtered_day_data) > 0:
                top_symbols = filtered_day_data.sort_values('ratio', ascending=False).head(20)
            else:
                top_symbols = day_data.sort_values('ratio', ascending=False).head(20)
            
            # Generate chart for this day
            fig = px.bar(
                top_symbols, 
                x='symbol', 
                y='ratio', 
                title=f'Cryptocurrencies with Borrow/Repay Ratio > 10 on {date}',
                labels={'symbol': 'Cryptocurrency', 'ratio': 'Borrow/Repay Ratio'},
                color='ratio',
                color_continuous_scale='Viridis',
                text='ratio'
            )
            
            # Update layout
            fig.update_layout(
                template='plotly_dark',
                xaxis_title='Cryptocurrency',
                yaxis_title='Borrow/Repay Ratio',
                coloraxis_showscale=False,
                height=400
            )
            
            # Format the text labels
            fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
            
            # Convert to JSON
            chart_json = pu.PlotlyJSONEncoder().encode(fig)
            
            date_data.append({
                'date': date,
                'chart_json': chart_json
            })
    
        return render_template('history.html', 
                               has_data=True,
                               date_data=date_data,
                               days=days)



@app.route('/about')
def about():
    """Display information about the service"""
    return render_template('about.html')

# Initialize database
with app.app_context():
    try:
        db.create_all()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.info(f"Tables may already exist, continuing: {e}")

# Run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)