from openai import ChatCompletion

class LLMEngine:
    def __init__(self, api_key, model="gpt-3.5-turbo"):
        self.api_key = api_key
        self.model = model

    def get_decision(self, market_data, recent_trades):
        prompt = self._create_prompt(market_data, recent_trades)
        response = self._call_llm(prompt)
        return self._parse_response(response)

    def _create_prompt(self, market_data, recent_trades):
        return f"""
        You are an expert binary options trader. Based on the following market data and recent trades, determine the next action:
        
        Market Data: {market_data}
        Recent Trades: {recent_trades}
        
        Provide your decision as CALL, PUT, or NO TRADE, along with a brief justification.
        """

    def _call_llm(self, prompt):
        completion = ChatCompletion.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            api_key=self.api_key
        )
        return completion.choices[0].message.content

    def _parse_response(self, response):
        if "CALL" in response:
            return "CALL"
        elif "PUT" in response:
            return "PUT"
        else:
            return "NO TRADE"