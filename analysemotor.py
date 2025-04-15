import asyncio
import aiohttp
import logging
import time
import re
from textblob import TextBlob
import pandas as pd
import os
import feedparser
from telegram_handler import send_telegram_message

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory cache for mentions (24-hour window)
mentions_cache = {}

# List of 5 coins for testing
COINS = ["BTC", "ETH", "BNB", "SOL", "ADA"]

# GitHub repo mapping for the 5 coins
REPO_MAPPING = {
    "BTC": "bitcoin/bitcoin",
    "ETH": "ethereum/go-ethereum",
    "BNB": "binance-chain/bsc",
    "SOL": "solana-labs/solana",
    "ADA": "input-output-hk/cardano-sl",
}

async def fetch_google_trends(coin, session):
    try:
        api_key = os.getenv("S
