# Feedback Loop Trading System

This project is a feedback-loop driven trading system designed for binary options trading. It integrates real-time market data sources (e.g., Alpha Vantage, Pocket Option OTC feed) and uses an LLM-based decision engine with configurable risk management.

## Project Structure

```plaintext
feedback_loop_trading_app
├── src
│   ├── data
│   │   ├── data_feed.py        # Handles real-time market data (Alpha Vantage)
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
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key
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