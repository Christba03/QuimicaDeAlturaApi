from datetime import datetime, timedelta
from uuid import UUID

import structlog
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from src.models.message import Message

logger = structlog.get_logger()


class MessageRepository:
    """Database operations for messages."""

    def __init__(self, engine: AsyncEngine):
        self.engine = engine

    async def create(
        self,
        conversation_id: UUID,
        role: str,
        content: str,
        intent: str | None = None,
        entities: list[dict] | None = None,
        metadata: dict | None = None,
    ) -> Message:
        """Create a new message."""
        async with AsyncSession(self.engine) as session:
            message = Message(
                conversation_id=conversation_id,
                role=role,
                content=content,
                intent=intent,
                entities=entities,
                metadata_=metadata,
            )
            session.add(message)
            await session.commit()
            await session.refresh(message)
            return message

    async def get_by_id(self, message_id: UUID) -> Message | None:
        """Get a message by ID."""
        async with AsyncSession(self.engine) as session:
            stmt = select(Message).where(Message.id == message_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def list_by_conversation(
        self,
        conversation_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Message]:
        """List messages for a conversation, ordered chronologically."""
        async with AsyncSession(self.engine) as session:
            stmt = (
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at.asc())
                .offset(skip)
                .limit(limit)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def update_feedback(
        self,
        message_id: UUID,
        rating: int,
        comment: str | None = None,
    ) -> bool:
        """Update feedback on a message."""
        async with AsyncSession(self.engine) as session:
            stmt = (
                update(Message)
                .where(Message.id == message_id)
                .values(feedback_rating=rating, feedback_comment=comment)
                .returning(Message.id)
            )
            result = await session.execute(stmt)
            await session.commit()
            return result.scalar_one_or_none() is not None

    async def get_feedback_stats(self, days: int = 30) -> dict:
        """Get aggregated feedback statistics for the given period."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        async with AsyncSession(self.engine) as session:
            stmt = (
                select(
                    func.count().label("total"),
                    func.count()
                    .filter(Message.feedback_rating == 1)
                    .label("positive"),
                    func.count()
                    .filter(Message.feedback_rating == -1)
                    .label("negative"),
                    func.count()
                    .filter(Message.feedback_rating == 0)
                    .label("neutral"),
                )
                .where(
                    Message.feedback_rating.isnot(None),
                    Message.created_at >= cutoff,
                )
            )
            result = await session.execute(stmt)
            row = result.one()
            return {
                "total": row.total,
                "positive": row.positive,
                "negative": row.negative,
                "neutral": row.neutral,
            }
