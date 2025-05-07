import pytest

import src.execution.broker_api as broker_module

class DummyPO:
    def __init__(self, ssid=None):
        self.connected = False
    def connect(self):
        self.connected = True
        return True, ''
    def subscribe_candles(self, asset, timeframe):
        self.candles = (asset, timeframe)
    def buy(self, asset, amount, direction, duration):
        return 'trade123'
    def check_win(self, trade_id):
        return True
    def disconnect(self):
        self.disconnected = True

@pytest.fixture(autouse=True)
def patch_pocketoption(monkeypatch):
    # Replace PocketOption in broker_api with DummyPO
    monkeypatch.setattr(broker_module, 'PocketOption', DummyPO)
    yield

@pytest.fixture
def broker():
    return broker_module.BrokerAPI(ssid='ssid')

def test_connect_and_subscription(broker):
    # connect called in init
    assert broker.connected is True
    # subscribe to candles
    broker.subscribe_candles('EURUSD', 60)
    assert getattr(broker.account, 'candles', None) == ('EURUSD', 60)

def test_place_and_check_trade(broker):
    trade_id = broker.place_trade('EURUSD', 10, 'CALL', 60)
    assert trade_id == 'trade123'
    result = broker.check_trade_result(trade_id)
    assert result is True

def test_disconnect(broker):
    broker.disconnect()
    assert getattr(broker.account, 'disconnected', False) is True