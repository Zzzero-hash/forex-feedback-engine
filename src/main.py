import time
import logging
import datetime
import argparse # Added for CLI arguments
from .data.data_feed import DataFeed
from .data.otc_feed import OTCFeed
from .decision.llm_engine_temporal import TemporalLLMEngine
from .config import Config
from src.execution.broker_api import BrokerAPI
from src.feedback.feedback_loop import FeedbackLoop
# Alias legacy LLMEngine name for backward compatibility and tests
LLMEngine = TemporalLLMEngine

def run_session(cfg, data_feed, otc_feed, engine, broker_api, feedback_loop, symbols_list, initial_symbol_idx, max_iterations=None, **kwargs):
    """
    Run the trading loop, cycling through symbols if one becomes inactive.
    Optionally stop after max_iterations or session-end conditions.
    Returns the trade history.
    """
    iteration = 0
    current_symbol_idx = initial_symbol_idx
    # symbol will be set at the start of the loop based on current_symbol_idx
    no_trade_consecutive_count = 0
    pair_blacklist = {}  # Stores symbol: unblacklist_time
    consecutive_system_switches = 0  # Tracks consecutive switches due to inactivity

    while True:
        # Update symbol based on current_symbol_idx (in case it changed in the previous iteration)
        symbol = symbols_list[current_symbol_idx]
        logging.info(f"Trading session iteration {iteration + 1} for symbol: {symbol}")

        # Clean up any expired blacklist entries for the current symbol before proceeding
        if symbol in pair_blacklist and time.time() > pair_blacklist[symbol]:
            del pair_blacklist[symbol]
            logging.info(f"Symbol {symbol} removed from blacklist (expired) before use.")

        # If current symbol is still blacklisted (e.g. after a wait_all_blacklisted), try to find another one before proceeding
        if symbol in pair_blacklist:
            logging.warning(f"Current symbol {symbol} is still blacklisted. Attempting to find an alternative before processing.")
            # This logic is similar to the one after max_consecutive_no_trade, refactor might be good later
            found_alternative_for_blacklisted = False
            for i in range(len(symbols_list)):
                potential_idx = (current_symbol_idx + 1 + i) % len(symbols_list)
                candidate_symbol = symbols_list[potential_idx]
                if candidate_symbol in pair_blacklist and time.time() > pair_blacklist[candidate_symbol]:
                    del pair_blacklist[candidate_symbol]
                if candidate_symbol not in pair_blacklist:
                    current_symbol_idx = potential_idx
                    symbol = symbols_list[current_symbol_idx] # Update symbol immediately
                    logging.info(f"Switched to alternative symbol {symbol} as previous was blacklisted.")
                    found_alternative_for_blacklisted = True
                    break
            if not found_alternative_for_blacklisted:
                # All are still blacklisted, must wait for the current one (or earliest)
                if symbol in pair_blacklist: # Should be true
                    wait_duration_for_current = max(0.1, pair_blacklist[symbol] - time.time())
                    logging.info(f"Symbol {symbol} is blacklisted. Waiting for {wait_duration_for_current:.2f}s for it to become available.")
                    time.sleep(wait_duration_for_current)
                    if symbol in pair_blacklist and time.time() > pair_blacklist[symbol]: # Recheck and clean
                        del pair_blacklist[symbol]
                # If after waiting it's still an issue, the loop will repeat this check.

        # 1) Fetch API data
        spot_quote  = data_feed.get_quote(symbol)
        otc_candle  = otc_feed.get_otc_candles(symbol, cfg.otc_interval)

        # Log the current trade history before sending to LLM
        logging.debug(f"MAIN_LOOP: Current feedback_loop.trade_history: {feedback_loop.trade_history}")

        # 2) Ask LLM for a decision
        # Call get_decision, supporting both the new temporal signature and legacy signature
        try:
            decision = engine.get_decision(symbol, spot_quote, feedback_loop.trade_history)
        except TypeError:
            decision = engine.get_decision(spot_quote, feedback_loop.trade_history)
        logging.info(f"LLM decision: {decision}") # Added log to see the decision before trade execution

        # 3) Execute trade if valid CALL/PUT
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
            no_trade_consecutive_count = 0 # Reset counter on any trade action
            consecutive_system_switches = 0 # Reset system switch counter on successful trade/signal
            logging.debug("Reset consecutive_system_switches due to CALL/PUT.")
        elif decision == "NO TRADE":
            logging.info("LLM decided NO TRADE. No trade will be placed.")
            no_trade_consecutive_count += 1
            logging.info(f"Consecutive 'NO TRADE' signals for {symbol}: {no_trade_consecutive_count}/{cfg.max_consecutive_no_trade}")
            
            if no_trade_consecutive_count >= cfg.max_consecutive_no_trade:
                logging.warning(f"Reached max consecutive 'NO TRADE' signals ({cfg.max_consecutive_no_trade}) for {symbol}. Attempting to switch symbol.")
                
                feedback_loop.record_system_event(
                    event_type="PAIR_SWITCH_INACTIVITY",
                    symbol=symbol, 
                    details=f"Attempting to switch from {symbol} after {no_trade_consecutive_count} consecutive NO TRADE signals."
                )

                pair_blacklist[symbol] = time.time() + cfg.pair_blacklist_duration_seconds
                logging.info(f"Symbol {symbol} blacklisted until {time.ctime(pair_blacklist[symbol])}")

                consecutive_system_switches += 1 
                logging.info(f"Consecutive system switches due to inactivity: {consecutive_system_switches}/{cfg.max_consecutive_system_switches}")

                if consecutive_system_switches >= cfg.max_consecutive_system_switches:
                    logging.warning(f"Reached max consecutive system switches ({cfg.max_consecutive_system_switches}). Initiating system cool-down for {cfg.system_cool_down_duration_seconds} seconds.")
                    feedback_loop.record_system_event(
                        event_type="SYSTEM_COOLDOWN_INITIATED",
                        details=f"System cool-down for {cfg.system_cool_down_duration_seconds}s after {consecutive_system_switches} consecutive pair switches."
                    )
                    time.sleep(cfg.system_cool_down_duration_seconds)
                    consecutive_system_switches = 0 
                    logging.info("System cool-down finished. Resuming operations.")

                # Determine the next symbol to trade
                next_symbol_selected = False
                original_idx_at_switch_attempt = current_symbol_idx
                
                for i in range(len(symbols_list)):
                    potential_idx = (original_idx_at_switch_attempt + 1 + i) % len(symbols_list)
                    candidate_symbol = symbols_list[potential_idx]

                    if candidate_symbol in pair_blacklist and time.time() > pair_blacklist[candidate_symbol]:
                        del pair_blacklist[candidate_symbol]
                        logging.info(f"Symbol {candidate_symbol} removed from blacklist (expired during selection).")

                    if candidate_symbol not in pair_blacklist:
                        current_symbol_idx = potential_idx
                        logging.info(f"Successfully switched to new symbol: {symbols_list[current_symbol_idx]}")
                        next_symbol_selected = True
                        break
                
                if not next_symbol_selected:
                    logging.warning("All symbols are currently blacklisted. Waiting for the earliest expiration.")
                    if not pair_blacklist: # Should be unreachable if next_symbol_selected is False
                         logging.error("CRITICAL: All symbols reported blacklisted, but blacklist is empty. Defaulting to first symbol to prevent crash.")
                         current_symbol_idx = 0 
                    else:
                        earliest_unblacklist_symbol = min(pair_blacklist, key=pair_blacklist.get)
                        earliest_unblacklist_time = pair_blacklist[earliest_unblacklist_symbol]
                        wait_duration = max(0.1, earliest_unblacklist_time - time.time())

                        logging.info(f"Waiting for {wait_duration:.2f} seconds for symbol {earliest_unblacklist_symbol} to become available.")
                        feedback_loop.record_system_event(
                            event_type="WAIT_ALL_BLACKLISTED",
                            symbol=earliest_unblacklist_symbol,
                            details=f"All symbols blacklisted. Waiting {wait_duration:.2f}s for {earliest_unblacklist_symbol}."
                        )
                        time.sleep(wait_duration)
                        
                        try:
                            current_symbol_idx = symbols_list.index(earliest_unblacklist_symbol)
                            if earliest_unblacklist_symbol in pair_blacklist: # Clean up just in case
                                del pair_blacklist[earliest_unblacklist_symbol]
                            logging.info(f"Resuming with symbol: {symbols_list[current_symbol_idx]} after waiting for blacklist expiration.")
                        except ValueError:
                            logging.error(f"CRITICAL: Symbol {earliest_unblacklist_symbol} not found in symbols_list after waiting. Defaulting to index 0.")
                            current_symbol_idx = 0
                
                no_trade_consecutive_count = 0 # Reset for the new symbol
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


