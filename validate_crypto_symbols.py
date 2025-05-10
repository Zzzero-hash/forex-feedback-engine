"""
Validation script to test cryptocurrency symbol support.

This script tests:
1. Detection of symbol types (forex vs crypto)
2. Proper formatting of Polygon API tickers
3. Historical data fetching for crypto symbols
"""

import os
import logging
import pandas as pd
from datetime import datetime

# Ensure we can import from the src directory
from src.data.data_feed import DataFeed
from src.data.historical_feed import HistoricalDataCollector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("validation")

def test_symbol_type_detection():
    """Test the symbol type detection for forex and crypto"""
    data_feed = DataFeed()
    
    forex_symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD"]
    crypto_symbols = ["BTCUSD", "ETHUSD", "SOLUSD", "ADAUSD", "DOTUSD"]
    
    print("\n===== Symbol Type Detection =====")
    print("Expected: All forex symbols should be detected as 'forex'")
    print("Expected: All crypto symbols should be detected as 'crypto'")
    
    for symbol in forex_symbols:
        symbol_type = data_feed.detect_symbol_type(symbol)
        print(f"Symbol: {symbol} -> Type: {symbol_type}")
        assert symbol_type == "forex", f"Expected {symbol} to be forex, got {symbol_type}"
        
    for symbol in crypto_symbols:
        symbol_type = data_feed.detect_symbol_type(symbol)
        print(f"Symbol: {symbol} -> Type: {symbol_type}")
        assert symbol_type == "crypto", f"Expected {symbol} to be crypto, got {symbol_type}"
    
    return True

def test_polygon_ticker_formatting():
    """Test the polygon ticker formatting for forex and crypto symbols"""
    data_feed = DataFeed()
    
    test_cases = [
        ("EURUSD", "C:EURUSD"),  # Forex
        ("BTCUSD", "X:BTCUSD"),  # Crypto
        ("ETHUSD", "X:ETHUSD"),  # Crypto
        ("GBPJPY", "C:GBPJPY"),  # Forex
    ]
    
    print("\n===== Polygon Ticker Formatting =====")
    print("Expected: Forex symbols should be prefixed with 'C:'")
    print("Expected: Crypto symbols should be prefixed with 'X:'")
    
    for symbol, expected_ticker in test_cases:
        ticker = data_feed.get_polygon_ticker(symbol)
        print(f"Symbol: {symbol} -> Ticker: {ticker}")
        assert ticker == expected_ticker, f"Expected {expected_ticker}, got {ticker}"
    
    return True

def test_historical_data_fetch():
    """Test fetching historical data for crypto symbols"""
    api_key = os.environ.get("POLYGON_API_KEY")
    if not api_key:
        print("\n===== Historical Data Fetch =====")
        print("POLYGON_API_KEY not set in environment variables. Skipping test.")
        return False
    
    data_feed = DataFeed(api_key=api_key)
    collector = HistoricalDataCollector(data_feed=data_feed)
    
    # Test fetch for Bitcoin and Ethereum
    symbols = ["BTCUSD", "ETHUSD"]
    results = {}
    
    print("\n===== Historical Data Fetch =====")
    print("Fetching historical data for crypto symbols...")
    
    for symbol in symbols:
        print(f"\nFetching data for {symbol}...")
        df = collector.get_historical_data(symbol, force_refresh=True)
        
        if df is None or df.empty:
            print(f"No data returned for {symbol}")
            results[symbol] = False
            continue
        
        print(f"Successfully fetched {len(df)} rows of data for {symbol}")
        print(f"Data range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        print(f"Latest price: {df['close'].iloc[-1]}")
        results[symbol] = True
        
        # Calculate some indicators to test
        indicators = collector.calculate_technical_indicators(symbol)
        print(f"Calculated indicators for {symbol}:")
        for key, value in indicators.items():
            if key in ["price_current", "rsi_14", "volatility_10_pct", "trend_direction"]:
                print(f"  - {key}: {value}")
    
    return all(results.values())

def main():
    """Run all validation tests"""
    print("Starting cryptocurrency symbol validation tests")
    
    type_detection_success = test_symbol_type_detection()
    print(f"\nSymbol type detection test: {'PASSED' if type_detection_success else 'FAILED'}")
    
    ticker_formatting_success = test_polygon_ticker_formatting()
    print(f"\nPolygon ticker formatting test: {'PASSED' if ticker_formatting_success else 'FAILED'}")
    
    historical_data_success = test_historical_data_fetch()
    print(f"\nHistorical data fetch test: {'PASSED' if historical_data_success else 'FAILED'}")
    
    if type_detection_success and ticker_formatting_success and historical_data_success:
        print("\nAll tests PASSED! Cryptocurrency symbol support is working correctly.")
    else:
        print("\nSome tests FAILED. Check the logs above for details.")

if __name__ == "__main__":
    main()
