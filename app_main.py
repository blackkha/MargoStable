import logging
from app import app

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# This file is used by Replit to run the Flask application
# The app is configured in app.py
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)