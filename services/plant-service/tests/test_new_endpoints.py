"""
Tests for the 12 new plant-service entity HTTP endpoints.
Uses FastAPI TestClient with mocked services — no real DB or network calls.
"""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.schemas.ethnobotanical import EthnobotanicalListResponse, EthnobotanicalResponse
from src.schemas.genomic_data import GenomicDataListResponse, GenomicDataResponse
from src.schemas.ontology_term import OntologyTermListResponse, OntologyTermResponse
from src.schemas.regional_availability import (
    RegionalAvailabilityListResponse,
    RegionalAvailabilityResponse,
)
from src.schemas.drug_reference import DrugReferenceListResponse, DrugReferenceResponse
from src.schemas.inference_job import InferenceJobListResponse, InferenceJobResponse
from src.schemas.data_pipeline import DataPipelineListResponse, DataPipelineResponse
from src.schemas.image_log import ImageLogListResponse, ImageLogResponse
from src.schemas.moderation import ModerationListResponse, ModerationResponse
from src.schemas.query_log import QueryLogListResponse, QueryLogResponse
from src.schemas.external_api import ExternalApiListResponse, ExternalApiResponse
from src.schemas.model_version import (
    ModelVersionActivateResponse,
    ModelVersionListResponse,
    ModelVersionResponse,
)
from src.models.moderation import ModerationItemType, ModerationStatus
from src.models.model_version import ModelStatus


# ---------------------------------------------------------------------------
# Helper – shared timestamp
# ---------------------------------------------------------------------------

def _now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Response factories
# ---------------------------------------------------------------------------

def _make_ethno_response() -> EthnobotanicalResponse:
    return EthnobotanicalResponse(
        id=uuid.uuid4(),
        species="Salvia hispanica",
        created_at=_now(),
        updated_at=_now(),
    )


def _make_genomic_response() -> GenomicDataResponse:
    return GenomicDataResponse(
        id=uuid.uuid4(),
        species="Salvia hispanica",
        created_at=_now(),
        updated_at=_now(),
    )


def _make_ontology_response() -> OntologyTermResponse:
    return OntologyTermResponse(
        id=uuid.uuid4(),
        canonical_term="headache",
        created_at=_now(),
        updated_at=_now(),
    )


def _make_regional_response() -> RegionalAvailabilityResponse:
    return RegionalAvailabilityResponse(
        id=uuid.uuid4(),
        species="Salvia hispanica",
        created_at=_now(),
        updated_at=_now(),
    )


def _make_drug_ref_response() -> DrugReferenceResponse:
    return DrugReferenceResponse(
        id=uuid.uuid4(),
        drug_name="Aspirin",
        created_at=_now(),
        updated_at=_now(),
    )


def _make_inference_job_response() -> InferenceJobResponse:
    return InferenceJobResponse(
        id=uuid.uuid4(),
        job_type="classification",
        created_at=_now(),
        updated_at=_now(),
    )


def _make_pipeline_response() -> DataPipelineResponse:
    return DataPipelineResponse(
        id=uuid.uuid4(),
        name="test-pipeline",
        created_at=_now(),
        updated_at=_now(),
    )


def _make_image_log_response() -> ImageLogResponse:
    return ImageLogResponse(
        id=uuid.uuid4(),
        image_url="http://example.com/img.jpg",
        flagged=False,
        created_at=_now(),
    )


def _make_moderation_response() -> ModerationResponse:
    return ModerationResponse(
        id=uuid.uuid4(),
        type=ModerationItemType.record,
        status=ModerationStatus.pending,
        created_at=_now(),
        updated_at=_now(),
    )


def _make_query_log_response() -> QueryLogResponse:
    return QueryLogResponse(
        id=uuid.uuid4(),
        query="test query",
        flagged=False,
        created_at=_now(),
    )


def _make_external_api_response() -> ExternalApiResponse:
    return ExternalApiResponse(
        id=uuid.uuid4(),
        name="test-api",
        base_url="http://example.com",
        created_at=_now(),
        updated_at=_now(),
    )


def _make_model_version_response() -> ModelVersionResponse:
    return ModelVersionResponse(
        id=uuid.uuid4(),
        name="plant-id-v1",
        version="1.0.0",
        created_at=_now(),
        updated_at=_now(),
    )


# ===========================================================================
# 1. Ethnobotanical
# ===========================================================================

@pytest.fixture
def mock_ethno_service():
    with patch("src.api.v1.endpoints.ethnobotanical.EthnobotanicalService") as M:
        inst = AsyncMock()
        M.return_value = inst
        yield inst


@pytest.fixture
def ethno_client(mock_ethno_service):
    from src.main import app
    from src.dependencies import get_db

    app.dependency_overrides[get_db] = lambda: AsyncMock()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


