import pytest
from src.feedback.feedback_loop import FeedbackLoop

def test_feedback_loop_initialization():
    feedback_loop = FeedbackLoop()
    assert feedback_loop is not None

def test_record_trade_outcome():
    feedback_loop = FeedbackLoop()
    feedback_loop.record_trade_outcome('CALL', True)
    assert feedback_loop.trade_history[-1]['decision'] == 'CALL'
    assert feedback_loop.trade_history[-1]['outcome'] is True

def test_calculate_win_rate():
    feedback_loop = FeedbackLoop()
    feedback_loop.record_trade_outcome('CALL', True)
    feedback_loop.record_trade_outcome('PUT', False)
    win_rate = feedback_loop.calculate_win_rate()
    assert win_rate == 0.5

def test_adjust_strategy():
    feedback_loop = FeedbackLoop()
    feedback_loop.record_trade_outcome('CALL', True)
    feedback_loop.record_trade_outcome('CALL', False)
    feedback_loop.adjust_strategy()
    assert feedback_loop.strategy_adjusted is True  # Assuming this flag indicates a strategy adjustment

def test_feedback_loop_logging():
    feedback_loop = FeedbackLoop()
    feedback_loop.record_trade_outcome('PUT', True)
    assert len(feedback_loop.trade_history) == 1
    assert feedback_loop.trade_history[0]['decision'] == 'PUT'