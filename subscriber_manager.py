"""
Module for managing subscriber data
"""

import json
import os
import logging
from typing import List

# Set up logging
logger = logging.getLogger(__name__)

# Constants
SUBSCRIBERS_FILE = 'subscribers.json'

def load_subscribers() -> List[int]:
    """
    Load subscribers from file.
    Returns a list of chat IDs.
    """
    try:
        if os.path.exists(SUBSCRIBERS_FILE):
            with open(SUBSCRIBERS_FILE, 'r') as f:
                subscribers = json.load(f)
                logger.info(f"Loaded {len(subscribers)} subscribers from file")
                return subscribers
        else:
            logger.info("Subscribers file doesn't exist, returning empty list")
            return []
    except Exception as e:
        logger.error(f"Error loading subscribers: {e}")
        # Return empty list in case of error to avoid breaking the app
        return []

def save_subscribers(subscribers: List[int]) -> bool:
    """
    Save subscribers to file.
    Returns True if successful, False otherwise.
    """
    try:
        with open(SUBSCRIBERS_FILE, 'w') as f:
            json.dump(subscribers, f)
        logger.info(f"Saved {len(subscribers)} subscribers to file")
        return True
    except Exception as e:
        logger.error(f"Error saving subscribers: {e}")
        return False

def add_subscriber(chat_id: int) -> bool:
    """
    Add a subscriber to the list.
    Returns True if successful, False otherwise.
    """
    try:
        subscribers = load_subscribers()
        if chat_id not in subscribers:
            subscribers.append(chat_id)
            save_subscribers(subscribers)
            logger.info(f"Added subscriber with chat ID: {chat_id}")
            return True
        else:
            logger.info(f"Chat ID {chat_id} is already subscribed")
            return True  # Already subscribed is still a success
    except Exception as e:
        logger.error(f"Error adding subscriber {chat_id}: {e}")
        return False

def remove_subscriber(chat_id: int) -> bool:
    """
    Remove a subscriber from the list.
    Returns True if successful, False otherwise.
    """
    try:
        subscribers = load_subscribers()
        if chat_id in subscribers:
            subscribers.remove(chat_id)
            save_subscribers(subscribers)
            logger.info(f"Removed subscriber with chat ID: {chat_id}")
            return True
        else:
            logger.info(f"Chat ID {chat_id} was not in the subscribers list")
            return True  # Not being subscribed is still a success for unsubscribe
    except Exception as e:
        logger.error(f"Error removing subscriber {chat_id}: {e}")
        return False

def get_subscriber_count() -> int:
    """
    Get the number of subscribers.
    """
    try:
        subscribers = load_subscribers()
        return len(subscribers)
    except Exception as e:
        logger.error(f"Error getting subscriber count: {e}")
        return 0
