from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Chatbot service configuration."""

    APP_NAME: str = "Chatbot Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/chatbot_db"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None

    # Anthropic
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"
    ANTHROPIC_MAX_TOKENS: int = 2048
    ANTHROPIC_TEMPERATURE: float = 0.7

    # Internal services
    PLANT_SERVICE_URL: str = "http://localhost:8001"

    # RAG settings
    RAG_TOP_K: int = 5
    RAG_SIMILARITY_THRESHOLD: float = 0.7
    EMBEDDING_DIMENSION: int = 384

    # Conversation settings
    MAX_CONVERSATION_HISTORY: int = 20
    CONVERSATION_TIMEOUT_MINUTES: int = 30

    @property
    def redis_url(self) -> str:
        password_part = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{password_part}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
