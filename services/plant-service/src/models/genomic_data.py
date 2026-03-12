import enum
import uuid

from sqlalchemy import Column, DateTime, Enum, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID

from src.models.plant import Base


class GenomicStatus(str, enum.Enum):
    pending = "pending"
    processed = "processed"
    error = "error"


class GenomicData(Base):
    __tablename__ = "genomic_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    species = Column(String(255), nullable=False, index=True)
    fasta_file = Column(Text, nullable=True)
    genbank_id = Column(String(128), nullable=True)
    kegg_pathway = Column(String(128), nullable=True)
    enzyme_homology = Column(Text, nullable=True)
    gene_cluster = Column(Text, nullable=True)
    blast_results = Column(JSONB, nullable=False, server_default="{}")
    uploaded_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(GenomicStatus), nullable=False, default=GenomicStatus.pending, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<GenomicData(id={self.id}, species={self.species})>"
