from fastapi import APIRouter, Depends, Query

from src.config import get_settings
from src.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["search"])


def get_search_service() -> SearchService:
    return SearchService(settings=get_settings())


@router.get("/")
async def search_plants(
    q: str = Query(..., min_length=1, description="Search query"),
    category: str | None = Query(None, description="Filter by category: plant, compound, activity"),
    family: str | None = Query(None, description="Filter by taxonomic family"),
    state: str | None = Query(None, description="Filter by Mexican state"),
    verification_status: str | None = Query(None, description="Filter by verification status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: SearchService = Depends(get_search_service),
):
    """Full-text search across plants, compounds, and activities."""
    filters = {}
    if category:
        filters["category"] = category
    if family:
        filters["family"] = family
    if state:
        filters["state"] = state
    if verification_status:
        filters["verification_status"] = verification_status

    results = await service.search(
        query=q,
        filters=filters,
        page=page,
        page_size=page_size,
    )
    return results


@router.get("/facets")
async def get_search_facets(
    q: str = Query("", description="Optional query to scope facets"),
    service: SearchService = Depends(get_search_service),
):
    """Get available facets/filters for search results."""
    return await service.get_facets(query=q)
