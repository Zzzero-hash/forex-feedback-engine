import os
import time
import logging
import traceback # Added for detailed exception logging
import numpy as np
from datetime import datetime, timedelta

# Get a specific logger for this module
logger = logging.getLogger(__name__)

# Try to import the OpenAI library and determine its version
try:
    import openai
    try:
        # Check if we're using OpenAI v1.x (newer)
        from openai import OpenAI
        OPENAI_V1 = True
        logger.info("Using OpenAI v1.x API")
        try:
            from openai import RateLimitError
        except ImportError:
            class RateLimitError(Exception): # type: ignore
                pass
    except ImportError:
        # We're using OpenAI v0.x (older)
        OPENAI_V1 = False
        logger.info("Using OpenAI v0.x API")
        try:
            from openai.error import RateLimitError # type: ignore
        except ImportError:
            class RateLimitError(Exception): # type: ignore
                pass
except ImportError:
    logger.error("OpenAI library not installed. Run 'pip install openai'")
    raise ImportError("OpenAI library not installed. Run 'pip install openai'")

class LLMEngine:
    def __init__(self, api_key, prompt_config=None, model="gpt-4-turbo-16k"):
        self.api_key = api_key
        self.model = model
        
        # Corrected f-string and use module-specific logger
        logger.info(f"API key provided: {'Yes' if self.api_key else 'No'}")
        
        if 'OPENAI_V1' in globals() and OPENAI_V1:
            self.client = OpenAI(api_key=self.api_key)
            logger.info(f"OpenAI version: {openai.__version__}")
        else:
            openai.api_key = self.api_key # type: ignore
            logger.info(f"OpenAI version: {openai.__version__}") # type: ignore
            
        from .prompt_config import PromptConfig
        self.prompt_config = prompt_config or PromptConfig()
        
    def get_decision(self, market_data, recent_trades):
        logger.debug(f"LLMEngine.get_decision called with market_data: {market_data}")
        logger.debug(f"LLMEngine.get_decision called with recent_trades: {recent_trades}")
        
        system_msg = self.prompt_config.get_system_prompt()
        user_content = (
            f"Market Data: {market_data}\\nRecent Trades: {recent_trades}"
        )
        max_retries = 3
        backoff = 1
        response = None # Initialize response
        api_timeout_seconds = 30 # Define a timeout for the API call

        for attempt in range(max_retries):
            try:
                # Use the configured model (default is gpt-4)
                current_model_to_use = self.model
                logger.debug(f"Attempting OpenAI API call with model: {current_model_to_use}, timeout: {api_timeout_seconds}s")

                # Attempt functional interface first (openai.ChatCompletion.create)
                try:
                    response = openai.ChatCompletion.create(
                        model=current_model_to_use,
                        messages=[
                            {"role": "system", "content": system_msg},
                            {"role": "user", "content": user_content}
                        ],
                        request_timeout=api_timeout_seconds
                    )
                except Exception:
                    # Fallback to new client interface if functional is unavailable or fails
                    response = self.client.chat.completions.create(
                        model=current_model_to_use,
                        messages=[
                            {"role": "system", "content": system_msg},
                            {"role": "user", "content": user_content}
                        ],
                        timeout=api_timeout_seconds
                    )
                 
                logger.debug(f"LLM API Raw Response object: {response}") 
                 
                if not response or not getattr(response, 'choices', None) or not response.choices:
                    logger.error("OpenAI API returned no completion or invalid choices structure.")
                    return "NO TRADE"
                break
            except RateLimitError:
                logger.warning(f"OpenAI rate limit hit on attempt {attempt + 1}/{max_retries}, retrying in {backoff} seconds...")
                if attempt < max_retries - 1:
                    time.sleep(backoff)
                    backoff *= 2
                else:
                    logger.error("OpenAI rate limit exceeded after all retries, defaulting to NO TRADE.")
                    return "NO TRADE"
            except openai.APITimeoutError as e: # Specific handling for timeouts
                logger.error(f"OpenAI API call timed out after {api_timeout_seconds} seconds on attempt {attempt + 1}/{max_retries}: {e}")
                logger.error(traceback.format_exc()) # Log full traceback
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {backoff} seconds...")
                    time.sleep(backoff)
                    backoff *= 2
                else:
                    logger.error("OpenAI API call failed due to timeout after all retries, defaulting to NO TRADE.")
                    return "NO TRADE"
            except Exception as e:
                logger.error(f"Error calling OpenAI API on attempt {attempt + 1}/{max_retries}: {e}")
                logger.error(traceback.format_exc()) # Log full traceback
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {backoff} seconds...")
                    time.sleep(backoff)
                    backoff *= 2
                else:
                    logger.error("Failed to call OpenAI API after all retries, defaulting to NO TRADE.")
                    return "NO TRADE"
        
        if not response or not getattr(response, 'choices', None) or not response.choices:
             logger.error("Failed to get a valid response from OpenAI API after retries (final check). Defaulting to NO TRADE.")
             return "NO TRADE"

        content = response.choices[0].message.content
        logger.debug(f"LLM decision raw content: '{content}'") # Log content before parsing
        return self._parse_response(content)

    def _parse_response(self, response_content):
        cleaned = response_content.strip().upper()  # Clean and uppercase
        # Check for NO TRADE first to handle cases where 'NO TRADE' appears
        if "NO TRADE" in cleaned:
            return "NO TRADE"
        # Check for CALL or PUT anywhere in the response
        if "CALL" in cleaned:
            return "CALL"
        if "PUT" in cleaned:
            return "PUT"
        # Fallback for unexpected responses
        logger.warning(f"LLM response '{response_content}' did not contain CALL, PUT, or NO TRADE after cleaning. Defaulting to NO TRADE.")
        return "NO TRADE"
        
    def _calculate_technical_indicators(self, data_feed, symbols):
        """
        Calculate technical indicators for each symbol to support pair selection
        
        Args:
            data_feed: DataFeed object to fetch price data
            symbols: List of symbols to analyze
            
        Returns:
            Dictionary with technical indicators for each symbol
        """
        logger.info("Calculating technical indicators for pair selection...")
        market_data = {}
        
        for symbol in symbols:
            try:
                # Get historical data for this symbol (last 20 minutes = 4 x 5-min candles)
                # In a real implementation, we would use actual historical data 
                # This simulates candles with price and timestamp from current data
                current_data = data_feed.get_quote(symbol)
                if not current_data or 'price' not in current_data:
                    logger.warning(f"Could not get price data for {symbol}, skipping")
                    continue
                
                # Current price and timestamp
                current_price = current_data.get('price', 0)
                timestamp = current_data.get('timestamp')
                
                # Simulate some historical data for technical indicators
                # This is a placeholder - in a real implementation we would fetch actual historical data
                # Generate synthetic price history with small random changes
                price_history = []
                base_price = current_price
                for i in range(10):  # Generate 10 historical price points
                    # Create small random price variations (±0.5%)
                    change = base_price * (1 + (np.random.random() - 0.5) * 0.005)
                    price_history.append(change)
                
                # Calculate volatility (standard deviation of price changes)
                if len(price_history) >= 2:
                    price_changes = np.diff(price_history)
                    volatility = float(np.std(price_changes))
                else:
                    volatility = 0.0
                
                # Calculate basic RSI (Relative Strength Index)
                if len(price_history) >= 5:
                    changes = np.diff(price_history)
                    gains = np.sum(np.clip(changes, 0, None))
                    losses = np.sum(np.abs(np.clip(changes, None, 0)))
                    
                    if losses == 0:
                        rsi = 100.0
                    else:
                        rs = gains / losses if losses > 0 else 1.0
                        rsi = 100.0 - (100.0 / (1.0 + rs))
                else:
                    rsi = 50.0  # Neutral value with insufficient data
                
                # Calculate momentum (difference between current price and 5 periods ago)
                momentum = current_price - price_history[0] if price_history else 0
                
                # Calculate price change percentage
                if price_history:
                    price_change_pct = ((current_price - price_history[0]) / price_history[0]) * 100
                else:
                    price_change_pct = 0.0
                
                # Store calculated indicators
                market_data[symbol] = {
                    'price': current_price,
                    'timestamp': timestamp,
                    'volatility': volatility,
                    'rsi': rsi,
                    'momentum': momentum,
                    'price_change_pct': price_change_pct,
                }
                
                logger.debug(f"Technical indicators for {symbol}: {market_data[symbol]}")
                
            except Exception as e:
                logger.error(f"Error calculating indicators for {symbol}: {e}")
                continue
        
        return market_data
                
    def select_pair(self, symbols, data_feed=None):
        """
        Select the best trading pair among the provided symbols using the LLM and market data.
        
        Args:
            symbols: List of symbol names to choose from
            data_feed: Optional DataFeed object to get real-time market data
        """
        logger.info(f"Selecting trading pair from symbols: {symbols}")
        if not symbols:
            logger.error("No symbols provided to select_pair.")
            return None
            
        market_data = {}
        market_analysis = ""
        
        # Fetch market data if data_feed is available
        if data_feed:
            try:
                market_data = self._calculate_technical_indicators(data_feed, symbols)
                
                # Format market data for LLM consumption
                if market_data:
                    market_analysis = "Current Market Data:\n"
                    for symbol, data in market_data.items():
                        market_analysis += f"{symbol}:\n"
                        market_analysis += f"  Price: {data.get('price', 'N/A')}\n"
                        market_analysis += f"  RSI: {data.get('rsi', 'N/A'):.1f}\n"
                        market_analysis += f"  Volatility: {data.get('volatility', 'N/A'):.6f}\n"
                        market_analysis += f"  Momentum: {data.get('momentum', 'N/A'):.6f}\n"
                        market_analysis += f"  Price Change %: {data.get('price_change_pct', 'N/A'):.2f}%\n"
                    logger.debug(f"Market analysis data prepared: {market_analysis}")
            except Exception as e:
                logger.error(f"Error preparing market data: {e}")
                market_analysis = ""
        
        system_msg = (
            "You are a professional trading expert selecting the best forex pair for a 5-minute binary options trade. "
            "Analyze the technical indicators and market data to identify the pair with the strongest directional "
            "signal (up or down). Consider volatility, momentum, RSI, and recent price movements. "
            "For binary options trading, look for pairs with clear trends, overbought/oversold RSI conditions, "
            "or significant momentum that suggest a high-probability move within the next 5 minutes. "
            "IMPORTANT: Respond with ONLY the exact symbol name. For example, if EURUSD is the best choice, "
            "respond with just 'EURUSD' and nothing else."
        )
        
        user_content = f"Available symbols: {symbols}\n\n"
        if market_analysis:
            user_content += market_analysis
        else:
            user_content += "No technical data available. Please select based on general forex market knowledge."
            
        max_retries = 3
        backoff = 1
        api_timeout_seconds = 30 # Define a timeout for the API call
        
        for attempt in range(max_retries):
            try:
                # Try the v1.x client interface first
                if 'OPENAI_V1' in globals() and OPENAI_V1:
                    try:
                        response = self.client.chat.completions.create(
                            model=self.model,
                            messages=[
                                {"role": "system", "content": system_msg},
                                {"role": "user", "content": user_content}
                            ],
                            timeout=api_timeout_seconds
                        )
                    except Exception as e:
                        logger.error(f"Error with v1 API in select_pair: {e}")
                        response = None
                else:
                    # Fallback to legacy interface for compatibility
                    response = openai.ChatCompletion.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": system_msg},
                            {"role": "user", "content": user_content}
                        ],
                        request_timeout=api_timeout_seconds
                    )
                
                if response:
                    full_response = response.choices[0].message.content.strip().upper()
                    logger.info(f"LLM selected symbol (raw): {full_response}")
                    
                    # Extract just the symbol name from the response
                    # First check for exact matches in the symbols list
                    for symbol in symbols:
                        if symbol.upper() in full_response:
                            logger.info(f"Extracted symbol: {symbol}")
                            return symbol
                    
                    # Next, try to find common forex pairs patterns like EUR/USD
                    import re
                    forex_pairs = re.findall(r'([A-Z]{3})/([A-Z]{3})', full_response)
                    if forex_pairs:
                        # Convert EUR/USD format to EURUSD format
                        extracted_symbol = forex_pairs[0][0] + forex_pairs[0][1]
                        if extracted_symbol in [s.upper() for s in symbols]:
                            logger.info(f"Extracted symbol from forex pair notation: {extracted_symbol}")
                            return extracted_symbol
                    
                    # If we couldn't extract a clear symbol, fall back to the first symbol
                    logger.warning(f"Could not extract a valid symbol from LLM response. Defaulting to first symbol: {symbols[0]}")
                    return symbols[0]
                
            except RateLimitError:
                logger.warning(f"OpenAI rate limit hit on attempt {attempt + 1}/{max_retries}, retrying in {backoff} seconds...")
                if attempt < max_retries - 1:
                    time.sleep(backoff)
                    backoff *= 2
            except Exception as e:
                logger.error(f"Error selecting trading pair via LLM: {e}", exc_info=True)
                if attempt < max_retries - 1:
                    time.sleep(backoff)
                    backoff *= 2
        
        # Fallback to first symbol if all retries fail
        logger.warning(f"All attempts to select pair failed. Defaulting to first symbol: {symbols[0]}")
        return symbols[0]
