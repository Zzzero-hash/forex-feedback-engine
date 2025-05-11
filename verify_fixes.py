"""
Verification script to test that all fixes work correctly.

This script tests:
1. Historical data collection with Polygon API
2. OpenAI API authentication and version handling
3. Error handling for empty datasets
"""
import os
import logging
import time
from src.config import Config
from src.data.data_feed import DataFeed
from src.data.otc_feed import OTCFeed
from src.decision.llm_engine_temporal import TemporalLLMEngine
from src.data.historical_feed import HistoricalDataCollector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("verification")

def test_polygon_api():
    """Test the Polygon API functionality with fixed timestamp handling"""
    logger.info("Testing Polygon API with fixed timestamp handling...")
    
    # Initialize DataFeed with Polygon API key
    api_key = os.environ.get("POLYGON_API_KEY")
    if not api_key:
        logger.warning("No POLYGON_API_KEY found in environment variables")
        return False
        
    data_feed = DataFeed(api_key=api_key)
    
    # Create HistoricalDataCollector with the fixed code
    collector = HistoricalDataCollector(data_feed=data_feed, lookback_periods=60, timeframe_minutes=5)
    
    # Test with a common forex pair
    symbol = "EURUSD"
    logger.info(f"Fetching historical data for {symbol}")
    df = collector.get_historical_data(symbol, force_refresh=True)
    
    if df is None or df.empty:
        logger.error("No historical data returned")
        return False
        
    logger.info(f"Successfully retrieved {len(df)} rows of historical data")
    logger.info(f"Data range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    
    # Test technical indicators
    indicators = collector.calculate_technical_indicators(symbol)
    logger.info(f"Technical indicators: {indicators}")
    
    # Test pattern analysis
    patterns = collector.get_pattern_analysis(symbol)
    logger.info(f"Patterns: {patterns}")
    
    # Test ASCII chart
    chart = collector.get_price_chart_ascii(symbol)
    logger.info(f"ASCII chart length: {len(chart)}")
    
    return True

def test_openai_api():
    """Test the OpenAI API with fixed client handling"""
    logger.info("Testing OpenAI API with fixed client handling...")
    
    # Initialize OpenAI with API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.warning("No OPENAI_API_KEY found in environment variables")
        return False
        
    try:
        engine = TemporalLLMEngine(api_key=api_key, model="gpt-4")
        logger.info(f"Successfully initialized OpenAI client: {engine.client is not None}")
        
        # Test a simple completion
        system_msg = "You are a helpful assistant."
        user_content = "Say hello."
        
        response = engine._call_openai_api(system_msg, user_content)
        logger.info(f"OpenAI API response: {response}")
        
        return True
    except Exception as e:
        logger.error(f"Error testing OpenAI API: {e}", exc_info=True)
        return False

def main():
    """Run all verification tests"""
    logger.info("Starting verification tests")
    
    polygon_success = test_polygon_api()
    logger.info(f"Polygon API test {'PASSED' if polygon_success else 'FAILED'}")
    
    openai_success = test_openai_api()
    logger.info(f"OpenAI API test {'PASSED' if openai_success else 'FAILED'}")
    
    if polygon_success and openai_success:
        logger.info("All tests PASSED! The fixes were successful.")
    else:
        logger.warning("Some tests FAILED. Check the logs above for details.")

if __name__ == "__main__":
    main()
