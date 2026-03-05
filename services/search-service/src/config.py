from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Search service configuration loaded from environment variables."""

    SERVICE_NAME: str = "search-service"
    SERVICE_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Elasticsearch
    ELASTICSEARCH_HOST: str = "localhost"
    ELASTICSEARCH_PORT: int = 9200
    ELASTICSEARCH_SCHEME: str = "http"
    ELASTICSEARCH_USERNAME: str = ""
    ELASTICSEARCH_PASSWORD: str = ""
    ELASTICSEARCH_CA_CERTS: str = ""
    ELASTICSEARCH_VERIFY_CERTS: bool = False

    # Index names
    ES_INDEX_PLANTS: str = "plants"
    ES_INDEX_COMPOUNDS: str = "compounds"
    ES_INDEX_ACTIVITIES: str = "activities"

    # Redis cache
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 2
    REDIS_PASSWORD: str = ""
    REDIS_CACHE_TTL: int = 300  # seconds

    # Search defaults
    SEARCH_DEFAULT_PAGE_SIZE: int = 20
    SEARCH_MAX_PAGE_SIZE: int = 100
    AUTOCOMPLETE_MAX_SUGGESTIONS: int = 10
    RECOMMENDATION_MAX_ITEMS: int = 10

    @property
    def elasticsearch_url(self) -> str:
        return f"{self.ELASTICSEARCH_SCHEME}://{self.ELASTICSEARCH_HOST}:{self.ELASTICSEARCH_PORT}"

    @property
    def redis_url(self) -> str:
        password_part = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{password_part}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    model_config = {"env_prefix": "", "case_sensitive": True}


settings = Settings()


def get_settings() -> Settings:
    return settings
