# Feedback Loop Trading System

This project is a feedback-loop driven trading system designed for binary options trading. It integrates real-time market data sources (e.g., Pocket Option OTC feed) and uses an LLM-based decision engine with configurable risk management.

## Project Structure

```plaintext
feedback_loop_trading_app
├── src
│   ├── data
│   │   ├── data_feed.py        # Handles real-time market data
│   │   └── otc_feed.py         # Manages OTC data via PocketOption API
│   ├── decision
│   │   ├── llm_engine.py       # Interfaces with the LLM API for trading decisions
│   │   └── prompt_config.py    # Configurable LLM prompt templates & thresholds
│   ├── execution
│   │   └── broker_api.py       # Manages trade execution through PocketOption API
│   ├── feedback
│   │   ├── models.py           # SQLAlchemy ORM models for persistence
│   │   └── feedback_loop.py    # Records trade outcomes, risk management, strategy adjustment
│   ├── config.py               # Loads environment variables and risk settings
│   └── main.py                 # Entry point; run_session() implements the trading loop
├── tests                       # Unit and integration tests
├── Dockerfile                  # Defines Docker image
├── requirements.txt            # Python dependencies
└── .env.example                # Example environment variables
```

## Setup Instructions

1. Clone the repository:
   ```bash
   git clone https://github.com/Zzzero-hash/forex-feedback-engine.git
   cd feedback_loop_trading_app
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Unix/macOS
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure environment variables:
   Copy `.env.example` to `.env` and fill in your API keys and session ID.

## Environment Variables

Set the following in your `.env` file:

```dotenv
OPENAI_API_KEY=your_openai_api_key
PO_SSID=your_pocket_option_session_id
POLYGON_API_KEY=your_polygon_api_key 
DATABASE_URL=sqlite:///trading_logs.db
LOG_LEVEL=INFO
INITIAL_BALANCE=1000.0       # Starting account balance for risk calculations
PROFIT_TARGET_PCT=5.0        # End session when profit reaches this percent
LOSS_LIMIT_PCT=2.0           # End session when loss reaches this percent
OTC_INTERVAL=60              # Seconds per OTC candle
SCREEN_INTERVAL=1.0          # Seconds between iterations
TRADE_AMOUNT=1.0             # Amount per trade
MAX_DAILY_LOSS=100.0         # (Optional) daily loss cap
DEMO_MODE=True               # Use dummy API implementations for testing
``` 

## Usage

### Local Run

Run the trading application:
```bash
python src/main.py
```

### Demo Mode

To run a short demo session (e.g., 10 iterations), add a small wrapper or call `run_session()` directly in a script, for example:
```python
from src.main import run_session, Config, DataFeed, OTCFeed, LLMEngine, BrokerAPI, FeedbackLoop

cfg = Config()
# build components...
trades = run_session(cfg, DataFeed(cfg.alpha_vantage_api_key), OTCFeed(), LLMEngine(cfg.openai_api_key), BrokerAPI(cfg.po_ssid), FeedbackLoop(cfg.database_url), max_iterations=10)
print(trades)
```

### Docker

Build and run the Docker image:
```bash
docker build -t feedback-trading .
docker run --env-file .env feedback-trading
```

## Testing

Run all tests:
```bash
pytest -q
```

## Contributing

Contributions are welcome! Please open an issue or pull request.

## License

This project is licensed under the MIT License.

## Next Steps / TODO (as of May 8, 2025)

1.  **Resolve `pocketoptionapi` Installation:**
    *   Ensure the `pocketoptionapi` library is correctly installed in the Python environment being used (e.g., `pip install pocketoptionapi`).
    *   Verify that `from pocketoptionapi.stable_api import PocketOption` in `src/execution/broker_api.py` no longer causes an import error and that the script does not fall back to the dummy API implementation.
2.  **Test Live Demo Trading:**
    *   Obtain a fresh `PO_SSID` from your Pocket Option **demo account**.
    *   Update the `PO_SSID` in the `.env` file.
    *   Run `tests/test_broker_demo_trade.py` to confirm that trades are actually placed and visible on the Pocket Option demo platform.
3.  **Refine Data Aggregation for LLM:**
    *   Currently, the main loop fetches 1-minute data and then waits 60 seconds. The LLM is prompted for a 5-minute prediction.
    *   Consider modifying the data fetching/aggregation logic to provide the LLM with more relevant data for a 5-minute prediction (e.g., the last 3-5 one-minute candles).
4.  **Review OTC Feed Integration:**
    *   The `otc_feed.py` is present but its data (`otc_candle`) isn't explicitly used in the `engine.get_decision` call in `main.py`. Determine if and how this data should be incorporated into the LLM prompt.
5.  **Monitor Costs:**
    *   Keep an eye on LLM API usage costs, especially if the polling frequency is increased or more complex prompts are used.