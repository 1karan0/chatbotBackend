import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """Application configuration settings."""
    
    # API Settings
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    secret_key: str = os.getenv("SECRET_KEY", "fallback-secret-key-change-in-production")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    admin_username: str = os.getenv("ADMIN_USERNAME", "")
    admin_password: str = os.getenv("ADMIN_PASSWORD", "")
    
    # Database Settings
    database_url: str = os.getenv("DATABASE_URL", "postgresql://chatbot_eni9_user:aohKgZKRws7r3X4TmLyJsPtMaY8cTdoE@dpg-d3vftpur433s73crgvog-a.singapore-postgres.render.com/chatbot_eni9")
    chroma_path: str = os.getenv("CHROMA_PATH", "./chroma_db")
    data_path: str = os.getenv("DATA_PATH", "./data")
    
    # External Services
    ngrok_auth_token: Optional[str] = os.getenv("NGROK_AUTH_TOKEN")
    
    # Model Settings
    embedding_model: str = "text-embedding-3-small"
    chat_model: str = "gpt-4o-mini"
    temperature: float = 0.0
    
    # Retrieval Settings
    dense_chunk_size: int = 800
    dense_chunk_overlap: int = 100
    sparse_chunk_size: int = 1600
    sparse_chunk_overlap: int = 200
    retrieval_k: int = 8
    # MMR: retrieve this many candidates first, then diversify down to retrieval_k
    retrieval_fetch_k: int = 32
    # MMR lambda: 1.0 = most relevant only, lower = more diverse excerpts (0.4–0.7 typical)
    mmr_lambda: float = 0.55
    # Max characters per chunk in the LLM context (truncate very long chunks to save tokens)
    context_max_chars_per_chunk: int = 2000
    # Max chunks to send to the model after retrieval (safety cap)
    context_max_chunks: int = 10
    # Max chunks per embedding API call (avoids OpenAI 300k tokens/request limit)
    embedding_batch_size: int = 100

    # PostgreSQL Settings
    pg_user: str = os.getenv("PG_USER", "")
    pg_db: str = os.getenv("PG_DB", "")
    pg_password: str = os.getenv("PG_PASSWORD", "")
    pg_port: int = int(os.getenv("PG_PORT", "5432"))

    class Config:
        env_file = ".env"
        extra = "allow"

# Global settings instance
settings = Settings()