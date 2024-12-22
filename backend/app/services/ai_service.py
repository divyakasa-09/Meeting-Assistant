from openai import OpenAI
from typing import Dict, List, Optional
import asyncio
import logging
from datetime import datetime

from ..config.settings import get_settings
from .token_counter import TokenCounter
from .rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.OPENAI_API_KEY)
        self.token_counter = TokenCounter(self.settings.GPT_MODEL)
        self.rate_limiter = RateLimiter(self.settings.RATE_LIMIT_PER_MIN)
        self.total_tokens_used = 0
        self.total_cost = 0.0

    async def process_with_retry(self, messages: List[Dict[str, str]], 
                               max_retries: int = 3) -> Optional[str]:
        """Process messages with retry logic"""
        retries = 0
        while retries < max_retries:
            try:
                if not self.rate_limiter.can_make_request():
                    await asyncio.sleep(2)
                    continue

                # Count input tokens
                input_tokens = sum(self.token_counter.count_tokens(msg["content"]) 
                                 for msg in messages)
                
                if input_tokens > self.settings.MAX_TOKENS_PER_REQUEST:
                    raise ValueError(f"Input tokens ({input_tokens}) exceed maximum")

                response = await self.client.chat.completions.create(
                    model=self.settings.GPT_MODEL,
                    messages=messages,
                    temperature=0.7,
                )

                output_tokens = self.token_counter.count_tokens(
                    response.choices[0].message.content
                )

                # Update usage statistics
                self.total_tokens_used += (input_tokens + output_tokens)
                self.total_cost += self.token_counter.estimate_cost(
                    input_tokens,
                    output_tokens,
                    self.settings.COST_PER_1K_INPUT_TOKENS,
                    self.settings.COST_PER_1K_OUTPUT_TOKENS
                )

                return response.choices[0].message.content

            except Exception as e:
                logger.error(f"Error processing OpenAI request: {e}")
                retries += 1
                if retries == max_retries:
                    logger.error("Max retries reached")
                    return None
                await asyncio.sleep(2 ** retries)  # Exponential backoff

    def get_usage_stats(self) -> Dict:
        """Get current usage statistics"""
        return {
            "total_tokens": self.total_tokens_used,
            "total_cost": round(self.total_cost, 4),
            "timestamp": datetime.now().isoformat()
        }