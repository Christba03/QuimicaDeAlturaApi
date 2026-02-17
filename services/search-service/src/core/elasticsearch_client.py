from __future__ import annotations

import structlog
from elasticsearch import AsyncElasticsearch

from src.config import settings

logger = structlog.get_logger(__name__)

# Module-level client reference managed via lifespan
_client: AsyncElasticsearch | None = None

# ------------------------------------------------------------------
# Index mappings for the medicinal-plants domain
# ------------------------------------------------------------------

PLANTS_MAPPING = {
    "mappings": {
        "properties": {
            "id": {"type": "keyword"},
            "scientific_name": {
                "type": "text",
                "analyzer": "standard",
                "fields": {
                    "keyword": {"type": "keyword"},
                    "suggest": {"type": "completion"},
                },
            },
            "common_names": {
                "type": "text",
                "analyzer": "standard",
                "fields": {
                    "keyword": {"type": "keyword"},
                    "suggest": {"type": "completion"},
                },
            },
            "family": {"type": "keyword"},
            "genus": {"type": "keyword"},
            "description": {"type": "text", "analyzer": "standard"},
            "traditional_uses": {"type": "text", "analyzer": "standard"},
            "habitat": {"type": "text", "analyzer": "standard"},
            "altitude_min": {"type": "integer"},
            "altitude_max": {"type": "integer"},
            "region": {"type": "keyword"},
            "tags": {"type": "keyword"},
            "created_at": {"type": "date"},
            "updated_at": {"type": "date"},
        }
    },
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "analysis": {
            "analyzer": {
                "standard": {
                    "type": "standard",
                    "stopwords": "_spanish_",
                }
            }
        },
    },
}

COMPOUNDS_MAPPING = {
    "mappings": {
        "properties": {
            "id": {"type": "keyword"},
            "name": {
                "type": "text",
                "analyzer": "standard",
                "fields": {
                    "keyword": {"type": "keyword"},
                    "suggest": {"type": "completion"},
                },
            },
            "iupac_name": {"type": "text"},
            "molecular_formula": {"type": "keyword"},
            "molecular_weight": {"type": "float"},
            "compound_class": {"type": "keyword"},
            "description": {"type": "text", "analyzer": "standard"},
            "plant_ids": {"type": "keyword"},
            "biological_activities": {"type": "keyword"},
            "cas_number": {"type": "keyword"},
            "created_at": {"type": "date"},
            "updated_at": {"type": "date"},
        }
    },
    "settings": {"number_of_shards": 1, "number_of_replicas": 0},
}

ACTIVITIES_MAPPING = {
    "mappings": {
        "properties": {
            "id": {"type": "keyword"},
            "name": {
                "type": "text",
                "fields": {
                    "keyword": {"type": "keyword"},
                    "suggest": {"type": "completion"},
                },
            },
            "category": {"type": "keyword"},
            "description": {"type": "text", "analyzer": "standard"},
            "compound_ids": {"type": "keyword"},
            "plant_ids": {"type": "keyword"},
            "evidence_level": {"type": "keyword"},
            "created_at": {"type": "date"},
            "updated_at": {"type": "date"},
        }
    },
    "settings": {"number_of_shards": 1, "number_of_replicas": 0},
}

INDEX_MAPPINGS: dict[str, dict] = {
    settings.ES_INDEX_PLANTS: PLANTS_MAPPING,
    settings.ES_INDEX_COMPOUNDS: COMPOUNDS_MAPPING,
    settings.ES_INDEX_ACTIVITIES: ACTIVITIES_MAPPING,
}


# ------------------------------------------------------------------
# Client lifecycle helpers
# ------------------------------------------------------------------


async def create_client() -> AsyncElasticsearch:
    """Create and return an async Elasticsearch client."""
    global _client

    kwargs: dict = {
        "hosts": [settings.elasticsearch_url],
        "verify_certs": settings.ELASTICSEARCH_VERIFY_CERTS,
    }
    if settings.ELASTICSEARCH_USERNAME and settings.ELASTICSEARCH_PASSWORD:
        kwargs["basic_auth"] = (
            settings.ELASTICSEARCH_USERNAME,
            settings.ELASTICSEARCH_PASSWORD,
        )
    if settings.ELASTICSEARCH_CA_CERTS:
        kwargs["ca_certs"] = settings.ELASTICSEARCH_CA_CERTS

    _client = AsyncElasticsearch(**kwargs)
    logger.info(
        "elasticsearch_client_created",
        url=settings.elasticsearch_url,
    )
    return _client


async def close_client() -> None:
    """Close the Elasticsearch client."""
    global _client
    if _client is not None:
        await _client.close()
        _client = None
        logger.info("elasticsearch_client_closed")


def get_client() -> AsyncElasticsearch:
    """Return the current Elasticsearch client, raising if not initialised."""
    if _client is None:
        raise RuntimeError("Elasticsearch client has not been initialised")
    return _client


# ------------------------------------------------------------------
# Index management
# ------------------------------------------------------------------


async def ensure_indices() -> None:
    """Create indices with their mappings if they do not already exist."""
    client = get_client()
    for index_name, body in INDEX_MAPPINGS.items():
        exists = await client.indices.exists(index=index_name)
        if not exists:
            await client.indices.create(index=index_name, body=body)
            logger.info("index_created", index=index_name)
        else:
            logger.info("index_already_exists", index=index_name)


async def health_check() -> dict:
    """Return basic cluster health information."""
    client = get_client()
    try:
        info = await client.cluster.health()
        return {
            "status": info.get("status", "unknown"),
            "number_of_nodes": info.get("number_of_nodes", 0),
            "active_shards": info.get("active_shards", 0),
        }
    except Exception as exc:
        logger.error("elasticsearch_health_check_failed", error=str(exc))
        return {"status": "unavailable", "error": str(exc)}
