"""
Unit tests for the 12 new plant-service entity services.
All DB calls are mocked via the mock_db_session fixture.
"""
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.services.ethnobotanical_service import EthnobotanicalService
from src.schemas.ethnobotanical import EthnobotanicalCreate, EthnobotanicalUpdate

from src.services.genomic_data_service import GenomicDataService
from src.schemas.genomic_data import GenomicDataCreate, GenomicDataUpdate

from src.services.ontology_term_service import OntologyTermService
from src.schemas.ontology_term import OntologyTermCreate, OntologyTermUpdate

from src.services.regional_availability_service import RegionalAvailabilityService
from src.schemas.regional_availability import RegionalAvailabilityCreate, RegionalAvailabilityUpdate

from src.services.drug_reference_service import DrugReferenceService
from src.schemas.drug_reference import DrugReferenceCreate, DrugReferenceUpdate

from src.services.inference_job_service import InferenceJobService
from src.schemas.inference_job import InferenceJobCreate, InferenceJobUpdate

from src.services.data_pipeline_service import DataPipelineService
from src.schemas.data_pipeline import DataPipelineCreate, DataPipelineUpdate

from src.services.image_log_service import ImageLogService
from src.schemas.image_log import ImageLogUpdate

from src.services.moderation_service import ModerationService
from src.schemas.moderation import ModerationCreate, ModerationUpdate
from src.models.moderation import ModerationItemType

from src.services.query_log_service import QueryLogService
from src.schemas.query_log import QueryLogFlagUpdate

from src.services.external_api_service import ExternalApiService
from src.schemas.external_api import ExternalApiCreate, ExternalApiUpdate

from src.services.model_version_service import ModelVersionService
from src.schemas.model_version import ModelVersionCreate, ModelVersionUpdate


# ===========================================================================
# 1. EthnobotanicalService
# ===========================================================================

