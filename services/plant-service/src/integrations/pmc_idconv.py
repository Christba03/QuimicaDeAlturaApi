from typing import Any

import httpx
import structlog

from src.config import get_settings

logger = structlog.get_logger()


class PMCIdConverterClient:
    """Convert between DOI, PMID, and PMCID using the PMC ID Converter API."""

    def __init__(self):
        settings = get_settings()
        self.base_url = settings.PMC_IDCONV_BASE_URL
        self.tool = settings.NCBI_TOOL_NAME
        self.email = settings.NCBI_TOOL_EMAIL

    def _params(self, extra: dict[str, Any] | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {"format": "json"}
        if self.tool:
            params["tool"] = self.tool
        if self.email:
            params["email"] = self.email
        if extra:
            params.update(extra)
        return params

    async def convert_ids(
        self,
        ids: list[str],
        id_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """Convert a list of IDs and return records with doi, pmid, pmcid.

        Args:
            ids: List of identifiers (DOIs, PMIDs, or PMCIDs).
            id_type: Optional hint — "doi", "pmcid", or "pmid".

        Returns:
            List of dicts, each with keys: doi, pmid, pmcid (any may be None).
        """
        if not ids:
            return []

        params = self._params({"ids": ",".join(ids)})
        if id_type:
            params["idtype"] = id_type

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                data = response.json()

                records = []
                for record in data.get("records", []):
                    if "errmsg" in record:
                        logger.warning(
                            "pmc_idconv_record_error",
                            requested_id=record.get("requested-id"),
                            error=record["errmsg"],
                        )
                        continue
                    records.append({
                        "doi": record.get("doi"),
                        "pmid": str(record["pmid"]) if record.get("pmid") else None,
                        "pmcid": record.get("pmcid"),
                    })

                logger.info(
                    "pmc_idconv_complete",
                    requested=len(ids),
                    resolved=len(records),
                )
                return records
        except httpx.HTTPError as exc:
            logger.error("pmc_idconv_error", error=str(exc))
            return []

    async def convert_single(self, identifier: str) -> dict[str, Any] | None:
        """Convenience wrapper for a single ID."""
        results = await self.convert_ids([identifier])
        return results[0] if results else None
