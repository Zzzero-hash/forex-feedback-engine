try:
    from dotenv import load_dotenv, dotenv_values
    PYTHON_DOTENV_FOUND = True
except ImportError:
    PYTHON_DOTENV_FOUND = False
    # Fallback if python-dotenv is not installed
    def load_dotenv(dotenv_path=None, verbose=False, override=False): # Added override to match potential calls
        print("DEBUG: WARNING: python-dotenv library not found (load_dotenv fallback).")
        return False
    def dotenv_values(dotenv_path=None, stream=None, verbose=False, interpolate=True, encoding="utf-8"):
        print("DEBUG: WARNING: python-dotenv library not found (dotenv_values fallback).")
        return {}


import os
import logging
from pathlib import Path

print("DEBUG: --- Starting config.py execution ---")
# ... existing debug prints for paths ...
try:
    project_root = Path(__file__).resolve().parent.parent
    env_path = project_root / '.env'
    print(f"DEBUG: Calculated project_root: {project_root}")
    print(f"DEBUG: Calculated .env path: {env_path}")
    print(f"DEBUG: Does .env file exist at calculated path? {env_path.exists()}")
except Exception as e:
    print(f"DEBUG: Error calculating env_path: {e}")
    env_path = None

print(f"DEBUG: python-dotenv library found: {PYTHON_DOTENV_FOUND}")

if env_path and env_path.exists():
    if PYTHON_DOTENV_FOUND:
        print(f"DEBUG: Using dotenv_values to load variables from '{env_path}'...")
        env_vars_from_file = dotenv_values(dotenv_path=env_path)

        if env_vars_from_file:
            print(f"DEBUG: dotenv_values returned: {env_vars_from_file}")
            print("DEBUG: Manually updating os.environ with variables from dotenv_values...")
            for key, value in env_vars_from_file.items():
                if value is not None:
                    os.environ[key] = value
                    # print(f"DEBUG: Set os.environ['{key}'] = '{value}'") # Too verbose for every var
                else:
                    # This case might happen if a var is in .env but has no value (e.g., MY_VAR=)
                    # os.environ can't store None, so we might skip or set to empty string
                    # For now, skipping if value is None from dotenv_values
                    print(f"DEBUG: Value for key '{key}' from dotenv_values is None, not setting in os.environ.")
        else:
            print("DEBUG: dotenv_values did not return any variables.")
    else:
        print("DEBUG: python-dotenv library not found, cannot load .env file.")
else:
    print(f"DEBUG: .env file not found at {env_path} or env_path is None. Skipping .env loading.")

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
    otc_interval = int(os.getenv("OTC_INTERVAL", 300)) # Changed default from 60 to 300
    screen_interval = float(os.getenv("SCREEN_INTERVAL", 1.0))
    trade_amount = float(os.getenv("TRADE_AMOUNT", 1.0))
    max_daily_loss = float(os.getenv("MAX_DAILY_LOSS", 100.0))
    profit_target_pct = float(os.getenv("PROFIT_TARGET_PCT", 5.0))
    loss_limit_pct = float(os.getenv("LOSS_LIMIT_PCT", 2.0))
    initial_balance = float(os.getenv("INITIAL_BALANCE", 1000.0))
    polygon_api_key = os.getenv("POLYGON_API_KEY")

    def __init__(self):
        print("DEBUG: Config class __init__ called.")
        instance_polygon_check = os.getenv("POLYGON_API_KEY")
        print(f"DEBUG: Inside Config __init__, os.getenv('POLYGON_API_KEY') directly: '{instance_polygon_check}'")

print("DEBUG: --- Finished config.py execution ---")