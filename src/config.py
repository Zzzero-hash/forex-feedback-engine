import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from dotenv import find_dotenv

# Load .env file at project root (if present)
dotenv_path = find_dotenv(usecwd=True)
if dotenv_path:
    load_dotenv(dotenv_path, override=True)
    logging.getLogger(__name__).info(f"Loaded environment variables from {dotenv_path}")
    # Manual parse .env to capture variables on lines not recognized by python-dotenv (e.g., lines starting with //)
    try:
        with open(dotenv_path, 'r', encoding='utf-8') as f:
            for line in f:
                raw = line.strip()
                # Skip empty or commented lines (# or //)
                if not raw or raw.startswith('#') or raw.startswith('//'):
                    continue
                if '=' in raw:
                    key, val = raw.split('=', 1)
                    key = key.strip()
                    val = val.strip()
                    os.environ[key] = val
        logging.getLogger(__name__).debug(f"Environment variables after manual merge: { {k: os.environ[k] for k in ('POLYGON_API_KEY','PO_SSID')} }")
    except Exception as e:
        logging.getLogger(__name__).error(f"Manual .env parsing failed: {e}")
else:
    logging.getLogger(__name__).warning(".env file not found, proceeding with existing environment variables.")

class Config:
    # These are evaluated when the class is defined (i.e., when config.py is imported)
    api_key = os.getenv("API_KEY")
    po_ssid = os.getenv("PO_SSID")
    openai_api_key = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
    _raw_log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, _raw_log_level, logging.INFO)
    database_url = os.getenv("DATABASE_URL", "sqlite:///trading_logs.db")
    screenshot_dir = os.getenv("SCREENSHOT_DIR", "./screenshots")
    enable_demo_mode = os.getenv("DEMO_MODE", "False").lower() == "true"
    otc_interval = int(os.getenv("OTC_INTERVAL", 300)) # Default 300s
    screen_interval = float(os.getenv("SCREEN_INTERVAL", 1.0))
    trade_amount = float(os.getenv("TRADE_AMOUNT", 1.0))
    max_daily_loss = float(os.getenv("MAX_DAILY_LOSS", 100.0))
    profit_target_pct = float(os.getenv("PROFIT_TARGET_PCT", 5.0))
    loss_limit_pct = float(os.getenv("LOSS_LIMIT_PCT", 2.0))
    initial_balance = float(os.getenv("INITIAL_BALANCE", 1000.0))
    polygon_api_key = os.getenv("POLYGON_API_KEY")
    llm_model = os.getenv("LLM_MODEL", "gpt-4")  # Default LLM model
    max_consecutive_no_trade = int(os.getenv("MAX_CONSECUTIVE_NO_TRADE", 5)) # Max consecutive "NO TRADE" signals before switching pairs
    pair_blacklist_duration_seconds = int(os.getenv("PAIR_BLACKLIST_DURATION_SECONDS", 3600)) # Duration to blacklist a pair after inactivity
    max_consecutive_system_switches = int(os.getenv("MAX_CONSECUTIVE_SYSTEM_SWITCHES", 3)) # Max consecutive pair switches before system cooldown
    system_cool_down_duration_seconds = int(os.getenv("SYSTEM_COOL_DOWN_DURATION_SECONDS", 1800)) # System cooldown duration

    def __init__(self):
        logging.getLogger(__name__).debug(f"Config initialized with POLYGON_API_KEY={self.polygon_api_key}")