class TestEthnobotanicalEndpoints:

    def test_list_200(self, ethno_client, mock_ethno_service):
        mock_ethno_service.list_ethnobotanical.return_value = EthnobotanicalListResponse(
            items=[], total=0, page=1, size=20, pages=0
        )
        r = ethno_client.get("/ethnobotanical/")
        assert r.status_code == 200
        mock_ethno_service.list_ethnobotanical.assert_called_once()

    def test_get_200(self, ethno_client, mock_ethno_service):
        item = _make_ethno_response()
        mock_ethno_service.get_ethnobotanical.return_value = item
        r = ethno_client.get(f"/ethnobotanical/{item.id}")
        assert r.status_code == 200

    def test_get_404(self, ethno_client, mock_ethno_service):
        mock_ethno_service.get_ethnobotanical.return_value = None
        r = ethno_client.get(f"/ethnobotanical/{uuid.uuid4()}")
        assert r.status_code == 404

    def test_create_201(self, ethno_client, mock_ethno_service):
        mock_ethno_service.create_ethnobotanical.return_value = _make_ethno_response()
        r = ethno_client.post("/ethnobotanical/", json={"species": "Salvia hispanica"})
        assert r.status_code == 201

    def test_update_200(self, ethno_client, mock_ethno_service):
        item = _make_ethno_response()
        mock_ethno_service.update_ethnobotanical.return_value = item
        r = ethno_client.put(f"/ethnobotanical/{item.id}", json={"notes": "updated"})
        assert r.status_code == 200

    def test_update_404(self, ethno_client, mock_ethno_service):
        mock_ethno_service.update_ethnobotanical.return_value = None
        r = ethno_client.put(f"/ethnobotanical/{uuid.uuid4()}", json={})
        assert r.status_code == 404

    def test_delete_204(self, ethno_client, mock_ethno_service):
        mock_ethno_service.delete_ethnobotanical.return_value = True
        r = ethno_client.delete(f"/ethnobotanical/{uuid.uuid4()}")
        assert r.status_code == 204

    def test_delete_404(self, ethno_client, mock_ethno_service):
        mock_ethno_service.delete_ethnobotanical.return_value = False
        r = ethno_client.delete(f"/ethnobotanical/{uuid.uuid4()}")
        assert r.status_code == 404


# ===========================================================================
# 2. Genomic Data
# ===========================================================================

@pytest.fixture
def mock_genomic_service():
    with patch("src.api.v1.endpoints.genomic_data.GenomicDataService") as M:
        inst = AsyncMock()
        M.return_value = inst
        yield inst


@pytest.fixture
def genomic_client(mock_genomic_service):
    from src.main import app
    from src.dependencies import get_db

    app.dependency_overrides[get_db] = lambda: AsyncMock()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


class TestGenomicDataEndpoints:

    def test_list_200(self, genomic_client, mock_genomic_service):
        mock_genomic_service.list_genomic_data.return_value = GenomicDataListResponse(
            items=[], total=0, page=1, size=20, pages=0
        )
        r = genomic_client.get("/genomic-data/")
        assert r.status_code == 200
        mock_genomic_service.list_genomic_data.assert_called_once()

    def test_get_200(self, genomic_client, mock_genomic_service):
        item = _make_genomic_response()
        mock_genomic_service.get_genomic_data.return_value = item
        r = genomic_client.get(f"/genomic-data/{item.id}")
        assert r.status_code == 200

    def test_get_404(self, genomic_client, mock_genomic_service):
        mock_genomic_service.get_genomic_data.return_value = None
        r = genomic_client.get(f"/genomic-data/{uuid.uuid4()}")
        assert r.status_code == 404

    def test_create_201(self, genomic_client, mock_genomic_service):
        mock_genomic_service.create_genomic_data.return_value = _make_genomic_response()
        r = genomic_client.post("/genomic-data/", json={"species": "Salvia hispanica"})
        assert r.status_code == 201

    def test_update_200(self, genomic_client, mock_genomic_service):
        item = _make_genomic_response()
        mock_genomic_service.update_genomic_data.return_value = item
        r = genomic_client.put(f"/genomic-data/{item.id}", json={"genbank_id": "AB123"})
        assert r.status_code == 200

    def test_update_404(self, genomic_client, mock_genomic_service):
        mock_genomic_service.update_genomic_data.return_value = None
        r = genomic_client.put(f"/genomic-data/{uuid.uuid4()}", json={})
        assert r.status_code == 404

    def test_delete_204(self, genomic_client, mock_genomic_service):
        mock_genomic_service.delete_genomic_data.return_value = True
        r = genomic_client.delete(f"/genomic-data/{uuid.uuid4()}")
        assert r.status_code == 204

    def test_delete_404(self, genomic_client, mock_genomic_service):
        mock_genomic_service.delete_genomic_data.return_value = False
        r = genomic_client.delete(f"/genomic-data/{uuid.uuid4()}")
        assert r.status_code == 404


