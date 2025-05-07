from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    api_key = os.getenv("API_KEY")
    po_ssid = os.getenv("PO_SSID")
    alpha_vantage_api_key = os.getenv("ALPHA_VANTAGE_KEY")
    openai_api_key = os.getenv("LLM_API_KEY")
    log_level = os.getenv("LOG_LEVEL", "INFO")
    database_url = os.getenv("DATABASE_URL", "sqlite:///trading_logs.db")
    screenshot_dir = os.getenv("SCREENSHOT_DIR", "./screenshots")
    enable_demo_mode = os.getenv("DEMO_MODE", "False").lower() == "true"
    otc_interval = int(os.getenv("OTC_INTERVAL", 60))
    screen_interval = float(os.getenv("SCREEN_INTERVAL", 1.0))
    trade_amount = float(os.getenv("TRADE_AMOUNT", 1.0))
    max_daily_loss = float(os.getenv("MAX_DAILY_LOSS", 100.0))
    # Risk management thresholds (percent)
    profit_target_pct = float(os.getenv("PROFIT_TARGET_PCT", 5.0))
    loss_limit_pct = float(os.getenv("LOSS_LIMIT_PCT", 2.0))
    # Initial account balance for PnL calculations
    initial_balance = float(os.getenv("INITIAL_BALANCE", 1000.0))