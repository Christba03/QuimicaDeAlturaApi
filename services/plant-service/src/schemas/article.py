from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Article CRUD schemas
# ---------------------------------------------------------------------------

class ArticleBase(BaseModel):
    title: str = Field(..., min_length=1)
    abstract: str | None = None
    doi: str | None = Field(None, max_length=255)
    pubmed_id: str | None = Field(None, max_length=50)
    pmcid: str | None = Field(None, max_length=50)
    arxiv_id: str | None = Field(None, max_length=50)
    journal: str | None = Field(None, max_length=500)
    publication_date: date | None = None
    volume: str | None = Field(None, max_length=50)
    issue: str | None = Field(None, max_length=50)
    pages: str | None = Field(None, max_length=50)
    authors: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    mesh_terms: list[str] = Field(default_factory=list)
    is_open_access: bool = False
    pdf_url: str | None = None
    full_text_url: str | None = None
    article_type: str | None = Field(None, max_length=100)
    peer_reviewed: bool = True


class ArticleCreate(ArticleBase):
    pass


class ArticleUpdate(BaseModel):
    title: str | None = Field(None, min_length=1)
    abstract: str | None = None
    doi: str | None = Field(None, max_length=255)
    pubmed_id: str | None = Field(None, max_length=50)
    pmcid: str | None = Field(None, max_length=50)
    arxiv_id: str | None = Field(None, max_length=50)
    journal: str | None = Field(None, max_length=500)
    publication_date: date | None = None
    volume: str | None = Field(None, max_length=50)
    issue: str | None = Field(None, max_length=50)
    pages: str | None = Field(None, max_length=50)
    authors: list[str] | None = None
    keywords: list[str] | None = None
    mesh_terms: list[str] | None = None
    is_open_access: bool | None = None
    pdf_url: str | None = None
    full_text_url: str | None = None
    article_type: str | None = Field(None, max_length=100)
    peer_reviewed: bool | None = None


class ArticleResponse(BaseModel):
    id: UUID
    title: str
    doi: str | None
    pubmed_id: str | None
    pmcid: str | None
    journal: str | None
    publication_date: date | None
    authors: list[str]
    is_open_access: bool
    verification_status: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ArticleDetail(ArticleResponse):
    abstract: str | None
    arxiv_id: str | None
    volume: str | None
    issue: str | None
    pages: str | None
    keywords: list[str]
    mesh_terms: list[str]
    pdf_url: str | None
    full_text_url: str | None
    article_type: str | None
    citation_count: int
    impact_factor: float | None
    quality_score: float | None
    peer_reviewed: bool
    last_fetched: datetime | None


class ArticleListResponse(BaseModel):
    items: list[ArticleResponse]
    total: int
    page: int
    size: int
    pages: int


# ---------------------------------------------------------------------------
# Association schemas
# ---------------------------------------------------------------------------

class ArticlePlantAssociationCreate(BaseModel):
    relevance_score: float | None = Field(None, ge=0, le=1)
    mentioned_in_abstract: bool = False
    mentioned_in_title: bool = False
    key_findings: str | None = None


class ArticlePlantAssociationResponse(BaseModel):
    id: UUID
    article_id: UUID
    plant_id: UUID
    relevance_score: float | None
    mentioned_in_abstract: bool
    mentioned_in_title: bool
    key_findings: str | None
    is_automated: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ArticleCompoundAssociationCreate(BaseModel):
    relevance_score: float | None = Field(None, ge=0, le=1)
    key_findings: str | None = None


class ArticleCompoundAssociationResponse(BaseModel):
    id: UUID
    article_id: UUID
    compound_id: UUID
    relevance_score: float | None
    key_findings: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Integration response schemas
# ---------------------------------------------------------------------------

class IdConversionResult(BaseModel):
    doi: str | None = None
    pmid: str | None = None
    pmcid: str | None = None


class IdConversionResponse(BaseModel):
    results: list[IdConversionResult]


class OALink(BaseModel):
    format: str | None = None
    href: str | None = None
    updated: str | None = None


class OAInfoResponse(BaseModel):
    id: str | None = None
    citation: str | None = None
    license: str | None = None
    retracted: bool = False
    links: list[OALink] = Field(default_factory=list)


class CitationResponse(BaseModel):
    pmid: str
    format: str
    citation: str


class EnrichmentResponse(BaseModel):
    article_id: UUID
    ids_resolved: IdConversionResult | None = None
    oa_info: OAInfoResponse | None = None
    updated_fields: list[str] = Field(default_factory=list)


class FullTextResponse(BaseModel):
    article_id: UUID
    pmcid: str
    passage_count: int
    stored: bool


class PubMedImportRequest(BaseModel):
    query: str = Field(..., min_length=1)
    max_results: int = Field(10, ge=1, le=100)


class PubMedImportResponse(BaseModel):
    query: str
    imported: int
    articles: list[ArticleResponse]
