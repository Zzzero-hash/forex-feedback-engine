from datetime import datetime
import time
import logging  # Added import
import importlib

# Get a logger for this module
logger = logging.getLogger(__name__)  # Added logger

# Dynamically attempt to import RESTClient from known Polygon packages
RESTClient = None
for pkg in ('polygon', 'polygon_api_client'):
    try:
        mod = importlib.import_module(pkg)
        if hasattr(mod, 'RESTClient'):
            RESTClient = getattr(mod, 'RESTClient')
            logger.info(f"Imported Polygon RESTClient from '{pkg}' package.")
            break
    except ImportError as e:
        logger.debug(f"Failed to import RESTClient from '{pkg}': {e}")
if RESTClient is None:
    logger.warning("Polygon RESTClient could not be imported from available packages. Polygon data feed will be unavailable.")

class DataFeed:
    def __init__(self, api_key=None):
        logger.debug(f"DataFeed __init__ called with api_key: {api_key}, RESTClient available: {bool(RESTClient)}")
        # Manage data sources
        self.data_sources = {}
        # Initialize Polygon.io RESTClient if available and API key provided
        if api_key and RESTClient:
            self.client = RESTClient(api_key)
            logger.info("Polygon RESTClient initialized.")  # Added log
        else:
            self.client = None
            if not RESTClient:
                logger.warning("Polygon RESTClient not available (import failed).")  # Added log
            if not api_key:
                logger.warning(
                    "Polygon API key not provided. Polygon client not initialized."
                )  # Added log
                
        # Define symbol types mapping
        self.symbol_prefixes = {
            'forex': 'C',     # Currency/Forex uses 'C:' prefix
            'crypto': 'X',    # Crypto uses 'X:' prefix
        }

    def add_data_source(self, name, key):
        self.data_sources[name] = key

    def remove_data_source(self, name):
        if name in self.data_sources:
            del self.data_sources[name]
            
    def detect_symbol_type(self, symbol):
        """
        Detect if a symbol is forex or crypto based on convention.
        
        Args:
            symbol: Symbol string (e.g., 'EURUSD' for forex or 'BTCUSD' for crypto)
            
        Returns:
            Symbol type ('forex' or 'crypto')
        """
        # Common crypto symbols that we want to treat as crypto regardless of format
        crypto_symbols = ['BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOT']
        
        # Check if the first three characters match any known crypto symbol
        if any(symbol.startswith(crypto) for crypto in crypto_symbols):
            return 'crypto'
            
        # Default to forex for 6-character symbols that don't match crypto patterns
        return 'forex'
        
    def get_polygon_ticker(self, symbol):
        """
        Convert a symbol to the proper Polygon API ticker format.
        
        Args:
            symbol: Symbol string (e.g., 'EURUSD', 'BTCUSD')
            
        Returns:
            Properly formatted ticker for Polygon API (e.g., 'C:EURUSD', 'X:BTCUSD')
        """
        symbol_type = self.detect_symbol_type(symbol)
        prefix = self.symbol_prefixes.get(symbol_type, 'C')  # Default to forex (C) if type unknown
        return f"{prefix}:{symbol}"

    def fetch_data(self, symbol):
        logger.debug(f"fetch_data called with symbol: {symbol}")  # Added log
        # Validate symbol format: must be 6-letter alphabetic (e.g., 'EURUSD', 'BTCUSD')
        if not isinstance(symbol, str) or len(symbol) != 6 or not symbol.isalpha():
            logger.error(f"Invalid symbol format: {symbol}")  # Added log
            raise ValueError(f"Invalid symbol: {symbol}")
        # Use Polygon.io RESTClient when available
        if self.client:
            # Detect symbol type and format for Polygon
            pair = self.get_polygon_ticker(symbol)
            logger.debug(f"Attempting to fetch data for Polygon pair: {pair}")  # Added log
            
            try:
                # Use yesterday and 5 minutes back to avoid weekend/future data issues
                # The API expects timestamps in milliseconds
                now = datetime.now()
                
                # For crypto, we can use more recent data since it trades 24/7
                if pair.startswith('X:'):  # Crypto
                    to_ts = int(time.time() * 1000)
                    from_ts = int((time.time() - (5 * 60)) * 1000)  # 5 minutes ago
                else:  # Forex - might need to go further back on weekends
                    if now.weekday() >= 5:  # Weekend (5=Saturday, 6=Sunday)
                        # Go back to Friday's data
                        days_to_friday = (now.weekday() - 4) % 7  # 5->1, 6->2
                        to_ts = int((time.time() - (days_to_friday * 24 * 60 * 60)) * 1000)
                        from_ts = int(to_ts - (5 * 60 * 1000))  # 5 minutes before 
                    else:
                        # Normal weekday
                        to_ts = int(time.time() * 1000)
                        from_ts = int((time.time() - (5 * 60)) * 1000)  # 5 minutes ago

                logger.debug(
                    f"Polygon API call: get_aggs(ticker={pair}, multiplier=1, timespan='minute', from_={from_ts}, to={to_ts}, limit=1)"
                )
                bars = self.client.get_aggs(
                    ticker=pair, multiplier=1, timespan="minute", from_=from_ts, to=to_ts, limit=1
                )
                logger.debug(f"Polygon API response (bars): {bars}")  # Added log
                if bars and len(bars) > 0:
                    bar = bars[0]
                    price = bar.close  # close price # Changed from bar.c
                    ts = bar.timestamp / 1000  # Polygon returns ms # Changed from bar.t
                    logger.info(
                        f"Successfully fetched data from Polygon: Price={price}, Timestamp={ts}"
                    )  # Added log
                    return {
                        "price": price,
                        "timestamp": datetime.fromtimestamp(ts).isoformat() if ts else None,
                    }
                else:
                    logger.warning(f"No bars returned from Polygon for {pair}.")  # Added log
            except Exception as e:
                logger.error(
                    f"Error calling Polygon API for {pair}: {e}", exc_info=True
                )  # Modified to log exception
        else:
            logger.warning("Polygon client not available. Falling back to dummy data.")  # Added log
        # Dummy fallback data only
        logger.warning(f"Returning dummy data for symbol {symbol}")  # Added log
        return {"price": 0.0, "timestamp": datetime.utcnow().isoformat()}

    # Alias for get_quote to be consistent with main
    get_quote = fetch_data