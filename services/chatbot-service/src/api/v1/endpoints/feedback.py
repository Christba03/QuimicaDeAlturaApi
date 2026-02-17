from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException

from src.schemas.chat import FeedbackRequest, FeedbackResponse, FeedbackStatsResponse
from src.services.conversation_service import ConversationService

logger = structlog.get_logger()
router = APIRouter()


def get_conversation_service() -> ConversationService:
    return ConversationService()


@router.post("/", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackRequest,
    service: ConversationService = Depends(get_conversation_service),
):
    """Submit feedback (thumbs up/down) on a chatbot message."""
    try:
        feedback = await service.submit_feedback(
            message_id=request.message_id,
            user_id=request.user_id,
            rating=request.rating,
            comment=request.comment,
        )
        return feedback
    except Exception as e:
        logger.error("Failed to submit feedback", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to submit feedback")


@router.get("/stats", response_model=FeedbackStatsResponse)
async def get_feedback_stats(
    days: int = 30,
    service: ConversationService = Depends(get_conversation_service),
):
    """Get aggregated feedback statistics."""
    try:
        stats = await service.get_feedback_stats(days=days)
        return stats
    except Exception as e:
        logger.error("Failed to get feedback stats", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get feedback stats")
