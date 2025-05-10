import os
import time
import logging
import traceback
import numpy as np
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

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

class TemporalLLMEngine:
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
            
        from .temporal_prompt_config import TemporalPromptConfig
        self.prompt_config = prompt_config or TemporalPromptConfig()
        
        # Import HistoricalDataCollector here to avoid circular imports
        from ..data.historical_feed import HistoricalDataCollector
        self.historical_collector = None
        
        # Decision memory to track recent decisions
        self.decision_memory = {}
        
    def initialize_historical_collector(self, data_feed, lookback_periods=60, timeframe_minutes=5):
        """Initialize the historical data collector with the provided data feed"""
        from ..data.historical_feed import HistoricalDataCollector
        self.historical_collector = HistoricalDataCollector(
            data_feed=data_feed,
            lookback_periods=lookback_periods,
            timeframe_minutes=timeframe_minutes
        )
        logger.info(f"Historical data collector initialized with {lookback_periods} periods of {timeframe_minutes}-min data")
    
    def get_decision(self, symbol, market_data, recent_trades):
        """
        Get a trading decision for the specified symbol using temporal context.
        
        Args:
            symbol: The currency pair symbol (e.g., 'EURUSD')
            market_data: Current market data point
            recent_trades: Recent trading history
            
        Returns:
            Decision as a string: "CALL", "PUT", or "NO TRADE"
        """
        logger.debug(f"TemporalLLMEngine.get_decision called for {symbol}")
        
        # Ensure historical collector is initialized
        if not self.historical_collector:
            logger.error("Historical data collector not initialized. Call initialize_historical_collector first.")
            return "NO TRADE"
            
        # Get historical data and calculate indicators
        try:
            # Fetch historical data and calculate technical indicators
            historical_data = self.historical_collector.get_historical_data(symbol)
            indicators = self.historical_collector.calculate_technical_indicators(symbol)
            patterns = self.historical_collector.get_pattern_analysis(symbol)
            
            # Generate ASCII chart for visual representation
            price_chart = self.historical_collector.get_price_chart_ascii(symbol, bars=20)
            
            # Prepare the context for the LLM
            system_msg = self.prompt_config.get_system_prompt()
            
            # Format the historical data and indicators for the prompt
            historical_summary = self._format_historical_summary(symbol, historical_data, indicators, patterns)
            
            # Check recent decisions from memory to provide continuity
            decision_context = self._get_decision_memory_context(symbol)
            
            # Combine all information for the user prompt
            user_content = self.prompt_config.get_user_prompt(
                symbol=symbol,
                price_chart=price_chart,
                historical_summary=historical_summary,
                current_price=market_data.get('price', 'unknown'),
                recent_trades=recent_trades,
                patterns=", ".join(patterns.get("patterns", [])),
                decision_context=decision_context
            )
            
            logger.debug(f"Prepared LLM prompt with temporal context for {symbol}")
            
            # Call the API with retry logic
            decision = self._call_openai_api(system_msg, user_content)
            
            # Store the decision in memory
            self._update_decision_memory(symbol, decision)
            
            return decision
            
        except Exception as e:
            logger.error(f"Error in get_decision for {symbol}: {e}", exc_info=True)
            return "NO TRADE"
    
    def _format_historical_summary(self, symbol, historical_data, indicators, patterns):
        """Format the historical data and indicators for the prompt"""
        # Summarize the historical data
        candle_count = len(historical_data)
        timeframe = f"{self.historical_collector.timeframe_minutes}-minute"
        
        # Create a summary of price action
        recent_close_prices = historical_data['close'].tail(5).tolist()
        price_direction = "upward" if recent_close_prices[-1] > recent_close_prices[0] else "downward"
        
        # Create trend information from different timeframes
        trend_description = f"The overall trend is {indicators.get('trend_direction', 'neutral')}. "
        
        if 'ma_14' in indicators and 'ma_50' in indicators:
            relationship = "above" if indicators['ma_14'] > indicators['ma_50'] else "below"
            trend_description += f"The 14-period MA is {relationship} the 50-period MA. "
        
        # Format technical indicator values
        indicators_formatted = []
        for key, value in indicators.items():
            # Skip some keys that are used in other sections
            if key == 'price_current' or key == 'trend_direction':
                continue
                
            if isinstance(value, float):
                formatted_value = f"{value:.5f}" if value < 0.1 else f"{value:.2f}"
                indicators_formatted.append(f"{key}: {formatted_value}")
            else:
                indicators_formatted.append(f"{key}: {value}")
        
        # Summarize patterns
        pattern_str = ", ".join(patterns.get("patterns", []))
        if not pattern_str:
            pattern_str = "No significant patterns detected"
            
        # Combine everything into a single context
        summary = (
            f"Analysis of {symbol} based on {candle_count} {timeframe} candles:\n"
            f"Current price: {indicators.get('price_current', 'unknown')}\n"
            f"Recent price action shows a {price_direction} movement.\n"
            f"{trend_description}\n"
            f"Technical Indicators:\n- " + "\n- ".join(indicators_formatted) + "\n"
            f"Patterns: {pattern_str}\n"
        )
        
        # Add volume information if available
        if patterns.get('volume_signal'):
            summary += f"Volume: {patterns.get('volume_signal', 'unknown')}\n"
            
        return summary
    
    def _call_openai_api(self, system_msg, user_content):
        """Call the OpenAI API with retry logic"""
        max_retries = 3
        backoff = 1
        response = None
        api_timeout_seconds = 30
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"Attempt {attempt+1}/{max_retries} to call OpenAI API with model: {self.model}")
                
                # Use the configured model
                current_model_to_use = self.model
                
                # Try the v1.x client interface first
                if 'OPENAI_V1' in globals() and OPENAI_V1:
                    try:
                        response = self.client.chat.completions.create(
                            model=current_model_to_use,
                            messages=[
                                {"role": "system", "content": system_msg},
                                {"role": "user", "content": user_content}
                            ],
                            timeout=api_timeout_seconds
                        )
                    except Exception as e:
                        logger.error(f"Error with v1 API: {e}")
                        response = None
                
                # Fallback to legacy interface
                if response is None:
                    response = openai.ChatCompletion.create(
                        model=current_model_to_use,
                        messages=[
                            {"role": "system", "content": system_msg},
                            {"role": "user", "content": user_content}
                        ],
                        request_timeout=api_timeout_seconds
                    )
                
                if response and hasattr(response, 'choices') and response.choices:
                    break
                
            except RateLimitError:
                logger.warning(f"OpenAI rate limit hit on attempt {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    time.sleep(backoff)
                    backoff *= 2
                else:
                    logger.error("OpenAI rate limit exceeded after all retries")
                    return "NO TRADE"
            except Exception as e:
                logger.error(f"Error calling OpenAI API: {e}", exc_info=True)
                if attempt < max_retries - 1:
                    time.sleep(backoff)
                    backoff *= 2
                else:
                    logger.error("Failed to call OpenAI API after all retries")
                    return "NO TRADE"
        
        if not response or not hasattr(response, 'choices') or not response.choices:
            logger.error("Invalid or empty response from OpenAI API")
            return "NO TRADE"
        
        content = response.choices[0].message.content
        logger.debug(f"LLM decision raw content: '{content}'")
        return self._parse_response(content)
    
    def _parse_response(self, response_content):
        """Parse the LLM response to extract the decision"""
        cleaned = response_content.strip().upper()
        
        # Check for NO TRADE first
        if "NO TRADE" in cleaned:
            return "NO TRADE"
        
        # Check for CALL or PUT anywhere in the response
        if "CALL" in cleaned:
            return "CALL"
        if "PUT" in cleaned:
            return "PUT"
        
        # Fallback for unexpected responses
        logger.warning(f"LLM response did not contain CALL, PUT, or NO TRADE. Defaulting to NO TRADE.")
        return "NO TRADE"
    
    def _get_decision_memory_context(self, symbol):
        """Get context from previous decisions for continuity"""
        if symbol not in self.decision_memory:
            return "No previous trading decisions for this symbol."
        
        memory = self.decision_memory[symbol]
        
        # Format the memory into a readable context
        context_lines = []
        context_lines.append(f"Previous decisions for {symbol}:")
        
        for timestamp, decision in memory["decisions"]:
            time_str = timestamp.strftime("%H:%M:%S")
            context_lines.append(f"- {time_str}: {decision}")
            
        return "\n".join(context_lines)
    
    def _update_decision_memory(self, symbol, decision):
        """Update the decision memory with the latest decision"""
        now = datetime.now()
        
        if symbol not in self.decision_memory:
            self.decision_memory[symbol] = {
                "decisions": []
            }
        
        # Add the new decision
        self.decision_memory[symbol]["decisions"].append((now, decision))
        
        # Keep only last 5 decisions
        if len(self.decision_memory[symbol]["decisions"]) > 5:
            self.decision_memory[symbol]["decisions"] = self.decision_memory[symbol]["decisions"][-5:]
    
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
        
        # Ensure historical collector is initialized
        if not self.historical_collector and data_feed:
            self.initialize_historical_collector(data_feed)
        
        # Prepare comparative analysis of all symbols
        symbol_analysis = {}
        
        for symbol in symbols:
            try:
                # Skip if historical collector not available
                if not self.historical_collector:
                    continue
                    
                # Get indicators for this symbol
                indicators = self.historical_collector.calculate_technical_indicators(symbol)
                patterns = self.historical_collector.get_pattern_analysis(symbol)
                
                # Create a trading opportunity score (higher is better)
                score = 0
                
                # Check for strong directional signals
                if 'trend_direction' in indicators:
                    if indicators['trend_direction'] in ('bullish', 'bullish_crossover'):
                        score += 2
                    elif indicators['trend_direction'] in ('bearish', 'bearish_crossover'):  
                        score += 2
                
                # Check RSI for overbought/oversold conditions (good for binary options)
                if 'rsi_14' in indicators:
                    rsi = indicators['rsi_14']
                    if rsi < 30 or rsi > 70:  # Strong oversold or overbought
                        score += 3
                    elif rsi < 40 or rsi > 60:  # Moderate signal
                        score += 1
                
                # Check for pattern signals
                if patterns.get('patterns'):
                    score += len(patterns['patterns'])
                    # Give extra points for strong patterns
                    strong_patterns = ['bullish_engulfing', 'bearish_engulfing', 
                                      'three_white_soldiers', 'three_black_crows']
                    for pattern in patterns['patterns']:
                        if pattern in strong_patterns:
                            score += 2
                
                # Check for volume confirmation
                if patterns.get('volume_signal') == 'strong':
                    score += 2
                
                # Store analysis and score
                symbol_analysis[symbol] = {
                    'score': score,
                    'indicators': indicators,
                    'patterns': patterns.get('patterns', [])
                }
                
                logger.debug(f"Symbol {symbol} analysis: score={score}")
                
            except Exception as e:
                logger.error(f"Error analyzing {symbol}: {e}")
                continue
        
        # If we have analysis for at least one symbol
        if symbol_analysis:
            # Sort symbols by score (descending)
            ranked_symbols = sorted(symbol_analysis.keys(), 
                                   key=lambda s: symbol_analysis[s]['score'],
                                   reverse=True)
            
            # If top symbol has a good score, return it directly
            if symbol_analysis[ranked_symbols[0]]['score'] >= 5:
                selected = ranked_symbols[0]
                logger.info(f"Selected {selected} with highest score: {symbol_analysis[selected]['score']}")
                return selected
                
            # Otherwise, let LLM make the final decision with the top candidates
            top_candidates = ranked_symbols[:min(3, len(ranked_symbols))]
        else:
            # If no analysis, use all symbols as candidates
            top_candidates = symbols
        
        # Fall back to LLM for final decision among top candidates
        system_msg = (
            "You are a professional trading expert selecting the best forex pair for a 5-minute binary options trade. "
            "Analyze the technical indicators and market data to identify the pair with the strongest directional "
            "signal (up or down). Consider volatility, momentum, RSI, and recent price movements. "
            "For binary options trading, look for pairs with clear trends, overbought/oversold RSI conditions, "
            "or significant momentum that suggest a high-probability move within the next 5 minutes. "
            "IMPORTANT: Respond with ONLY the exact symbol name. For example, if EURUSD is the best choice, "
            "respond with just 'EURUSD' and nothing else."
        )
        
        # Format the analysis for the LLM
        user_content = f"Available symbols: {top_candidates}\n\n"
        if symbol_analysis:
            user_content += "Symbol Analysis:\n"
            for symbol in top_candidates:
                if symbol in symbol_analysis:
                    analysis = symbol_analysis[symbol]
                    user_content += f"\n{symbol}:\n"
                    user_content += f"  Score: {analysis['score']}\n"
                    
                    if 'indicators' in analysis:
                        ind = analysis['indicators']
                        if 'price_current' in ind:
                            user_content += f"  Price: {ind.get('price_current', 'N/A')}\n"
                        if 'rsi_14' in ind:
                            user_content += f"  RSI: {ind.get('rsi_14', 'N/A'):.1f}\n"
                        if 'volatility_10_pct' in ind:
                            user_content += f"  Volatility: {ind.get('volatility_10_pct', 'N/A'):.2f}%\n"
                        if 'trend_direction' in ind:
                            user_content += f"  Trend: {ind.get('trend_direction', 'neutral')}\n"
                    
                    if analysis['patterns']:
                        user_content += f"  Patterns: {', '.join(analysis['patterns'])}\n"
        else:
            user_content += "No technical data available. Please select based on general forex market knowledge."
        
        # Call the OpenAI API
        decision = self._call_openai_api(system_msg, user_content)
        
        # Extract symbol from the response
        for symbol in symbols:
            if symbol.upper() in decision.upper():
                logger.info(f"LLM selected symbol: {symbol}")
                return symbol
        
        # Default to first candidate if no match
        logger.warning(f"Could not extract valid symbol from LLM response: '{decision}'. Defaulting to {top_candidates[0]}")
        return top_candidates[0]
