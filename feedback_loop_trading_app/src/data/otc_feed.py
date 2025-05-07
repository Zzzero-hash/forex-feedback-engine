from pocketoptionapi.stable_api import PocketOption

class OTCFeed:
    def __init__(self, ssid):
        self.account = PocketOption(ssid=ssid)
        self.connected = False
        self.candles = {}

    def connect(self):
        self.connected, msg = self.account.connect()
        return self.connected, msg

    def subscribe_candles(self, asset, timeframe):
        if not self.connected:
            raise Exception("Not connected to the Pocket Option API.")
        self.account.subscribe_candles(asset, timeframe)

    def get_candles(self, asset):
        return self.candles.get(asset, [])

    def on_candle_update(self, asset, candle):
        if asset not in self.candles:
            self.candles[asset] = []
        self.candles[asset].append(candle)