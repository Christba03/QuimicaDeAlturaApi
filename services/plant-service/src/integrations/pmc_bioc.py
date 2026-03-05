from typing import Any

import httpx
import structlog

from src.config import get_settings

logger = structlog.get_logger()


class PMCBioCClient:
    """Fetch full text of OA articles in BioC JSON format."""

    def __init__(self):
        settings = get_settings()
        self.base_url = settings.PMC_BIOC_BASE_URL

    async def get_full_text(self, pmcid: str) -> dict[str, Any] | None:
        """Retrieve structured full text for an OA article.

        Args:
            pmcid: PubMed Central ID (e.g. "PMC13900").

        Returns:
            Dict with pmcid, title, abstract, sections, and raw passages,
            or None on failure.
        """
        url = f"{self.base_url}/BioC_json/{pmcid}/unicode"
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(url)
                if response.status_code == 404:
                    logger.warning("pmc_bioc_not_found", pmcid=pmcid)
                    return None
                response.raise_for_status()
                data = response.json()
                return self._parse_bioc(data, pmcid)
        except httpx.HTTPError as exc:
            logger.error("pmc_bioc_error", pmcid=pmcid, error=str(exc))
            return None

    def _parse_bioc(
        self, data: list[dict[str, Any]], pmcid: str
    ) -> dict[str, Any] | None:
        if not data:
            return None

        collection = data[0] if isinstance(data, list) else data
        documents = collection.get("documents", [])
        if not documents:
            return None

        doc = documents[0]
        passages = doc.get("passages", [])

        title = ""
        abstract = ""
        sections: list[dict[str, str]] = []
        full_text_parts: list[str] = []

        for passage in passages:
            infons = passage.get("infons", {})
            section_type = infons.get("section_type", "")
            passage_type = infons.get("type", "")
            text = passage.get("text", "")

            if passage_type == "front" and section_type == "TITLE":
                title = text
            elif section_type == "ABSTRACT" and passage_type in ("abstract", "paragraph"):
                abstract = text if not abstract else f"{abstract}\n{text}"
            elif passage_type in ("paragraph", "title_1", "title_2"):
                sections.append({
                    "section_type": section_type,
                    "type": passage_type,
                    "text": text,
                })
                if passage_type == "paragraph":
                    full_text_parts.append(text)

        result = {
            "pmcid": pmcid,
            "title": title,
            "abstract": abstract,
            "sections": sections,
            "full_text": "\n\n".join(full_text_parts),
            "passage_count": len(passages),
        }

        logger.info(
            "pmc_bioc_complete",
            pmcid=pmcid,
            passages=len(passages),
            sections=len(sections),
        )
        return result
