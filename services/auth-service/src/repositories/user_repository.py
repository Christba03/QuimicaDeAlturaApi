import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.user import User
from src.models.role import Role


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        stmt = select(User).options(selectinload(User.roles)).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).options(selectinload(User.roles)).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_users(
        self,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
        verified: bool | None = None,
        role: str | None = None,
    ) -> tuple[list[User], int]:
        """List users with optional filters and pagination."""
        stmt = select(User)
        count_stmt = select(func.count()).select_from(User)
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)

        # Apply filters
        if status == "locked":
            stmt = stmt.where(User.locked_until > now)
            count_stmt = count_stmt.where(User.locked_until > now)
        elif status == "active":
            stmt = stmt.where(User.is_active == True)
            count_stmt = count_stmt.where(User.is_active == True)
        elif status == "inactive":
            stmt = stmt.where(User.is_active == False)
            count_stmt = count_stmt.where(User.is_active == False)

        if verified is not None:
            stmt = stmt.where(User.email_verified == verified)
            count_stmt = count_stmt.where(User.email_verified == verified)

        if role is not None:
            stmt = stmt.join(User.roles).where(Role.name == role)
            count_stmt = count_stmt.join(User.roles).where(Role.name == role)

        # Count total
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        # Fetch page
        offset = (page - 1) * page_size
        stmt = (
            stmt.options(selectinload(User.roles))
            .order_by(User.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self.session.execute(stmt)
        users = list(result.scalars().all())
        return users, total

    async def create(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        # Refresh so server-generated created_at/updated_at (and roles) are loaded for response serialization
        await self.session.refresh(user)
        return user

    async def update(self, user: User, update_data: dict) -> User:
        for key, value in update_data.items():
            if key == "role_ids":
                continue
            setattr(user, key, value)

        if "role_ids" in update_data and update_data["role_ids"] is not None:
            role_ids = update_data["role_ids"]
            stmt = select(Role).where(Role.id.in_(role_ids))
            result = await self.session.execute(stmt)
            roles = list(result.scalars().all())
            user.roles = roles

        await self.session.flush()
        await self.session.refresh(user, attribute_names=["roles"])
        return user

    async def delete(self, user: User) -> None:
        await self.session.delete(user)
        await self.session.flush()

    async def exists_by_email(self, email: str) -> bool:
        stmt = select(func.count()).select_from(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one() > 0
