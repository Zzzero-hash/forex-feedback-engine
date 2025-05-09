import pytest
from src.execution.broker_api import BrokerAPI

@pytest.fixture
def broker():
    return BrokerAPI(ssid='dummy_ssid')

def test_init(broker):
    # Just verify the broker was initialized properly
    assert broker.connected is True

def test_place_signal(broker):
    # Test signal recording in signal-only mode
    trade_id = broker.place_trade('EURUSD', 10, 'CALL', 60)
    assert trade_id == 'signal_only_dummy_trade_id'

def test_check_signal_result(broker):
    # Check that the signal result is always returned as True in dummy mode
    result = broker.check_trade_result('any_trade_id')
    assert result is True