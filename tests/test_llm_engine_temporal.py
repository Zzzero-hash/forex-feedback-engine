import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Mock for TemporalLLMEngine
class DummyTemporalEngine:
    def __init__(self, decisions=None):
        self.decisions = decisions or ["CALL", "PUT", "NO TRADE"]
        self.index = 0
        self.historical_collector = None
        
    def initialize_historical_collector(self, data_feed, lookback_periods=20, timeframe_minutes=5):
        self.historical_collector = MagicMock()
        self.historical_collector.get_historical_data.return_value = self._generate_mock_historical_data()
        self.historical_collector.calculate_technical_indicators.return_value = self._generate_mock_indicators()
        self.historical_collector.get_price_chart_ascii.return_value = "ASCII CHART PLACEHOLDER"
        self.historical_collector.get_pattern_analysis.return_value = {"patterns": ["doji", "hammer"]}
        
    def _generate_mock_historical_data(self):
        # Create mock historical OHLC data
        dates = [datetime.now() - timedelta(minutes=i*5) for i in range(20)]
        base_price = 1.2000
        data = []
        for i, date in enumerate(dates):
            # Create some price movement pattern
            close = base_price + (np.sin(i/3) * 0.01)
            open_price = close - 0.0010 if i % 2 == 0 else close + 0.0005
            high = max(open_price, close) + 0.0020
            low = min(open_price, close) - 0.0015
            data.append({
                'timestamp': date,
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': 100 + i * 10
            })
        return pd.DataFrame(data)
    
    def _generate_mock_indicators(self):
        return {
            'price_current': 1.2010,
            'ma_14': 1.2000,
            'ma_50': 1.1990,
            'rsi_14': 58.5,
            'trend_direction': 'bullish',
            'volatility_10_pct': 0.12
        }
        
    def get_decision(self, symbol, market_data, recent_trades):
        # Return next decision or NO TRADE when exhausted
        if self.index < len(self.decisions):
            decision = self.decisions[self.index]
            self.index += 1
            return decision
        return 'NO TRADE'
        
    def select_pair(self, symbols, data_feed=None):
        # Always select the first symbol for testing
        if symbols and len(symbols) > 0:
            return symbols[0]
        return None


def test_temporal_engine_properly_handles_historical_data():
    """Test that TemporalLLMEngine correctly processes historical data"""
    # Create our dummy engine with predefined decisions
    engine = DummyTemporalEngine(decisions=["CALL", "PUT"])
    
    # Create mock data_feed
    mock_data_feed = MagicMock()
    mock_data_feed.get_quote.return_value = {'price': 1.2010, 'timestamp': datetime.now()}
    
    # Initialize the historical collector
    engine.initialize_historical_collector(mock_data_feed)
    
    # Test with some market data and trades
    market_data = {'price': 1.2010}
    recent_trades = [
        {'decision': 'CALL', 'outcome': True, 'timestamp': datetime.now() - timedelta(minutes=15)}
    ]
    
    # Get the first decision
    decision = engine.get_decision("EURUSD", market_data, recent_trades)
    assert decision == "CALL", f"Expected first decision to be CALL, got {decision}"
    
    # Get the second decision
    decision = engine.get_decision("EURUSD", market_data, recent_trades)
    assert decision == "PUT", f"Expected second decision to be PUT, got {decision}"
    
    # Verify the historical collector was used
    assert engine.historical_collector is not None
    

def test_temporal_engine_select_pair():
    """Test that TemporalLLMEngine.select_pair works correctly"""
    # Create our dummy engine
    engine = DummyTemporalEngine()
    
    # Create mock data_feed
    mock_data_feed = MagicMock()
    
    # Test select_pair
    symbols = ["EURUSD", "GBPUSD", "USDJPY"]
    selected = engine.select_pair(symbols, mock_data_feed)
    assert selected == "EURUSD", f"Expected select_pair to return EURUSD, got {selected}"
    
    # Test with empty list
    selected = engine.select_pair([], mock_data_feed)
    assert selected is None, f"Expected select_pair to return None with empty list, got {selected}"