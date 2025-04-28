# Crypto Leverage Indicator Tracker

A specialized web application and Telegram bot for analyzing and monitoring cryptocurrency leverage indicators, with a focus on high-leverage cryptocurrencies.

## Features

- **Web Application**: View real-time data on the top 20 cryptocurrencies with the highest leverage indicators
- **Data Visualization**: Interactive charts for better data analysis
- **Telegram Bot**: Get updates via Telegram with commands like `/margin`, `/subscribe`, and `/unsubscribe`
- **Daily Reports**: Subscribers receive daily reports of the top cryptocurrencies by leverage indicator
- **API Integration**: Uses CoinGecko API to derive leverage indicators from volume/market cap ratios

## Technology Stack

- **Backend**: Python with Flask framework
- **API**: CoinGecko for cryptocurrency market data
- **Bot**: Python Telegram Bot library
- **Visualization**: Plotly for interactive charts
- **Scheduling**: APScheduler for periodic updates
- **Database**: SQLAlchemy with PostgreSQL

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL database
- Telegram Bot Token

### Environment Variables

Set the following environment variables:

- `TELEGRAM_TOKEN`: Your Telegram bot token
- `CG_API_KEY`: Your CoinGecko API key (optional)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/crypto-leverage-indicator.git
   cd crypto-leverage-indicator
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the web application:
   ```
   python main.py
   ```

4. Run the Telegram bot in a separate process:
   ```
   python telegram_workflow.py
   ```

## Usage

### Web Application

Visit `http://localhost:5000` to view the web interface showing cryptocurrency leverage indicator data.

### Telegram Bot

Use the following commands with your Telegram bot:

- `/start` - Introduction to the bot
- `/margin` - Get current top cryptocurrency leverage indicators
- `/subscribe` - Subscribe to daily reports
- `/unsubscribe` - Unsubscribe from daily reports

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Data provided by [CoinGecko](https://www.coingecko.com/)
- Built with [Python Telegram Bot](https://python-telegram-bot.org/)