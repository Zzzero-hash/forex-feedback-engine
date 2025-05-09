import pytest
import os
from src.data.otc_feed import OTCFeed

@pytest.fixture
def otc_feed():
    return OTCFeed()

def test_get_otc_feed(otc_feed):
    data = otc_feed.get_otc_feed()
    # Should return empty dict in signal-only mode
    assert isinstance(data, dict)
    assert len(data) == 0

def test_get_otc_candles(otc_feed):
    res = otc_feed.get_otc_candles('EURUSD', 60)
    # Should return empty dict in signal-only mode
    assert isinstance(res, dict)
    assert len(res) == 0

def test_get_otc_symbols(otc_feed):
    syms = otc_feed.get_otc_symbols()
    # Check if it returns the static list of symbols
    assert 'EURUSD' in syms
    assert 'GBPUSD' in syms
    assert 'USDJPY' in syms

def test_get_otc_symbol_info(otc_feed):
    info = otc_feed.get_otc_symbol_info('EURUSD')
    # Check that it returns the expected dummy format
    assert info['symbol'] == 'EURUSD'

def test_environment_setup():
    # Test environment setup (a replacement for the previous missing_ssid_env test)
    # Verify config values are accessible but not required for dummy implementation
    po_ssid = os.environ.get('PO_SSID')
    
    # Our new OTCFeed doesn't need SSID, so instantiation should always work
    feed = OTCFeed()
    assert isinstance(feed, OTCFeed)