from __future__ import annotations

from typing import Any

import structlog

from src.config import settings
from src.core.elasticsearch_client import get_client

logger = structlog.get_logger(__name__)


async def get_related_plants(
    plant_id: str,
    max_items: int | None = None,
) -> list[dict[str, Any]]:
    """Return plants related to *plant_id* using a More Like This query.

    Similarity is based on shared family, genus, traditional uses, and
    habitat descriptions.
    """
    client = get_client()
    limit = min(max_items or settings.RECOMMENDATION_MAX_ITEMS, 50)

    body = {
        "query": {
            "more_like_this": {
                "fields": [
                    "family",
                    "genus",
                    "traditional_uses",
                    "habitat",
                    "tags",
                    "description",
                ],
                "like": [
                    {
                        "_index": settings.ES_INDEX_PLANTS,
                        "_id": plant_id,
                    }
                ],
                "min_term_freq": 1,
                "min_doc_freq": 1,
                "max_query_terms": 25,
            }
        },
        "size": limit,
    }

    logger.info("get_related_plants", plant_id=plant_id, limit=limit)

    response = await client.search(index=settings.ES_INDEX_PLANTS, body=body)

    return [
        {
            "id": hit["_id"],
            "score": hit["_score"],
            **hit["_source"],
        }
        for hit in response["hits"]["hits"]
    ]


async def get_similar_compounds(
    compound_id: str,
    max_items: int | None = None,
) -> list[dict[str, Any]]:
    """Return compounds similar to *compound_id*.

    Similarity is determined by shared compound class, biological activities,
    and description text.
    """
    client = get_client()
    limit = min(max_items or settings.RECOMMENDATION_MAX_ITEMS, 50)

    body = {
        "query": {
            "more_like_this": {
                "fields": [
                    "compound_class",
                    "biological_activities",
                    "description",
                    "name",
                ],
                "like": [
                    {
                        "_index": settings.ES_INDEX_COMPOUNDS,
                        "_id": compound_id,
                    }
                ],
                "min_term_freq": 1,
                "min_doc_freq": 1,
                "max_query_terms": 25,
            }
        },
        "size": limit,
    }

    logger.info("get_similar_compounds", compound_id=compound_id, limit=limit)

    response = await client.search(index=settings.ES_INDEX_COMPOUNDS, body=body)

    return [
        {
            "id": hit["_id"],
            "score": hit["_score"],
            **hit["_source"],
        }
        for hit in response["hits"]["hits"]
    ]


async def get_plants_for_activity(
    activity_id: str,
    max_items: int | None = None,
) -> list[dict[str, Any]]:
    """Given a biological activity, return plants linked to it.

    First retrieves the activity document to get the list of associated
    plant IDs, then fetches those plants.
    """
    client = get_client()
    limit = min(max_items or settings.RECOMMENDATION_MAX_ITEMS, 50)

    try:
        activity = await client.get(
            index=settings.ES_INDEX_ACTIVITIES, id=activity_id
        )
    except Exception:
        logger.warning("activity_not_found", activity_id=activity_id)
        return []

    plant_ids: list[str] = activity["_source"].get("plant_ids", [])
    if not plant_ids:
        return []

    body = {
        "query": {"ids": {"values": plant_ids[:limit]}},
        "size": limit,
    }

    response = await client.search(index=settings.ES_INDEX_PLANTS, body=body)

    return [
        {
            "id": hit["_id"],
            "score": hit["_score"],
            **hit["_source"],
        }
        for hit in response["hits"]["hits"]
    ]


async def get_compounds_for_plant(
    plant_id: str,
    max_items: int | None = None,
) -> list[dict[str, Any]]:
    """Return compounds associated with *plant_id*."""
    client = get_client()
    limit = min(max_items or settings.RECOMMENDATION_MAX_ITEMS, 50)

    body = {
        "query": {"term": {"plant_ids": plant_id}},
        "size": limit,
    }

    response = await client.search(index=settings.ES_INDEX_COMPOUNDS, body=body)

    return [
        {
            "id": hit["_id"],
            "score": hit["_score"],
            **hit["_source"],
        }
        for hit in response["hits"]["hits"]
    ]


class RecommendationService:
    """Thin class wrapper around module-level recommendation functions for DI compatibility."""

    def __init__(self, settings=None):
        pass

    async def get_related_plants(self, plant_id: str, limit: int = 5) -> dict:
        return await get_related_plants(plant_id=plant_id, limit=limit)

    async def get_similar_compounds(self, compound_id: str, limit: int = 5) -> dict:
        return await get_similar_compounds(compound_id=compound_id, limit=limit)

    async def get_user_recommendations(self, user_id: str, limit: int = 10) -> dict:
        return await get_plants_for_activity(activity_id=user_id, limit=limit)
