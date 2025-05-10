import pytest
from unittest.mock import MagicMock, patch, call


@pytest.fixture
def mock_all_imports():
    """Mock all imports in src.main module to prevent any real API calls or file access"""
    patches = [
        patch('src.data.data_feed.DataFeed'),
        patch('src.data.otc_feed.OTCFeed'),
        patch('src.decision.llm_engine_temporal.TemporalLLMEngine'),
        patch('src.config.Config'),
        patch('src.execution.broker_api.BrokerAPI'),
        patch('src.feedback.feedback_loop.FeedbackLoop'),
        patch('src.main.run_session')
    ]
    
    mocks = {}
    
    for patcher in patches:
        name = patcher.target.split('.')[-1]
        mock = patcher.start()
        mocks[name] = mock
    
    # Configure specific mock behaviors
    mocks['Config'].return_value.openai_api_key = "test_key"
    mocks['Config'].return_value.po_ssid = "test_ssid"
    mocks['Config'].return_value.polygon_api_key = "test_polygon"
    mocks['Config'].return_value.log_level = "INFO"
    
    mocks['OTCFeed'].return_value.get_otc_symbols.return_value = ["EURUSD", "GBPUSD", "USDJPY"]
    
    # Create mock engine instance with select_pair method
    mock_engine = MagicMock()
    mock_engine.select_pair.return_value = "EURUSD"
    mocks['TemporalLLMEngine'].return_value = mock_engine
    mocks['engine_instance'] = mock_engine
    
    yield mocks
    
    # Stop all patches
    for patcher in patches:
        patcher.stop()


def test_main_imports_and_executes_without_api():
    """Verify that main imports correctly and executes without making real API calls"""
    with patch('src.main.LLMEngine', autospec=True) as mock_engine_class, \
         patch('src.main.run_session') as mock_run_session:
         
        # Create mock engine instance
        mock_engine_instance = MagicMock()
        mock_engine_instance.select_pair.return_value = "EURUSD"
        mock_engine_class.return_value = mock_engine_instance
        
        # Now import main
        from src.main import main
        
        # Call main with all mocked dependencies
        main()
        
        # Verify select_pair was called
        assert mock_engine_instance.select_pair.called
        
        # Verify run_session was called with the expected arguments including symbol
        args, kwargs = mock_run_session.call_args
        assert 'symbol' in kwargs
        assert kwargs['symbol'] == 'EURUSD'


def test_main_full_system_mocked(mock_all_imports):
    """Test the main function with all dependencies mocked"""
    # Import main
    from src.main import main
    
    # Call main function
    main()
    
    # Make assertions
    mock_engine = mock_all_imports['engine_instance']
    assert mock_engine.select_pair.called
    
    mock_run_session = mock_all_imports['run_session']
    assert mock_run_session.called
    
    # Check that select_pair was called with the expected args
    symbols_arg = mock_engine.select_pair.call_args[0][0]
    assert isinstance(symbols_arg, list)
    assert "EURUSD" in symbols_arg

    # Check that run_session was called with keyword args including symbol
    args, kwargs = mock_run_session.call_args
    assert 'symbol' in kwargs
    assert kwargs['symbol'] == 'EURUSD'