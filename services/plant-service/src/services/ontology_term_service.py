import math
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.ontology_term import OntologyTerm
from src.repositories.ontology_term_repository import OntologyTermRepository
from src.schemas.ontology_term import (
    OntologyTermCreate,
    OntologyTermListResponse,
    OntologyTermUpdate,
)

logger = structlog.get_logger()


class OntologyTermService:
    def __init__(self, session: AsyncSession):
        self.repo = OntologyTermRepository(session)
        self.session = session

    async def list_ontology_terms(
        self,
        page: int = 1,
        size: int = 20,
        search: str | None = None,
    ) -> OntologyTermListResponse:
        items, total = await self.repo.get_list(
            page=page,
            size=size,
            search=search,
        )
        pages = math.ceil(total / size) if total > 0 else 0
        return OntologyTermListResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    async def get_ontology_term(self, id: UUID) -> OntologyTerm | None:
        return await self.repo.get_by_id(id)

    async def create_ontology_term(self, data: OntologyTermCreate) -> OntologyTerm:
        term = OntologyTerm(**data.model_dump())
        term = await self.repo.create(term)
        await self.session.commit()
        logger.info("ontology_term_created", term_id=str(term.id))
        return term

    async def update_ontology_term(
        self, id: UUID, data: OntologyTermUpdate
    ) -> OntologyTerm | None:
        term = await self.repo.get_by_id(id)
        if not term:
            return None

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return term

        term = await self.repo.update(term, update_data)
        await self.session.commit()
        logger.info("ontology_term_updated", term_id=str(id))
        return term

    async def delete_ontology_term(self, id: UUID) -> bool:
        term = await self.repo.get_by_id(id)
        if not term:
            return False
        await self.repo.delete(term)
        await self.session.commit()
        logger.info("ontology_term_deleted", term_id=str(id))
        return True
