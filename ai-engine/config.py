# config.py
#
# LESSON: pydantic-settings
# Instead of scattered os.getenv("X") calls everywhere, we define ONE
# Settings class. Pydantic reads the .env file, validates each value
# (wrong type = crash on startup, not at 3am in production), and gives
# us a typed object we import anywhere. Clean and safe.

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Each field maps to an env var of the same name (uppercase in .env)
    database_url: str
    redis_url: str
    openai_api_key: str

    # Embedding model — text-embedding-3-small is fast and cheap
    # text-embedding-3-large is more accurate but 5x the cost
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    # The LLM that generates counter-arguments and verdicts
    chat_model: str = "gpt-4o"

    # How many precedents to retrieve per argument (RAG top-k)
    top_k_precedents: int = 5

    # Tell pydantic where to find the .env file
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# Single shared instance — import this everywhere
# `lru_cache` means it's only created once (not re-read on every import)
from functools import lru_cache

@lru_cache
def get_settings() -> Settings:
    return Settings()
