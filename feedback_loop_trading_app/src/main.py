from src.data.data_feed import DataFeed
from src.data.otc_feed import OTCFeed
from src.ocr.capture import Capture
from src.ocr.analyzer import Analyzer
from src.decision.llm_engine import LLMEngine
from src.execution.broker_api import BrokerAPI
from src.feedback.feedback_loop import FeedbackLoop
from src.config import Config

def main():
    # Initialize components
    data_feed = DataFeed()
    otc_feed = OTCFeed()
    capture = Capture()
    analyzer = Analyzer()
    llm_engine = LLMEngine()
    broker_api = BrokerAPI()
    feedback_loop = FeedbackLoop()

    # Start the trading system
    while True:
        # Fetch market data
        market_data = data_feed.get_data()
        otc_data = otc_feed.get_otc_data()

        # Capture and analyze screen data
        screenshot = capture.take_screenshot()
        trading_info = analyzer.process_image(screenshot)

        # Make a trading decision
        decision = llm_engine.make_decision(market_data, otc_data, trading_info)

        # Execute the trade
        if decision:
            broker_api.execute_trade(decision)

        # Log the outcome and adjust strategy
        feedback_loop.track_outcome(decision)

if __name__ == "__main__":
    main()