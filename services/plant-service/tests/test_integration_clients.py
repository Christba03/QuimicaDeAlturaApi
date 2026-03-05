"""
Unit tests for the four PMC/NCBI integration clients.
All HTTP calls are mocked — no network required.
"""
import json
from unittest.mock import AsyncMock, patch, MagicMock

import httpx
import pytest

from src.integrations.pmc_idconv import PMCIdConverterClient
from src.integrations.pmc_oa import PMCOAClient
from src.integrations.pmc_citation import PMCCitationClient
from src.integrations.pmc_bioc import PMCBioCClient


# ===================================================================
# PMC ID Converter
# ===================================================================

class TestPMCIdConverterClient:

    @pytest.fixture(autouse=True)
    def _patch_settings(self):
        mock_settings = MagicMock()
        mock_settings.PMC_IDCONV_BASE_URL = "https://pmc.ncbi.nlm.nih.gov/tools/idconv/api/v1/articles/"
        mock_settings.NCBI_TOOL_NAME = "TestTool"
        mock_settings.NCBI_TOOL_EMAIL = "test@example.com"
        with patch("src.integrations.pmc_idconv.get_settings", return_value=mock_settings):
            yield

    @pytest.mark.asyncio
    async def test_convert_ids_success(self, idconv_json_response):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = idconv_json_response

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get.return_value = mock_response
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            client = PMCIdConverterClient()
            records = await client.convert_ids(["PMC9999999"])

        assert len(records) == 1
        assert records[0]["doi"] == "10.1234/test.2024.001"
        assert records[0]["pmid"] == "12345678"
        assert records[0]["pmcid"] == "PMC9999999"

    @pytest.mark.asyncio
    async def test_convert_ids_empty_input(self):
        client = PMCIdConverterClient()
        result = await client.convert_ids([])
        assert result == []

    @pytest.mark.asyncio
    async def test_convert_ids_http_error(self):
        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get.side_effect = httpx.HTTPError("connection refused")
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            client = PMCIdConverterClient()
            result = await client.convert_ids(["PMC0000000"])

        assert result == []

    @pytest.mark.asyncio
    async def test_convert_ids_skips_error_records(self):
        response_data = {
            "status": "ok",
            "records": [
                {"requested-id": "INVALID", "errmsg": "not found"},
                {"doi": "10.1/ok", "pmcid": "PMC1", "pmid": 1},
            ],
        }
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = response_data

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get.return_value = mock_response
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            client = PMCIdConverterClient()
            records = await client.convert_ids(["INVALID", "PMC1"])

        assert len(records) == 1
        assert records[0]["doi"] == "10.1/ok"

    @pytest.mark.asyncio
    async def test_convert_single(self, idconv_json_response):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = idconv_json_response

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get.return_value = mock_response
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            client = PMCIdConverterClient()
            record = await client.convert_single("PMC9999999")

        assert record is not None
        assert record["pmcid"] == "PMC9999999"


# ===================================================================
# PMC OA Client
# ===================================================================

class TestPMCOAClient:

    @pytest.fixture(autouse=True)
    def _patch_settings(self):
        mock_settings = MagicMock()
        mock_settings.PMC_OA_BASE_URL = "https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi"
        with patch("src.integrations.pmc_oa.get_settings", return_value=mock_settings):
            yield

    @pytest.mark.asyncio
    async def test_get_oa_info_success(self, oa_xml_response):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.text = oa_xml_response

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get.return_value = mock_response
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            client = PMCOAClient()
            result = await client.get_oa_info("PMC9999999")

        assert result is not None
        assert result["id"] == "PMC9999999"
        assert result["license"] == "CC BY"
        assert result["retracted"] is False
        assert len(result["links"]) == 2
        assert result["links"][1]["format"] == "pdf"

    @pytest.mark.asyncio
    async def test_get_oa_info_not_found(self, oa_xml_not_found):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.text = oa_xml_not_found

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get.return_value = mock_response
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            client = PMCOAClient()
            result = await client.get_oa_info("PMC0000000")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_oa_info_http_error(self):
        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get.side_effect = httpx.HTTPError("timeout")
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            client = PMCOAClient()
            result = await client.get_oa_info("PMC9999999")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_oa_info_malformed_xml(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.text = "NOT VALID XML <<<"

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get.return_value = mock_response
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            client = PMCOAClient()
            result = await client.get_oa_info("PMC9999999")

        assert result is None


# ===================================================================
# PMC Citation Client
# ===================================================================

class TestPMCCitationClient:

    @pytest.fixture(autouse=True)
    def _patch_settings(self):
        mock_settings = MagicMock()
        mock_settings.PMC_CITATION_BASE_URL = "https://api.ncbi.nlm.nih.gov/lit/ctxp/v1/pubmed/"
        with patch("src.integrations.pmc_citation.get_settings", return_value=mock_settings):
            yield

    @pytest.mark.asyncio
    async def test_get_citation_success(self, ris_citation_text):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.text = ris_citation_text

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get.return_value = mock_response
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            client = PMCCitationClient()
            result = await client.get_citation("12345678", fmt="ris")

        assert result is not None
        assert "TY  - JOUR" in result
        assert "Garcia A" in result

    @pytest.mark.asyncio
    async def test_get_citation_empty_response(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.text = ""

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get.return_value = mock_response
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            client = PMCCitationClient()
            result = await client.get_citation("99999999")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_citation_invalid_format_defaults_to_ris(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.text = "TY  - JOUR\nER  - "

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get.return_value = mock_response
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            client = PMCCitationClient()
            result = await client.get_citation("12345678", fmt="invalid_format")

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_citation_http_error(self):
        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get.side_effect = httpx.HTTPError("500")
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            client = PMCCitationClient()
            result = await client.get_citation("12345678")

        assert result is None


# ===================================================================
# PMC BioC Client
# ===================================================================

class TestPMCBioCClient:

    @pytest.fixture(autouse=True)
    def _patch_settings(self):
        mock_settings = MagicMock()
        mock_settings.PMC_BIOC_BASE_URL = "https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi"
        with patch("src.integrations.pmc_bioc.get_settings", return_value=mock_settings):
            yield

    @pytest.mark.asyncio
    async def test_get_full_text_success(self, bioc_json_response):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = bioc_json_response

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get.return_value = mock_response
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            client = PMCBioCClient()
            result = await client.get_full_text("PMC9999999")

        assert result is not None
        assert result["pmcid"] == "PMC9999999"
        assert result["title"] == "Pharmacological evaluation of Salvia hispanica L."
        assert "Chia seeds" in result["abstract"]
        assert len(result["sections"]) == 3
        assert result["passage_count"] == 5
        assert "Salvia hispanica" in result["full_text"]

    @pytest.mark.asyncio
    async def test_get_full_text_404(self):
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get.return_value = mock_response
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            client = PMCBioCClient()
            result = await client.get_full_text("PMC0000000")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_full_text_empty_documents(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = [{"documents": []}]

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get.return_value = mock_response
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            client = PMCBioCClient()
            result = await client.get_full_text("PMC0000000")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_full_text_http_error(self):
        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get.side_effect = httpx.HTTPError("timeout")
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            client = PMCBioCClient()
            result = await client.get_full_text("PMC9999999")

        assert result is None