# ===========================================================================
# 3. Ontology Terms
# ===========================================================================

@pytest.fixture
def mock_ontology_service():
    with patch("src.api.v1.endpoints.ontology_terms.OntologyTermService") as M:
        inst = AsyncMock()
        M.return_value = inst
        yield inst


@pytest.fixture
def ontology_client(mock_ontology_service):
    from src.main import app
    from src.dependencies import get_db

    app.dependency_overrides[get_db] = lambda: AsyncMock()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


class TestOntologyTermEndpoints:

    def test_list_200(self, ontology_client, mock_ontology_service):
        mock_ontology_service.list_ontology_terms.return_value = OntologyTermListResponse(
            items=[], total=0, page=1, size=20, pages=0
        )
        r = ontology_client.get("/ontology-terms/")
        assert r.status_code == 200
        mock_ontology_service.list_ontology_terms.assert_called_once()

    def test_get_200(self, ontology_client, mock_ontology_service):
        item = _make_ontology_response()
        mock_ontology_service.get_ontology_term.return_value = item
        r = ontology_client.get(f"/ontology-terms/{item.id}")
        assert r.status_code == 200

    def test_get_404(self, ontology_client, mock_ontology_service):
        mock_ontology_service.get_ontology_term.return_value = None
        r = ontology_client.get(f"/ontology-terms/{uuid.uuid4()}")
        assert r.status_code == 404

    def test_create_201(self, ontology_client, mock_ontology_service):
        mock_ontology_service.create_ontology_term.return_value = _make_ontology_response()
        r = ontology_client.post("/ontology-terms/", json={"canonical_term": "headache"})
        assert r.status_code == 201

    def test_update_200(self, ontology_client, mock_ontology_service):
        item = _make_ontology_response()
        mock_ontology_service.update_ontology_term.return_value = item
        r = ontology_client.put(f"/ontology-terms/{item.id}", json={"description": "pain in the head"})
        assert r.status_code == 200

    def test_update_404(self, ontology_client, mock_ontology_service):
        mock_ontology_service.update_ontology_term.return_value = None
        r = ontology_client.put(f"/ontology-terms/{uuid.uuid4()}", json={})
        assert r.status_code == 404

    def test_delete_204(self, ontology_client, mock_ontology_service):
        mock_ontology_service.delete_ontology_term.return_value = True
        r = ontology_client.delete(f"/ontology-terms/{uuid.uuid4()}")
        assert r.status_code == 204

    def test_delete_404(self, ontology_client, mock_ontology_service):
        mock_ontology_service.delete_ontology_term.return_value = False
        r = ontology_client.delete(f"/ontology-terms/{uuid.uuid4()}")
        assert r.status_code == 404


# ===========================================================================
# 4. Regional Availability
# ===========================================================================

@pytest.fixture
def mock_regional_service():
    with patch("src.api.v1.endpoints.regional_availability.RegionalAvailabilityService") as M:
        inst = AsyncMock()
        M.return_value = inst
        yield inst


@pytest.fixture
def regional_client(mock_regional_service):
    from src.main import app
    from src.dependencies import get_db

    app.dependency_overrides[get_db] = lambda: AsyncMock()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


class TestRegionalAvailabilityEndpoints:

    def test_list_200(self, regional_client, mock_regional_service):
        mock_regional_service.list_regional_availability.return_value = RegionalAvailabilityListResponse(
            items=[], total=0, page=1, size=20, pages=0
        )
        r = regional_client.get("/regional-availability/")
        assert r.status_code == 200
        mock_regional_service.list_regional_availability.assert_called_once()

    def test_get_200(self, regional_client, mock_regional_service):
        item = _make_regional_response()
        mock_regional_service.get_regional_availability.return_value = item
        r = regional_client.get(f"/regional-availability/{item.id}")
        assert r.status_code == 200

    def test_get_404(self, regional_client, mock_regional_service):
        mock_regional_service.get_regional_availability.return_value = None
        r = regional_client.get(f"/regional-availability/{uuid.uuid4()}")
        assert r.status_code == 404

    def test_create_201(self, regional_client, mock_regional_service):
        mock_regional_service.create_regional_availability.return_value = _make_regional_response()
        r = regional_client.post("/regional-availability/", json={"species": "Salvia hispanica"})
        assert r.status_code == 201

    def test_update_200(self, regional_client, mock_regional_service):
        item = _make_regional_response()
        mock_regional_service.update_regional_availability.return_value = item
        r = regional_client.put(f"/regional-availability/{item.id}", json={"state": "Oaxaca"})
        assert r.status_code == 200

    def test_update_404(self, regional_client, mock_regional_service):
        mock_regional_service.update_regional_availability.return_value = None
        r = regional_client.put(f"/regional-availability/{uuid.uuid4()}", json={})
        assert r.status_code == 404

    def test_delete_204(self, regional_client, mock_regional_service):
        mock_regional_service.delete_regional_availability.return_value = True
        r = regional_client.delete(f"/regional-availability/{uuid.uuid4()}")
        assert r.status_code == 204

    def test_delete_404(self, regional_client, mock_regional_service):
        mock_regional_service.delete_regional_availability.return_value = False
        r = regional_client.delete(f"/regional-availability/{uuid.uuid4()}")
        assert r.status_code == 404


