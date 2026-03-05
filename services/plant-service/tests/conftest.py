"""Shared fixtures for plant-service tests."""
import uuid
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.article import ScientificArticle


@pytest.fixture
def mock_db_session():
    """Async DB session mock usable as a context manager or dependency."""
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def sample_article_data():
    """Raw dict suitable for ArticleCreate."""
    return {
        "title": "Pharmacological evaluation of Salvia hispanica L.",
        "abstract": "Chia seeds have been used in traditional medicine.",
        "doi": "10.1234/test.2024.001",
        "pubmed_id": "12345678",
        "pmcid": "PMC9999999",
        "journal": "Journal of Ethnopharmacology",
        "publication_date": date(2024, 6, 15),
        "authors": ["Garcia A", "Lopez B", "Martinez C"],
        "keywords": ["chia", "pharmacology"],
        "mesh_terms": ["Plants, Medicinal"],
        "is_open_access": True,
        "peer_reviewed": True,
    }


@pytest.fixture
def sample_article(sample_article_data):
    """A ScientificArticle ORM instance for repo / service tests."""
    article = ScientificArticle(
        id=uuid.uuid4(),
        **sample_article_data,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    return article


# ---------------------------------------------------------------------------
# PMC ID Converter responses
# ---------------------------------------------------------------------------

@pytest.fixture
def idconv_json_response():
    return {
        "status": "ok",
        "responseDate": "2024-01-01 00:00:00",
        "records": [
            {
                "doi": "10.1234/test.2024.001",
                "pmcid": "PMC9999999",
                "pmid": 12345678,
                "requested-id": "PMC9999999",
            }
        ],
    }


# ---------------------------------------------------------------------------
# OA XML response
# ---------------------------------------------------------------------------

@pytest.fixture
def oa_xml_response():
    return """<?xml version="1.0" encoding="UTF-8"?>
<OA>
  <responseDate>2024-01-01 00:00:00</responseDate>
  <request id="PMC9999999">https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id=PMC9999999</request>
  <records returned-count="1" total-count="1">
    <record id="PMC9999999" citation="J Ethnopharmacol. 2024; 300:100-110" license="CC BY" retracted="no">
      <link format="tgz" updated="2024-06-01 10:00:00" href="ftp://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_package/PMC9999999.tar.gz"/>
      <link format="pdf" updated="2024-06-01 10:00:00" href="ftp://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_pdf/PMC9999999.pdf"/>
    </record>
  </records>
</OA>"""


@pytest.fixture
def oa_xml_not_found():
    return """<?xml version="1.0" encoding="UTF-8"?>
<OA>
  <responseDate>2024-01-01 00:00:00</responseDate>
  <request id="PMC0000000">https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id=PMC0000000</request>
  <error code="idIsNotOpenAccess">PMC0000000 is not Open Access</error>
</OA>"""


# ---------------------------------------------------------------------------
# BioC JSON response (trimmed)
# ---------------------------------------------------------------------------

@pytest.fixture
def bioc_json_response():
    return [
        {
            "bioctype": "BioCCollection",
            "source": "PMC",
            "documents": [
                {
                    "bioctype": "BioCDocument",
                    "id": "PMC9999999",
                    "passages": [
                        {
                            "offset": 0,
                            "infons": {"section_type": "TITLE", "type": "front"},
                            "text": "Pharmacological evaluation of Salvia hispanica L.",
                        },
                        {
                            "offset": 51,
                            "infons": {"section_type": "ABSTRACT", "type": "abstract"},
                            "text": "Chia seeds have been used in traditional medicine.",
                        },
                        {
                            "offset": 102,
                            "infons": {"section_type": "INTRO", "type": "title_1"},
                            "text": "Introduction",
                        },
                        {
                            "offset": 115,
                            "infons": {"section_type": "INTRO", "type": "paragraph"},
                            "text": "Salvia hispanica is an annual herbaceous plant.",
                        },
                        {
                            "offset": 163,
                            "infons": {"section_type": "METHODS", "type": "paragraph"},
                            "text": "Ethanolic extracts were prepared from dried seeds.",
                        },
                    ],
                }
            ],
        }
    ]


# ---------------------------------------------------------------------------
# Citation text
# ---------------------------------------------------------------------------

@pytest.fixture
def ris_citation_text():
    return """TY  - JOUR
AU  - Garcia A
AU  - Lopez B
TI  - Pharmacological evaluation of Salvia hispanica L.
JO  - J Ethnopharmacol
PY  - 2024
DO  - 10.1234/test.2024.001
ER  - """
