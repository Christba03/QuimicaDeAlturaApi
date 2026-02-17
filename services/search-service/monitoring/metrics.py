from prometheus_client import Counter, Histogram

SEARCH_REQUESTS = Counter(
    "search_requests_total",
    "Total search requests",
    ["type", "status"],
)

SEARCH_LATENCY = Histogram(
    "search_latency_seconds",
    "Search request latency",
    ["type"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5],
)

SEARCH_RESULTS_COUNT = Histogram(
    "search_results_count",
    "Number of results returned per search",
    ["type"],
    buckets=[0, 1, 5, 10, 20, 50, 100],
)

AUTOCOMPLETE_REQUESTS = Counter(
    "autocomplete_requests_total",
    "Total autocomplete requests",
    ["status"],
)