# ===========================================================================
# 5. Drug References
# ===========================================================================

@pytest.fixture
def mock_drug_ref_service():
    with patch("src.api.v1.endpoints.drug_references.DrugReferenceService") as M:
        inst = AsyncMock()
        M.return_value = inst
        yield inst


@pytest.fixture
def drug_ref_client(mock_drug_ref_service):
    from src.main import app
    from src.dependencies import get_db

    app.dependency_overrides[get_db] = lambda: AsyncMock()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


class TestDrugReferenceEndpoints:

    def test_list_200(self, drug_ref_client, mock_drug_ref_service):
        mock_drug_ref_service.list_drug_references.return_value = DrugReferenceListResponse(
            items=[], total=0, page=1, size=20, pages=0
        )
        r = drug_ref_client.get("/drug-references/")
        assert r.status_code == 200
        mock_drug_ref_service.list_drug_references.assert_called_once()

    def test_get_200(self, drug_ref_client, mock_drug_ref_service):
        item = _make_drug_ref_response()
        mock_drug_ref_service.get_drug_reference.return_value = item
        r = drug_ref_client.get(f"/drug-references/{item.id}")
        assert r.status_code == 200

    def test_get_404(self, drug_ref_client, mock_drug_ref_service):
        mock_drug_ref_service.get_drug_reference.return_value = None
        r = drug_ref_client.get(f"/drug-references/{uuid.uuid4()}")
        assert r.status_code == 404

    def test_create_201(self, drug_ref_client, mock_drug_ref_service):
        mock_drug_ref_service.create_drug_reference.return_value = _make_drug_ref_response()
        r = drug_ref_client.post("/drug-references/", json={"drug_name": "Aspirin"})
        assert r.status_code == 201

    def test_update_200(self, drug_ref_client, mock_drug_ref_service):
        item = _make_drug_ref_response()
        mock_drug_ref_service.update_drug_reference.return_value = item
        r = drug_ref_client.put(f"/drug-references/{item.id}", json={"mechanism": "COX inhibitor"})
        assert r.status_code == 200

    def test_update_404(self, drug_ref_client, mock_drug_ref_service):
        mock_drug_ref_service.update_drug_reference.return_value = None
        r = drug_ref_client.put(f"/drug-references/{uuid.uuid4()}", json={})
        assert r.status_code == 404

    def test_delete_204(self, drug_ref_client, mock_drug_ref_service):
        mock_drug_ref_service.delete_drug_reference.return_value = True
        r = drug_ref_client.delete(f"/drug-references/{uuid.uuid4()}")
        assert r.status_code == 204

    def test_delete_404(self, drug_ref_client, mock_drug_ref_service):
        mock_drug_ref_service.delete_drug_reference.return_value = False
        r = drug_ref_client.delete(f"/drug-references/{uuid.uuid4()}")
        assert r.status_code == 404


# ===========================================================================
# 6. Inference Jobs
# ===========================================================================

@pytest.fixture
def mock_inference_service():
    with patch("src.api.v1.endpoints.inference_jobs.InferenceJobService") as M:
        inst = AsyncMock()
        M.return_value = inst
        yield inst


@pytest.fixture
def inference_client(mock_inference_service):
    from src.main import app
    from src.dependencies import get_db

    app.dependency_overrides[get_db] = lambda: AsyncMock()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


