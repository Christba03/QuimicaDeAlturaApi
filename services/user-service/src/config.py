from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """User Service configuration loaded from environment variables."""

    SERVICE_NAME: str = "user-service"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user_svc:user_svc_pass@postgres-user:5432/user_db"

    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 2
    REDIS_PASSWORD: str = ""

    # Service
    HOST: str = "0.0.0.0"
    PORT: int = 8005

    # Pagination defaults
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    @property
    def redis_url(self) -> str:
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    model_config = {
        "env_file": ".env",
        "env_prefix": "USER_SERVICE_",
        "case_sensitive": True,
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()
