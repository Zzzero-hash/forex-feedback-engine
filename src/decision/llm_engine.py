from openai import OpenAI

class LLMEngine:
    def __init__(self, api_key, prompt_config=None, model="gpt-3.5-turbo"):
        self.api_key = api_key
        self.model = model
        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.api_key)
        # Use provided PromptConfig or default
        from .prompt_config import PromptConfig
        self.prompt_config = prompt_config or PromptConfig()

    def get_decision(self, market_data, recent_trades):
        # Build prompts via PromptConfig
        system_msg = self.prompt_config.get_system_prompt()
        # Flatten market_data and recent_trades into strings
        user_content = (
            f"Market Data: {market_data}\nRecent Trades: {recent_trades}"
        )
        # Use OpenAI client to create a chat completion
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_content}
            ]
        )
        content = completion.choices[0].message.content
        return self._parse_response(content)

    def _parse_response(self, response):
        if "CALL" in response:
            return "CALL"
        elif "PUT" in response:
            return "PUT"
        else:
            return "NO TRADE"