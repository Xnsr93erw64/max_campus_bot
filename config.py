import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    
    if not BOT_TOKEN:
        raise ValueError(
            "BOT_TOKEN not found in environment variables. "
            "Please create .env file with BOT_TOKEN=your_bot_token"
        )