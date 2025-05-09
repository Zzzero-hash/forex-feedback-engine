# Tests for signal-only mode of the BrokerAPI

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

def test_place_demo_signal():
    """Test that signals can be generated (but not real trades) in demo/signal-only mode"""
    logging.info("Starting signal generation test in signal-only mode...")
    
    try:
        # Create config with demo mode enabled
        cfg = Config()
        cfg.enable_demo_mode = True
        
        # Using a dummy SSID is fine since we're in signal-only mode
        broker = BrokerAPI(ssid="dummy_ssid")
        
        if not broker.connected:
            logging.error("Failed to initialize BrokerAPI in signal-only mode.")
            return

        asset = 'EURUSD'
        amount = 1.0
        direction = 'CALL'
        duration = 60

        logging.info(f"Generating a {direction} signal for {asset} with amount {amount} for {duration} seconds...")

        # In signal-only mode, this just returns a dummy ID
        signal_id = broker.place_trade(asset, amount, direction, duration)
        
        assert signal_id == 'signal_only_dummy_trade_id', "Expected dummy signal ID wasn't returned"
        logging.info(f"Signal generated with ID: {signal_id}")
        
        # Check result (should always be True in signal mode)
        result = broker.check_trade_result(signal_id)
        assert result is True, "Signal result should be True in signal-only mode"
        logging.info("Signal logged successfully")

    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)
        raise
    
    logging.info("Signal generation test completed successfully.")

if __name__ == "__main__":
    test_place_demo_trade()