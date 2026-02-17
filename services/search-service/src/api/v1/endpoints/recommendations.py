from fastapi import APIRouter, Depends, Query

from src.config import get_settings
from src.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


def get_recommendation_service() -> RecommendationService:
    return RecommendationService(settings=get_settings())


@router.get("/plants/{plant_id}/related")
async def get_related_plants(
    plant_id: str,
    limit: int = Query(5, ge=1, le=20),
    service: RecommendationService = Depends(get_recommendation_service),
):
    """Get plants related to a specific plant (by shared compounds, activities, taxonomy)."""
    return await service.get_related_plants(plant_id=plant_id, limit=limit)


@router.get("/compounds/{compound_id}/similar")
async def get_similar_compounds(
    compound_id: str,
    limit: int = Query(5, ge=1, le=20),
    service: RecommendationService = Depends(get_recommendation_service),
):
    """Get compounds similar to a specific compound."""
    return await service.get_similar_compounds(compound_id=compound_id, limit=limit)


@router.get("/user/{user_id}")
async def get_user_recommendations(
    user_id: str,
    limit: int = Query(10, ge=1, le=50),
    service: RecommendationService = Depends(get_recommendation_service),
):
    """Get personalized plant recommendations based on user history."""
    return await service.get_user_recommendations(user_id=user_id, limit=limit)
