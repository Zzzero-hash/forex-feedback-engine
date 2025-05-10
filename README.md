# Forex Feedback Engine

This project is a feedback-loop driven trading system designed for binary options trading. It integrates real-time market data sources, uses an LLM-based decision engine with configurable risk management, and features enhanced market analysis with technical indicators for better pair selection.

**Warning:** This system uses Large Language Models (LLMs) for decision making. Using sophisticated LLMs can be very expensive. It is highly recommended to start with simpler, less costly models and monitor your API usage closely.

## Features

- Signal-Only Mode: System generates trading signals without executing real trades
- OpenAI Integration: Uses o4-mini LLM model to make trading decisions (configurable)
- Enhanced Pair Selection: Uses real-time market data and technical indicators for better trading pair selection
- Technical Analysis: Calculates RSI, volatility, momentum and price changes for more informed decisions
- Risk Management: Configurable profit targets and loss limits
- Trade History: Records trades for analysis and model feedback
- Weekend Trading: Supports cryptocurrency symbols (BTCUSD, ETHUSD, etc.) that trade 24/7.
- Dynamic Symbol Switching: Automatically switches to other available symbols if a pair becomes inactive or consistently yields "NO TRADE" signals.
- System Cooldown: Implements a cool-down mechanism if too many consecutive symbol switches occur, preventing rapid, unproductive cycling.

## Recent Enhancements & Fixes

1. **Timestamp Issue with Polygon API Fixed**:
   - Corrected timestamp handling in `historical_feed.py` for proper date formats expected by Polygon API.
   - Ensured start/end dates are correctly formatted and not in the future.
2. **OpenAI API Authentication and Compatibility Updated**:
   - Revised client initialization to support both v0.x and v1.x OpenAI APIs.
   - Removed `pkg_resources` dependency for version detection.
   - Improved error handling for API calls.
3. **Empty Historical Data Handling Improved**:
   - Added robust error handling for empty DataFrames.
   - Included fallback to simulated data when real data is unavailable.
   - Prevented KeyError exceptions when accessing DataFrame columns.
4. **Weekend Trading Support with Cryptocurrency Added**:
   - Integrated support for cryptocurrency symbols (e.g., BTCUSD, ETHUSD) available 24/7.
   - Implemented smart detection of symbol types (forex vs. crypto).
   - Added correct formatting for Polygon API tickers (C: for forex, X: for crypto).
   - System now automatically prioritizes crypto symbols on weekends.
5. **Updated LLM Model**: Changed from "gpt-3.5-turbo" to "o4-mini" for improved performance (still configurable).
6. **Signal-Only Mode**: System can operate in signal-only mode, generating trading signals without executing real trades.
7. **Enhanced Trading Pair Selection**: Improved algorithm now uses real-time market data and technical indicators.
8. **Expanded Forex Pairs**: Updated to include a comprehensive list of 28 major and minor forex pairs.

## Technical Indicators

The system analyzes multiple technical indicators to select the optimal trading pair:

- RSI (Relative Strength Index): Measures the momentum of price movements
- Volatility: Calculates standard deviation of price changes
- Momentum: Tracks the rate of price changes over time
- Price Change Percentage: Monitors recent price movements

## Testing the Fixes

Verification scripts have been created to test that all fixes work correctly:

```powershell
# Set required environment variables
$env:POLYGON_API_KEY="your_polygon_api_key"
$env:OPENAI_API_KEY="your_openai_api_key"

# Run the general verification script
python verify_fixes.py

# Run the cryptocurrency support validation script
python validate_crypto_symbols.py
```

The verification scripts will test:

1. Historical data collection with Polygon API (both forex and crypto)
2. OpenAI API authentication and version handling
3. Error handling for empty datasets
4. Symbol type detection and formatting
5. Weekend data availability with cryptocurrencies

## Running the System

To run the trading system:

1. **Set Environment Variables**:
   Make sure you have the following environment variables set:
   - `POLYGON_API_KEY`: Your API key for Polygon.io (for market data).
   - `OPENAI_API_KEY`: Your API key for OpenAI (for the LLM decision engine).
   - `PO_SSID`: Your Pocket Option SSID (if you intend to execute live trades). If not set, or if `ENABLE_DEMO_MODE` is true, the system will run in signal-only mode.
   - `DATABASE_URL` (Optional): SQLAlchemy connection string for storing trade history (e.g., `sqlite:///trading_logs.db`). Defaults to an in-memory SQLite database if not set.
   - `ENABLE_DEMO_MODE` (Optional): Set to `true` to run in signal-only mode, even if `PO_SSID` is provided. Defaults to `false`.
   - `LOG_LEVEL` (Optional): Set the logging level (e.g., `DEBUG`, `INFO`, `WARNING`). Defaults to `INFO`.
   - `LLM_MODEL` (Optional): Specify the LLM model to be used (e.g., `o4-mini`, `gpt-3.5-turbo`). Defaults to `o4-mini`.

   Example for PowerShell:

   ```powershell
   $env:POLYGON_API_KEY="your_polygon_api_key"
   $env:OPENAI_API_KEY="your_openai_api_key"
   $env:PO_SSID="your_pocket_option_ssid" # Optional for live trading
   ```

2. **Install Dependencies**:

   ```bash
   pip install .
   ```

   This command builds and installs the package, making the `forex-engine` command available in your environment.

3. **Run the Application**:

   After installation, you can run the application using the `forex-engine` command:

   ```bash
   forex-engine
   ```

   **CLI Arguments (Optional):**
   You can customize the behavior using command-line arguments. For example:

   ```bash
   forex-engine --symbol EURUSD --trade_amount 10 --profit_target 5 --loss_limit 2 --log_level DEBUG
   ```

   Run `forex-engine --help` for a full list of available options.

   (For development or running directly from source without full installation, you can also use `python -m src.main`)

## Next Steps

With these fixes and enhancements in place, future development could focus on:

1. Multi-timeframe analysis (combining different timeframes for more robust signals)
2. Decision memory module (learning from past trades and system events)
3. Comprehensive backtesting framework (testing strategies against historical data)
4. Advanced performance metrics and analytics
5. User interface improvements (better visualization and control)
