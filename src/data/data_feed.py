from datetime import datetime

class DataFeed:
    def __init__(self):
        self.data_sources = {}

    def add_data_source(self, name, key):
        self.data_sources[name] = key

    def remove_data_source(self, name):
        if name in self.data_sources:
            del self.data_sources[name]

    def fetch_data(self, symbol):
        # Symbol must be 6-character currency pair
        if not isinstance(symbol, str) or len(symbol) != 6:
            raise ValueError(f"Invalid symbol: {symbol}")
        # Return dummy data for testing
        return {
            "price": 0.0,
            "timestamp": datetime.utcnow().isoformat()
        }