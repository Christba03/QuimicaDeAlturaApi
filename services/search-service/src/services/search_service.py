from __future__ import annotations

from typing import Any

import structlog

from src.config import settings
from src.core.elasticsearch_client import get_client

logger = structlog.get_logger(__name__)


# ------------------------------------------------------------------
# Query builders
# ------------------------------------------------------------------


def _build_multi_match_query(
    query: str,
    fields: list[str] | None = None,
    fuzziness: str = "AUTO",
) -> dict:
    """Build a multi_match query with optional fuzziness."""
    default_fields = [
        "scientific_name^3",
        "common_names^2",
        "description",
        "traditional_uses",
        "name^3",
        "iupac_name",
        "habitat",
    ]
    return {
        "multi_match": {
            "query": query,
            "fields": fields or default_fields,
            "type": "best_fields",
            "fuzziness": fuzziness,
            "prefix_length": 2,
        }
    }


def _build_filters(
    family: str | None = None,
    genus: str | None = None,
    region: str | None = None,
    compound_class: str | None = None,
    evidence_level: str | None = None,
    altitude_min: int | None = None,
    altitude_max: int | None = None,
    tags: list[str] | None = None,
) -> list[dict]:
    """Return a list of Elasticsearch filter clauses."""
    filters: list[dict] = []
    if family:
        filters.append({"term": {"family": family}})
    if genus:
        filters.append({"term": {"genus": genus}})
    if region:
        filters.append({"term": {"region": region}})
    if compound_class:
        filters.append({"term": {"compound_class": compound_class}})
    if evidence_level:
        filters.append({"term": {"evidence_level": evidence_level}})
    if altitude_min is not None:
        filters.append({"range": {"altitude_max": {"gte": altitude_min}}})
    if altitude_max is not None:
        filters.append({"range": {"altitude_min": {"lte": altitude_max}}})
    if tags:
        filters.append({"terms": {"tags": tags}})
    return filters


def _build_aggregations() -> dict:
    """Standard facet aggregations returned alongside search results."""
    return {
        "families": {"terms": {"field": "family", "size": 30}},
        "genera": {"terms": {"field": "genus", "size": 30}},
        "regions": {"terms": {"field": "region", "size": 30}},
        "compound_classes": {"terms": {"field": "compound_class", "size": 30}},
        "evidence_levels": {"terms": {"field": "evidence_level", "size": 10}},
        "tags": {"terms": {"field": "tags", "size": 50}},
    }


# ------------------------------------------------------------------
# Search operations
# ------------------------------------------------------------------


async def full_text_search(
    query: str,
    indices: list[str] | None = None,
    family: str | None = None,
    genus: str | None = None,
    region: str | None = None,
    compound_class: str | None = None,
    evidence_level: str | None = None,
    altitude_min: int | None = None,
    altitude_max: int | None = None,
    tags: list[str] | None = None,
    page: int = 1,
    page_size: int | None = None,
    include_facets: bool = True,
) -> dict[str, Any]:
    """Execute a full-text search across one or more indices with filters and facets."""
    client = get_client()
    page_size = min(
        page_size or settings.SEARCH_DEFAULT_PAGE_SIZE,
        settings.SEARCH_MAX_PAGE_SIZE,
    )
    offset = (page - 1) * page_size

    target_indices = indices or [
        settings.ES_INDEX_PLANTS,
        settings.ES_INDEX_COMPOUNDS,
        settings.ES_INDEX_ACTIVITIES,
    ]

    filters = _build_filters(
        family=family,
        genus=genus,
        region=region,
        compound_class=compound_class,
        evidence_level=evidence_level,
        altitude_min=altitude_min,
        altitude_max=altitude_max,
        tags=tags,
    )

    body: dict[str, Any] = {
        "query": {
            "bool": {
                "must": [_build_multi_match_query(query)],
                "filter": filters,
            }
        },
        "from": offset,
        "size": page_size,
        "highlight": {
            "fields": {
                "scientific_name": {},
                "common_names": {},
                "description": {"fragment_size": 200, "number_of_fragments": 2},
                "traditional_uses": {"fragment_size": 200, "number_of_fragments": 2},
                "name": {},
            }
        },
    }

    if include_facets:
        body["aggs"] = _build_aggregations()

    logger.info(
        "executing_search",
        query=query,
        indices=target_indices,
        page=page,
        page_size=page_size,
    )

    response = await client.search(index=",".join(target_indices), body=body)

    hits = response["hits"]
    results = []
    for hit in hits["hits"]:
        item = {
            "id": hit["_id"],
            "index": hit["_index"],
            "score": hit["_score"],
            **hit["_source"],
        }
        if "highlight" in hit:
            item["highlight"] = hit["highlight"]
        results.append(item)

    output: dict[str, Any] = {
        "total": hits["total"]["value"],
        "page": page,
        "page_size": page_size,
        "results": results,
    }

    if include_facets and "aggregations" in response:
        facets: dict[str, list[dict]] = {}
        for agg_name, agg_data in response["aggregations"].items():
            facets[agg_name] = [
                {"key": bucket["key"], "count": bucket["doc_count"]}
                for bucket in agg_data.get("buckets", [])
            ]
        output["facets"] = facets

    return output


async def search_single_index(
    index: str,
    query: str,
    page: int = 1,
    page_size: int | None = None,
) -> dict[str, Any]:
    """Convenience wrapper to search a single index."""
    return await full_text_search(
        query=query,
        indices=[index],
        page=page,
        page_size=page_size,
        include_facets=False,
    )


async def get_document_by_id(index: str, doc_id: str) -> dict[str, Any] | None:
    """Retrieve a single document by ID."""
    client = get_client()
    try:
        resp = await client.get(index=index, id=doc_id)
        return {"id": resp["_id"], "index": resp["_index"], **resp["_source"]}
    except Exception:
        return None


class SearchService:
    """Thin class wrapper around module-level search functions for DI compatibility."""

    def __init__(self, settings=None):
        pass

    async def search(self, query: str, filters: dict | None = None, page: int = 1, page_size: int = 20) -> dict:
        filters = filters or {}
        return await full_text_search(
            query=query,
            family=filters.get("family"),
            region=filters.get("state"),
            page=page,
            page_size=page_size,
        )

    async def get_facets(self, query: str = "") -> dict:
        result = await full_text_search(query=query or "*", include_facets=True, page_size=0)
        return result.get("facets", {})

    async def autocomplete(self, query: str, suggestion_type: str = "all", limit: int = 10) -> list:
        indices = None
        if suggestion_type == "plant":
            indices = [settings.ES_INDEX_PLANTS]
        elif suggestion_type == "compound":
            indices = [settings.ES_INDEX_COMPOUNDS]
        result = await full_text_search(query=query, indices=indices, page_size=limit, include_facets=False)
        hits = result.get("hits", [])
        return [{"id": h.get("id"), "label": h.get("scientific_name") or h.get("name", "")} for h in hits]

    async def get_popular_searches(self, limit: int = 10) -> list:
        result = await full_text_search(query="*", page_size=limit, include_facets=False)
        hits = result.get("hits", [])
        return [h.get("scientific_name") or h.get("name", "") for h in hits]
