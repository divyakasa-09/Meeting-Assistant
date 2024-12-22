from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    MAX_TOKENS_PER_REQUEST: int = 4000
    GPT_MODEL: str = "gpt-3.5-turbo"  # Can be changed to gpt-4 later
    RATE_LIMIT_PER_MIN: int = 50
    COST_PER_1K_INPUT_TOKENS: float = 0.0005   # GPT-3.5 rate
    COST_PER_1K_OUTPUT_TOKENS: float = 0.0015  # GPT-3.5 rate
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()