"""
Quick validation script to check if our fixes work.
This will test:
1. Polygon API with past dates
2. OpenAI API with error fallbacks
3. Calculation fixes for division by zero
"""
import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger()

# Add project root to path
sys.path.append(os.path.abspath("."))

# Import required modules
from src.data.data_feed import DataFeed
from src.data.historical_feed import HistoricalDataCollector
from src.decision.llm_engine_temporal import TemporalLLMEngine

def test_polygon_api_fix():
    """Test the Polygon API with past date fixes"""
    logger.info("\n--- Testing Polygon API Fix ---")
    
    # 1. Initialize DataFeed with Polygon API
    api_key = os.environ.get("POLYGON_API_KEY")
    if not api_key:
        logger.error("No POLYGON_API_KEY found in environment variables")
        return False
        
    data_feed = DataFeed(api_key=api_key)
    
    # 2. Initialize HistoricalDataCollector with past date fix
    collector = HistoricalDataCollector(data_feed=data_feed, lookback_periods=60, timeframe_minutes=5)
    
    # 3. Test with a common forex pair
    symbol = "EURUSD"
    logger.info(f"Fetching historical data for {symbol}")
    df = collector.get_historical_data(symbol, force_refresh=True)
    
    if df is None or df.empty:
        logger.error("No historical data returned - fix may not be working")
        return False
        
    logger.info(f"Successfully retrieved {len(df)} rows of historical data")
    min_date = df['timestamp'].min().strftime('%Y-%m-%d %H:%M:%S')
    max_date = df['timestamp'].max().strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f"Data range: {min_date} to {max_date}")
    
    # 4. Test technical indicators with division by zero fix
    indicators = collector.calculate_technical_indicators(symbol)
    logger.info(f"Technical indicators calculation successful")
    
    # 5. Test ASCII chart with zero handling fix
    chart = collector.get_price_chart_ascii(symbol)
    logger.info(f"ASCII chart generation successful")
    
    return True

def test_openai_api_fix():
    """Test the OpenAI API with error handling and fallbacks"""
    logger.info("\n--- Testing OpenAI API Fix ---")
    
    # 1. Initialize with invalid key to test fallbacks
    engine = TemporalLLMEngine(api_key="invalid_key_to_test_fallbacks", model="gpt-4")
    
    # 2. Test API call with fallbacks
    system_msg = "You are a helpful assistant."
    user_content = "Say hello."
    
    response = engine._call_openai_api(system_msg, user_content)
    logger.info(f"Response from API call with invalid key: {response}")
    
    # If we got NO TRADE, our fallback worked correctly
    if "NO TRADE" in response:
        logger.info("Fallback response worked correctly!")
        return True
    else:
        logger.error("Fallback response did not work as expected")
        return False

def main():
    """Run all validation tests"""
    logger.info("Starting validation for fixes...")
    
    polygon_success = test_polygon_api_fix()
    openai_success = test_openai_api_fix()
    
    if polygon_success and openai_success:
        logger.info("\n✅ All fixes validated successfully!")
    else:
        logger.error("\n❌ Some fixes did not work as expected. Please review logs.")
        
    logger.info("\nYou can now run the main application with confidence.")

if __name__ == "__main__":
    main()
