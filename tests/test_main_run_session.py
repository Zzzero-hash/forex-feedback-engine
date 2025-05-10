import pytest
from src.main import run_session

class DummyFeed:
    def get_quote(self, symbol):
        return {'price': 100.0}

class DummyOTC:
    def get_otc_candles(self, symbol, interval):
        return {'candle': 'dummy'}

class DummyEngine:
    def __init__(self, decisions):
        self.decisions = decisions
        self.index = 0
    def get_decision(self, market_data, recent_trades):
        # Return next decision or NO TRADE when exhausted
        if self.index < len(self.decisions):
            d = self.decisions[self.index]
            self.index += 1
            return d
        return 'NO TRADE'

class DummyBroker:
    def __init__(self, outcomes):
        self.outcomes = outcomes
        self.index = 0
    def place_trade(self, asset, amount, direction, duration):
        return f"trade{self.index}"
    def check_trade_result(self, trade_id):
        # Return next outcome
        if self.index < len(self.outcomes):
            result = self.outcomes[self.index]
            self.index += 1
            return result
        return False
    def subscribe_candles(self, asset, timeframe):
        pass
    def disconnect(self):
        pass

def make_cfg():
    # Build a simple config object with needed attributes
    class C:
        pass
    cfg = C()
    cfg.otc_interval = 1
    cfg.trade_amount = 10
    cfg.initial_balance = 100
    cfg.profit_target_pct = 5
    cfg.loss_limit_pct = 2
    cfg.enable_demo_mode = True  # Add this for signal-only mode
    # Add other config parameters needed for run_session
    cfg.max_consecutive_no_trade = 5
    cfg.pair_blacklist_duration_seconds = 300
    cfg.max_consecutive_system_switches = 3
    cfg.system_cool_down_duration_seconds = 60
    return cfg

@pytest.mark.parametrize("decisions,outcomes,expected_trades", [
    # Single win (PnL +10 = +10% of initial_balance 100) meets profit target (5%). Stops.
    (["CALL"], [True], 1),
    # First loss (PnL -10 = -10% of initial_balance 100) meets loss limit (2%, i.e. PnL <= -2). Stops.
    (["PUT", "PUT"], [False, False], 1), # Was 2
    # First win (PnL +10 = +10% of initial_balance 100) meets profit target (5%). Stops.
    (["CALL", "PUT", "CALL"], [True, False, True], 1), # Was 3
])
def test_run_session_stops_on_risk(decisions, outcomes, expected_trades):
    cfg = make_cfg()
    data_feed = DummyFeed()
    otc_feed = DummyOTC()
    engine = DummyEngine(decisions)
    broker = DummyBroker(outcomes)
    feedback = pytest.importorskip('src.feedback.feedback_loop').FeedbackLoop()
    # Add symbols_list and initial_symbol_idx arguments for compatibility with new run_session signature
    symbols_list = ["TEST_SYMBOL"]
    initial_symbol_idx = 0
    trades = run_session(cfg, data_feed, otc_feed, engine, broker, feedback, symbols_list, initial_symbol_idx, max_iterations=3)  # Set a small max_iterations value
    assert len(trades) == expected_trades

def test_run_session_max_iterations():
    cfg = make_cfg()
    data_feed = DummyFeed()
    otc_feed = DummyOTC()
    # Decisions no trades
    engine = DummyEngine(['NO TRADE', 'NO TRADE', 'NO TRADE'])
    broker = DummyBroker([])
    feedback = pytest.importorskip('src.feedback.feedback_loop').FeedbackLoop()
    # Add symbols_list and initial_symbol_idx arguments for compatibility with new run_session signature
    symbols_list = ["TEST_SYMBOL"]
    initial_symbol_idx = 0
    trades = run_session(cfg, data_feed, otc_feed, engine, broker, feedback, symbols_list, initial_symbol_idx, max_iterations=3)
    # No trades executed
    assert trades == []
    # After 3 iterations it stops
    assert engine.index == 3
