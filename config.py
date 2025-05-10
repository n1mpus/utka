import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv ("BOT_TOKEN") 
CRYPTO_PAY_TOKEN = os.getenv ("CRYPTO_PAY_TOKEN") 
ADMIN_ID = int (os.getenv ("ADMIN_ID")) 
PAY_AMOUNT_USD = 20
DB_PATH = "data.db"
SUPPORT_USERNAME = os.getenv ("SUPPORT_USERNAME") 