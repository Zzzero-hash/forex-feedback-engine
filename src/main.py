import time
import logging
from .data.data_feed import DataFeed
from .data.otc_feed import OTCFeed
from .decision.llm_engine import LLMEngine
from .execution.broker_api import BrokerAPI
from .feedback.feedback_loop import FeedbackLoop
from .config import Config

def run_session(cfg, data_feed, otc_feed, engine, broker_api, feedback_loop, max_iterations=None):
    """
    Run the trading loop. Optionally stop after max_iterations or session-end conditions.
    Returns the trade history.
    """
    iteration = 0
    while True:
        # 1) Fetch API data
        spot_quote  = data_feed.get_quote('EURUSD')
        otc_candle  = otc_feed.get_otc_candles('EURUSD', cfg.otc_interval)

        # Log the current trade history before sending to LLM
        logging.debug(f"MAIN_LOOP: Current feedback_loop.trade_history: {feedback_loop.trade_history}")

        # 2) Ask LLM for a decision
        decision = engine.get_decision(spot_quote, feedback_loop.trade_history)
        logging.info(f"LLM decision: {decision}") # Added log to see the decision before trade execution

        # 3) Execute trade if valid CALL/PUT
        if decision == "CALL" or decision == "PUT": # Modified condition
            logging.info(f"Executing trade based on LLM decision: {decision}") # Added log
            trade_id = broker_api.place_trade('EURUSD', cfg.trade_amount, decision, cfg.otc_interval)
            if trade_id: # Ensure trade_id is not None (e.g. if broker API failed)
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
        logging.debug("MAIN_LOOP: Waiting for 60 seconds before next iteration...")
        time.sleep(60) # Add a 60-second delay

    return feedback_loop.trade_history

def main():
    # Initialize components
    cfg = Config()
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
    # Configure logging
    logging.basicConfig(level=cfg.log_level)
    data_feed     = DataFeed(api_key=cfg.polygon_api_key)
    otc_feed      = OTCFeed()
    engine        = LLMEngine(api_key=cfg.openai_api_key)
    broker_api    = BrokerAPI(ssid=cfg.po_ssid)
    feedback_loop = FeedbackLoop(database_url=cfg.database_url)

    # Run session (infinite unless session-end reached)
    run_session(cfg, data_feed, otc_feed, engine, broker_api, feedback_loop)

if __name__ == "__main__":
    main()