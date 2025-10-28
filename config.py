import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    DATABASE_NAME = 'bot_database.db'
    FREE_REQUESTS_LIMIT = 20
    SUBSCRIPTION_PRICES = {
        'week': {'price': 89, 'days': 7},
        'month': {'price': 299, 'days': 30},
        '3month': {'price': 549, 'days': 90}
    }
