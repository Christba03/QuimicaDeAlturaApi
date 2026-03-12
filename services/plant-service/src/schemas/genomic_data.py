from datetime import datetime
from uuid import UUID
from typing import Any, Optional

from pydantic import BaseModel

from src.models.genomic_data import GenomicStatus


class GenomicDataBase(BaseModel):
    species: str
    fasta_file: Optional[str] = None
    genbank_id: Optional[str] = None
    kegg_pathway: Optional[str] = None
    enzyme_homology: Optional[str] = None
    gene_cluster: Optional[str] = None
    blast_results: Optional[dict[str, Any]] = None
    uploaded_at: Optional[datetime] = None
    status: Optional[GenomicStatus] = GenomicStatus.pending


class GenomicDataCreate(GenomicDataBase):
    pass


class GenomicDataUpdate(BaseModel):
    species: Optional[str] = None
    fasta_file: Optional[str] = None
    genbank_id: Optional[str] = None
    kegg_pathway: Optional[str] = None
    enzyme_homology: Optional[str] = None
    gene_cluster: Optional[str] = None
    blast_results: Optional[dict[str, Any]] = None
    uploaded_at: Optional[datetime] = None
    status: Optional[GenomicStatus] = None


class GenomicDataResponse(GenomicDataBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GenomicDataListResponse(BaseModel):
    items: list[GenomicDataResponse]
    total: int
    page: int
    size: int
    pages: int
