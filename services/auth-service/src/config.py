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

    # JWT — RS256 asymmetric signing
    # Set JWT_PRIVATE_KEY / JWT_PUBLIC_KEY to PEM strings (with literal \n) in env.
    # Falls back to HS256 with JWT_SECRET_KEY when RSA keys are not provided (dev only).
    JWT_PRIVATE_KEY: str = ""
    JWT_PUBLIC_KEY: str = ""
    JWT_SECRET_KEY: str = "change-me-in-production"  # HS256 fallback (dev only)
    JWT_ALGORITHM: str = "RS256"
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

    # IP-level brute force protection
    IP_LOCKOUT_THRESHOLD: int = 20       # failed attempts across any accounts
    IP_LOCKOUT_WINDOW_MINUTES: int = 15
    IP_LOCKOUT_DURATION_MINUTES: int = 60

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

    # OAuth 2.0 Social Login
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    OAUTH_REDIRECT_BASE_URL: str = "http://localhost:8001"

    # OpenTelemetry
    OTEL_ENABLED: bool = False
    OTEL_SERVICE_NAME: str = "auth-service"
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://localhost:4317"

    # GeoIP (ip-api.com, free tier — no key required)
    GEOIP_ENABLED: bool = True
    GEOIP_API_URL: str = "http://ip-api.com/json/{ip}?fields=status,country,countryCode,regionName,city,lat,lon"

    # Webhooks / Pub-Sub
    WEBHOOK_ENABLED: bool = True
    WEBHOOK_REDIS_CHANNEL: str = "auth-service:events"
    # Comma-separated list of HTTP webhook URLs to POST auth events to
    WEBHOOK_HTTP_URLS: str = ""

    @property
    def redis_url(self) -> str:
        password_part = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{password_part}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def use_rsa(self) -> bool:
        """True when RSA keypair is configured (production mode)."""
        return bool(self.JWT_PRIVATE_KEY and self.JWT_PUBLIC_KEY)

    @property
    def webhook_http_url_list(self) -> list[str]:
        return [u.strip() for u in self.WEBHOOK_HTTP_URLS.split(",") if u.strip()]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "case_sensitive": True}


settings = Settings()
