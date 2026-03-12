"""
Tests for /articles API endpoints using FastAPI TestClient.
All database and external-API calls are mocked.
"""
import uuid
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.models.article import (
    ArticleCompoundAssociation,
    ArticlePlantAssociation,
    ScientificArticle,
    VerificationStatus,
)


def _make_article(**overrides):
    """Build a ScientificArticle with sensible defaults."""
    defaults = dict(
        id=uuid.uuid4(),
        title="Test Article",
        abstract="Abstract text",
        doi="10.1234/test",
        pubmed_id="12345678",
        pmcid="PMC9999999",
        journal="J Test",
        publication_date=date(2024, 1, 1),
        authors=["Author A"],
        keywords=[],
        mesh_terms=[],
        is_open_access=False,
        arxiv_id=None,
        volume=None,
        issue=None,
        pages=None,
        pdf_url=None,
        full_text_url=None,
        article_type="research-article",
        country=None,
        citation_count=0,
        impact_factor=None,
        quality_score=None,
        peer_reviewed=True,
        last_fetched=None,
        verification_status=VerificationStatus.UNVERIFIED,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    article = MagicMock(spec=ScientificArticle)
    for k, v in defaults.items():
        setattr(article, k, v)
    return article


@pytest.fixture
def mock_article_service():
    """Patch ArticleService so endpoints use a mock."""
    with patch("src.api.v1.endpoints.articles.ArticleService") as MockSvc:
        instance = AsyncMock()
        MockSvc.return_value = instance
        yield instance


@pytest.fixture
def client(mock_article_service):
    """FastAPI TestClient with mocked dependencies."""
    from src.main import app
    from src.dependencies import get_db

    app.dependency_overrides[get_db] = lambda: AsyncMock()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ===================================================================
# CRUD endpoints
# ===================================================================

class TestArticleEndpointsCRUD:

    def test_list_articles(self, client, mock_article_service):
        article = _make_article()
        mock_article_service.list_articles.return_value = MagicMock(
            items=[article],
            total=1,
            page=1,
            size=20,
            pages=1,
        )

        resp = client.get("/articles/?page=1&size=20")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1

    def test_get_article(self, client, mock_article_service):
        article = _make_article()
        mock_article_service.get_article.return_value = article

        resp = client.get(f"/articles/{article.id}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "Test Article"

    def test_get_article_not_found(self, client, mock_article_service):
        mock_article_service.get_article.return_value = None

        resp = client.get(f"/articles/{uuid.uuid4()}")
        assert resp.status_code == 404

    def test_create_article(self, client, mock_article_service):
        article = _make_article(title="New Article")
        mock_article_service.create_article.return_value = article

        resp = client.post("/articles/", json={
            "title": "New Article",
            "authors": ["Author A"],
        })
        assert resp.status_code == 201
        assert resp.json()["title"] == "New Article"

    def test_update_article(self, client, mock_article_service):
        article = _make_article(title="Updated")
        mock_article_service.update_article.return_value = article

        resp = client.put(f"/articles/{article.id}", json={"title": "Updated"})
        assert resp.status_code == 200

    def test_update_article_not_found(self, client, mock_article_service):
        mock_article_service.update_article.return_value = None

        resp = client.put(f"/articles/{uuid.uuid4()}", json={"title": "Nope"})
        assert resp.status_code == 404

    def test_delete_article(self, client, mock_article_service):
        mock_article_service.delete_article.return_value = True

        resp = client.delete(f"/articles/{uuid.uuid4()}")
        assert resp.status_code == 204

    def test_delete_article_not_found(self, client, mock_article_service):
        mock_article_service.delete_article.return_value = False

        resp = client.delete(f"/articles/{uuid.uuid4()}")
        assert resp.status_code == 404


# ===================================================================
# Enrichment endpoint
# ===================================================================

class TestEnrichEndpoint:

    def test_enrich_article(self, client, mock_article_service):
        aid = uuid.uuid4()
        mock_article_service.enrich_article.return_value = {
            "article_id": aid,
            "ids_resolved": {"doi": "10.1/x", "pmid": "1", "pmcid": "PMC1"},
            "oa_info": None,
            "updated_fields": ["doi", "pmid", "pmcid"],
        }

        resp = client.post(f"/articles/{aid}/enrich")
        assert resp.status_code == 200
        data = resp.json()
        assert "doi" in data["updated_fields"]

    def test_enrich_article_not_found(self, client, mock_article_service):
        mock_article_service.enrich_article.return_value = {"error": "not_found"}

        resp = client.post(f"/articles/{uuid.uuid4()}/enrich")
        assert resp.status_code == 404


# ===================================================================
# Citation endpoint
# ===================================================================

class TestCitationEndpoint:

    def test_get_citation(self, client, mock_article_service):
        aid = uuid.uuid4()
        mock_article_service.get_citation.return_value = {
            "pmid": "12345678",
            "format": "ris",
            "citation": "TY  - JOUR\nER  - ",
        }

        resp = client.get(f"/articles/{aid}/citation?format=ris")
        assert resp.status_code == 200
        assert "TY  - JOUR" in resp.json()["citation"]

    def test_get_citation_no_pmid(self, client, mock_article_service):
        mock_article_service.get_citation.return_value = None

        resp = client.get(f"/articles/{uuid.uuid4()}/citation")
        assert resp.status_code == 404


# ===================================================================
# Full text endpoint
# ===================================================================

class TestFullTextEndpoint:

    def test_fetch_full_text(self, client, mock_article_service):
        aid = uuid.uuid4()
        mock_article_service.fetch_full_text.return_value = {
            "article_id": aid,
            "pmcid": "PMC9999999",
            "passage_count": 42,
            "stored": True,
        }

        resp = client.post(f"/articles/{aid}/full-text")
        assert resp.status_code == 200
        assert resp.json()["stored"] is True

    def test_fetch_full_text_no_pmcid(self, client, mock_article_service):
        aid = uuid.uuid4()
        mock_article_service.fetch_full_text.return_value = {
            "error": "no_pmcid",
            "article_id": aid,
        }

        resp = client.post(f"/articles/{aid}/full-text")
        assert resp.status_code == 422

    def test_fetch_full_text_not_found(self, client, mock_article_service):
        mock_article_service.fetch_full_text.return_value = None

        resp = client.post(f"/articles/{uuid.uuid4()}/full-text")
        assert resp.status_code == 404


# ===================================================================
# Import endpoint
# ===================================================================

class TestImportEndpoint:

    def test_import_from_pubmed(self, client, mock_article_service):
        article = _make_article()
        mock_article_service.import_from_pubmed.return_value = [article]

        resp = client.post("/articles/import", json={
            "query": "chia medicinal",
            "max_results": 5,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["imported"] == 1
        assert data["query"] == "chia medicinal"

    def test_import_empty_query_rejected(self, client, mock_article_service):
        resp = client.post("/articles/import", json={"query": "", "max_results": 5})
        assert resp.status_code == 422


# ===================================================================
# Association endpoints
# ===================================================================

class TestAssociationEndpoints:

    def test_associate_with_plant(self, client, mock_article_service):
        assoc = MagicMock(spec=ArticlePlantAssociation)
        assoc.id = uuid.uuid4()
        assoc.article_id = uuid.uuid4()
        assoc.plant_id = uuid.uuid4()
        assoc.relevance_score = 0.9
        assoc.mentioned_in_abstract = True
        assoc.mentioned_in_title = False
        assoc.key_findings = "Significant activity"
        assoc.is_automated = False
        assoc.created_at = datetime.now(timezone.utc)
        mock_article_service.associate_with_plant.return_value = assoc

        resp = client.post(
            f"/articles/{assoc.article_id}/plants/{assoc.plant_id}",
            json={"relevance_score": 0.9, "mentioned_in_abstract": True},
        )
        assert resp.status_code == 201

    def test_associate_with_compound(self, client, mock_article_service):
        assoc = MagicMock(spec=ArticleCompoundAssociation)
        assoc.id = uuid.uuid4()
        assoc.article_id = uuid.uuid4()
        assoc.compound_id = uuid.uuid4()
        assoc.relevance_score = 0.75
        assoc.key_findings = None
        assoc.created_at = datetime.now(timezone.utc)
        mock_article_service.associate_with_compound.return_value = assoc

        resp = client.post(
            f"/articles/{assoc.article_id}/compounds/{assoc.compound_id}",
            json={"relevance_score": 0.75},
        )
        assert resp.status_code == 201

    def test_associate_duplicate_returns_409(self, client, mock_article_service):
        mock_article_service.associate_with_plant.side_effect = Exception("duplicate")

        resp = client.post(
            f"/articles/{uuid.uuid4()}/plants/{uuid.uuid4()}",
        )
        assert resp.status_code == 409