class TestEthnobotanicalService:

    def _make_service(self, session):
        svc = EthnobotanicalService(session=session)
        svc.repo = AsyncMock()
        return svc

    @pytest.mark.asyncio
    async def test_list(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_list.return_value = ([], 0)
        result = await svc.list_ethnobotanical(page=1, size=20)
        assert result.total == 0
        assert result.items == []

    @pytest.mark.asyncio
    async def test_get_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        mock_obj = MagicMock()
        mock_obj.id = uuid.uuid4()
        svc.repo.get_by_id.return_value = mock_obj
        result = await svc.get_ethnobotanical(mock_obj.id)
        assert result == mock_obj

    @pytest.mark.asyncio
    async def test_get_not_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = None
        result = await svc.get_ethnobotanical(uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_create(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        mock_obj = MagicMock()
        svc.repo.create.return_value = mock_obj
        data = EthnobotanicalCreate(species="Salvia hispanica")
        result = await svc.create_ethnobotanical(data)
        svc.repo.create.assert_called_once()
        mock_db_session.commit.assert_called_once()
        assert result == mock_obj

    @pytest.mark.asyncio
    async def test_update_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        mock_obj = MagicMock()
        svc.repo.get_by_id.return_value = mock_obj
        svc.repo.update.return_value = mock_obj
        data = EthnobotanicalUpdate(notes="updated")
        result = await svc.update_ethnobotanical(uuid.uuid4(), data)
        assert result == mock_obj
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_not_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = None
        result = await svc.update_ethnobotanical(uuid.uuid4(), EthnobotanicalUpdate())
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = MagicMock()
        result = await svc.delete_ethnobotanical(uuid.uuid4())
        assert result is True
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_not_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = None
        result = await svc.delete_ethnobotanical(uuid.uuid4())
        assert result is False


# ===========================================================================
# 2. GenomicDataService
# ===========================================================================

class TestGenomicDataService:

    def _make_service(self, session):
        svc = GenomicDataService(session=session)
        svc.repo = AsyncMock()
        return svc

    @pytest.mark.asyncio
    async def test_list(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_list.return_value = ([], 0)
        result = await svc.list_genomic_data(page=1, size=20)
        assert result.total == 0
        assert result.items == []

    @pytest.mark.asyncio
    async def test_get_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        mock_obj = MagicMock()
        mock_obj.id = uuid.uuid4()
        svc.repo.get_by_id.return_value = mock_obj
        result = await svc.get_genomic_data(mock_obj.id)
        assert result == mock_obj

    @pytest.mark.asyncio
    async def test_get_not_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = None
        result = await svc.get_genomic_data(uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_create(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        mock_obj = MagicMock()
        svc.repo.create.return_value = mock_obj
        data = GenomicDataCreate(species="Salvia hispanica")
        result = await svc.create_genomic_data(data)
        svc.repo.create.assert_called_once()
        mock_db_session.commit.assert_called_once()
        assert result == mock_obj

    @pytest.mark.asyncio
    async def test_update_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        mock_obj = MagicMock()
        svc.repo.get_by_id.return_value = mock_obj
        svc.repo.update.return_value = mock_obj
        data = GenomicDataUpdate(genbank_id="XY123")
        result = await svc.update_genomic_data(uuid.uuid4(), data)
        assert result == mock_obj
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_not_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = None
        result = await svc.update_genomic_data(uuid.uuid4(), GenomicDataUpdate())
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = MagicMock()
        result = await svc.delete_genomic_data(uuid.uuid4())
        assert result is True
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_not_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = None
        result = await svc.delete_genomic_data(uuid.uuid4())
        assert result is False


# ===========================================================================
# 3. OntologyTermService
# ===========================================================================

class TestOntologyTermService:

    def _make_service(self, session):
        svc = OntologyTermService(session=session)
        svc.repo = AsyncMock()
        return svc

    @pytest.mark.asyncio
    async def test_list(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_list.return_value = ([], 0)
        result = await svc.list_ontology_terms(page=1, size=20)
        assert result.total == 0
        assert result.items == []

    @pytest.mark.asyncio
    async def test_get_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        mock_obj = MagicMock()
        mock_obj.id = uuid.uuid4()
        svc.repo.get_by_id.return_value = mock_obj
        result = await svc.get_ontology_term(mock_obj.id)
        assert result == mock_obj

    @pytest.mark.asyncio
    async def test_get_not_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = None
        result = await svc.get_ontology_term(uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_create(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        mock_obj = MagicMock()
        svc.repo.create.return_value = mock_obj
        data = OntologyTermCreate(canonical_term="headache")
        result = await svc.create_ontology_term(data)
        svc.repo.create.assert_called_once()
        mock_db_session.commit.assert_called_once()
        assert result == mock_obj

    @pytest.mark.asyncio
    async def test_update_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        mock_obj = MagicMock()
        svc.repo.get_by_id.return_value = mock_obj
        svc.repo.update.return_value = mock_obj
        data = OntologyTermUpdate(description="updated")
        result = await svc.update_ontology_term(uuid.uuid4(), data)
        assert result == mock_obj
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_not_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = None
        result = await svc.update_ontology_term(uuid.uuid4(), OntologyTermUpdate())
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = MagicMock()
        result = await svc.delete_ontology_term(uuid.uuid4())
        assert result is True
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_not_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = None
        result = await svc.delete_ontology_term(uuid.uuid4())
        assert result is False


# ===========================================================================
# 4. RegionalAvailabilityService
# ===========================================================================

class TestRegionalAvailabilityService:

    def _make_service(self, session):
        svc = RegionalAvailabilityService(session=session)
        svc.repo = AsyncMock()
        return svc

    @pytest.mark.asyncio
    async def test_list(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_list.return_value = ([], 0)
        result = await svc.list_regional_availability(page=1, size=20)
        assert result.total == 0
        assert result.items == []

    @pytest.mark.asyncio
    async def test_get_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        mock_obj = MagicMock()
        mock_obj.id = uuid.uuid4()
        svc.repo.get_by_id.return_value = mock_obj
        result = await svc.get_regional_availability(mock_obj.id)
        assert result == mock_obj

    @pytest.mark.asyncio
    async def test_get_not_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = None
        result = await svc.get_regional_availability(uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_create(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        mock_obj = MagicMock()
        svc.repo.create.return_value = mock_obj
        data = RegionalAvailabilityCreate(species="Salvia hispanica")
        result = await svc.create_regional_availability(data)
        svc.repo.create.assert_called_once()
        mock_db_session.commit.assert_called_once()
        assert result == mock_obj

    @pytest.mark.asyncio
    async def test_update_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        mock_obj = MagicMock()
        svc.repo.get_by_id.return_value = mock_obj
        svc.repo.update.return_value = mock_obj
        data = RegionalAvailabilityUpdate(notes="updated")
        result = await svc.update_regional_availability(uuid.uuid4(), data)
        assert result == mock_obj
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_not_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = None
        result = await svc.update_regional_availability(uuid.uuid4(), RegionalAvailabilityUpdate())
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = MagicMock()
        result = await svc.delete_regional_availability(uuid.uuid4())
        assert result is True
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_not_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = None
        result = await svc.delete_regional_availability(uuid.uuid4())
        assert result is False


# ===========================================================================
# 5. DrugReferenceService
# ===========================================================================

class TestDrugReferenceService:

    def _make_service(self, session):
        svc = DrugReferenceService(session=session)
        svc.repo = AsyncMock()
        return svc

    @pytest.mark.asyncio
    async def test_list(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_list.return_value = ([], 0)
        result = await svc.list_drug_references(page=1, size=20)
        assert result.total == 0
        assert result.items == []

    @pytest.mark.asyncio
    async def test_get_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        mock_obj = MagicMock()
        mock_obj.id = uuid.uuid4()
        svc.repo.get_by_id.return_value = mock_obj
        result = await svc.get_drug_reference(mock_obj.id)
        assert result == mock_obj

    @pytest.mark.asyncio
    async def test_get_not_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = None
        result = await svc.get_drug_reference(uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_create(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        mock_obj = MagicMock()
        svc.repo.create.return_value = mock_obj
        data = DrugReferenceCreate(drug_name="Aspirin")
        result = await svc.create_drug_reference(data)
        svc.repo.create.assert_called_once()
        mock_db_session.commit.assert_called_once()
        assert result == mock_obj

    @pytest.mark.asyncio
    async def test_update_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        mock_obj = MagicMock()
        svc.repo.get_by_id.return_value = mock_obj
        svc.repo.update.return_value = mock_obj
        data = DrugReferenceUpdate(notes="updated")
        result = await svc.update_drug_reference(uuid.uuid4(), data)
        assert result == mock_obj
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_not_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = None
        result = await svc.update_drug_reference(uuid.uuid4(), DrugReferenceUpdate())
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = MagicMock()
        result = await svc.delete_drug_reference(uuid.uuid4())
        assert result is True
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_not_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = None
        result = await svc.delete_drug_reference(uuid.uuid4())
        assert result is False


# ===========================================================================
# 6. InferenceJobService
# ===========================================================================

class TestInferenceJobService:

    def _make_service(self, session):
        svc = InferenceJobService(session=session)
        svc.repo = AsyncMock()
        return svc

    @pytest.mark.asyncio
    async def test_list(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_list.return_value = ([], 0)
        result = await svc.list_inference_jobs(page=1, size=20)
        assert result.total == 0
        assert result.items == []

    @pytest.mark.asyncio
    async def test_get_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        mock_obj = MagicMock()
        mock_obj.id = uuid.uuid4()
        svc.repo.get_by_id.return_value = mock_obj
        result = await svc.get_inference_job(mock_obj.id)
        assert result == mock_obj

    @pytest.mark.asyncio
    async def test_get_not_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = None
        result = await svc.get_inference_job(uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_create(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        mock_obj = MagicMock()
        svc.repo.create.return_value = mock_obj
        data = InferenceJobCreate(job_type="classification")
        result = await svc.create_inference_job(data)
        svc.repo.create.assert_called_once()
        mock_db_session.commit.assert_called_once()
        assert result == mock_obj

    @pytest.mark.asyncio
    async def test_update_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        mock_obj = MagicMock()
        svc.repo.get_by_id.return_value = mock_obj
        svc.repo.update.return_value = mock_obj
        data = InferenceJobUpdate(flagged_for_review=True)
        result = await svc.update_inference_job(uuid.uuid4(), data)
        assert result == mock_obj
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_not_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = None
        result = await svc.update_inference_job(uuid.uuid4(), InferenceJobUpdate())
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = MagicMock()
        result = await svc.delete_inference_job(uuid.uuid4())
        assert result is True
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_not_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = None
        result = await svc.delete_inference_job(uuid.uuid4())
        assert result is False


# ===========================================================================
# 7. DataPipelineService
# ===========================================================================

class TestDataPipelineService:

    def _make_service(self, session):
        svc = DataPipelineService(session=session)
        svc.repo = AsyncMock()
        return svc

    @pytest.mark.asyncio
    async def test_list(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_list.return_value = ([], 0)
        result = await svc.list_pipelines(page=1, size=20)
        assert result.total == 0
        assert result.items == []

    @pytest.mark.asyncio
    async def test_get_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        mock_obj = MagicMock()
        mock_obj.id = uuid.uuid4()
        svc.repo.get_by_id.return_value = mock_obj
        result = await svc.get_pipeline(mock_obj.id)
        assert result == mock_obj

    @pytest.mark.asyncio
    async def test_get_not_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = None
        result = await svc.get_pipeline(uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_create(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        mock_obj = MagicMock()
        svc.repo.create.return_value = mock_obj
        data = DataPipelineCreate(name="test-pipeline")
        result = await svc.create_pipeline(data)
        svc.repo.create.assert_called_once()
        mock_db_session.commit.assert_called_once()
        assert result == mock_obj

    @pytest.mark.asyncio
    async def test_update_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        mock_obj = MagicMock()
        svc.repo.get_by_id.return_value = mock_obj
        svc.repo.update.return_value = mock_obj
        data = DataPipelineUpdate(source="updated")
        result = await svc.update_pipeline(uuid.uuid4(), data)
        assert result == mock_obj
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_not_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = None
        result = await svc.update_pipeline(uuid.uuid4(), DataPipelineUpdate())
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = MagicMock()
        result = await svc.delete_pipeline(uuid.uuid4())
        assert result is True
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_not_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = None
        result = await svc.delete_pipeline(uuid.uuid4())
        assert result is False

    @pytest.mark.asyncio
    async def test_trigger_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        mock_obj = MagicMock()
        svc.repo.get_by_id.return_value = mock_obj
        svc.repo.trigger.return_value = mock_obj
        pipeline_id = uuid.uuid4()
        result = await svc.trigger_pipeline(pipeline_id)
        assert result == mock_obj
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_trigger_not_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = None
        result = await svc.trigger_pipeline(uuid.uuid4())
        assert result is None


# ===========================================================================
# 8. ImageLogService (no create)
# ===========================================================================

class TestImageLogService:

    def _make_service(self, session):
        svc = ImageLogService(session=session)
        svc.repo = AsyncMock()
        return svc

    @pytest.mark.asyncio
    async def test_list(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_list.return_value = ([], 0)
        result = await svc.list_image_logs(page=1, size=20)
        assert result.total == 0
        assert result.items == []

    @pytest.mark.asyncio
    async def test_get_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        mock_obj = MagicMock()
        mock_obj.id = uuid.uuid4()
        svc.repo.get_by_id.return_value = mock_obj
        result = await svc.get_image_log(mock_obj.id)
        assert result == mock_obj

    @pytest.mark.asyncio
    async def test_get_not_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = None
        result = await svc.get_image_log(uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_update_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        mock_obj = MagicMock()
        svc.repo.get_by_id.return_value = mock_obj
        svc.repo.update.return_value = mock_obj
        data = ImageLogUpdate(flagged=True)
        result = await svc.update_image_log(uuid.uuid4(), data)
        assert result == mock_obj
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_not_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = None
        result = await svc.update_image_log(uuid.uuid4(), ImageLogUpdate())
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = MagicMock()
        result = await svc.delete_image_log(uuid.uuid4())
        assert result is True
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_not_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = None
        result = await svc.delete_image_log(uuid.uuid4())
        assert result is False


# ===========================================================================
# 9. ModerationService
# ===========================================================================

class TestModerationService:

    def _make_service(self, session):
        svc = ModerationService(session=session)
        svc.repo = AsyncMock()
        return svc

    @pytest.mark.asyncio
    async def test_list(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_list.return_value = ([], 0)
        result = await svc.list_moderation_items(page=1, size=20)
        assert result.total == 0
        assert result.items == []

    @pytest.mark.asyncio
    async def test_get_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        mock_obj = MagicMock()
        mock_obj.id = uuid.uuid4()
        svc.repo.get_by_id.return_value = mock_obj
        result = await svc.get_moderation_item(mock_obj.id)
        assert result == mock_obj

    @pytest.mark.asyncio
    async def test_get_not_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = None
        result = await svc.get_moderation_item(uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_create(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        mock_obj = MagicMock()
        svc.repo.create.return_value = mock_obj
        data = ModerationCreate(type=ModerationItemType.record, content={})
        result = await svc.create_moderation_item(data)
        svc.repo.create.assert_called_once()
        mock_db_session.commit.assert_called_once()
        assert result == mock_obj

    @pytest.mark.asyncio
    async def test_update_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        mock_obj = MagicMock()
        svc.repo.get_by_id.return_value = mock_obj
        svc.repo.update.return_value = mock_obj
        data = ModerationUpdate(notes="updated")
        result = await svc.update_moderation_item(uuid.uuid4(), data)
        assert result == mock_obj
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_not_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = None
        result = await svc.update_moderation_item(uuid.uuid4(), ModerationUpdate())
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = MagicMock()
        result = await svc.delete_moderation_item(uuid.uuid4())
        assert result is True
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_not_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = None
        result = await svc.delete_moderation_item(uuid.uuid4())
        assert result is False

    @pytest.mark.asyncio
    async def test_approve_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        mock_obj = MagicMock()
        svc.repo.get_by_id.return_value = mock_obj
        svc.repo.approve.return_value = mock_obj
        reviewer_id = uuid.uuid4()
        result = await svc.approve_item(uuid.uuid4(), reviewer_id=reviewer_id, notes="looks good")
        assert result == mock_obj
        svc.repo.approve.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_approve_not_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = None
        result = await svc.approve_item(uuid.uuid4(), reviewer_id=uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_reject_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        mock_obj = MagicMock()
        svc.repo.get_by_id.return_value = mock_obj
        svc.repo.reject.return_value = mock_obj
        reviewer_id = uuid.uuid4()
        result = await svc.reject_item(uuid.uuid4(), reviewer_id=reviewer_id, notes="invalid")
        assert result == mock_obj
        svc.repo.reject.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_reject_not_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = None
        result = await svc.reject_item(uuid.uuid4(), reviewer_id=uuid.uuid4())
        assert result is None


# ===========================================================================
# 10. QueryLogService (no create)
# ===========================================================================

class TestQueryLogService:

    def _make_service(self, session):
        svc = QueryLogService(session=session)
        svc.repo = AsyncMock()
        return svc

    @pytest.mark.asyncio
    async def test_list(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_list.return_value = ([], 0)
        result = await svc.list_query_logs(page=1, size=20)
        assert result.total == 0
        assert result.items == []

    @pytest.mark.asyncio
    async def test_get_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        mock_obj = MagicMock()
        mock_obj.id = uuid.uuid4()
        svc.repo.get_by_id.return_value = mock_obj
        result = await svc.get_query_log(mock_obj.id)
        assert result == mock_obj

    @pytest.mark.asyncio
    async def test_get_not_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = None
        result = await svc.get_query_log(uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_update_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        mock_obj = MagicMock()
        svc.repo.get_by_id.return_value = mock_obj
        svc.repo.update.return_value = mock_obj
        data = QueryLogFlagUpdate(flagged=True)
        result = await svc.update_query_log(uuid.uuid4(), data)
        assert result == mock_obj
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_not_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = None
        result = await svc.update_query_log(uuid.uuid4(), QueryLogFlagUpdate(flagged=True))
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = MagicMock()
        result = await svc.delete_query_log(uuid.uuid4())
        assert result is True
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_not_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = None
        result = await svc.delete_query_log(uuid.uuid4())
        assert result is False


# ===========================================================================
# 11. ExternalApiService
# ===========================================================================

class TestExternalApiService:

    def _make_service(self, session):
        svc = ExternalApiService(session=session)
        svc.repo = AsyncMock()
        return svc

    @pytest.mark.asyncio
    async def test_list(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_list.return_value = ([], 0)
        result = await svc.list_apis(page=1, size=20)
        assert result.total == 0
        assert result.items == []

    @pytest.mark.asyncio
    async def test_get_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        mock_obj = MagicMock()
        mock_obj.id = uuid.uuid4()
        svc.repo.get_by_id.return_value = mock_obj
        result = await svc.get_api(mock_obj.id)
        assert result == mock_obj

    @pytest.mark.asyncio
    async def test_get_not_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = None
        result = await svc.get_api(uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_create(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        mock_obj = MagicMock()
        svc.repo.create.return_value = mock_obj
        data = ExternalApiCreate(name="test-api", base_url="http://example.com")
        result = await svc.create_api(data)
        svc.repo.create.assert_called_once()
        mock_db_session.commit.assert_called_once()
        assert result == mock_obj

    @pytest.mark.asyncio
    async def test_update_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        mock_obj = MagicMock()
        svc.repo.get_by_id.return_value = mock_obj
        svc.repo.update.return_value = mock_obj
        data = ExternalApiUpdate(description="updated")
        result = await svc.update_api(uuid.uuid4(), data)
        assert result == mock_obj
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_not_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = None
        result = await svc.update_api(uuid.uuid4(), ExternalApiUpdate())
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = MagicMock()
        result = await svc.delete_api(uuid.uuid4())
        assert result is True
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_not_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = None
        result = await svc.delete_api(uuid.uuid4())
        assert result is False


# ===========================================================================
# 12. ModelVersionService
# ===========================================================================

class TestModelVersionService:

    def _make_service(self, session):
        svc = ModelVersionService(session=session)
        svc.repo = AsyncMock()
        return svc

    @pytest.mark.asyncio
    async def test_list(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_list.return_value = ([], 0)
        result = await svc.list_versions(page=1, size=20)
        assert result.total == 0
        assert result.items == []

    @pytest.mark.asyncio
    async def test_get_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        mock_obj = MagicMock()
        mock_obj.id = uuid.uuid4()
        svc.repo.get_by_id.return_value = mock_obj
        result = await svc.get_version(mock_obj.id)
        assert result == mock_obj

    @pytest.mark.asyncio
    async def test_get_not_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = None
        result = await svc.get_version(uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_create(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        mock_obj = MagicMock()
        svc.repo.create.return_value = mock_obj
        data = ModelVersionCreate(name="plant-id-v1", version="1.0.0")
        result = await svc.create_version(data)
        svc.repo.create.assert_called_once()
        mock_db_session.commit.assert_called_once()
        assert result == mock_obj

    @pytest.mark.asyncio
    async def test_update_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        mock_obj = MagicMock()
        svc.repo.get_by_id.return_value = mock_obj
        svc.repo.update.return_value = mock_obj
        data = ModelVersionUpdate(notes="updated")
        result = await svc.update_version(uuid.uuid4(), data)
        assert result == mock_obj
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_not_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = None
        result = await svc.update_version(uuid.uuid4(), ModelVersionUpdate())
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = MagicMock()
        result = await svc.delete_version(uuid.uuid4())
        assert result is True
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_not_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = None
        result = await svc.delete_version(uuid.uuid4())
        assert result is False

    @pytest.mark.asyncio
    async def test_activate_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        mock_obj = MagicMock()
        svc.repo.get_by_id.return_value = mock_obj
        svc.repo.activate.return_value = mock_obj
        result = await svc.activate_version(uuid.uuid4())
        assert result == mock_obj
        svc.repo.activate.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_activate_not_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = None
        result = await svc.activate_version(uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_rollback_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        mock_obj = MagicMock()
        svc.repo.get_by_id.return_value = mock_obj
        svc.repo.rollback.return_value = mock_obj
        result = await svc.rollback_version(uuid.uuid4())
        assert result == mock_obj
        svc.repo.rollback.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_rollback_not_found(self, mock_db_session):
        svc = self._make_service(mock_db_session)
        svc.repo.get_by_id.return_value = None
        result = await svc.rollback_version(uuid.uuid4())
        assert result is None
