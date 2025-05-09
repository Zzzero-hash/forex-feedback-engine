import os
import time
import logging
import traceback # Added for detailed exception logging

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
    def __init__(self, api_key, prompt_config=None, model="o4-mini"):
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
                # Use the configured model (default is o4-mini)
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
        
    def select_pair(self, symbols: list[str]):
        """
        Select the best trading pair among the provided symbols using the LLM.
        """
        logger.info(f"Selecting trading pair from symbols: {symbols}")
        if not symbols:
            logger.error("No symbols provided to select_pair.")
            return None
            
        system_msg = (
            "You are a professional trading expert. "
            "Choose the single best trading pair to trade next from the following list of symbols. "
            "IMPORTANT: Respond with ONLY the exact symbol name. For example, if EURUSD is the best choice, "
            "respond with just 'EURUSD' and nothing else."
        )
        user_content = f"Available symbols: {symbols}"
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
