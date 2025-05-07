import time
from data.data_feed import DataFeed
from data.otc_feed import OTCFeed
from decision.llm_engine import LLMEngine
from execution.broker_api import BrokerAPI
from feedback.feedback_loop import FeedbackLoop
from config import Config

def main():
    # Initialize components
    cfg = Config()
    data_feed     = DataFeed(api_key=cfg.alpha_vantage_api_key)
    otc_feed      = OTCFeed()
    engine        = LLMEngine(api_key=cfg.openai_api_key)
    broker_api    = BrokerAPI(ssid=cfg.po_ssid)
    feedback_loop = FeedbackLoop(database_url=cfg.database_url)

    # Start the trading system
    while True:
        # 1) Fetch API data
        spot_quote  = data_feed.get_quote('EURUSD')
        otc_candle  = otc_feed.get_otc_candles('EURUSD', cfg.otc_interval)

        # 2) Ask LLM for a decision
        decision = engine.get_decision(spot_quote, feedback_loop.trade_history)

        # 3) Execute trade if valid CALL/PUT
        if decision in ("CALL", "PUT"):
            # Place trade and record outcome
            trade_id = broker_api.place_trade('EURUSD', cfg.trade_amount, decision, cfg.otc_interval)
            outcome = broker_api.check_trade_result(trade_id)
            feedback_loop.record_trade_outcome(decision, outcome)

        # 4) Log feedback & update strategy
        # Strategy adjustment can be triggered based on recent performance
        feedback_loop.adjust_strategy()

        # 5) Pause until next iteration
        time.sleep(cfg.screen_interval)

if __name__ == "__main__":
    main()