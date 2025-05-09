from typing import Dict

class PromptConfig:
    def __init__(self) -> None:
        self.system_prompt = (
            "You are an expert binary options analyst. You receive current market data, "
            "recent price trends, and possibly detected chart patterns. Determine if the "
            "next 5-minute move is likely Up (CALL) or Down (PUT). Only suggest a trade "
            "if there is a clear statistical edge; if the signals are conflicting or weak, "
            "respond with NO TRADE. Provide reasoning for your decision focusing on the data given."
        )
        self.user_prompt_template = (
            "Recent price action: {price_action}\n"
            "Current indicators: {indicators}\n"
            "Detected patterns: {patterns}\n"
            "Please provide your trading decision."
        )
        self.confidence_threshold = 0.7

    def get_system_prompt(self) -> str:
        return self.system_prompt

    def get_user_prompt(self, price_action: str, indicators: str, patterns: str) -> str:
        return self.user_prompt_template.format(
            price_action=price_action,
            indicators=indicators,
            patterns=patterns
        )

    def is_trade_recommended(self, confidence: float) -> bool:
        return confidence >= self.confidence_threshold