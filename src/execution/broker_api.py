import random
import logging
import uuid
import time

logger = logging.getLogger(__name__)

class BrokerAPI:
    """
    Simulated BrokerAPI for trading.
    Determines win/loss based on actual price movement from entry over a set duration,
    using a provided data_feed instance.
    """
    def __init__(self, ssid, data_feed_instance):
        self.connected = True
        self.active_trades = {}  # Stores trade_id: {details}
        self.simulated_wins = 0
        self.simulated_losses = 0
        self.data_feed = data_feed_instance
        if self.data_feed is None:
            logger.error("BrokerAPI initialized WITHOUT a data_feed_instance. Price fetching will fail.")
        logger.info(f"Simulated BrokerAPI initialized. SSID (dummy): {ssid}. DataFeed connected: {self.data_feed is not None}")

    def connect(self):
        logger.info("Simulated BrokerAPI: connect() called.")
        return True

    def subscribe_candles(self, asset, timeframe):
        logger.info(f"Simulated BrokerAPI: subscribe_candles({asset}, {timeframe}) called.")
        pass

    def place_trade(self, asset: str, amount: float, direction: str, duration_seconds: int) -> str:
        """
        Simulates placing a trade. Fetches current price as entry_price.
        Duration is in seconds.
        """
        trade_id = f"sim_trade_{uuid.uuid4()}"
        
        entry_price = None
        if not self.data_feed:
            logger.error(f"Cannot place trade for {asset}: data_feed is not available.")
            # Potentially raise an error or return a specific failure indicator
            return f"sim_trade_failure_no_data_feed_{uuid.uuid4()}" 

        try:
            quote = self.data_feed.get_quote(asset)
            if quote and 'price' in quote and isinstance(quote['price'], (float, int)) and quote['price'] > 0:
                entry_price = float(quote['price'])
            else:
                logger.warning(f"Could not get a valid entry price for {asset} from data_feed. Quote: {quote}. Trade will use a placeholder price and likely result in an error or unrealistic outcome.")
                entry_price = 1.0 # Fallback, though this scenario should be handled better
        except Exception as e:
            logger.error(f"Error fetching entry price for {asset} from data_feed: {e}. Trade will use a placeholder price.")
            entry_price = 1.0 # Fallback

        self.active_trades[trade_id] = {
            "asset": asset,
            "amount": amount,
            "direction": direction,
            "duration_seconds": duration_seconds,
            "open_time": time.time(),
            "entry_price": entry_price
        }
        logger.info(f"Simulated trade placed: ID={trade_id}, Asset={asset}, Amount={amount}, Direction={direction}, Duration={duration_seconds}s, EntryPrice={entry_price or 'N/A'}")
        return trade_id

    def check_trade_result(self, trade_id: str) -> bool:
        """
        Checks a trade result after its duration by fetching the current price.
        Waits for the trade duration to elapse before checking.
        """
        if trade_id not in self.active_trades:
            logger.error(f"Simulated BrokerAPI: Trade ID {trade_id} not found for checking result.")
            return False # Assume loss if ID is unknown or already processed

        trade_info = self.active_trades[trade_id] # Keep it in active_trades until outcome is determined
        
        entry_price = trade_info["entry_price"]
        direction = trade_info["direction"]
        asset = trade_info["asset"]
        open_time = trade_info["open_time"]
        duration_seconds = trade_info["duration_seconds"]

        if entry_price is None or entry_price <= 0: # Check if entry price was valid
            logger.error(f"Trade ID {trade_id} for {asset} has invalid entry price {entry_price}. Marking as loss.")
            self.active_trades.pop(trade_id, None) # Remove from active trades
            self.simulated_losses += 1
            return False

        expiry_time = open_time + duration_seconds
        current_time = time.time()
        
        wait_time = expiry_time - current_time
        if wait_time > 0:
            logger.info(f"Waiting {wait_time:.2f} seconds for trade {trade_id} ({asset}) to expire...")
            time.sleep(wait_time)
        
        exit_price = None
        if not self.data_feed:
            logger.error(f"Cannot check trade result for {trade_id} ({asset}): data_feed is not available for exit price.")
            self.active_trades.pop(trade_id, None)
            self.simulated_losses += 1 # Assume loss if we can't get exit price
            return False

        try:
            quote = self.data_feed.get_quote(asset)
            if quote and 'price' in quote and isinstance(quote['price'], (float, int)) and quote['price'] > 0:
                exit_price = float(quote['price'])
            else:
                logger.warning(f"Could not get a valid exit price for {trade_id} ({asset}) from data_feed. Quote: {quote}. Marking as loss.")
                self.active_trades.pop(trade_id, None)
                self.simulated_losses += 1
                return False
        except Exception as e:
            logger.error(f"Error fetching exit price for {trade_id} ({asset}) from data_feed: {e}. Marking as loss.")
            self.active_trades.pop(trade_id, None)
            self.simulated_losses += 1
            return False

        # Now remove from active_trades as we are about to determine outcome
        self.active_trades.pop(trade_id, None) 

        outcome_is_win = False
        if direction == "CALL":
            if exit_price > entry_price:
                outcome_is_win = True
        elif direction == "PUT":
            if exit_price < entry_price:
                outcome_is_win = True
        
        # If exit_price == entry_price, it's a loss for binary options.

        if outcome_is_win:
            self.simulated_wins += 1
            logger.info(f"Simulated trade result for ID {trade_id} ({asset}, {direction}): WIN. Entry: {entry_price:.5f}, Exit: {exit_price:.5f}")
        else:
            self.simulated_losses += 1
            logger.info(f"Simulated trade result for ID {trade_id} ({asset}, {direction}): LOSS. Entry: {entry_price:.5f}, Exit: {exit_price:.5f}")
            
        return outcome_is_win

    def get_simulated_stats(self):
        return {
            "wins": self.simulated_wins,
            "losses": self.simulated_losses,
            "total": self.simulated_wins + self.simulated_losses
        }

    def disconnect(self):
        logger.info("Simulated BrokerAPI: disconnect() called.")
        pass