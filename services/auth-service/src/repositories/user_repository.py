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

    async def list_users(self, page: int = 1, page_size: int = 20) -> tuple[list[User], int]:
        # Count total
        count_stmt = select(func.count()).select_from(User)
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        # Fetch page
        offset = (page - 1) * page_size
        stmt = (
            select(User)
            .options(selectinload(User.roles))
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
