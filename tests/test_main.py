import pytest
from unittest.mock import MagicMock, patch

@pytest.fixture
def mock_components():
    """Create mock components for testing main.py"""
    with patch('src.main.DataFeed') as mock_data_feed, \
         patch('src.main.OTCFeed') as mock_otc_feed, \
         patch('src.main.LLMEngine') as mock_engine, \
         patch('src.main.BrokerAPI') as mock_broker, \
         patch('src.main.FeedbackLoop') as mock_feedback, \
         patch('src.main.Config') as mock_config, \
         patch('src.main.run_session') as mock_run_session:
        
        # Configure mocks
        mock_config.return_value.openai_api_key = "test_key"
        mock_config.return_value.po_ssid = "test_ssid"
        mock_config.return_value.polygon_api_key = "test_polygon"
        mock_config.return_value.log_level = "INFO"
        
        # Set up OTCFeed to return symbols
        mock_otc_feed.return_value.get_otc_symbols.return_value = ["EURUSD", "GBPUSD", "USDJPY"]
        
        # Set up engine to select a pair
        mock_engine.return_value.select_pair.return_value = "EURUSD"
        
        yield {
            'data_feed': mock_data_feed,
            'otc_feed': mock_otc_feed,
            'engine': mock_engine,
            'broker': mock_broker,
            'feedback': mock_feedback,
            'config': mock_config,
            'run_session': mock_run_session
        }

def test_main_passes_data_feed_to_select_pair(mock_components):
    """Test that main passes the data_feed to the select_pair method"""
    # Import main here to use the mocked components
    from src.main import main
    
    # Call the main function
    main()
    
    # Check that select_pair was called with both symbols and data_feed
    mock_engine_instance = mock_components['engine'].return_value
    select_pair_call = mock_engine_instance.select_pair
    
    # First argument should be the symbols list
    args, kwargs = select_pair_call.call_args
    assert len(args) >= 1
    assert isinstance(args[0], list)  # First arg should be symbols list
    
    # Second argument should be the data_feed
    assert len(args) >= 2
    assert args[1] == mock_components['data_feed'].return_value  # Second arg should be data_feed
    
    # Check that run_session is called with the selected pair
    mock_run_session_call = mock_components['run_session']
    run_session_kwargs = mock_run_session_call.call_args[1]
    assert run_session_kwargs['symbol'] == 'EURUSD'
