import httpx
import structlog

from src.config import get_settings

logger = structlog.get_logger()

VALID_FORMATS = {"ris", "medline", "bibtex", "nbib"}


class PMCCitationClient:
    """Fetch formatted citations from the Literature Citation Exporter API."""

    def __init__(self):
        settings = get_settings()
        self.base_url = settings.PMC_CITATION_BASE_URL

    async def get_citation(
        self,
        pmid: str,
        fmt: str = "ris",
    ) -> str | None:
        """Return a formatted citation string for a PubMed article.

        Args:
            pmid: PubMed ID.
            fmt: Output format — one of ris, medline, bibtex, nbib.
        """
        if fmt not in VALID_FORMATS:
            logger.warning("pmc_citation_invalid_format", fmt=fmt)
            fmt = "ris"

        params = {"format": fmt, "id": pmid}
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                text = response.text
                if not text or not text.strip():
                    logger.warning("pmc_citation_empty", pmid=pmid, fmt=fmt)
                    return None
                logger.info("pmc_citation_complete", pmid=pmid, fmt=fmt)
                return text
        except httpx.HTTPError as exc:
            logger.error("pmc_citation_error", pmid=pmid, error=str(exc))
            return None
