from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException

from src.schemas.chat import ChatRequest, ChatResponse, QuickReply, QuickReplyResponse
from src.services.chatbot_service import ChatbotService

logger = structlog.get_logger()
router = APIRouter()


def get_chatbot_service() -> ChatbotService:
    return ChatbotService()


@router.post("/send", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    service: ChatbotService = Depends(get_chatbot_service),
):
    """Send a message to the chatbot and receive an AI-generated response."""
    try:
        response = await service.process_message(
            user_id=request.user_id,
            conversation_id=request.conversation_id,
            message=request.message,
            language=request.language,
        )
        return response
    except Exception as e:
        logger.error("Failed to process chat message", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to process message")


@router.get("/quick-replies", response_model=QuickReplyResponse)
async def get_quick_replies(language: str = "es"):
    """Get suggested quick reply options for the user."""
    quick_replies = [
        QuickReply(
            id="plant_search",
            label="Buscar planta medicinal" if language == "es" else "Search medicinal plant",
            intent="plant_query",
        ),
        QuickReply(
            id="symptom_query",
            label="Tengo un sintoma" if language == "es" else "I have a symptom",
            intent="symptom_query",
        ),
        QuickReply(
            id="compound_info",
            label="Informacion sobre compuestos" if language == "es" else "Compound information",
            intent="compound_query",
        ),
        QuickReply(
            id="preparation_guide",
            label="Como preparar un remedio" if language == "es" else "How to prepare a remedy",
            intent="preparation_query",
        ),
        QuickReply(
            id="safety_info",
            label="Seguridad y contraindicaciones" if language == "es" else "Safety and contraindications",
            intent="safety_query",
        ),
    ]
    return QuickReplyResponse(quick_replies=quick_replies, language=language)