class TestInferenceJobEndpoints:

    def test_list_200(self, inference_client, mock_inference_service):
        mock_inference_service.list_inference_jobs.return_value = InferenceJobListResponse(
            items=[], total=0, page=1, size=20, pages=0
        )
        r = inference_client.get("/inference-jobs/")
        assert r.status_code == 200
        mock_inference_service.list_inference_jobs.assert_called_once()

    def test_get_200(self, inference_client, mock_inference_service):
        item = _make_inference_job_response()
        mock_inference_service.get_inference_job.return_value = item
        r = inference_client.get(f"/inference-jobs/{item.id}")
        assert r.status_code == 200

    def test_get_404(self, inference_client, mock_inference_service):
        mock_inference_service.get_inference_job.return_value = None
        r = inference_client.get(f"/inference-jobs/{uuid.uuid4()}")
        assert r.status_code == 404

    def test_create_201(self, inference_client, mock_inference_service):
        mock_inference_service.create_inference_job.return_value = _make_inference_job_response()
        r = inference_client.post("/inference-jobs/", json={"job_type": "classification"})
        assert r.status_code == 201

    def test_update_200(self, inference_client, mock_inference_service):
        item = _make_inference_job_response()
        mock_inference_service.update_inference_job.return_value = item
        r = inference_client.put(f"/inference-jobs/{item.id}", json={"flagged_for_review": True})
        assert r.status_code == 200

    def test_update_404(self, inference_client, mock_inference_service):
        mock_inference_service.update_inference_job.return_value = None
        r = inference_client.put(f"/inference-jobs/{uuid.uuid4()}", json={})
        assert r.status_code == 404

    def test_delete_204(self, inference_client, mock_inference_service):
        mock_inference_service.delete_inference_job.return_value = True
        r = inference_client.delete(f"/inference-jobs/{uuid.uuid4()}")
        assert r.status_code == 204

    def test_delete_404(self, inference_client, mock_inference_service):
        mock_inference_service.delete_inference_job.return_value = False
        r = inference_client.delete(f"/inference-jobs/{uuid.uuid4()}")
        assert r.status_code == 404


# ===========================================================================
# 7. Data Pipelines
# ===========================================================================

@pytest.fixture
def mock_pipeline_service():
    with patch("src.api.v1.endpoints.data_pipelines.DataPipelineService") as M:
        inst = AsyncMock()
        M.return_value = inst
        yield inst


@pytest.fixture
def pipeline_client(mock_pipeline_service):
    from src.main import app
    from src.dependencies import get_db

    app.dependency_overrides[get_db] = lambda: AsyncMock()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


class TestDataPipelineEndpoints:

    def test_list_200(self, pipeline_client, mock_pipeline_service):
        mock_pipeline_service.list_pipelines.return_value = DataPipelineListResponse(
            items=[], total=0, page=1, size=20, pages=0
        )
        r = pipeline_client.get("/data-pipelines/")
        assert r.status_code == 200
        mock_pipeline_service.list_pipelines.assert_called_once()

    def test_get_200(self, pipeline_client, mock_pipeline_service):
        item = _make_pipeline_response()
        mock_pipeline_service.get_pipeline.return_value = item
        r = pipeline_client.get(f"/data-pipelines/{item.id}")
        assert r.status_code == 200

    def test_get_404(self, pipeline_client, mock_pipeline_service):
        mock_pipeline_service.get_pipeline.return_value = None
        r = pipeline_client.get(f"/data-pipelines/{uuid.uuid4()}")
        assert r.status_code == 404

    def test_create_201(self, pipeline_client, mock_pipeline_service):
        mock_pipeline_service.create_pipeline.return_value = _make_pipeline_response()
        r = pipeline_client.post("/data-pipelines/", json={"name": "test-pipeline"})
        assert r.status_code == 201

    def test_update_200(self, pipeline_client, mock_pipeline_service):
        item = _make_pipeline_response()
        mock_pipeline_service.update_pipeline.return_value = item
        r = pipeline_client.put(f"/data-pipelines/{item.id}", json={"source": "gbif"})
        assert r.status_code == 200

    def test_update_404(self, pipeline_client, mock_pipeline_service):
        mock_pipeline_service.update_pipeline.return_value = None
        r = pipeline_client.put(f"/data-pipelines/{uuid.uuid4()}", json={})
        assert r.status_code == 404

    def test_delete_204(self, pipeline_client, mock_pipeline_service):
        mock_pipeline_service.delete_pipeline.return_value = True
        r = pipeline_client.delete(f"/data-pipelines/{uuid.uuid4()}")
        assert r.status_code == 204

    def test_delete_404(self, pipeline_client, mock_pipeline_service):
        mock_pipeline_service.delete_pipeline.return_value = False
        r = pipeline_client.delete(f"/data-pipelines/{uuid.uuid4()}")
        assert r.status_code == 404

    def test_trigger_200(self, pipeline_client, mock_pipeline_service):
        item = _make_pipeline_response()
        mock_pipeline_service.trigger_pipeline.return_value = item
        r = pipeline_client.post(f"/data-pipelines/{item.id}/trigger")
        assert r.status_code == 200

    def test_trigger_404(self, pipeline_client, mock_pipeline_service):
        mock_pipeline_service.trigger_pipeline.return_value = None
        r = pipeline_client.post(f"/data-pipelines/{uuid.uuid4()}/trigger")
        assert r.status_code == 404


# ===========================================================================
# 8. Image Logs  (no POST)
# ===========================================================================

@pytest.fixture
def mock_image_log_service():
    with patch("src.api.v1.endpoints.image_logs.ImageLogService") as M:
        inst = AsyncMock()
        M.return_value = inst
        yield inst


