from uuid import UUID

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.orm import selectinload

from src.models.conversation import Conversation

logger = structlog.get_logger()


class ConversationRepository:
    """Database operations for conversations."""

    def __init__(self, engine: AsyncEngine):
        self.engine = engine

    async def create(
        self,
        user_id: UUID,
        title: str | None = None,
        language: str = "es",
    ) -> Conversation:
        """Create a new conversation."""
        async with AsyncSession(self.engine) as session:
            conversation = Conversation(
                user_id=user_id,
                title=title,
                language=language,
                status="active",
            )
            session.add(conversation)
            await session.commit()
            await session.refresh(conversation)
            return conversation

    async def get_by_id(self, conversation_id: UUID) -> Conversation | None:
        """Get a conversation by ID."""
        async with AsyncSession(self.engine) as session:
            stmt = select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.status != "deleted",
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_with_messages(self, conversation_id: UUID) -> Conversation | None:
        """Get a conversation with all its messages eagerly loaded."""
        async with AsyncSession(self.engine) as session:
            stmt = (
                select(Conversation)
                .options(selectinload(Conversation.messages))
                .where(
                    Conversation.id == conversation_id,
                    Conversation.status != "deleted",
                )
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Conversation]:
        """List conversations for a user, ordered by most recent."""
        async with AsyncSession(self.engine) as session:
            stmt = (
                select(Conversation)
                .where(
                    Conversation.user_id == user_id,
                    Conversation.status != "deleted",
                )
                .order_by(Conversation.updated_at.desc())
                .offset(skip)
                .limit(limit)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def soft_delete(self, conversation_id: UUID) -> bool:
        """Soft-delete a conversation by setting its status to 'deleted'."""
        async with AsyncSession(self.engine) as session:
            stmt = (
                update(Conversation)
                .where(Conversation.id == conversation_id)
                .values(status="deleted")
                .returning(Conversation.id)
            )
            result = await session.execute(stmt)
            await session.commit()
            return result.scalar_one_or_none() is not None

    async def update_title(self, conversation_id: UUID, title: str) -> Conversation | None:
        """Update a conversation title."""
        async with AsyncSession(self.engine) as session:
            stmt = (
                update(Conversation)
                .where(Conversation.id == conversation_id)
                .values(title=title)
                .returning(Conversation.id)
            )
            result = await session.execute(stmt)
            await session.commit()
            if result.scalar_one_or_none():
                return await self.get_by_id(conversation_id)
            return None
