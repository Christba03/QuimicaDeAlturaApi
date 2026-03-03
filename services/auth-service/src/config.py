from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Auth Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/auth_db"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""

    # JWT
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    ALLOWED_ORIGINS: list[str] = ["*"]

    # Email/SMTP
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@medicinalplants.mx"
    SMTP_USE_TLS: bool = True
    SMTP_FROM_NAME: str = "Medicinal Plants API"

    # Email Verification
    EMAIL_VERIFICATION_CODE_EXPIRY_MINUTES: int = 15

    # Password Reset
    PASSWORD_RESET_CODE_EXPIRY_MINUTES: int = 15

    # Security
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 30
    RATE_LIMIT_LOGIN_PER_15MIN: int = 5

    # 2FA
    TWO_FACTOR_ISSUER_NAME: str = "Medicinal Plants API"

    # Password Policy
    PASSWORD_MIN_LENGTH: int = 12
    PASSWORD_MIN_STRENGTH_SCORE: int = 3  # zxcvbn score 0-4
    PASSWORD_HISTORY_SIZE: int = 5

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REGISTER_PER_HOUR: int = 3
    RATE_LIMIT_PASSWORD_RESET_PER_HOUR: int = 3
    RATE_LIMIT_VERIFICATION_PER_HOUR: int = 5

    # Device Trust
    TRUSTED_DEVICE_DURATION_DAYS: int = 30
    REQUIRE_2FA_FOR_NEW_DEVICES: bool = True

    # Email Queue
    EMAIL_QUEUE_ENABLED: bool = True
    EMAIL_QUEUE_MAX_RETRIES: int = 3
    EMAIL_QUEUE_RETRY_DELAY_SECONDS: int = 60
    EMAIL_SEND_RATE_LIMIT_PER_MINUTE: int = 10

    @property
    def redis_url(self) -> str:
        password_part = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{password_part}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "case_sensitive": True}


settings = Settings()
