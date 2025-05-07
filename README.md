# Feedback Loop Trading System

This project is a feedback-loop driven trading system designed for binary options trading. It integrates real-time market data from various exchanges and utilizes screen capture analysis to enhance trading decisions. The system is built using Python and is containerized with Docker for easy deployment and portability.

## Project Structure

```
feedback_loop_trading_app
├── src
│   ├── data
│   │   ├── data_feed.py        # Handles real-time market data integration
│   │   └── otc_feed.py         # Manages over-the-counter market data
│   ├── ocr
│   │   ├── capture.py          # Responsible for taking screenshots
│   │   └── analyzer.py         # Processes images using OCR
│   ├── decision
│   │   ├── llm_engine.py       # Interfaces with the LLM API for trading decisions
│   │   └── prompt_config.py     # Configuration for LLM prompts
│   ├── execution
│   │   └── broker_api.py       # Manages trade execution through the broker's API
│   ├── feedback
│   │   └── feedback_loop.py     # Tracks trade outcomes and adjusts strategies
│   ├── config.py               # Configuration settings for the application
│   └── main.py                 # Entry point of the application
├── tests
│   ├── test_data_feed.py       # Unit tests for data feed functionality
│   ├── test_capture.py         # Unit tests for screen capture functionality
│   └── test_feedback.py        # Unit tests for feedback loop functionality
├── Dockerfile                   # Defines the Docker image for the application
├── docker-compose.yml           # Orchestrates the services needed for the application
├── requirements.txt             # Lists the Python dependencies required
└── .env.example                 # Example of environment variables needed
```

## Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd feedback_loop_trading_app
   ```

2. **Create a Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**
   Copy `.env.example` to `.env` and fill in the required variables.

5. **Build and Run the Docker Container**
   ```bash
   docker-compose up --build
   ```

## Usage

- The application will start automatically and begin trading based on the configured strategies.
- Monitor the logs for trade outcomes and performance metrics.

## Testing

To run the tests, ensure the virtual environment is activated and execute:
```bash
pytest tests/
```

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.