@pytest.fixture
def image_log_client(mock_image_log_service):
    from src.main import app
    from src.dependencies import get_db

    app.dependency_overrides[get_db] = lambda: AsyncMock()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


class TestImageLogEndpoints:

    def test_list_200(self, image_log_client, mock_image_log_service):
        mock_image_log_service.list_image_logs.return_value = ImageLogListResponse(
            items=[], total=0, page=1, size=20, pages=0
        )
        r = image_log_client.get("/image-logs/")
        assert r.status_code == 200
        mock_image_log_service.list_image_logs.assert_called_once()

    def test_get_200(self, image_log_client, mock_image_log_service):
        item = _make_image_log_response()
        mock_image_log_service.get_image_log.return_value = item
        r = image_log_client.get(f"/image-logs/{item.id}")
        assert r.status_code == 200

    def test_get_404(self, image_log_client, mock_image_log_service):
        mock_image_log_service.get_image_log.return_value = None
        r = image_log_client.get(f"/image-logs/{uuid.uuid4()}")
        assert r.status_code == 404

    def test_update_200(self, image_log_client, mock_image_log_service):
        item = _make_image_log_response()
        mock_image_log_service.update_image_log.return_value = item
        r = image_log_client.put(f"/image-logs/{item.id}", json={"flagged": True})
        assert r.status_code == 200

    def test_update_404(self, image_log_client, mock_image_log_service):
        mock_image_log_service.update_image_log.return_value = None
        r = image_log_client.put(f"/image-logs/{uuid.uuid4()}", json={"flagged": True})
        assert r.status_code == 404

    def test_delete_204(self, image_log_client, mock_image_log_service):
        mock_image_log_service.delete_image_log.return_value = True
        r = image_log_client.delete(f"/image-logs/{uuid.uuid4()}")
        assert r.status_code == 204

    def test_delete_404(self, image_log_client, mock_image_log_service):
        mock_image_log_service.delete_image_log.return_value = False
        r = image_log_client.delete(f"/image-logs/{uuid.uuid4()}")
        assert r.status_code == 404


# ===========================================================================
# 9. Moderation
# ===========================================================================

@pytest.fixture
def mock_moderation_service():
    with patch("src.api.v1.endpoints.moderation.ModerationService") as M:
        inst = AsyncMock()
        M.return_value = inst
        yield inst


@pytest.fixture
def moderation_client(mock_moderation_service):
    from src.main import app
    from src.dependencies import get_db

    app.dependency_overrides[get_db] = lambda: AsyncMock()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


class TestModerationEndpoints:

    def test_list_200(self, moderation_client, mock_moderation_service):
        mock_moderation_service.list_moderation_items.return_value = ModerationListResponse(
            items=[], total=0, page=1, size=20, pages=0
        )
        r = moderation_client.get("/moderation/")
        assert r.status_code == 200
        mock_moderation_service.list_moderation_items.assert_called_once()

    def test_get_200(self, moderation_client, mock_moderation_service):
        item = _make_moderation_response()
        mock_moderation_service.get_moderation_item.return_value = item
        r = moderation_client.get(f"/moderation/{item.id}")
        assert r.status_code == 200

    def test_get_404(self, moderation_client, mock_moderation_service):
        mock_moderation_service.get_moderation_item.return_value = None
        r = moderation_client.get(f"/moderation/{uuid.uuid4()}")
        assert r.status_code == 404

    def test_create_201(self, moderation_client, mock_moderation_service):
        mock_moderation_service.create_moderation_item.return_value = _make_moderation_response()
        r = moderation_client.post("/moderation/", json={"type": "record", "content": {}})
        assert r.status_code == 201

    def test_update_200(self, moderation_client, mock_moderation_service):
        item = _make_moderation_response()
        mock_moderation_service.update_moderation_item.return_value = item
        r = moderation_client.put(f"/moderation/{item.id}", json={"notes": "reviewed"})
        assert r.status_code == 200

    def test_update_404(self, moderation_client, mock_moderation_service):
        mock_moderation_service.update_moderation_item.return_value = None
        r = moderation_client.put(f"/moderation/{uuid.uuid4()}", json={})
        assert r.status_code == 404

    def test_delete_204(self, moderation_client, mock_moderation_service):
        mock_moderation_service.delete_moderation_item.return_value = True
        r = moderation_client.delete(f"/moderation/{uuid.uuid4()}")
        assert r.status_code == 204

    def test_delete_404(self, moderation_client, mock_moderation_service):
        mock_moderation_service.delete_moderation_item.return_value = False
        r = moderation_client.delete(f"/moderation/{uuid.uuid4()}")
        assert r.status_code == 404

    def test_approve_200(self, moderation_client, mock_moderation_service):
        item = _make_moderation_response()
        mock_moderation_service.approve_item.return_value = item
        r = moderation_client.put(f"/moderation/{item.id}/approve", json={})
        assert r.status_code == 200

    def test_approve_404(self, moderation_client, mock_moderation_service):
        mock_moderation_service.approve_item.return_value = None
        r = moderation_client.put(f"/moderation/{uuid.uuid4()}/approve", json={})
        assert r.status_code == 404

    def test_reject_200(self, moderation_client, mock_moderation_service):
        item = _make_moderation_response()
        mock_moderation_service.reject_item.return_value = item
        r = moderation_client.put(f"/moderation/{item.id}/reject", json={})
        assert r.status_code == 200

    def test_reject_404(self, moderation_client, mock_moderation_service):
        mock_moderation_service.reject_item.return_value = None
        r = moderation_client.put(f"/moderation/{uuid.uuid4()}/reject", json={})
        assert r.status_code == 404


