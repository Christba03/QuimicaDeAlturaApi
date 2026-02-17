from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query

from src.schemas.conversation import (
    ConversationListResponse,
    ConversationResponse,
    MessageResponse,
)
from src.services.conversation_service import ConversationService

logger = structlog.get_logger()
router = APIRouter()


def get_conversation_service() -> ConversationService:
    return ConversationService()


@router.get("/", response_model=ConversationListResponse)
async def list_conversations(
    user_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: ConversationService = Depends(get_conversation_service),
):
    """List all conversations for a user."""
    try:
        conversations = await service.list_conversations(
            user_id=user_id, skip=skip, limit=limit
        )
        return ConversationListResponse(
            conversations=conversations,
            total=len(conversations),
        )
    except Exception as e:
        logger.error("Failed to list conversations", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list conversations")


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    service: ConversationService = Depends(get_conversation_service),
):
    """Get a conversation with its message history."""
    try:
        conversation = await service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get conversation", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get conversation")


@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
async def get_conversation_history(
    conversation_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: ConversationService = Depends(get_conversation_service),
):
    """Get message history for a conversation."""
    try:
        messages = await service.get_messages(
            conversation_id=conversation_id, skip=skip, limit=limit
        )
        return messages
    except Exception as e:
        logger.error("Failed to get conversation history", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get conversation history")


@router.delete("/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: UUID,
    service: ConversationService = Depends(get_conversation_service),
):
    """Delete a conversation and all its messages."""
    try:
        deleted = await service.delete_conversation(conversation_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Conversation not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete conversation", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete conversation")
