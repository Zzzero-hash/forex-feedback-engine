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
    engine        = DecisionEngine(api_key=cfg.openai_api_key)
    broker_api    = BrokerAPI(ssid=cfg.po_ssid, demo=cfg.enable_demo_mode)
    feedback_loop = FeedbackLoop(database_url=cfg.database_url)

    # Start the trading system
    while True:
        # 1) Fetch API data
        spot_quote  = data_feed.get_quote()
        otc_candle  = otc_feed.get_latest_candle("SYMBOL", cfg.otc_interval)

        # 2) Ask LLM for a decision
        decision = engine.decide(spot_quote, otc_candle)

        # 3) Execute trade if valid CALL/PUT
        if decision.action in ("CALL", "PUT"):
            broker_api.execute_trade(decision)

        # 4) Log feedback & update strategy
        feedback_loop.track(decision)

        # 5) Pause until next iteration
        time.sleep(cfg.screen_interval)

if __name__ == "__main__":
    main()