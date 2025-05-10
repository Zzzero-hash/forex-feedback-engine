from typing import Dict, Optional

class TemporalPromptConfig:
    def __init__(self) -> None:
        """
        Initialize the temporal prompt configuration with enhanced prompts
        that incorporate historical price data and technical analysis.
        """
        self.system_prompt = (
            "You are an expert binary options analyst with deep knowledge of technical analysis "
            "and chart patterns. You will analyze forex price charts and technical indicators "
            "across multiple timeframes to determine the likely price direction for a 5-minute "
            "binary options trade.\n\n"
            "You will be given:\n"
            "1. An ASCII chart of recent price action\n"
            "2. Technical indicators and their values\n"
            "3. Detected chart patterns\n"
            "4. Current price data\n"
            "5. Recent trading history (if available)\n\n"
            "Based on this information, determine if the price is likely to move UP (CALL) or DOWN (PUT) "
            "in the next 5 minutes. If the signals are conflicting, unclear, or show range-bound conditions "
            "with no clear directional bias, respond with NO TRADE.\n\n"
            "For binary options, look specifically for:\n"
            "- Strong trend continuations or potential reversals at key levels\n"
            "- Overbought/oversold conditions (RSI above 70 or below 30)\n"
            "- Recent momentum that suggests continuation\n"
            "- High-probability chart patterns (engulfing, pinbars, etc.)\n"
            "- Support/resistance levels that may influence price action\n\n"
            "Your answer must end with one of: CALL, PUT, or NO TRADE."
        )
        
        self.user_prompt_template = (
            "Symbol: {symbol}\n\n"
            "PRICE CHART (last candles):\n"
            "{price_chart}\n\n"
            "TECHNICAL ANALYSIS:\n"
            "{historical_summary}\n\n"
            "CURRENT PRICE: {current_price}\n\n"
            "DETECTED PATTERNS: {patterns}\n\n"
            "PREVIOUS DECISIONS:\n"
            "{decision_context}\n\n"
            "RECENT TRADE HISTORY:\n"
            "{recent_trades}\n\n"
            "Based on the chart pattern, technical indicators, and price action, "
            "what is your trading decision for this 5-minute binary options trade? "
            "First provide your analysis, then end your response with CALL, PUT, or NO TRADE."
        )
        
        self.confidence_threshold = 0.7

    def get_system_prompt(self) -> str:
        """Return the system prompt for the LLM."""
        return self.system_prompt

    def get_user_prompt(self, symbol: str, price_chart: str, 
                      historical_summary: str, current_price: str,
                      recent_trades: str, patterns: str,
                      decision_context: str) -> str:
        """
        Format the user prompt with the provided data.
        
        Args:
            symbol: The trading symbol (e.g., 'EURUSD')
            price_chart: ASCII representation of recent price action
            historical_summary: Summary of historical data and indicators
            current_price: Current price of the symbol
            recent_trades: Recent trading history
            patterns: Detected chart patterns
            decision_context: Previous decisions for continuity
            
        Returns:
            Formatted user prompt
        """
        return self.user_prompt_template.format(
            symbol=symbol,
            price_chart=price_chart,
            historical_summary=historical_summary,
            current_price=current_price,
            patterns=patterns or "None detected",
            recent_trades=recent_trades or "No recent trades",
            decision_context=decision_context or "No previous decisions"
        )

    def is_trade_recommended(self, confidence: float) -> bool:
        """
        Check if a trade should be recommended based on the confidence level.
        
        Args:
            confidence: The confidence level (between 0 and 1)
            
        Returns:
            Boolean indicating whether to recommend the trade
        """
        return confidence >= self.confidence_threshold
