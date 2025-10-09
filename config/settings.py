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
    
    # Database Settings
    database_url: str = os.getenv("DATABASE_URL", "postgresql://charbot_user:5E4TfARMyCzcSqsOEqckkbYCRG2kMVED@dpg-d3ads5gdl3ps73enmr5g-a.singapore-postgres.render.com/charbot")
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
    retrieval_k: int = 4

    # PostgreSQL Settings
    pg_user: str
    pg_db: str
    pg_password: str
    pg_port: int
    
    class Config:
        env_file = ".env"

# Global settings instance
settings = Settings()