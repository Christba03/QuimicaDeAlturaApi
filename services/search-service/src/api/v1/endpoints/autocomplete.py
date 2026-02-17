from fastapi import APIRouter, Depends, Query

from src.config import get_settings
from src.services.search_service import SearchService

router = APIRouter(prefix="/autocomplete", tags=["autocomplete"])


def get_search_service() -> SearchService:
    return SearchService(settings=get_settings())


@router.get("/")
async def autocomplete(
    q: str = Query(..., min_length=1, description="Partial query for suggestions"),
    type: str = Query("all", description="Suggestion type: all, plant, compound"),
    limit: int = Query(10, ge=1, le=50),
    service: SearchService = Depends(get_search_service),
):
    """Get autocomplete suggestions for plant names, compounds, etc."""
    suggestions = await service.autocomplete(
        query=q,
        suggestion_type=type,
        limit=limit,
    )
    return {"suggestions": suggestions}


@router.get("/popular")
async def popular_searches(
    limit: int = Query(10, ge=1, le=50),
    service: SearchService = Depends(get_search_service),
):
    """Get popular/trending search terms."""
    return await service.get_popular_searches(limit=limit)
