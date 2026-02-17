from typing import Any

import httpx
import structlog

from src.config import get_settings

logger = structlog.get_logger()


class PubChemClient:
    def __init__(self):
        settings = get_settings()
        self.base_url = settings.PUBCHEM_BASE_URL

    async def search_compound_by_name(
        self, name: str
    ) -> dict[str, Any] | None:
        """Search PubChem for a compound by name and return its properties."""
        url = f"{self.base_url}/compound/name/{name}/JSON"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                if response.status_code == 404:
                    logger.info("pubchem_compound_not_found", name=name)
                    return None
                response.raise_for_status()
                data = response.json()
                compounds = (
                    data.get("PC_Compounds", [])
                )
                if not compounds:
                    return None
                return self._parse_compound(compounds[0])
        except httpx.HTTPError as exc:
            logger.error("pubchem_search_error", error=str(exc))
            return None

    async def get_compound_by_cid(
        self, cid: str
    ) -> dict[str, Any] | None:
        """Fetch compound details by PubChem CID."""
        url = f"{self.base_url}/compound/cid/{cid}/property/MolecularFormula,MolecularWeight,IUPACName,InChIKey,CanonicalSMILES/JSON"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                data = response.json()
                props_table = data.get("PropertyTable", {})
                properties = props_table.get("Properties", [])
                if not properties:
                    return None
                prop = properties[0]
                return {
                    "pubchem_cid": str(prop.get("CID", "")),
                    "molecular_formula": prop.get("MolecularFormula"),
                    "molecular_weight": prop.get("MolecularWeight"),
                    "iupac_name": prop.get("IUPACName"),
                    "inchi_key": prop.get("InChIKey"),
                    "smiles": prop.get("CanonicalSMILES"),
                }
        except httpx.HTTPError as exc:
            logger.error("pubchem_cid_fetch_error", error=str(exc))
            return None

    async def get_compound_synonyms(self, cid: str) -> list[str]:
        """Fetch synonyms for a compound by CID."""
        url = f"{self.base_url}/compound/cid/{cid}/synonyms/JSON"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                if response.status_code == 404:
                    return []
                response.raise_for_status()
                data = response.json()
                info_list = data.get("InformationList", {})
                information = info_list.get("Information", [])
                if information:
                    return information[0].get("Synonym", [])[:20]
                return []
        except httpx.HTTPError as exc:
            logger.error("pubchem_synonyms_error", error=str(exc))
            return []

    def _parse_compound(self, compound: dict) -> dict[str, Any]:
        """Parse a raw PubChem compound JSON into a structured dict."""
        result: dict[str, Any] = {}
        result["pubchem_cid"] = str(compound.get("id", {}).get("id", {}).get("cid", ""))

        props = compound.get("props", [])
        for prop in props:
            urn = prop.get("urn", {})
            label = urn.get("label", "")
            value = prop.get("value", {})

            if label == "Molecular Formula":
                result["molecular_formula"] = value.get("sval")
            elif label == "Molecular Weight":
                result["molecular_weight"] = value.get("fval")
            elif label == "IUPAC Name" and urn.get("name") == "Preferred":
                result["iupac_name"] = value.get("sval")
            elif label == "InChIKey":
                result["inchi_key"] = value.get("sval")
            elif label == "SMILES" and urn.get("name") == "Canonical":
                result["smiles"] = value.get("sval")

        return result
