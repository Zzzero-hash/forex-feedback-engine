import pytest
from unittest.mock import MagicMock, patch
from src.decision.llm_engine import LLMEngine
from src.config import Config

@pytest.fixture
def llm_engine():
    # Mock Config to provide a dummy API key for testing
    mock_config = Config()
    mock_config.openai_api_key = "test_api_key" 
    
    # Patch the OpenAI client within the LLMEngine instance
    with patch('src.decision.llm_engine.OpenAI') as mock_openai:
        # Configure the mock client's chat.completions.create method
        mock_chat_completion = MagicMock()
        mock_chat_completion.choices = [MagicMock(message=MagicMock(content="CALL"))]
        mock_openai.return_value.chat.completions.create.return_value = mock_chat_completion
        
        engine = LLMEngine(api_key=mock_config.openai_api_key)
        # Store the mock_openai instance on the engine for assertions if needed
        engine.mock_openai_client = mock_openai 
        return engine

def test_llm_engine_initialization(llm_engine):
    assert llm_engine is not None
    assert llm_engine.api_key == "test_api_key"
    # Check if OpenAI client was called with the api_key
    llm_engine.mock_openai_client.assert_called_once_with(api_key="test_api_key")

def test_get_decision_call(llm_engine):
    market_data = {"price": "1.1000"}
    recent_trades = []
    
    # Set up the mock response for this specific test case if different from fixture
    mock_chat_completion = MagicMock()
    mock_chat_completion.choices = [MagicMock(message=MagicMock(content="Predicted action: CALL"))]
    llm_engine.client.chat.completions.create.return_value = mock_chat_completion
    
    decision = llm_engine.get_decision(market_data, recent_trades)
    assert decision == "CALL"
    llm_engine.client.chat.completions.create.assert_called_once()
    call_args = llm_engine.client.chat.completions.create.call_args
    assert call_args[1]['model'] == "gpt-4"
    assert call_args[1]['messages'][0]['role'] == "system"
    assert call_args[1]['messages'][1]['role'] == "user"
    assert "Market Data: {'price': '1.1000'}" in call_args[1]['messages'][1]['content']
    assert "Recent Trades: []" in call_args[1]['messages'][1]['content']


def test_get_decision_put(llm_engine):
    market_data = {"price": "1.0900"}
    recent_trades = [{"type": "CALL", "outcome": "loss"}]

    # Set up the mock response
    mock_chat_completion = MagicMock()
    mock_chat_completion.choices = [MagicMock(message=MagicMock(content="Predicted action: PUT"))]
    llm_engine.client.chat.completions.create.return_value = mock_chat_completion
    
    decision = llm_engine.get_decision(market_data, recent_trades)
    assert decision == "PUT"

def test_get_decision_no_trade(llm_engine):
    market_data = {"price": "1.0950"}
    recent_trades = []

    # Set up the mock response
    mock_chat_completion = MagicMock()
    mock_chat_completion.choices = [MagicMock(message=MagicMock(content="Predicted action: NO TRADE"))]
    llm_engine.client.chat.completions.create.return_value = mock_chat_completion
    
    decision = llm_engine.get_decision(market_data, recent_trades)
    assert decision == "NO TRADE"

def test_parse_response(llm_engine):
    assert llm_engine._parse_response("This is a CALL") == "CALL"
    assert llm_engine._parse_response("I suggest a PUT") == "PUT"
    assert llm_engine._parse_response("No clear signal, NO TRADE") == "NO TRADE"
    assert llm_engine._parse_response("Uncertain outcome") == "NO TRADE"

