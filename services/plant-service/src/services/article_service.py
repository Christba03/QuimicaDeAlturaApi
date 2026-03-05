import math
from datetime import date, datetime, timezone
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.integrations.pmc_bioc import PMCBioCClient
from src.integrations.pmc_citation import PMCCitationClient
from src.integrations.pmc_idconv import PMCIdConverterClient
from src.integrations.pmc_oa import PMCOAClient
from src.integrations.pubmed import PubMedClient
from src.models.article import (
    ArticleCompoundAssociation,
    ArticlePlantAssociation,
    ScientificArticle,
)
from src.repositories.article_repository import ArticleRepository
from src.schemas.article import (
    ArticleCreate,
    ArticleListResponse,
    ArticleUpdate,
)

logger = structlog.get_logger()


class ArticleService:
    def __init__(self, session: AsyncSession):
        self.repo = ArticleRepository(session)
        self.session = session
        self.pubmed = PubMedClient()
        self.idconv = PMCIdConverterClient()
        self.oa = PMCOAClient()
        self.citation = PMCCitationClient()
        self.bioc = PMCBioCClient()

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    async def create_article(self, data: ArticleCreate) -> ScientificArticle:
        article = ScientificArticle(**data.model_dump())
        article = await self.repo.create(article)
        await self.session.commit()
        logger.info("article_created", article_id=str(article.id))
        return article

    async def get_article(self, article_id: UUID) -> ScientificArticle | None:
        return await self.repo.get_by_id(article_id)

    async def list_articles(
        self,
        page: int = 1,
        size: int = 20,
        search: str | None = None,
        journal: str | None = None,
        is_open_access: bool | None = None,
    ) -> ArticleListResponse:
        articles, total = await self.repo.list_articles(
            page=page,
            size=size,
            search=search,
            journal=journal,
            is_open_access=is_open_access,
        )
        pages = math.ceil(total / size) if total > 0 else 0
        return ArticleListResponse(
            items=articles,
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    async def update_article(
        self, article_id: UUID, data: ArticleUpdate
    ) -> ScientificArticle | None:
        article = await self.repo.get_by_id(article_id)
        if not article:
            return None
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return article
        article = await self.repo.update(article, update_data)
        await self.session.commit()
        logger.info("article_updated", article_id=str(article_id))
        return article

    async def delete_article(self, article_id: UUID) -> bool:
        article = await self.repo.get_by_id(article_id)
        if not article:
            return False
        await self.repo.soft_delete(article)
        await self.session.commit()
        logger.info("article_deleted", article_id=str(article_id))
        return True

    # ------------------------------------------------------------------
    # Enrichment: ID conversion + OA metadata
    # ------------------------------------------------------------------

    async def enrich_article(
        self, article_id: UUID
    ) -> dict:
        """Fill in missing IDs via PMC ID Converter, then fetch OA metadata."""
        article = await self.repo.get_by_id(article_id)
        if not article:
            return {"error": "not_found"}

        updated_fields: list[str] = []
        ids_resolved = None
        oa_info = None

        # --- Step 1: Resolve missing identifiers ---
        lookup_id = article.doi or article.pubmed_id or article.pmcid
        if lookup_id:
            records = await self.idconv.convert_ids([lookup_id])
            if records:
                ids_resolved = records[0]
                if not article.doi and ids_resolved.get("doi"):
                    article.doi = ids_resolved["doi"]
                    updated_fields.append("doi")
                if not article.pubmed_id and ids_resolved.get("pmid"):
                    article.pubmed_id = ids_resolved["pmid"]
                    updated_fields.append("pubmed_id")
                if not article.pmcid and ids_resolved.get("pmcid"):
                    article.pmcid = ids_resolved["pmcid"]
                    updated_fields.append("pmcid")

        # --- Step 2: Fetch OA info if we have a PMCID ---
        oa_lookup_id = article.pmcid or article.pubmed_id
        if oa_lookup_id:
            oa_result = await self.oa.get_oa_info(oa_lookup_id)
            if oa_result:
                oa_info = oa_result
                if not article.is_open_access:
                    article.is_open_access = True
                    updated_fields.append("is_open_access")

                for link in oa_result.get("links", []):
                    href = link.get("href", "")
                    fmt = link.get("format", "")
                    if fmt == "pdf" and not article.pdf_url:
                        article.pdf_url = href
                        updated_fields.append("pdf_url")
                    elif not article.full_text_url:
                        article.full_text_url = href
                        updated_fields.append("full_text_url")

        if updated_fields:
            article.last_fetched = datetime.now(timezone.utc)
            updated_fields.append("last_fetched")
            await self.session.commit()

        logger.info(
            "article_enriched",
            article_id=str(article_id),
            updated_fields=updated_fields,
        )
        return {
            "article_id": article.id,
            "ids_resolved": ids_resolved,
            "oa_info": oa_info,
            "updated_fields": updated_fields,
        }

    # ------------------------------------------------------------------
    # Citation export
    # ------------------------------------------------------------------

    async def get_citation(
        self, article_id: UUID, fmt: str = "ris"
    ) -> dict | None:
        article = await self.repo.get_by_id(article_id)
        if not article or not article.pubmed_id:
            return None
        text = await self.citation.get_citation(article.pubmed_id, fmt=fmt)
        if not text:
            return None
        return {"pmid": article.pubmed_id, "format": fmt, "citation": text}

    # ------------------------------------------------------------------
    # Full text via BioC
    # ------------------------------------------------------------------

    async def fetch_full_text(self, article_id: UUID) -> dict | None:
        article = await self.repo.get_by_id(article_id)
        if not article:
            return None

        pmcid = article.pmcid
        if not pmcid:
            return {"error": "no_pmcid", "article_id": article.id}

        result = await self.bioc.get_full_text(pmcid)
        if not result:
            return {"error": "bioc_fetch_failed", "article_id": article.id}

        article.full_text = result.get("full_text", "")
        article.last_fetched = datetime.now(timezone.utc)
        await self.session.commit()

        logger.info(
            "article_full_text_stored",
            article_id=str(article_id),
            pmcid=pmcid,
            passages=result.get("passage_count", 0),
        )
        return {
            "article_id": article.id,
            "pmcid": pmcid,
            "passage_count": result.get("passage_count", 0),
            "stored": True,
        }

    # ------------------------------------------------------------------
    # Import from PubMed
    # ------------------------------------------------------------------

    async def import_from_pubmed(
        self, query: str, max_results: int = 10
    ) -> list[ScientificArticle]:
        raw_articles = await self.pubmed.search_plant_research(
            query, max_results=max_results
        )
        if not raw_articles:
            pmids = await self.pubmed.search_articles(query, max_results=max_results)
            if pmids:
                raw_articles = await self.pubmed.fetch_article_details(pmids)

        imported: list[ScientificArticle] = []
        for raw in raw_articles:
            doi_raw = raw.get("doi", "")
            doi = doi_raw.replace("doi: ", "").strip() if doi_raw else None

            data = {
                "title": raw.get("title", "Unknown"),
                "pubmed_id": raw.get("pmid"),
                "doi": doi if doi else None,
                "journal": raw.get("source"),
                "authors": raw.get("authors", []),
                "publication_date": self._parse_pubdate(raw.get("pubdate")),
            }
            article, _ = await self.repo.upsert_by_identifiers(data)
            imported.append(article)

        await self.session.commit()
        logger.info("pubmed_import_complete", query=query, count=len(imported))
        return imported

    # ------------------------------------------------------------------
    # Combined: search PubMed → import → associate with plant
    # ------------------------------------------------------------------

    async def search_and_import_for_plant(
        self,
        plant_id: UUID,
        plant_name: str,
        max_results: int = 10,
    ) -> list[ScientificArticle]:
        articles = await self.import_from_pubmed(plant_name, max_results=max_results)
        for article in articles:
            try:
                assoc = ArticlePlantAssociation(
                    article_id=article.id,
                    plant_id=plant_id,
                    is_automated=True,
                )
                await self.repo.create_plant_association(assoc)
            except Exception:
                await self.session.rollback()
                logger.debug(
                    "plant_association_exists",
                    article_id=str(article.id),
                    plant_id=str(plant_id),
                )
        await self.session.commit()
        return articles

    # ------------------------------------------------------------------
    # Association management
    # ------------------------------------------------------------------

    async def associate_with_plant(
        self,
        article_id: UUID,
        plant_id: UUID,
        relevance_score: float | None = None,
        mentioned_in_abstract: bool = False,
        mentioned_in_title: bool = False,
        key_findings: str | None = None,
    ) -> ArticlePlantAssociation:
        assoc = ArticlePlantAssociation(
            article_id=article_id,
            plant_id=plant_id,
            relevance_score=relevance_score,
            mentioned_in_abstract=mentioned_in_abstract,
            mentioned_in_title=mentioned_in_title,
            key_findings=key_findings,
        )
        assoc = await self.repo.create_plant_association(assoc)
        await self.session.commit()
        return assoc

    async def associate_with_compound(
        self,
        article_id: UUID,
        compound_id: UUID,
        relevance_score: float | None = None,
        key_findings: str | None = None,
    ) -> ArticleCompoundAssociation:
        assoc = ArticleCompoundAssociation(
            article_id=article_id,
            compound_id=compound_id,
            relevance_score=relevance_score,
            key_findings=key_findings,
        )
        assoc = await self.repo.create_compound_association(assoc)
        await self.session.commit()
        return assoc

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_pubdate(pubdate_str: str | None) -> date | None:
        if not pubdate_str:
            return None
        for fmt in ("%Y %b %d", "%Y %b", "%Y"):
            try:
                return datetime.strptime(pubdate_str.strip(), fmt).date()
            except ValueError:
                continue
        return None
