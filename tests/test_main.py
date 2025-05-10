import pytest
from unittest.mock import MagicMock, patch

@pytest.fixture
def mock_components():
    """Create mock components for testing main.py"""
    with patch('src.main.DataFeed') as mock_data_feed, \
         patch('src.main.OTCFeed') as mock_otc_feed, \
         patch('src.main.LLMEngine') as mock_llm_engine_class, \  # Changed patch target
         patch('src.main.BrokerAPI') as mock_broker, \
         patch('src.main.FeedbackLoop') as mock_feedback, \
         patch('src.main.Config') as mock_config, \
         patch('src.main.run_session') as mock_run_session:
        
        mock_config.return_value.openai_api_key = "test_key"
        mock_config.return_value.po_ssid = "test_ssid"
        mock_config.return_value.polygon_api_key = "test_polygon"
        mock_config.return_value.log_level = "INFO"
        
        mock_otc_feed.return_value.get_otc_symbols.return_value = ["EURUSD", "GBPUSD", "USDJPY"]
        
        # Configure the select_pair method on the instance that the mocked class will return
        mock_llm_engine_class.return_value.select_pair.return_value = "EURUSD"
        
        yield {
            'data_feed': mock_data_feed,
            'otc_feed': mock_otc_feed,
            'engine_class_mock': mock_llm_engine_class, # This now refers to the mock of src.main.LLMEngine
            'broker': mock_broker,
            'feedback': mock_feedback,
            'config': mock_config,
            'run_session': mock_run_session
        }

def test_main_passes_data_feed_to_select_pair(mock_components):
    """Test that main passes the data_feed to the select_pair method"""
    
    import src.main

    # Assert that src.main.LLMEngine is indeed our mocked class
    assert src.main.LLMEngine is mock_components['engine_class_mock'], \
        "src.main.LLMEngine was not replaced by the mock class"

    from src.main import main
    
    main()
    
    mock_engine_instance = mock_components['engine_class_mock'].return_value
    select_pair_method_mock = mock_engine_instance.select_pair
    
    assert select_pair_method_mock.called, \
        "select_pair was not called on the mocked engine instance"
    
    args, kwargs = select_pair_method_mock.call_args
    
    assert len(args) >= 1
    assert isinstance(args[0], list)  # First arg should be symbols list
    
    assert len(args) >= 2
    assert args[1] is mock_components['data_feed'].return_value
    
    mock_run_session_call = mock_components['run_session']
    assert mock_run_session_call.called, "run_session was not called"
    
    run_session_pos_args, run_session_kw_args = mock_run_session_call.call_args
    assert run_session_kw_args.get('symbol') == "EURUSD"
