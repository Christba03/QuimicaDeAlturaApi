from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db
from src.schemas.article import (
    ArticleCompoundAssociationCreate,
    ArticleCompoundAssociationResponse,
    ArticleCreate,
    ArticleDetail,
    ArticleListResponse,
    ArticlePlantAssociationCreate,
    ArticlePlantAssociationResponse,
    ArticleResponse,
    ArticleUpdate,
    CitationResponse,
    EnrichmentResponse,
    FullTextResponse,
    PubMedImportRequest,
    PubMedImportResponse,
)
from src.services.article_service import ArticleService

router = APIRouter()


async def _get_article_service(
    db: AsyncSession = Depends(get_db),
) -> ArticleService:
    return ArticleService(session=db)


# ------------------------------------------------------------------
# CRUD
# ------------------------------------------------------------------


@router.get("/", response_model=ArticleListResponse)
async def list_articles(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: str | None = Query(None, description="Search by title, DOI, or PMID"),
    journal: str | None = Query(None, description="Filter by journal name"),
    is_open_access: bool | None = Query(None, description="Filter by open-access status"),
    service: ArticleService = Depends(_get_article_service),
):
    return await service.list_articles(
        page=page,
        size=size,
        search=search,
        journal=journal,
        is_open_access=is_open_access,
    )


@router.get("/{article_id}", response_model=ArticleDetail)
async def get_article(
    article_id: UUID,
    service: ArticleService = Depends(_get_article_service),
):
    article = await service.get_article(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.post("/", response_model=ArticleResponse, status_code=201)
async def create_article(
    data: ArticleCreate,
    service: ArticleService = Depends(_get_article_service),
):
    return await service.create_article(data)


@router.put("/{article_id}", response_model=ArticleResponse)
async def update_article(
    article_id: UUID,
    data: ArticleUpdate,
    service: ArticleService = Depends(_get_article_service),
):
    article = await service.update_article(article_id, data)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.delete("/{article_id}", status_code=204)
async def delete_article(
    article_id: UUID,
    service: ArticleService = Depends(_get_article_service),
):
    deleted = await service.delete_article(article_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Article not found")


# ------------------------------------------------------------------
# Enrichment (ID conversion + OA metadata)
# ------------------------------------------------------------------


@router.post("/{article_id}/enrich", response_model=EnrichmentResponse)
async def enrich_article(
    article_id: UUID,
    service: ArticleService = Depends(_get_article_service),
):
    result = await service.enrich_article(article_id)
    if result.get("error") == "not_found":
        raise HTTPException(status_code=404, detail="Article not found")
    return result


# ------------------------------------------------------------------
# Citation export
# ------------------------------------------------------------------


@router.get("/{article_id}/citation", response_model=CitationResponse)
async def get_article_citation(
    article_id: UUID,
    fmt: str = Query("ris", alias="format", description="Citation format: ris, medline, bibtex, nbib"),
    service: ArticleService = Depends(_get_article_service),
):
    result = await service.get_citation(article_id, fmt=fmt)
    if not result:
        raise HTTPException(
            status_code=404,
            detail="Article not found or has no PubMed ID",
        )
    return result


# ------------------------------------------------------------------
# Full text (BioC)
# ------------------------------------------------------------------


@router.post("/{article_id}/full-text", response_model=FullTextResponse)
async def fetch_full_text(
    article_id: UUID,
    service: ArticleService = Depends(_get_article_service),
):
    result = await service.fetch_full_text(article_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Article not found")
    if result.get("error") == "no_pmcid":
        raise HTTPException(
            status_code=422,
            detail="Article has no PMCID; enrich it first",
        )
    if result.get("error") == "bioc_fetch_failed":
        raise HTTPException(
            status_code=502,
            detail="Failed to fetch full text from BioC API",
        )
    return result


# ------------------------------------------------------------------
# PubMed import
# ------------------------------------------------------------------


@router.post("/import", response_model=PubMedImportResponse)
async def import_from_pubmed(
    body: PubMedImportRequest,
    service: ArticleService = Depends(_get_article_service),
):
    articles = await service.import_from_pubmed(
        query=body.query, max_results=body.max_results
    )
    return PubMedImportResponse(
        query=body.query,
        imported=len(articles),
        articles=articles,
    )


# ------------------------------------------------------------------
# Associations
# ------------------------------------------------------------------


@router.post(
    "/{article_id}/plants/{plant_id}",
    response_model=ArticlePlantAssociationResponse,
    status_code=201,
)
async def associate_article_with_plant(
    article_id: UUID,
    plant_id: UUID,
    body: ArticlePlantAssociationCreate | None = None,
    service: ArticleService = Depends(_get_article_service),
):
    data = body.model_dump() if body else {}
    try:
        assoc = await service.associate_with_plant(
            article_id=article_id,
            plant_id=plant_id,
            **data,
        )
    except Exception as exc:
        raise HTTPException(status_code=409, detail="Association already exists") from exc
    return assoc


@router.post(
    "/{article_id}/compounds/{compound_id}",
    response_model=ArticleCompoundAssociationResponse,
    status_code=201,
)
async def associate_article_with_compound(
    article_id: UUID,
    compound_id: UUID,
    body: ArticleCompoundAssociationCreate | None = None,
    service: ArticleService = Depends(_get_article_service),
):
    data = body.model_dump() if body else {}
    try:
        assoc = await service.associate_with_compound(
            article_id=article_id,
            compound_id=compound_id,
            **data,
        )
    except Exception as exc:
        raise HTTPException(status_code=409, detail="Association already exists") from exc
    return assoc
