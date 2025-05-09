class OTCFeed:
    """
    Dummy OTCFeed for signal-only mode. No live OTC data, just static/dummy responses.
    """
    def __init__(self):
        pass

    def get_otc_feed(self):
        return {}

    def get_otc_candles(self, symbol, interval):
        return {}

    def get_otc_symbols(self):
        # Return a comprehensive list of major and minor forex pairs for signal-only mode
        return [
            # Major pairs
            'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD',
            # Minor pairs (Euro crosses)
            'EURGBP', 'EURJPY', 'EURCHF', 'EURAUD', 'EURCAD', 'EURNZD',
            # Minor pairs (Yen crosses)
            'GBPJPY', 'AUDJPY', 'CADJPY', 'NZDJPY', 'CHFJPY',
            # Minor pairs (Pound crosses)
            'GBPAUD', 'GBPCAD', 'GBPCHF', 'GBPNZD',
            # Other minor pairs
            'AUDCAD', 'AUDCHF', 'AUDNZD', 'CADCHF', 'NZDCAD', 'NZDCHF'
        ]

    def get_otc_symbol_info(self, symbol):
        return {'symbol': symbol}