# ===========================================================================
# 10. Query Logs  (no POST)
# ===========================================================================

@pytest.fixture
def mock_query_log_service():
    with patch("src.api.v1.endpoints.query_logs.QueryLogService") as M:
        inst = AsyncMock()
        M.return_value = inst
        yield inst


@pytest.fixture
def query_log_client(mock_query_log_service):
    from src.main import app
    from src.dependencies import get_db

    app.dependency_overrides[get_db] = lambda: AsyncMock()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


class TestQueryLogEndpoints:

    def test_list_200(self, query_log_client, mock_query_log_service):
        mock_query_log_service.list_query_logs.return_value = QueryLogListResponse(
            items=[], total=0, page=1, size=20, pages=0
        )
        r = query_log_client.get("/query-logs/")
        assert r.status_code == 200
        mock_query_log_service.list_query_logs.assert_called_once()

    def test_get_200(self, query_log_client, mock_query_log_service):
        item = _make_query_log_response()
        mock_query_log_service.get_query_log.return_value = item
        r = query_log_client.get(f"/query-logs/{item.id}")
        assert r.status_code == 200

    def test_get_404(self, query_log_client, mock_query_log_service):
        mock_query_log_service.get_query_log.return_value = None
        r = query_log_client.get(f"/query-logs/{uuid.uuid4()}")
        assert r.status_code == 404

    def test_update_200(self, query_log_client, mock_query_log_service):
        item = _make_query_log_response()
        mock_query_log_service.update_query_log.return_value = item
        r = query_log_client.put(f"/query-logs/{item.id}", json={"flagged": True})
        assert r.status_code == 200

    def test_update_404(self, query_log_client, mock_query_log_service):
        mock_query_log_service.update_query_log.return_value = None
        r = query_log_client.put(f"/query-logs/{uuid.uuid4()}", json={"flagged": True})
        assert r.status_code == 404

    def test_delete_204(self, query_log_client, mock_query_log_service):
        mock_query_log_service.delete_query_log.return_value = True
        r = query_log_client.delete(f"/query-logs/{uuid.uuid4()}")
        assert r.status_code == 204

    def test_delete_404(self, query_log_client, mock_query_log_service):
        mock_query_log_service.delete_query_log.return_value = False
        r = query_log_client.delete(f"/query-logs/{uuid.uuid4()}")
        assert r.status_code == 404


# ===========================================================================
# 11. External APIs
# ===========================================================================

@pytest.fixture
def mock_external_api_service():
    with patch("src.api.v1.endpoints.external_apis.ExternalApiService") as M:
        inst = AsyncMock()
        M.return_value = inst
        yield inst


@pytest.fixture
def external_api_client(mock_external_api_service):
    from src.main import app
    from src.dependencies import get_db

    app.dependency_overrides[get_db] = lambda: AsyncMock()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


