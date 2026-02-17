from prometheus_client import Counter, Histogram, Gauge

# ── Favorites Metrics ──────────────────────────────────────────────────

FAVORITES_ADDED = Counter(
    "user_service_favorites_added_total",
    "Total number of plants added to favorites",
    ["user_id"],
)

FAVORITES_REMOVED = Counter(
    "user_service_favorites_removed_total",
    "Total number of plants removed from favorites",
    ["user_id"],
)

# ── Usage Report Metrics ──────────────────────────────────────────────

USAGE_REPORTS_SUBMITTED = Counter(
    "user_service_usage_reports_submitted_total",
    "Total number of usage reports submitted",
    ["effectiveness"],
)

USAGE_REPORT_RATINGS = Histogram(
    "user_service_usage_report_rating",
    "Distribution of usage report ratings",
    buckets=[1, 2, 3, 4, 5],
)

# ── Profile Metrics ───────────────────────────────────────────────────

PROFILE_VIEWS = Counter(
    "user_service_profile_views_total",
    "Total number of profile views",
)

PROFILE_UPDATES = Counter(
    "user_service_profile_updates_total",
    "Total number of profile updates",
)

# ── History Metrics ───────────────────────────────────────────────────

SEARCH_HISTORY_RECORDED = Counter(
    "user_service_search_history_recorded_total",
    "Total number of search queries recorded",
)

PLANT_VIEWS_RECORDED = Counter(
    "user_service_plant_views_recorded_total",
    "Total number of plant views recorded",
)

# ── Cache Metrics ─────────────────────────────────────────────────────

CACHE_HITS = Counter(
    "user_service_cache_hits_total",
    "Total cache hits",
    ["cache_type"],
)

CACHE_MISSES = Counter(
    "user_service_cache_misses_total",
    "Total cache misses",
    ["cache_type"],
)

# ── Active Users Gauge ────────────────────────────────────────────────

ACTIVE_USERS = Gauge(
    "user_service_active_users",
    "Number of users active in the last 15 minutes",
)
