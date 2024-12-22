from typing import Dict, List, Optional, Tuple
import asyncio
import logging
from datetime import datetime
from openai import OpenAI
from ..config.settings import get_settings  # Add this import line
from .token_counter import TokenCounter
from .rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

class EnhancedAIService:
    def __init__(self):
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.OPENAI_API_KEY)
        self.token_counter = TokenCounter(self.settings.GPT_MODEL)
        self.rate_limiter = RateLimiter(self.settings.RATE_LIMIT_PER_MIN)
        self.total_tokens_used = 0
        self.total_cost = 0.0

    async def generate_progressive_summary(self, recent_transcripts: List[str]) -> Optional[Dict]:
        """Generate a real-time summary of recent discussion"""
        messages = [
            {
                "role": "system",
                "content": """You are a real-time meeting assistant. Analyze the recent discussion and provide:
                1. A brief summary of the main points (2-3 sentences)
                2. Key topics discussed
                3. Any decisions made
                4. Action items identified
                Format the response as JSON with these keys: summary, topics, decisions, action_items"""
            },
            {
                "role": "user",
                "content": f"Recent discussion transcript:\n\n{' '.join(recent_transcripts)}"
            }
        ]
        
        result = await self.process_with_retry(messages)
        return result if result else None

    async def generate_followup_questions(self, context: str) -> Optional[List[str]]:
        """Generate relevant follow-up questions based on discussion context"""
        messages = [
            {
                "role": "system",
                "content": """You are an attentive meeting participant. Based on the discussion context, 
                generate 3-5 insightful follow-up questions that would help clarify or expand on key points.
                Focus on questions that:
                - Clarify ambiguous points
                - Probe deeper into important topics
                - Address potential gaps
                - Help with next steps
                Format as a JSON array of strings."""
            },
            {
                "role": "user",
                "content": f"Discussion context:\n\n{context}"
            }
        ]
        
        result = await self.process_with_retry(messages)
        return result if result else None

    async def extract_action_items(self, transcript: str) -> Optional[List[Dict]]:
        """Extract action items from the transcript"""
        messages = [
            {
                "role": "system",
                "content": """You are a meeting assistant focusing on action items.
                Analyze the transcript and extract action items with:
                - Description of the task
                - Assigned person (if mentioned)
                - Due date (if mentioned)
                - Priority (if implied)
                Format as JSON array with these keys: description, assigned_to, due_date, priority"""
            },
            {
                "role": "user",
                "content": f"Meeting transcript:\n\n{transcript}"
            }
        ]
        
        result = await self.process_with_retry(messages)
        return result if result else None

    async def generate_final_summary(self, full_transcript: str) -> Optional[Dict]:
        """Generate a comprehensive final meeting summary"""
        messages = [
            {
                "role": "system",
                "content": """You are a meeting summarizer. Create a comprehensive summary with:
                1. Executive summary (2-3 sentences)
                2. Main discussion points
                3. Decisions made
                4. Action items
                5. Key takeaways
                6. Follow-up items
                Format as JSON with these keys: executive_summary, discussion_points, 
                decisions, action_items, takeaways, followup_items"""
            },
            {
                "role": "user",
                "content": f"Full meeting transcript:\n\n{full_transcript}"
            }
        ]
        
        result = await self.process_with_retry(messages)
        return result if result else None

    async def identify_topics(self, transcript: str) -> Optional[List[Dict]]:
        """Identify main topics discussed in the meeting"""
        messages = [
            {
                "role": "system",
                "content": """You are a topic analyzer. Identify the main topics discussed with:
                - Topic name
                - Brief description
                - Time spent (if apparent)
                - Key participants (if mentioned)
                Format as JSON array with these keys: topic, description, time_spent, participants"""
            },
            {
                "role": "user",
                "content": f"Meeting transcript:\n\n{transcript}"
            }
        ]
        
        result = await self.process_with_retry(messages)
        return result if result else None

    async def process_with_retry(self, messages: List[Dict[str, str]], max_retries: int = 3) -> Optional[str]:
        retries = 0
        while retries < max_retries:
            try:
                if not self.rate_limiter.can_make_request():
                    await asyncio.sleep(2)
                    continue
            
                input_tokens = sum(self.token_counter.count_tokens(msg["content"])
                             for msg in messages)
            
                if input_tokens > self.settings.MAX_TOKENS_PER_REQUEST:
                    raise ValueError(f"Input tokens ({input_tokens}) exceed maximum")
            
            # Create client with sync completion
                client = OpenAI(api_key=self.settings.OPENAI_API_KEY)
            
            # Make the API call synchronously
                response = client.chat.completions.create(
                    model=self.settings.GPT_MODEL,
                    messages=messages,
                temperature=0.7,
                response_format={ "type": "json_object" }
                )
              
            # Access the response content
                content = response.choices[0].message.content
            
                output_tokens = self.token_counter.count_tokens(content)
            
                self.total_tokens_used += (input_tokens + output_tokens)
                self.total_cost += self.token_counter.estimate_cost(
                input_tokens,
                output_tokens,
                self.settings.COST_PER_1K_INPUT_TOKENS,
                self.settings.COST_PER_1K_OUTPUT_TOKENS
               )
            
                return content
            
            except Exception as e:
                logger.error(f"Error processing OpenAI request: {str(e)}")
                retries += 1
                if retries == max_retries:
                    logger.error("Max retries reached")
                    return None
                await asyncio.sleep(2 ** retries)

        return None

    def get_usage_stats(self) -> Dict:
        """Get current usage statistics"""
        return {
            "total_tokens": self.total_tokens_used,
            "total_cost": round(self.total_cost, 4),
            "timestamp": datetime.now().isoformat()
        }