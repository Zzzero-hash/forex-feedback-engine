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
    def __init__(self, api_key, prompt_config=None, model="gpt-3.5-turbo"):
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
                # Using "o4-mini" as it was previously confirmed to work with your key.
                current_model_to_use = "o4-mini" 
                logger.debug(f"Attempting OpenAI API call with model: {current_model_to_use}, timeout: {api_timeout_seconds}s")

                if 'OPENAI_V1' in globals() and OPENAI_V1:
                    response = self.client.chat.completions.create(
                        model=current_model_to_use, 
                        messages=[
                            {"role": "system", "content": system_msg},
                            {"role": "user", "content": user_content}
                        ],
                        timeout=api_timeout_seconds # Added timeout for v1.x
                    )
                else: # OpenAI v0.x
                    response = openai.ChatCompletion.create( # type: ignore
                        model=current_model_to_use,
                        messages=[
                            {"role": "system", "content": system_msg},
                            {"role": "user", "content": user_content}
                        ],
                        request_timeout=api_timeout_seconds # Added timeout for v0.x
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
        cleaned_content = response_content.strip().upper()  # Clean and uppercase
        if cleaned_content.startswith("CALL"):
            return "CALL"
        elif cleaned_content.startswith("PUT"):
            return "PUT"
        elif cleaned_content.startswith("NO TRADE"): # Explicitly check for NO TRADE first
            return "NO TRADE"
        else:
            # Fallback if the response is unexpected, but log the original content
            logger.warning(f"LLM response \\'{response_content}\\' did not start with CALL, PUT, or NO TRADE after cleaning. Defaulting to NO TRADE.")
            return "NO TRADE"