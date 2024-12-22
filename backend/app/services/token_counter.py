import tiktoken

class TokenCounter:
    def __init__(self, model_name="gpt-3.5-turbo"):
        self.encoding = tiktoken.encoding_for_model(model_name)
        
    def count_tokens(self, text: str) -> int:
        return len(self.encoding.encode(text))
    
    def estimate_cost(self, input_tokens: int, output_tokens: int, 
                     cost_per_1k_input: float, cost_per_1k_output: float) -> float:
        input_cost = (input_tokens / 1000) * cost_per_1k_input
        output_cost = (output_tokens / 1000) * cost_per_1k_output
        return input_cost + output_cost