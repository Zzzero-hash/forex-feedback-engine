class BrokerAPI:
    """
    Dummy BrokerAPI for signal-only mode. No live trading, no exchange connection.
    """
    def __init__(self, ssid):
        self.connected = True

    def connect(self):
        return True

    def subscribe_candles(self, asset, timeframe):
        pass

    def place_trade(self, asset, amount, direction, duration):
        # No real trade, just return a dummy id
        return 'signal_only_dummy_trade_id'

    def check_trade_result(self, trade_id):
        # No real result, always return True for signal logging
        return True

    def disconnect(self):
        pass