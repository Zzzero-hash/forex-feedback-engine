import pytest
from src.decision.prompt_config import PromptConfig

@ pytest.fixture
def cfg():
    return PromptConfig()

def test_user_prompt_format(cfg):
    pa = "up/down movement"
    indicators = "RSI high"
    patterns = "head and shoulders"
    user_prompt = cfg.get_user_prompt(pa, indicators, patterns)
    assert pa in user_prompt
    assert indicators in user_prompt
    assert patterns in user_prompt

def test_system_prompt_contains_keywords(cfg):
    sys_prompt = cfg.get_system_prompt()
    # Should mention CALL, PUT, NO TRADE
    assert "CALL" in sys_prompt
    assert "PUT" in sys_prompt
    assert "NO TRADE" in sys_prompt

def test_confidence_threshold(cfg):
    thr = cfg.confidence_threshold
    assert cfg.is_trade_recommended(thr)
    assert not cfg.is_trade_recommended(thr - 0.1)