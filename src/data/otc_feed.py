import os
from typing import Dict, Any
from pocketoptionapi.stable_api import PocketOption

class OTCFeed:
    def __init__(self): 
        ssid = os.getenv("PO_SSID")
        if not ssid:
            raise ValueError("Environtment viariable PO_SSID is required")
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
            otc_candles = self.api.get_otc_candles(symbol, interval)
            return otc_candles
        except Exception as e:
            raise RuntimeError(f"Failed to fetch OTC candles: {e}")


    def get_otc_symbols(self) -> Dict[str, Any]:
        """
        Fetches the OTC symbols from the PocketOption API.
        
        Returns:
            dict: The OTC symbols data.
        """
        try:
            otc_symbols = self.api.get_otc_symbols()
            return otc_symbols
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
            otc_symbol_info = self.api.get_otc_symbol_info(symbol)
            return otc_symbol_info
        except Exception as e:
            raise RuntimeError(f"Failed to fetch OTC symbol info: {e}")