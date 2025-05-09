from datetime import datetime
import time
import logging  # Added import

# Get a logger for this module
logger = logging.getLogger(__name__)  # Added logger

try:
    from polygon import RESTClient
    logger.info("Successfully imported Polygon RESTClient.")  # Added log
except ImportError:
    RESTClient = None
    logger.warning(
        "Polygon RESTClient could not be imported. Polygon data feed will be unavailable."
    )  # Added log


class DataFeed:
    def __init__(self, api_key=None):
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

    def add_data_source(self, name, key):
        self.data_sources[name] = key

    def remove_data_source(self, name):
        if name in self.data_sources:
            del self.data_sources[name]

    def fetch_data(self, symbol):
        logger.debug(f"fetch_data called with symbol: {symbol}")  # Added log
        # Symbol must be 6-character currency pair, e.g. \'EURUSD\'
        if not isinstance(symbol, str) or len(symbol) != 6:
            logger.error(f"Invalid symbol format: {symbol}")  # Added log
            raise ValueError(f"Invalid symbol: {symbol}")
        # Use Polygon.io RESTClient when available
        if self.client:
            # Polygon expects e.g. \'C:EURUSD\'
            pair = f"C:{symbol}"
            logger.debug(f"Attempting to fetch data for Polygon pair: {pair}")  # Added log
            # Get last minute bar (1-min granularity)
            try:
                # Polygon.io API requires a 'from' and 'to' timestamp for aggregates.
                # Let's fetch for the last few minutes to ensure we get data.
                # The API expects timestamps in milliseconds.
                to_ts = int(time.time() * 1000)
                from_ts = int((time.time() - (5 * 60)) * 1000)  # 5 minutes ago

                logger.debug(
                    f"Polygon API call: get_aggs(ticker={pair}, multiplier=1, timespan=\'minute\', from_={from_ts}, to={to_ts}, limit=1)"
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