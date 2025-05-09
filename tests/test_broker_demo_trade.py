# filepath: c:\\Users\\chris\\forex-feedback-engine\\tests\\test_broker_demo_trade.py
# TODO (Next Steps for tomorrow - May 9, 2025):
# 1. Verify 'pocketoptionapi' is installed in the Python environment (e.g., `pip install pocketoptionapi`).
#    If not, the script will use a dummy API and trades won't reflect on Pocket Option.
# 2. Ensure PO_SSID in .env is current and for your DEMO account on Pocket Option.
# 3. Run this test script to confirm real trades can be placed and results checked.

import time
import logging
import sys
import os

# Add the src directory to the Python path
# This is necessary so we can import modules from src when running this script directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from execution.broker_api import BrokerAPI
from config import Config

# Configure basic logging for the test
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_place_demo_trade():
    logging.info("Starting demo trade placement test...")
    broker = None  # Initialize broker to None for finally block
    try:
        cfg = Config()
        if not cfg.po_ssid:
            logging.error("PO_SSID not found in .env file or environment variables. Cannot proceed.")
            return

        logging.info(f"PO_SSID found: {cfg.po_ssid[:10]}... (truncated for display)")

        broker = BrokerAPI(ssid=cfg.po_ssid)

        if not broker.connected:
            logging.error("Failed to connect to BrokerAPI. Please check your PO_SSID and network connection.")
            return

        asset = 'EURUSD'
        amount = 1.0  # Trade amount for the test
        direction = 'CALL'
        duration = 60 # Trade duration in seconds for this test (1 minute)

        logging.info(f"Attempting to place a {direction} trade for {asset} with amount {amount} for {duration} seconds...")

        trade_id = broker.place_trade(asset, amount, direction, duration)

        if trade_id:
            logging.info(f"Trade placed successfully! Trade ID: {trade_id}")
            logging.info(f"Waiting for {duration + 10} seconds before checking trade result (to allow for expiration)...")
            time.sleep(duration + 10) # Wait for trade to expire plus a small buffer

            logging.info(f"Checking result for Trade ID: {trade_id}...")
            outcome = broker.check_trade_result(trade_id)

            if outcome is not None:
                # Assuming outcome is True for WIN, False for LOSS as per dummy API and common boolean interpretations
                logging.info(f"Trade result for {trade_id}: {'WIN' if outcome else 'LOSS'}")
            else:
                logging.warning(f"Could not retrieve outcome for trade {trade_id}. It might still be pending or an error occurred.")
        else:
            logging.error("Failed to place trade. No trade_id received.")

    except ImportError as e:
        logging.error(f"ImportError: {e}. Make sure you are in the correct environment and path.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)
    finally:
        if broker and broker.connected: # Check if broker was initialized and connected
            logging.info("Disconnecting from BrokerAPI...")
            broker.disconnect()
        logging.info("Demo trade placement test finished.")

if __name__ == "__main__":
    test_place_demo_trade()