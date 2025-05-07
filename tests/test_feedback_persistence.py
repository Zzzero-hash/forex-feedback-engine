import os
import sqlite3
import pytest
from src.feedback.feedback_loop import FeedbackLoop
from src.feedback.models import Trade
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def test_should_end_session_profit_loss():
    loop = FeedbackLoop()
    # No trades yet, should not end
    assert not loop.should_end_session(initial_balance=100, trade_amount=1, profit_target_pct=5, loss_limit_pct=2)
    # Record 5 wins and 3 losses: pnl = (5-3)*1 = 2, pnl_pct = 2%
    for _ in range(5):
        loop.record_trade_outcome('CALL', True)
    for _ in range(3):
        loop.record_trade_outcome('PUT', False)
    # Should end session at profit target 2% or loss limit
    assert loop.should_end_session(initial_balance=100, trade_amount=1, profit_target_pct=2, loss_limit_pct=2)


def test_persistence_to_disk(tmp_path):
    # Use a file-based SQLite database
    db_file = tmp_path / "trades.db"
    db_url = f"sqlite:///{db_file}"
    # Initialize and record a trade
    loop = FeedbackLoop(database_url=db_url)
    loop.record_trade_outcome('CALL', True)
    # Connect directly to the database to verify persistence
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    trades = session.query(Trade).all()
    assert len(trades) == 1
    assert trades[0].decision == 'CALL'
    assert trades[0].outcome is True
