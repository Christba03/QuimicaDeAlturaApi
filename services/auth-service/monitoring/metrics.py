from prometheus_client import Counter, Histogram

# Authentication metrics
AUTH_LOGIN_TOTAL = Counter(
    "auth_login_total",
    "Total number of login attempts",
    ["status"],  # success, failure
)

AUTH_REGISTER_TOTAL = Counter(
    "auth_register_total",
    "Total number of registration attempts",
    ["status"],  # success, failure
)

AUTH_TOKEN_REFRESH_TOTAL = Counter(
    "auth_token_refresh_total",
    "Total number of token refresh attempts",
    ["status"],  # success, failure
)

AUTH_LOGOUT_TOTAL = Counter(
    "auth_logout_total",
    "Total number of logout operations",
)

AUTH_TOKEN_VERIFICATION_TOTAL = Counter(
    "auth_token_verification_total",
    "Total number of token verification attempts",
    ["status"],  # valid, invalid, expired
)

# Latency metrics
AUTH_OPERATION_DURATION = Histogram(
    "auth_operation_duration_seconds",
    "Duration of authentication operations in seconds",
    ["operation"],  # login, register, refresh, logout, verify
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5],
)

# Session metrics
AUTH_ACTIVE_SESSIONS = Counter(
    "auth_session_created_total",
    "Total number of sessions created",
)

AUTH_SESSIONS_REVOKED = Counter(
    "auth_session_revoked_total",
    "Total number of sessions revoked",
    ["reason"],  # logout, refresh, admin, expired_cleanup
)

# Password hashing metrics
AUTH_PASSWORD_HASH_DURATION = Histogram(
    "auth_password_hash_duration_seconds",
    "Duration of password hashing operations",
    buckets=[0.05, 0.1, 0.2, 0.3, 0.5, 1.0],
)
