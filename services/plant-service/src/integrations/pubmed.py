from typing import Any

import httpx
import structlog

from src.config import get_settings

logger = structlog.get_logger()


class PubMedClient:
    def __init__(self):
        settings = get_settings()
        self.base_url = settings.PUBMED_BASE_URL
        self.api_key = settings.PUBMED_API_KEY

    def _params(self, extra: dict[str, Any] | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {"retmode": "json"}
        if self.api_key:
            params["api_key"] = self.api_key
        if extra:
            params.update(extra)
        return params

    async def search_articles(
        self,
        query: str,
        max_results: int = 10,
    ) -> list[str]:
        """Search PubMed and return a list of PMIDs."""
        url = f"{self.base_url}/esearch.fcgi"
        params = self._params(
            {"db": "pubmed", "term": query, "retmax": max_results}
        )
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                pmids = data.get("esearchresult", {}).get("idlist", [])
                logger.info(
                    "pubmed_search_complete",
                    query=query,
                    results=len(pmids),
                )
                return pmids
        except httpx.HTTPError as exc:
            logger.error("pubmed_search_error", error=str(exc))
            return []

    async def fetch_article_details(
        self, pmids: list[str]
    ) -> list[dict[str, Any]]:
        """Fetch article summaries for a list of PMIDs."""
        if not pmids:
            return []

        url = f"{self.base_url}/esummary.fcgi"
        params = self._params(
            {"db": "pubmed", "id": ",".join(pmids)}
        )
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                result = data.get("result", {})
                articles = []
                for pmid in pmids:
                    article_data = result.get(pmid)
                    if article_data:
                        articles.append(
                            {
                                "pmid": pmid,
                                "title": article_data.get("title", ""),
                                "source": article_data.get("source", ""),
                                "pubdate": article_data.get("pubdate", ""),
                                "authors": [
                                    a.get("name", "")
                                    for a in article_data.get("authors", [])
                                ],
                                "doi": article_data.get("elocationid", ""),
                            }
                        )
                logger.info(
                    "pubmed_fetch_complete", count=len(articles)
                )
                return articles
        except httpx.HTTPError as exc:
            logger.error("pubmed_fetch_error", error=str(exc))
            return []

    async def search_plant_research(
        self,
        plant_name: str,
        max_results: int = 10,
    ) -> list[dict[str, Any]]:
        """Search for research articles about a specific plant."""
        query = f'"{plant_name}"[Title/Abstract] AND (medicinal OR pharmacological OR therapeutic)'
        pmids = await self.search_articles(query, max_results=max_results)
        if pmids:
            return await self.fetch_article_details(pmids)
        return []