# It might be good to test the prompt generation if it becomes complex
def test_prompt_generation_content(llm_engine):
    # This test assumes PromptConfig is working correctly and focuses on LLMEngine's use of it.
    # We can spy on prompt_config methods if needed, but here we'll just check the user content.
    market_data = {"eurusd_price": 1.12345}
    recent_trades = [{"action": "CALL", "profit": 10}, {"action": "PUT", "profit": -5}]
    
    # Reset mock for this specific call verification
    llm_engine.client.chat.completions.create.reset_mock()
    mock_chat_completion = MagicMock()
    mock_chat_completion.choices = [MagicMock(message=MagicMock(content="CALL"))]
    llm_engine.client.chat.completions.create.return_value = mock_chat_completion

    llm_engine.get_decision(market_data, recent_trades)

    llm_engine.client.chat.completions.create.assert_called_once()
    args, kwargs = llm_engine.client.chat.completions.create.call_args
    
    # Check that the user message content is formatted as expected
    user_message_content = kwargs['messages'][1]['content']
    expected_market_data_str = f"Market Data: {market_data}"
    expected_trades_str = f"Recent Trades: {recent_trades}"
    
    assert expected_market_data_str in user_message_content
    assert expected_trades_str in user_message_content
    
    # Verify system prompt is also passed (optional, depends on how deep you want to test)
    system_message_content = kwargs['messages'][0]['content']
    assert len(system_message_content) > 0 # Basic check that it's not empty

def test_select_pair_success(llm_engine):
    symbols = ['EURUSD', 'GBPUSD', 'USDJPY']
    
    # The mock fixture response 'CALL' doesn't match any symbol,
    # so our function will default to the first symbol
    selected = llm_engine.select_pair(symbols)
    assert selected == 'EURUSD'  # First symbol is returned as fallback
    
    # Verify that the client was called
    llm_engine.client.chat.completions.create.assert_called_once()
    call_args = llm_engine.client.chat.completions.create.call_args
    assert call_args[1]['model'] == 'gpt-4'  # Updated to use gpt-4
    msgs = call_args[1]['messages']
    assert msgs[0]['role'] == 'system'
    assert 'Available symbols' in msgs[1]['content']


def test_select_pair_exception_fallback(llm_engine):
    symbols = ['EURUSD', 'GBPUSD']
    
    # When all API calls fail, we should get the first symbol as fallback
    with patch('src.decision.llm_engine.openai.ChatCompletion.create', side_effect=Exception('API error')):
        selected = llm_engine.select_pair(symbols)
        # Should fall back to the first symbol
        assert selected == 'EURUSD'

def test_select_pair_with_market_data(llm_engine):
    """Test that the select_pair method uses technical indicators from data_feed when available."""
    symbols = ['EURUSD', 'GBPUSD', 'USDJPY']
    
    # Create a mock data_feed object
    mock_data_feed = MagicMock()
    
    # Configure mock data_feed to return sample market data
    def mock_get_quote(symbol):
        # Return different prices for different symbols
        prices = {
            'EURUSD': 1.0850,
            'GBPUSD': 1.2750,
            'USDJPY': 150.25
        }
        return {
            'price': prices.get(symbol, 100.0),
            'timestamp': '2025-05-09T10:00:00'
        }
    
    mock_data_feed.get_quote = MagicMock(side_effect=mock_get_quote)
    
    # Configure LLM to return a specific symbol
    mock_chat_completion = MagicMock()
    mock_chat_completion.choices = [MagicMock(message=MagicMock(content="GBPUSD"))]
    llm_engine.client.chat.completions.create.return_value = mock_chat_completion
    
    # Call select_pair with data_feed
    selected = llm_engine.select_pair(symbols, mock_data_feed)
    assert selected == 'GBPUSD'
    
    # Verify that data_feed.get_quote was called for each symbol
    assert mock_data_feed.get_quote.call_count == len(symbols)
    
    # Verify that technical data was included in the prompt
    call_args = llm_engine.client.chat.completions.create.call_args
    user_message = call_args[1]['messages'][1]['content']
    assert 'Current Market Data:' in user_message
    
    # Verify system message contains technical analysis guidance
    system_message = call_args[1]['messages'][0]['content']
    assert 'technical indicators' in system_message.lower()
    assert 'directional signal' in system_message.lower()
