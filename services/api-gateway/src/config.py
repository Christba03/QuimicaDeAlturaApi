from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """API Gateway configuration loaded from environment variables."""

    # Service identity
    service_name: str = "api-gateway"
    debug: bool = False

    # Downstream service URLs
    auth_service_url: str = "http://auth-service:8001"
    plant_service_url: str = "http://plant-service:8002"
    chatbot_service_url: str = "http://chatbot-service:8003"
    search_service_url: str = "http://search-service:8004"
    user_service_url: str = "http://user-service:8005"

    # Redis configuration
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""

    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:8080"

    # JWT / Auth
    jwt_secret: str = "change-me-in-production"

    # HTTP client settings
    request_timeout_seconds: float = 30.0

    @property
    def redis_url(self) -> str:
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
