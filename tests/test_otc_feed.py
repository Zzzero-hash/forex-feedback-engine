import os
import pytest

from src.data.otc_feed import OTCFeed

class DummyAPI:
    def __init__(self, ssid=None):
        self.ssid = ssid
        self.connected = False
    def connect(self):
        self.connected = True
        return True
    def get_otc_feed(self):
        return {'feed': 'dummy'}
    def get_otc_candles(self, symbol, interval):
        return {symbol: interval}
    def get_otc_symbols(self):
        return ['SYM1', 'SYM2']
    def get_otc_symbol_info(self, symbol):
        return {'symbol': symbol}

@pytest.fixture(autouse=True)
def patch_pocketoption(monkeypatch):
    # Patch the PocketOption class to use DummyAPI
    monkeypatch.setenv('PO_SSID', 'test_ssid')
    import src.data.otc_feed as module
    monkeypatch.setattr(module, 'PocketOption', DummyAPI)
    yield

@ pytest.fixture
def otc_feed():
    return OTCFeed()

def test_get_otc_feed(otc_feed):
    data = otc_feed.get_otc_feed()
    assert data == {'feed': 'dummy'}

def test_get_otc_candles(otc_feed):
    res = otc_feed.get_otc_candles('EURUSD', 60)
    assert res == {'EURUSD': 60}

def test_get_otc_symbols(otc_feed):
    syms = otc_feed.get_otc_symbols()
    assert 'SYM1' in syms and 'SYM2' in syms

def test_get_otc_symbol_info(otc_feed):
    info = otc_feed.get_otc_symbol_info('EURUSD')
    assert info['symbol'] == 'EURUSD'

def test_missing_ssid_env(monkeypatch):
    monkeypatch.delenv('PO_SSID', raising=False)
    with pytest.raises(ValueError):
        OTCFeed()