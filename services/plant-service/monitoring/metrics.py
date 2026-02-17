from prometheus_client import Counter, Histogram, Gauge

# Plant operation counters
PLANTS_CREATED = Counter(
    "plant_service_plants_created_total",
    "Total number of plants created",
)

PLANTS_UPDATED = Counter(
    "plant_service_plants_updated_total",
    "Total number of plants updated",
)

PLANTS_DELETED = Counter(
    "plant_service_plants_deleted_total",
    "Total number of plants deleted",
)

# Verification workflow counters
PLANTS_SUBMITTED = Counter(
    "plant_service_plants_submitted_total",
    "Total plants submitted for review",
)

PLANTS_APPROVED = Counter(
    "plant_service_plants_approved_total",
    "Total plants approved",
)

PLANTS_REJECTED = Counter(
    "plant_service_plants_rejected_total",
    "Total plants rejected",
)

# Compound counters
COMPOUNDS_CREATED = Counter(
    "plant_service_compounds_created_total",
    "Total compounds created",
)

COMPOUNDS_LINKED = Counter(
    "plant_service_compounds_linked_total",
    "Total compound-plant links created",
)

# External API metrics
PUBMED_REQUESTS = Counter(
    "plant_service_pubmed_requests_total",
    "Total PubMed API requests",
    ["endpoint", "status"],
)

PUBCHEM_REQUESTS = Counter(
    "plant_service_pubchem_requests_total",
    "Total PubChem API requests",
    ["endpoint", "status"],
)

EXTERNAL_API_LATENCY = Histogram(
    "plant_service_external_api_latency_seconds",
    "External API call latency in seconds",
    ["service"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# Cache metrics
CACHE_HITS = Counter(
    "plant_service_cache_hits_total",
    "Total cache hits",
)

CACHE_MISSES = Counter(
    "plant_service_cache_misses_total",
    "Total cache misses",
)

# Database metrics
DB_QUERY_LATENCY = Histogram(
    "plant_service_db_query_latency_seconds",
    "Database query latency in seconds",
    ["operation"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)

# Active connections gauge
ACTIVE_DB_CONNECTIONS = Gauge(
    "plant_service_active_db_connections",
    "Number of active database connections",
)