class TestExternalApiEndpoints:

    def test_list_200(self, external_api_client, mock_external_api_service):
        mock_external_api_service.list_apis.return_value = ExternalApiListResponse(
            items=[], total=0, page=1, size=20, pages=0
        )
        r = external_api_client.get("/external-apis/")
        assert r.status_code == 200
        mock_external_api_service.list_apis.assert_called_once()

    def test_get_200(self, external_api_client, mock_external_api_service):
        item = _make_external_api_response()
        mock_external_api_service.get_api.return_value = item
        r = external_api_client.get(f"/external-apis/{item.id}")
        assert r.status_code == 200

    def test_get_404(self, external_api_client, mock_external_api_service):
        mock_external_api_service.get_api.return_value = None
        r = external_api_client.get(f"/external-apis/{uuid.uuid4()}")
        assert r.status_code == 404

    def test_create_201(self, external_api_client, mock_external_api_service):
        mock_external_api_service.create_api.return_value = _make_external_api_response()
        r = external_api_client.post(
            "/external-apis/",
            json={"name": "test-api", "base_url": "http://example.com"},
        )
        assert r.status_code == 201

    def test_update_200(self, external_api_client, mock_external_api_service):
        item = _make_external_api_response()
        mock_external_api_service.update_api.return_value = item
        r = external_api_client.put(f"/external-apis/{item.id}", json={"description": "updated"})
        assert r.status_code == 200

    def test_update_404(self, external_api_client, mock_external_api_service):
        mock_external_api_service.update_api.return_value = None
        r = external_api_client.put(f"/external-apis/{uuid.uuid4()}", json={})
        assert r.status_code == 404

    def test_delete_204(self, external_api_client, mock_external_api_service):
        mock_external_api_service.delete_api.return_value = True
        r = external_api_client.delete(f"/external-apis/{uuid.uuid4()}")
        assert r.status_code == 204

    def test_delete_404(self, external_api_client, mock_external_api_service):
        mock_external_api_service.delete_api.return_value = False
        r = external_api_client.delete(f"/external-apis/{uuid.uuid4()}")
        assert r.status_code == 404


# ===========================================================================
# 12. Model Versions
# ===========================================================================

@pytest.fixture
def mock_mv_service():
    with patch("src.api.v1.endpoints.model_versions.ModelVersionService") as M:
        inst = AsyncMock()
        M.return_value = inst
        yield inst


@pytest.fixture
def mv_client(mock_mv_service):
    from src.main import app
    from src.dependencies import get_db

    app.dependency_overrides[get_db] = lambda: AsyncMock()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


class TestModelVersionEndpoints:

    def test_list_200(self, mv_client, mock_mv_service):
        mock_mv_service.list_versions.return_value = ModelVersionListResponse(
            items=[], total=0, page=1, size=20, pages=0
        )
        r = mv_client.get("/model-versions/")
        assert r.status_code == 200
        mock_mv_service.list_versions.assert_called_once()

    def test_get_200(self, mv_client, mock_mv_service):
        item = _make_model_version_response()
        mock_mv_service.get_version.return_value = item
        r = mv_client.get(f"/model-versions/{item.id}")
        assert r.status_code == 200

    def test_get_404(self, mv_client, mock_mv_service):
        mock_mv_service.get_version.return_value = None
        r = mv_client.get(f"/model-versions/{uuid.uuid4()}")
        assert r.status_code == 404

    def test_create_201(self, mv_client, mock_mv_service):
        mock_mv_service.create_version.return_value = _make_model_version_response()
        r = mv_client.post(
            "/model-versions/",
            json={"name": "plant-id-v1", "version": "1.0.0"},
        )
        assert r.status_code == 201

    def test_update_200(self, mv_client, mock_mv_service):
        item = _make_model_version_response()
        mock_mv_service.update_version.return_value = item
        r = mv_client.put(f"/model-versions/{item.id}", json={"notes": "patched"})
        assert r.status_code == 200

    def test_update_404(self, mv_client, mock_mv_service):
        mock_mv_service.update_version.return_value = None
        r = mv_client.put(f"/model-versions/{uuid.uuid4()}", json={})
        assert r.status_code == 404

    def test_delete_204(self, mv_client, mock_mv_service):
        mock_mv_service.delete_version.return_value = True
        r = mv_client.delete(f"/model-versions/{uuid.uuid4()}")
        assert r.status_code == 204

    def test_delete_404(self, mv_client, mock_mv_service):
        mock_mv_service.delete_version.return_value = False
        r = mv_client.delete(f"/model-versions/{uuid.uuid4()}")
        assert r.status_code == 404

    def test_activate_200(self, mv_client, mock_mv_service):
        mock_version = MagicMock()
        mock_version.id = uuid.uuid4()
        mock_version.status = ModelStatus.active
        mock_mv_service.activate_version.return_value = mock_version
        r = mv_client.put(f"/model-versions/{mock_version.id}/activate")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == ModelStatus.active.value

    def test_activate_404(self, mv_client, mock_mv_service):
        mock_mv_service.activate_version.return_value = None
        r = mv_client.put(f"/model-versions/{uuid.uuid4()}/activate")
        assert r.status_code == 404

    def test_rollback_200(self, mv_client, mock_mv_service):
        mock_version = MagicMock()
        mock_version.id = uuid.uuid4()
        mock_version.status = ModelStatus.deprecated
        mock_mv_service.rollback_version.return_value = mock_version
        r = mv_client.put(f"/model-versions/{mock_version.id}/rollback")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == ModelStatus.deprecated.value

    def test_rollback_404(self, mv_client, mock_mv_service):
        mock_mv_service.rollback_version.return_value = None
        r = mv_client.put(f"/model-versions/{uuid.uuid4()}/rollback")
        assert r.status_code == 404
