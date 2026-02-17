from datetime import datetime, timedelta
from uuid import UUID

import structlog
from sqlalchemy import delete, select, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import selectinload

from src.config import settings
from src.models.conversation import Conversation
from src.models.message import Message
from src.repositories.conversation_repository import ConversationRepository
from src.repositories.message_repository import MessageRepository
from src.schemas.chat import FeedbackResponse, FeedbackStatsResponse
from src.schemas.conversation import ConversationResponse, MessageResponse

logger = structlog.get_logger()

engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)


class ConversationService:
    """Service for managing conversations and messages."""

    def __init__(self):
        self.conversation_repo = ConversationRepository(engine)
        self.message_repo = MessageRepository(engine)

    async def create_conversation(
        self,
        user_id: UUID,
        title: str | None = None,
        language: str = "es",
    ) -> ConversationResponse:
        """Create a new conversation."""
        conversation = await self.conversation_repo.create(
            user_id=user_id,
            title=title,
            language=language,
        )
        return ConversationResponse(
            id=conversation.id,
            user_id=conversation.user_id,
            title=conversation.title,
            status=conversation.status,
            language=conversation.language,
            messages=[],
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
        )

    async def get_conversation(self, conversation_id: UUID) -> ConversationResponse | None:
        """Get a conversation with its messages."""
        conversation = await self.conversation_repo.get_with_messages(conversation_id)
        if not conversation:
            return None

        messages = [
            MessageResponse(
                id=msg.id,
                conversation_id=msg.conversation_id,
                role=msg.role,
                content=msg.content,
                intent=msg.intent,
                entities=msg.entities,
                feedback_rating=msg.feedback_rating,
                created_at=msg.created_at,
            )
            for msg in conversation.messages
        ]

        return ConversationResponse(
            id=conversation.id,
            user_id=conversation.user_id,
            title=conversation.title,
            status=conversation.status,
            language=conversation.language,
            messages=messages,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
        )

    async def list_bokehconversations(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> list[ConversationResponse]:
        """List conversations for a user."""
        conversations = await self.conversation_repo.list_by_user(
            user_id=user_id, skip=skip, limit=limit
        )
        return [
            ConversationResponse(
                id=conv.id,
                user_id=conv.user_id,
                title=conv.title,
                status=conv.status,
                language=conv.language,
                messages=[],
                created_at=conv.created_at,
                updated_at=conv.updated_at,
            )
            for conv in conversations
        ]

    async def list_conversations(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> list[ConversationResponse]:
        """List conversations for a user."""
        conversations = await self.conversation_repo.list_by_user(
            user_id=user_id, skip=skip, limit=limit
        )
        return [
            ConversationResponse(
                id=conv.id,
                user_id=conv.user_id,
                title=conv.title,
                status=conv.status,
                language=conv.language,
                messages=[],
                created_at=conv.created_at,
                updated_at=conv.updated_at,
            )
            for conv in conversations
        ]

    async def delete_conversation(self, conversation_id: UUID) -> bool:
        """Soft-delete a conversation by setting status to deleted."""
        return await self.conversation_repo.soft_delete(conversation_id)

    async def get_messages(
        self,
        conversation_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> list[MessageResponse]:
        """Get messages for a conversation."""
        messages = await self.message_repo.list_by_conversation(
            conversation_id=conversation_id, skip=skip, limit=limit
        )
        return [
            MessageResponse(
                id=msg.id,
                conversation_id=msg.conversation_id,
                role=msg.role,
                content=msg.content,
                intent=msg.intent,
                entities=msg.entities,
                feedback_rating=msg.feedback_rating,
                created_at=msg.created_at,
            )
            for msg in messages
        ]

    async def add_message(
        self,
        conversation_id: UUID,
        role: str,
        content: str,
        intent: str | None = None,
        entities: list[dict] | None = None,
    ) -> MessageResponse:
        """Add a message to a conversation."""
        message = await self.message_repo.create(
            conversation_id=conversation_id,
            role=role,
            content=content,
            intent=intent,
            entities=entities,
        )
        return MessageResponse(
            id=message.id,
            conversation_id=message.conversation_id,
            role=message.role,
            content=message.content,
            intent=message.intent,
            entities=message.entities,
            feedback_rating=message.feedback_rating,
            created_at=message.created_at,
        )

    async def submit_feedback(
        self,
        message_id: UUID,
        user_id: UUID,
        rating: int,
        comment: str | None = None,
    ) -> FeedbackResponse:
        """Submit feedback on a chatbot message."""
        updated = await self.message_repo.update_feedback(
            message_id=message_id,
            rating=rating,
            comment=comment,
        )
        return FeedbackResponse(
            message_id=message_id,
            rating=rating,
            comment=comment,
            recorded_at=datetime.utcnow(),
        )

    async def get_feedback_stats(self, days: int = 30) -> FeedbackStatsResponse:
        """Get aggregated feedback statistics."""
        stats = await self.message_repo.get_feedback_stats(days=days)
        total = stats.get("total", 0)
        positive = stats.get("positive", 0)
        negative = stats.get("negative", 0)
        neutral = stats.get("neutral", 0)
        positive_rate = positive / total if total > 0 else 0.0

        return FeedbackStatsResponse(
            total_feedback=total,
            positive=positive,
            negative=negative,
            neutral=neutral,
            positive_rate=positive_rate,
            period_days=days,
        )
