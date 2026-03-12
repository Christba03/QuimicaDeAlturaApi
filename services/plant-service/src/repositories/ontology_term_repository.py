from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.ontology_term import OntologyTerm


class OntologyTermRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_list(
        self,
        page: int = 1,
        size: int = 20,
        search: str | None = None,
    ) -> tuple[list[OntologyTerm], int]:
        stmt = select(OntologyTerm)
        count_stmt = select(func.count(OntologyTerm.id))

        if search:
            search_filter = OntologyTerm.canonical_term.ilike(f"%{search}%")
            stmt = stmt.where(search_filter)
            count_stmt = count_stmt.where(search_filter)

        total = (await self.session.execute(count_stmt)).scalar_one()

        stmt = (
            stmt.order_by(OntologyTerm.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        items = list((await self.session.execute(stmt)).scalars().all())

        return items, total

    async def get_by_id(self, id: UUID) -> OntologyTerm | None:
        result = await self.session.execute(
            select(OntologyTerm).where(OntologyTerm.id == id)
        )
        return result.scalar_one_or_none()

    async def create(self, obj: OntologyTerm) -> OntologyTerm:
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: OntologyTerm, data: dict) -> OntologyTerm:
        for key, value in data.items():
            if value is not None:
                setattr(obj, key, value)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, obj: OntologyTerm) -> None:
        await self.session.delete(obj)
        await self.session.flush()
