from datetime import datetime
from alpha_vantage.foreignexchange import ForeignExchange

class DataFeed:
    def __init__(self, api_key=None):
        # Manage data sources
        self.data_sources = {}
        # Initialize Alpha Vantage ForeignExchange client if API key provided
        self.fx = ForeignExchange(key=api_key) if api_key else None

    def add_data_source(self, name, key):
        self.data_sources[name] = key

    def remove_data_source(self, name):
        if name in self.data_sources:
            del self.data_sources[name]

    def fetch_data(self, symbol):
        # Symbol must be 6-character currency pair
        if not isinstance(symbol, str) or len(symbol) != 6:
            raise ValueError(f"Invalid symbol: {symbol}")
        # Use live data if client is available
        if self.fx:
            base = symbol[:3]
            quote = symbol[3:]
            data, _ = self.fx.get_currency_exchange_rate(from_currency=base, to_currency=quote)
            price = float(data.get('5. Exchange Rate', 0.0))
            timestamp = data.get('6. Last Refreshed', datetime.utcnow().isoformat())
            return {"price": price, "timestamp": timestamp}
        # Return dummy data for testing
        return {"price": 0.0, "timestamp": datetime.utcnow().isoformat()}

    # Alias for get_quote to be consistent with main
    get_quote = fetch_data