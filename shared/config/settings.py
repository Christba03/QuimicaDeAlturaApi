from pydantic_settings import BaseSettings


class BaseServiceSettings(BaseSettings):
    """Base settings shared across all services."""

    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def redis_url(self) -> str:
        password_part = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{password_part}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    model_config = {"env_file": ".env", "extra": "ignore"}


class DatabaseSettings(BaseSettings):
    """Database settings for services that use PostgreSQL."""

    database_url: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}
