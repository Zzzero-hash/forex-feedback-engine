import os
from typing import Dict, Any
try:
    from pocketoptionapi.stable_api import PocketOption
except ImportError:
    # Dummy PocketOption for testing/demo
    class PocketOption:
        def __init__(self, ssid=None):
            pass
        def connect(self):
            return True
        def get_otc_feed(self):
            return {}
        def get_otc_candles(self, symbol, interval):
            return {}
        def get_otc_symbols(self):
            return {}
        def get_otc_symbol_info(self, symbol):
            return {}

class OTCFeed:
    def __init__(self): 
        ssid = os.getenv("PO_SSID")
        if not ssid:
            raise ValueError("Environment variable PO_SSID is required")
        self.api = PocketOption(ssid)
        connected = self.api.connect()
        if not connected:
            raise ConnectionError("Failed to connect to PocketOption API")
    
    def get_otc_feed(self) -> Dict[str, Any]:
        """
        Fetches the OTC feed from the PocketOption API.
        
        Returns:
            dict: The OTC feed data.
        """
        try:
            otc_feed = self.api.get_otc_feed()
            return otc_feed
        except Exception as e:
            raise RuntimeError(f"Failed to fetch OTC feed: {e}")

    def get_otc_candles(self, symbol: str, interval: int) -> Dict[str, Any]:
        """
        Fetches the OTC candles for a given symbol and interval from the PocketOption API.
        
        Args:
            symbol (str): The symbol to fetch candles for.
            interval (int): The interval in seconds for the candles.
        
        Returns:
            dict: The OTC candles data.
        """
        try:
            return self.api.get_otc_candles(symbol, interval)
        except Exception as e:
            raise RuntimeError(f"Failed to fetch OTC candles: {e}")

    def get_otc_symbols(self) -> Dict[str, Any]:
        """
        Fetches the OTC symbols from the PocketOption API.
        
        Returns:
            dict: The OTC symbols data.
        """
        try:
            return self.api.get_otc_symbols()
        except Exception as e:
            raise RuntimeError(f"Failed to fetch OTC symbols: {e}")

    def get_otc_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """
        Fetches the OTC symbol information for a given symbol from the PocketOption API.
        
        Args:
            symbol (str): The symbol to fetch information for.
        
        Returns:
            dict: The OTC symbol information data.
        """
        try:
            return self.api.get_otc_symbol_info(symbol)
        except Exception as e:
            raise RuntimeError(f"Failed to fetch OTC symbol info: {e}")