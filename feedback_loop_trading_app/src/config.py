from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    API_KEY = os.getenv("API_KEY")
    PO_SSID = os.getenv("PO_SSID")
    ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY")
    LLM_API_KEY = os.getenv("LLM_API_KEY")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///trading_logs.db")
    SCREENSHOT_DIR = os.getenv("SCREENSHOT_DIR", "./screenshots")
    TRADE_AMOUNT = float(os.getenv("TRADE_AMOUNT", 1.0))
    MAX_DAILY_LOSS = float(os.getenv("MAX_DAILY_LOSS", 100.0))