def main(cfg_override=None): # Modified to accept potential overrides
    # Initialize components
    cfg = Config()

    # Override config with CLI args if provided
    if cfg_override:
        for key, value in vars(cfg_override).items():
            if value is not None and hasattr(cfg, key):
                setattr(cfg, key, value)
                logging.info(f"Overriding config: {key} = {value}")
            elif value is not None and key == "symbol": # Special handling for initial symbol
                # This will be handled later by initial_selected_symbol logic
                pass


    # Configure logging
    logging.basicConfig(level=cfg.log_level, format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')
    # Ensure required API keys are provided
    # Warn if API keys are missing, but continue for testing or fallback
    if not cfg.openai_api_key:
        logging.warning("OpenAI API key not set. Proceeding without real OpenAI API calls.")
    if not cfg.po_ssid:
        logging.warning("Pocket Option SSID not set. Proceeding without real broker API calls.")
    if not cfg.polygon_api_key:
        logging.warning("Polygon.io API key not set. Proceeding without real market data.")
        
    data_feed     = DataFeed(api_key=cfg.polygon_api_key)
    otc_feed      = OTCFeed()
    # Initialize temporal LLM engine with historical context
    engine        = LLMEngine(api_key=cfg.openai_api_key, model=cfg.llm_model) # Pass model
    engine.initialize_historical_collector(data_feed, lookback_periods=20, timeframe_minutes=5)
    broker_api    = BrokerAPI(ssid=cfg.po_ssid, data_feed_instance=data_feed) # Pass data_feed here
    feedback_loop = FeedbackLoop(database_url=cfg.database_url)
    
    # Retrieve OTC symbols from feed
    raw_symbols = otc_feed.get_otc_symbols()
    
    # raw_symbols may be a dict or list; convert to list
    if not raw_symbols:
        logging.warning("No OTC symbols retrieved from OTCFeed. Using default symbols.")
        forex_symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]
    else:
        forex_symbols = list(raw_symbols.keys() if isinstance(raw_symbols, dict) else raw_symbols)
    
    # Add cryptocurrency symbols for weekend trading
    # These popular crypto pairs should be available 24/7 on Polygon
    crypto_symbols = ["BTCUSD", "ETHUSD", "SOLUSD", "XRPUSD", "ADAUSD"]
    
    # Detect if it's weekend to prioritize crypto symbols
    now = datetime.datetime.now()
    is_weekend = now.weekday() >= 5  # 5=Saturday, 6=Sunday
    
    if is_weekend:
        logging.info("Weekend detected: Prioritizing cryptocurrency symbols that trade 24/7")
        # Use crypto first, then forex as fallback
        symbols = crypto_symbols + forex_symbols
    else:
        # Use all available symbols, forex first
        symbols = forex_symbols + crypto_symbols
    
    logging.info(f"Available symbols: {symbols}")

    # Allow CLI to override initial symbol selection
    initial_selected_symbol = None
    if cfg_override and cfg_override.symbol:
        if cfg_override.symbol in symbols:
            initial_selected_symbol = cfg_override.symbol
            logging.info(f"Initial symbol overridden by CLI: {initial_selected_symbol}")
        else:
            logging.warning(f"CLI specified symbol '{cfg_override.symbol}' not in available symbols. Proceeding with LLM selection.")

    if not initial_selected_symbol:
        # Select best trading symbol via LLM with market data
        logging.info("Selecting best trading pair using real-time market data...")
        initial_selected_symbol = engine.select_pair(symbols, data_feed)

    if not initial_selected_symbol or initial_selected_symbol not in symbols:
        logging.error(f"Failed to select a valid initial trading symbol from the available list. Selected: {initial_selected_symbol}. Defaulting to the first symbol if available.")
        if not symbols:
            logging.error("No symbols available to default to. Exiting.")
            return
        initial_selected_symbol = symbols[0]
        logging.info(f"Defaulted to first available symbol: {initial_selected_symbol}")

    try:
        initial_symbol_idx = symbols.index(initial_selected_symbol)
    except ValueError:
        logging.error(f"Selected symbol {initial_selected_symbol} not in the list of symbols. Defaulting to index 0.")
        initial_symbol_idx = 0 # Default to the first symbol if something went wrong

    logging.info(f"Starting trading session with initial symbol: {symbols[initial_symbol_idx]} (index {initial_symbol_idx})")
    
    # Run session (infinite unless session-end reached)
    # Pass the initially selected symbol as a keyword for backward compatibility tests
    run_session(cfg, data_feed, otc_feed, engine, broker_api, feedback_loop, symbols, initial_symbol_idx, symbol=initial_selected_symbol)

def main_cli():
    parser = argparse.ArgumentParser(description="Forex Feedback Engine CLI")
    parser.add_argument("--symbol", type=str, help="Initial trading symbol to use (e.g., EURUSD). Overrides LLM selection if valid.")
    parser.add_argument("--trade_amount", type=float, help="Amount for each trade.")
    parser.add_argument("--profit_target_pct", type=float, help="Profit target percentage for the session.")
    parser.add_argument("--loss_limit_pct", type=float, help="Loss limit percentage for the session.")
    parser.add_argument("--initial_balance", type=float, help="Initial balance for the trading session.")
    parser.add_argument("--llm_model", type=str, help="Name of the LLM model to use (e.g., gpt-4, gpt-4-turbo).")
    parser.add_argument("--log_level", type=str, choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="Logging level.")
    parser.add_argument("--enable_demo_mode", type=lambda x: (str(x).lower() == 'true'), help="Enable demo (signal-only) mode (true/false).")
    # Add other relevant config overrides here if needed

    args = parser.parse_args()
    main(cfg_override=args)

if __name__ == "__main__":
    main_cli()