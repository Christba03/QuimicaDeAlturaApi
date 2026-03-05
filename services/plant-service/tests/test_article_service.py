"""
Unit tests for ArticleService orchestration logic.
All external calls (DB, HTTP) are mocked.
"""
import uuid
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.models.article import (
    ArticleCompoundAssociation,
    ArticlePlantAssociation,
    ScientificArticle,
)
from src.schemas.article import ArticleCreate, ArticleUpdate
from src.services.article_service import ArticleService


def _make_service(mock_session):
    """Construct an ArticleService with all integrations mocked."""
    with patch("src.services.article_service.PubMedClient"), \
         patch("src.services.article_service.PMCIdConverterClient"), \
         patch("src.services.article_service.PMCOAClient"), \
         patch("src.services.article_service.PMCCitationClient"), \
         patch("src.services.article_service.PMCBioCClient"):
        svc = ArticleService(session=mock_session)
    svc.pubmed = AsyncMock()
    svc.idconv = AsyncMock()
    svc.oa = AsyncMock()
    svc.citation = AsyncMock()
    svc.bioc = AsyncMock()
    svc.repo = AsyncMock()
    return svc


# ===================================================================
# CRUD
# ===================================================================

class TestArticleServiceCRUD:

    @pytest.mark.asyncio
    async def test_create_article(self, mock_db_session, sample_article):
        svc = _make_service(mock_db_session)
        svc.repo.create.return_value = sample_article

        data = ArticleCreate(
            title="Test Article",
            authors=["Author A"],
        )
        result = await svc.create_article(data)

        svc.repo.create.assert_called_once()
        mock_db_session.commit.assert_called_once()
        assert result == sample_article

    @pytest.mark.asyncio
    async def test_get_article(self, mock_db_session, sample_article):
        svc = _make_service(mock_db_session)
        svc.repo.get_by_id.return_value = sample_article

        result = await svc.get_article(sample_article.id)

        assert result == sample_article
        svc.repo.get_by_id.assert_called_once_with(sample_article.id)

    @pytest.mark.asyncio
    async def test_get_article_not_found(self, mock_db_session):
        svc = _make_service(mock_db_session)
        svc.repo.get_by_id.return_value = None

        result = await svc.get_article(uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_update_article(self, mock_db_session, sample_article):
        svc = _make_service(mock_db_session)
        svc.repo.get_by_id.return_value = sample_article
        svc.repo.update.return_value = sample_article

        data = ArticleUpdate(title="Updated Title")
        result = await svc.update_article(sample_article.id, data)

        assert result == sample_article
        svc.repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_article_not_found(self, mock_db_session):
        svc = _make_service(mock_db_session)
        svc.repo.get_by_id.return_value = None

        data = ArticleUpdate(title="Nope")
        result = await svc.update_article(uuid.uuid4(), data)
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_article(self, mock_db_session, sample_article):
        svc = _make_service(mock_db_session)
        svc.repo.get_by_id.return_value = sample_article

        result = await svc.delete_article(sample_article.id)

        assert result is True
        svc.repo.soft_delete.assert_called_once_with(sample_article)

    @pytest.mark.asyncio
    async def test_delete_article_not_found(self, mock_db_session):
        svc = _make_service(mock_db_session)
        svc.repo.get_by_id.return_value = None

        result = await svc.delete_article(uuid.uuid4())
        assert result is False


# ===================================================================
# Enrichment
# ===================================================================

class TestArticleServiceEnrichment:

    @pytest.mark.asyncio
    async def test_enrich_fills_missing_ids(self, mock_db_session, sample_article):
        svc = _make_service(mock_db_session)
        sample_article.doi = "10.1234/test"
        sample_article.pubmed_id = None
        sample_article.pmcid = None
        svc.repo.get_by_id.return_value = sample_article

        svc.idconv.convert_ids.return_value = [
            {"doi": "10.1234/test", "pmid": "99999", "pmcid": "PMC888"}
        ]
        svc.oa.get_oa_info.return_value = None

        result = await svc.enrich_article(sample_article.id)

        assert "pubmed_id" in result["updated_fields"]
        assert "pmcid" in result["updated_fields"]
        assert sample_article.pubmed_id == "99999"
        assert sample_article.pmcid == "PMC888"

    @pytest.mark.asyncio
    async def test_enrich_fills_oa_info(self, mock_db_session, sample_article):
        svc = _make_service(mock_db_session)
        sample_article.is_open_access = False
        sample_article.pdf_url = None
        svc.repo.get_by_id.return_value = sample_article

        svc.idconv.convert_ids.return_value = []
        svc.oa.get_oa_info.return_value = {
            "id": sample_article.pmcid,
            "license": "CC BY",
            "retracted": False,
            "links": [
                {"format": "pdf", "href": "ftp://example.com/article.pdf", "updated": "2024-01-01"},
            ],
        }

        result = await svc.enrich_article(sample_article.id)

        assert "is_open_access" in result["updated_fields"]
        assert "pdf_url" in result["updated_fields"]
        assert sample_article.is_open_access is True
        assert sample_article.pdf_url == "ftp://example.com/article.pdf"

    @pytest.mark.asyncio
    async def test_enrich_article_not_found(self, mock_db_session):
        svc = _make_service(mock_db_session)
        svc.repo.get_by_id.return_value = None

        result = await svc.enrich_article(uuid.uuid4())
        assert result.get("error") == "not_found"


# ===================================================================
# Citation
# ===================================================================

class TestArticleServiceCitation:

    @pytest.mark.asyncio
    async def test_get_citation_success(self, mock_db_session, sample_article):
        svc = _make_service(mock_db_session)
        svc.repo.get_by_id.return_value = sample_article
        svc.citation.get_citation.return_value = "TY  - JOUR\nER  - "

        result = await svc.get_citation(sample_article.id, fmt="ris")

        assert result is not None
        assert result["format"] == "ris"
        assert "TY  - JOUR" in result["citation"]

    @pytest.mark.asyncio
    async def test_get_citation_no_pmid(self, mock_db_session, sample_article):
        svc = _make_service(mock_db_session)
        sample_article.pubmed_id = None
        svc.repo.get_by_id.return_value = sample_article

        result = await svc.get_citation(sample_article.id)
        assert result is None


# ===================================================================
# Full text
# ===================================================================

class TestArticleServiceFullText:

    @pytest.mark.asyncio
    async def test_fetch_full_text_success(self, mock_db_session, sample_article):
        svc = _make_service(mock_db_session)
        svc.repo.get_by_id.return_value = sample_article

        svc.bioc.get_full_text.return_value = {
            "pmcid": sample_article.pmcid,
            "full_text": "Full text content here.",
            "passage_count": 12,
        }

        result = await svc.fetch_full_text(sample_article.id)

        assert result["stored"] is True
        assert result["passage_count"] == 12
        assert sample_article.full_text == "Full text content here."

    @pytest.mark.asyncio
    async def test_fetch_full_text_no_pmcid(self, mock_db_session, sample_article):
        svc = _make_service(mock_db_session)
        sample_article.pmcid = None
        svc.repo.get_by_id.return_value = sample_article

        result = await svc.fetch_full_text(sample_article.id)
        assert result["error"] == "no_pmcid"

    @pytest.mark.asyncio
    async def test_fetch_full_text_bioc_failure(self, mock_db_session, sample_article):
        svc = _make_service(mock_db_session)
        svc.repo.get_by_id.return_value = sample_article
        svc.bioc.get_full_text.return_value = None

        result = await svc.fetch_full_text(sample_article.id)
        assert result["error"] == "bioc_fetch_failed"


# ===================================================================
# PubMed import
# ===================================================================

class TestArticleServiceImport:

    @pytest.mark.asyncio
    async def test_import_from_pubmed(self, mock_db_session, sample_article):
        svc = _make_service(mock_db_session)
        svc.pubmed.search_plant_research.return_value = [
            {
                "pmid": "12345678",
                "title": "Chia research",
                "source": "J Ethnopharmacol",
                "pubdate": "2024 Jun",
                "authors": ["Garcia A"],
                "doi": "doi: 10.1234/test.2024.001",
            }
        ]
        svc.repo.upsert_by_identifiers.return_value = (sample_article, True)

        result = await svc.import_from_pubmed("chia medicinal")

        assert len(result) == 1
        svc.repo.upsert_by_identifiers.assert_called_once()
        mock_db_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_import_from_pubmed_no_results(self, mock_db_session):
        svc = _make_service(mock_db_session)
        svc.pubmed.search_plant_research.return_value = []
        svc.pubmed.search_articles.return_value = []

        result = await svc.import_from_pubmed("nonexistent query xyz")
        assert len(result) == 0


# ===================================================================
# Associations
# ===================================================================

class TestArticleServiceAssociations:

    @pytest.mark.asyncio
    async def test_associate_with_plant(self, mock_db_session):
        svc = _make_service(mock_db_session)
        assoc = MagicMock(spec=ArticlePlantAssociation)
        svc.repo.create_plant_association.return_value = assoc

        result = await svc.associate_with_plant(
            article_id=uuid.uuid4(),
            plant_id=uuid.uuid4(),
            relevance_score=0.85,
        )

        assert result == assoc
        svc.repo.create_plant_association.assert_called_once()

    @pytest.mark.asyncio
    async def test_associate_with_compound(self, mock_db_session):
        svc = _make_service(mock_db_session)
        assoc = MagicMock(spec=ArticleCompoundAssociation)
        svc.repo.create_compound_association.return_value = assoc

        result = await svc.associate_with_compound(
            article_id=uuid.uuid4(),
            compound_id=uuid.uuid4(),
        )

        assert result == assoc
        svc.repo.create_compound_association.assert_called_once()


# ===================================================================
# Helper: date parsing
# ===================================================================

class TestDateParsing:

    def test_parse_full_date(self):
        result = ArticleService._parse_pubdate("2024 Jun 15")
        assert result == date(2024, 6, 15)

    def test_parse_month_year(self):
        result = ArticleService._parse_pubdate("2024 Jun")
        assert result == date(2024, 6, 1)

    def test_parse_year_only(self):
        result = ArticleService._parse_pubdate("2024")
        assert result == date(2024, 1, 1)

    def test_parse_none(self):
        assert ArticleService._parse_pubdate(None) is None

    def test_parse_garbage(self):
        assert ArticleService._parse_pubdate("not a date") is None
