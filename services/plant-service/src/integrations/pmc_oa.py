from typing import Any
import xml.etree.ElementTree as ET

import httpx
import structlog

from src.config import get_settings

logger = structlog.get_logger()


class PMCOAClient:
    """Query the PMC Open Access service for license, citation, and FTP links."""

    def __init__(self):
        settings = get_settings()
        self.base_url = settings.PMC_OA_BASE_URL

    async def get_oa_info(self, article_id: str) -> dict[str, Any] | None:
        """Fetch OA metadata for a PMCID or PMID.

        Returns:
            Dict with citation, license, retracted flag, and download links,
            or None if the article is not in the OA subset.
        """
        params = {"id": article_id}
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                return self._parse_xml(response.text, article_id)
        except httpx.HTTPError as exc:
            logger.error("pmc_oa_error", article_id=article_id, error=str(exc))
            return None

    def _parse_xml(self, xml_text: str, article_id: str) -> dict[str, Any] | None:
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as exc:
            logger.error("pmc_oa_xml_parse_error", error=str(exc))
            return None

        error = root.find(".//error")
        if error is not None:
            logger.warning("pmc_oa_not_found", article_id=article_id, error=error.text)
            return None

        records = root.find(".//records")
        if records is None or int(records.get("returned-count", "0")) == 0:
            return None

        record = root.find(".//record")
        if record is None:
            return None

        links = []
        for link_el in record.findall("link"):
            links.append({
                "format": link_el.get("format"),
                "href": link_el.get("href"),
                "updated": link_el.get("updated"),
            })

        result = {
            "id": record.get("id"),
            "citation": record.get("citation"),
            "license": record.get("license"),
            "retracted": record.get("retracted", "no") == "yes",
            "links": links,
        }

        logger.info("pmc_oa_complete", article_id=article_id, license=result["license"])
        return result
