"""Tests for the 7 analytics endpoints in plant-service.

Analytics endpoints use raw SQLAlchemy queries (no service layer), so we
mock the DB session's `execute` method directly.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def analytics_client():
    from src.main import app
    from src.dependencies import get_db

    mock_session = AsyncMock()

    # Mock execute to return empty results for all queries
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_result.scalar.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    app.dependency_overrides[get_db] = lambda: mock_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


class TestAnalyticsEndpoints:
    def test_biodiversity_200(self, analytics_client):
        r = analytics_client.get("/analytics/biodiversity")
        assert r.status_code == 200
        data = r.json()
        assert "speciesByRegion" in data
        assert "speciesByCategory" in data
        assert "topFamilies" in data

    def test_phytochemical_200(self, analytics_client):
        r = analytics_client.get("/analytics/phytochemical")
        assert r.status_code == 200
        data = r.json()
        assert "compoundClassDistribution" in data
        assert "averageMolecularWeight" in data

    def test_evidence_quality_200(self, analytics_client):
        r = analytics_client.get("/analytics/evidence-quality")
        assert r.status_code == 200
        data = r.json()
        assert "evidenceLevelDistribution" in data

    def test_genomic_tracker_200(self, analytics_client):
        r = analytics_client.get("/analytics/genomic-tracker")
        assert r.status_code == 200
        data = r.json()
        assert "genomicStatusBreakdown" in data

    def test_epidemiology_200(self, analytics_client):
        r = analytics_client.get("/analytics/epidemiology")
        assert r.status_code == 200
        data = r.json()
        assert "conditionsByRegion" in data
        assert "recordsByYear" in data

    def test_drug_analogs_200(self, analytics_client):
        r = analytics_client.get("/analytics/drug-analogs")
        assert r.status_code == 200
        data = r.json()
        assert "topDrugAnalogs" in data
        assert "averageSimilarityScore" in data

    def test_research_gaps_200(self, analytics_client):
        r = analytics_client.get("/analytics/research-gaps")
        assert r.status_code == 200
        data = r.json()
        assert "plantsWithNoCompounds" in data
        assert "regionsWithFewRecords" in data

    def test_biodiversity_empty_lists(self, analytics_client):
        """Empty DB returns empty lists for all three biodiversity buckets."""
        r = analytics_client.get("/analytics/biodiversity")
        assert r.status_code == 200
        data = r.json()
        assert data["speciesByRegion"] == []
        assert data["speciesByCategory"] == []
        assert data["topFamilies"] == []

    def test_phytochemical_null_avg(self, analytics_client):
        """With no compounds the average molecular weight should be null."""
        r = analytics_client.get("/analytics/phytochemical")
        assert r.status_code == 200
        data = r.json()
        # scalar() returns None → endpoint returns None
        assert data["averageMolecularWeight"] is None

    def test_drug_analogs_null_avg(self, analytics_client):
        """With no drug references the average similarity score should be null."""
        r = analytics_client.get("/analytics/drug-analogs")
        assert r.status_code == 200
        data = r.json()
        assert data["averageSimilarityScore"] is None

    def test_biodiversity_with_data(self, analytics_client):
        """Test that returned data is properly formatted."""
        from src.main import app
        from src.dependencies import get_db

        # Set up mock with actual data
        mock_session = AsyncMock()

        # Three sequential execute calls: by_region, by_category, by_family
        region_result = MagicMock()
        region_result.all.return_value = [("Oaxaca", 5), ("Chiapas", 3)]
        category_result = MagicMock()
        category_result.all.return_value = [("herb", 8)]
        family_result = MagicMock()
        family_result.all.return_value = [("Lamiaceae", 4)]

        mock_session.execute = AsyncMock(
            side_effect=[region_result, category_result, family_result]
        )

        app.dependency_overrides[get_db] = lambda: mock_session
        with TestClient(app) as c:
            r = c.get("/analytics/biodiversity")
        app.dependency_overrides.clear()

        assert r.status_code == 200
        data = r.json()
        assert len(data["speciesByRegion"]) == 2
        assert data["speciesByRegion"][0]["region"] == "Oaxaca"
        assert data["speciesByRegion"][0]["count"] == 5
        assert data["speciesByRegion"][1]["region"] == "Chiapas"
        assert data["speciesByRegion"][1]["count"] == 3
        assert len(data["speciesByCategory"]) == 1
        assert data["speciesByCategory"][0]["category"] == "herb"
        assert len(data["topFamilies"]) == 1
        assert data["topFamilies"][0]["family"] == "Lamiaceae"

    def test_phytochemical_with_data(self, analytics_client):
        """Phytochemical endpoint returns correct compound class distribution."""
        from src.main import app
        from src.dependencies import get_db

        mock_session = AsyncMock()

        by_class_result = MagicMock()
        by_class_result.all.return_value = [("alkaloid", 12), ("flavonoid", 8)]

        avg_result = MagicMock()
        avg_result.scalar.return_value = 250.5

        mock_session.execute = AsyncMock(side_effect=[by_class_result, avg_result])

        app.dependency_overrides[get_db] = lambda: mock_session
        with TestClient(app) as c:
            r = c.get("/analytics/phytochemical")
        app.dependency_overrides.clear()

        assert r.status_code == 200
        data = r.json()
        assert len(data["compoundClassDistribution"]) == 2
        assert data["compoundClassDistribution"][0]["class"] == "alkaloid"
        assert data["compoundClassDistribution"][0]["count"] == 12
        assert data["averageMolecularWeight"] == pytest.approx(250.5)

    def test_epidemiology_with_data(self, analytics_client):
        """Epidemiology endpoint returns conditions by region and records by year."""
        from src.main import app
        from src.dependencies import get_db

        mock_session = AsyncMock()

        conditions_result = MagicMock()
        conditions_result.all.return_value = [
            ("diabetes", "Oaxaca", 7),
            ("hypertension", "Chiapas", 4),
        ]
        year_result = MagicMock()
        year_result.all.return_value = [(2020, 10), (2021, 15)]

        mock_session.execute = AsyncMock(side_effect=[conditions_result, year_result])

        app.dependency_overrides[get_db] = lambda: mock_session
        with TestClient(app) as c:
            r = c.get("/analytics/epidemiology")
        app.dependency_overrides.clear()

        assert r.status_code == 200
        data = r.json()
        assert len(data["conditionsByRegion"]) == 2
        assert data["conditionsByRegion"][0]["condition"] == "diabetes"
        assert data["conditionsByRegion"][0]["region"] == "Oaxaca"
        assert data["conditionsByRegion"][0]["count"] == 7
        assert len(data["recordsByYear"]) == 2
        assert data["recordsByYear"][0]["year"] == 2020

    def test_drug_analogs_with_data(self, analytics_client):
        """Drug analogs endpoint returns top analogs with similarity scores."""
        from src.main import app
        from src.dependencies import get_db

        mock_session = AsyncMock()

        top_result = MagicMock()
        top_result.all.return_value = [("Aspirin", 0.95), ("Ibuprofen", 0.88)]

        avg_result = MagicMock()
        avg_result.scalar.return_value = 0.915

        mock_session.execute = AsyncMock(side_effect=[top_result, avg_result])

        app.dependency_overrides[get_db] = lambda: mock_session
        with TestClient(app) as c:
            r = c.get("/analytics/drug-analogs")
        app.dependency_overrides.clear()

        assert r.status_code == 200
        data = r.json()
        assert len(data["topDrugAnalogs"]) == 2
        assert data["topDrugAnalogs"][0]["drugName"] == "Aspirin"
        assert data["topDrugAnalogs"][0]["similarityScore"] == pytest.approx(0.95)
        assert data["averageSimilarityScore"] == pytest.approx(0.915)

    def test_research_gaps_with_data(self, analytics_client):
        """Research gaps returns plants without compounds and sparse regions."""
        from src.main import app
        from src.dependencies import get_db

        mock_session = AsyncMock()

        no_compounds_result = MagicMock()
        no_compounds_result.all.return_value = [
            ("Salvia hispanica", "Oaxaca"),
            ("Agave tequilana", "Jalisco"),
        ]

        few_records_result = MagicMock()
        few_records_result.all.return_value = [("Baja California", 1)]

        mock_session.execute = AsyncMock(
            side_effect=[no_compounds_result, few_records_result]
        )

        app.dependency_overrides[get_db] = lambda: mock_session
        with TestClient(app) as c:
            r = c.get("/analytics/research-gaps")
        app.dependency_overrides.clear()

        assert r.status_code == 200
        data = r.json()
        assert len(data["plantsWithNoCompounds"]) == 2
        assert data["plantsWithNoCompounds"][0]["scientificName"] == "Salvia hispanica"
        assert data["plantsWithNoCompounds"][0]["region"] == "Oaxaca"
        assert len(data["regionsWithFewRecords"]) == 1
        assert data["regionsWithFewRecords"][0]["region"] == "Baja California"
        assert data["regionsWithFewRecords"][0]["count"] == 1

    def test_genomic_tracker_with_data(self, analytics_client):
        """Genomic tracker endpoint returns status breakdown."""
        from src.main import app
        from src.dependencies import get_db

        mock_session = AsyncMock()

        status_result = MagicMock()
        status_result.all.return_value = [("sequenced", 20), ("pending", 5)]

        mock_session.execute = AsyncMock(return_value=status_result)

        app.dependency_overrides[get_db] = lambda: mock_session
        with TestClient(app) as c:
            r = c.get("/analytics/genomic-tracker")
        app.dependency_overrides.clear()

        assert r.status_code == 200
        data = r.json()
        assert len(data["genomicStatusBreakdown"]) == 2
        assert data["genomicStatusBreakdown"][0]["status"] == "sequenced"
        assert data["genomicStatusBreakdown"][0]["count"] == 20

    def test_evidence_quality_with_data(self, analytics_client):
        """Evidence quality endpoint returns distribution by evidence level."""
        from src.main import app
        from src.dependencies import get_db

        mock_session = AsyncMock()

        level_result = MagicMock()
        level_result.all.return_value = [("high", 30), ("medium", 15), ("low", 5)]

        mock_session.execute = AsyncMock(return_value=level_result)

        app.dependency_overrides[get_db] = lambda: mock_session
        with TestClient(app) as c:
            r = c.get("/analytics/evidence-quality")
        app.dependency_overrides.clear()

        assert r.status_code == 200
        data = r.json()
        assert len(data["evidenceLevelDistribution"]) == 3
        assert data["evidenceLevelDistribution"][0]["level"] == "high"
        assert data["evidenceLevelDistribution"][0]["count"] == 30
