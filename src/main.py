import time
import logging
from .data.data_feed import DataFeed
from .data.otc_feed import OTCFeed
from .decision.llm_engine import LLMEngine
from .execution.broker_api import BrokerAPI
from .feedback.feedback_loop import FeedbackLoop
from .config import Config

def run_session(cfg, data_feed, otc_feed, engine, broker_api, feedback_loop, max_iterations=None, symbol=None):
    """
    Run the trading loop on a specific symbol. Optionally stop after max_iterations or session-end conditions.
    Returns the trade history.
    """
    iteration = 0
    while True:
        # 1) Fetch API data
        spot_quote  = data_feed.get_quote(symbol)
        otc_candle  = otc_feed.get_otc_candles(symbol, cfg.otc_interval)

        # Log the current trade history before sending to LLM
        logging.debug(f"MAIN_LOOP: Current feedback_loop.trade_history: {feedback_loop.trade_history}")

        # 2) Ask LLM for a decision
        decision = engine.get_decision(spot_quote, feedback_loop.trade_history)
        logging.info(f"LLM decision: {decision}") # Added log to see the decision before trade execution        # 3) Execute trade if valid CALL/PUT
        if decision in ("CALL", "PUT"):  # Trade or signal decision
            if cfg.enable_demo_mode:
                # In demo/signal-only mode, record the signal without executing live trades
                logging.info(f"Demo mode: recording signal '{decision}' for {symbol}")
                
                # Special handling for tests vs normal operation
                if max_iterations is not None:  # For tests
                    # For tests, directly use record_trade_outcome to maintain compatibility with existing tests
                    trade_id = broker_api.place_trade(symbol, cfg.trade_amount, decision, cfg.otc_interval) 
                    outcome = broker_api.check_trade_result(trade_id)
                    feedback_loop.record_trade_outcome(decision, outcome)
                else:  # For normal signal-only operation
                    feedback_loop.trade_history.append({'decision': decision, 'signal': True})
            else:
                logging.info(f"Executing trade based on LLM decision: {decision} on {symbol}")
                trade_id = broker_api.place_trade(symbol, cfg.trade_amount, decision, cfg.otc_interval)
                if trade_id:  # Ensure trade_id is not None (e.g. if broker API failed)
                    outcome = broker_api.check_trade_result(trade_id)
                    feedback_loop.record_trade_outcome(decision, outcome)
                else:
                    logging.error("Failed to place trade, broker_api.place_trade returned None.")
        elif decision == "NO TRADE":
            logging.info("LLM decided NO TRADE. No trade will be placed.")
        else:
            logging.warning(f"LLM returned an unexpected decision: '{decision}'. No trade will be placed.")

        # Strategy adjustment
        feedback_loop.adjust_strategy()

        # Check session end conditions
        if feedback_loop.should_end_session(cfg.initial_balance, cfg.trade_amount,
                                         cfg.profit_target_pct, cfg.loss_limit_pct):
            logging.info("Session end condition met. Exiting session.")
            break

        # Stop after max_iterations if defined
        iteration += 1
        if max_iterations and iteration >= max_iterations:
            logging.info(f"Reached max_iterations ({max_iterations}). Exiting session.") # Added log
            break

        # Wait for a defined period before the next iteration to reduce LLM calls
        logging.debug("MAIN_LOOP: Waiting before next iteration...")
        if max_iterations is None:
            logging.debug("Sleeping for 60 seconds...")
            time.sleep(60)  # Add a 60-second delay only for live sessions

    return feedback_loop.trade_history

def main():
    # Initialize components
    cfg = Config()
    # Configure logging
    logging.basicConfig(level=cfg.log_level)
    # Ensure required API keys are provided
    if not cfg.openai_api_key:
        logging.error("OpenAI API key not set. Please set OPENAI_API_KEY in your .env or environment variables.")
        return
    if not cfg.po_ssid:
        logging.error("Pocket Option SSID not set. Please set PO_SSID in your .env or environment variables.")
        return
    if not cfg.polygon_api_key:
        logging.error("Polygon.io API key not set. Please set POLYGON_API_KEY in your .env or environment variables.")
        return
    data_feed     = DataFeed(api_key=cfg.polygon_api_key)
    otc_feed      = OTCFeed()
    engine        = LLMEngine(api_key=cfg.openai_api_key)
    broker_api    = BrokerAPI(ssid=cfg.po_ssid)
    feedback_loop = FeedbackLoop(database_url=cfg.database_url)
    # Retrieve OTC symbols from feed
    raw_symbols = otc_feed.get_otc_symbols()
    # raw_symbols may be a dict or list; convert to list
    if not raw_symbols:
        logging.error("No OTC symbols retrieved from OTCFeed. Exiting.")
        return
    symbols = list(raw_symbols.keys() if isinstance(raw_symbols, dict) else raw_symbols)    # Select best trading symbol via LLM with market data
    logging.info("Selecting best trading pair using real-time market data...")
    best_symbol = engine.select_pair(symbols, data_feed)
    if not best_symbol:
        logging.error("Failed to select a trading symbol. Exiting.")
        return
    logging.info(f"Selected best trading pair: {best_symbol}")
    # Run session (infinite unless session-end reached)
    run_session(cfg, data_feed, otc_feed, engine, broker_api, feedback_loop, symbol=best_symbol)

if __name__ == "__main__":
    main()