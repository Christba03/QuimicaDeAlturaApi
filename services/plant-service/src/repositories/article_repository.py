from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.article import (
    ArticleCompoundAssociation,
    ArticlePlantAssociation,
    ScientificArticle,
)


class ArticleRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # ------------------------------------------------------------------
    # Single-record lookups
    # ------------------------------------------------------------------

    async def get_by_id(self, article_id: UUID) -> ScientificArticle | None:
        stmt = (
            select(ScientificArticle)
            .options(
                selectinload(ScientificArticle.plant_associations),
                selectinload(ScientificArticle.compound_associations),
            )
            .where(
                ScientificArticle.id == article_id,
                ScientificArticle.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_doi(self, doi: str) -> ScientificArticle | None:
        stmt = select(ScientificArticle).where(
            ScientificArticle.doi == doi,
            ScientificArticle.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_pmid(self, pmid: str) -> ScientificArticle | None:
        stmt = select(ScientificArticle).where(
            ScientificArticle.pubmed_id == pmid,
            ScientificArticle.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_pmcid(self, pmcid: str) -> ScientificArticle | None:
        stmt = select(ScientificArticle).where(
            ScientificArticle.pmcid == pmcid,
            ScientificArticle.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # List / search
    # ------------------------------------------------------------------

    async def list_articles(
        self,
        page: int = 1,
        size: int = 20,
        search: str | None = None,
        journal: str | None = None,
        is_open_access: bool | None = None,
    ) -> tuple[list[ScientificArticle], int]:
        base = ScientificArticle.deleted_at.is_(None)
        stmt = select(ScientificArticle).where(base)
        count_stmt = select(func.count(ScientificArticle.id)).where(base)

        if search:
            search_filter = or_(
                ScientificArticle.title.ilike(f"%{search}%"),
                ScientificArticle.doi.ilike(f"%{search}%"),
                ScientificArticle.pubmed_id.ilike(f"%{search}%"),
            )
            stmt = stmt.where(search_filter)
            count_stmt = count_stmt.where(search_filter)

        if journal:
            stmt = stmt.where(ScientificArticle.journal.ilike(f"%{journal}%"))
            count_stmt = count_stmt.where(ScientificArticle.journal.ilike(f"%{journal}%"))

        if is_open_access is not None:
            stmt = stmt.where(ScientificArticle.is_open_access == is_open_access)
            count_stmt = count_stmt.where(ScientificArticle.is_open_access == is_open_access)

        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = (
            stmt.order_by(ScientificArticle.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        result = await self.session.execute(stmt)
        articles = list(result.scalars().all())
        return articles, total

    # ------------------------------------------------------------------
    # Create / update / soft-delete
    # ------------------------------------------------------------------

    async def create(self, article: ScientificArticle) -> ScientificArticle:
        self.session.add(article)
        await self.session.flush()
        await self.session.refresh(article)
        return article

    async def update(self, article: ScientificArticle, data: dict) -> ScientificArticle:
        for key, value in data.items():
            if value is not None:
                setattr(article, key, value)
        await self.session.flush()
        await self.session.refresh(article)
        return article

    async def soft_delete(self, article: ScientificArticle) -> None:
        article.deleted_at = datetime.now(timezone.utc)
        await self.session.flush()

    # ------------------------------------------------------------------
    # Upsert by identifiers (dedup on DOI / PMID / PMCID)
    # ------------------------------------------------------------------

    async def upsert_by_identifiers(
        self, data: dict
    ) -> tuple[ScientificArticle, bool]:
        """Find existing article by DOI, PMID, or PMCID; update or create.

        Returns (article, created) where created is True for new records.
        """
        existing = None
        if data.get("doi"):
            existing = await self.get_by_doi(data["doi"])
        if not existing and data.get("pubmed_id"):
            existing = await self.get_by_pmid(data["pubmed_id"])
        if not existing and data.get("pmcid"):
            existing = await self.get_by_pmcid(data["pmcid"])

        if existing:
            return await self.update(existing, data), False

        article = ScientificArticle(**data)
        return await self.create(article), True

    # ------------------------------------------------------------------
    # Association helpers
    # ------------------------------------------------------------------

    async def get_articles_for_plant(
        self, plant_id: UUID
    ) -> list[ScientificArticle]:
        stmt = (
            select(ScientificArticle)
            .join(ArticlePlantAssociation)
            .where(
                ArticlePlantAssociation.plant_id == plant_id,
                ScientificArticle.deleted_at.is_(None),
            )
            .order_by(ScientificArticle.publication_date.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_articles_for_compound(
        self, compound_id: UUID
    ) -> list[ScientificArticle]:
        stmt = (
            select(ScientificArticle)
            .join(ArticleCompoundAssociation)
            .where(
                ArticleCompoundAssociation.compound_id == compound_id,
                ScientificArticle.deleted_at.is_(None),
            )
            .order_by(ScientificArticle.publication_date.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_plant_association(
        self, assoc: ArticlePlantAssociation
    ) -> ArticlePlantAssociation:
        self.session.add(assoc)
        await self.session.flush()
        await self.session.refresh(assoc)
        return assoc

    async def create_compound_association(
        self, assoc: ArticleCompoundAssociation
    ) -> ArticleCompoundAssociation:
        self.session.add(assoc)
        await self.session.flush()
        await self.session.refresh(assoc)
        return assoc
