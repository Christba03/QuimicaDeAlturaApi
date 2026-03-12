import uuid
import enum

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from src.models.plant import Base


class VerificationStatus(str, enum.Enum):
    UNVERIFIED = "UNVERIFIED"
    UNDER_REVIEW = "UNDER_REVIEW"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    NEEDS_MORE_DATA = "NEEDS_MORE_DATA"
    CONFLICTING_DATA = "CONFLICTING_DATA"


class ScientificArticle(Base):
    __tablename__ = "scientific_articles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    title = Column(Text, nullable=False)
    abstract = Column(Text, nullable=True)

    doi = Column(String(255), unique=True, nullable=True, index=True)
    pubmed_id = Column(String(50), unique=True, nullable=True, index=True)
    pmcid = Column(String(50), nullable=True)
    arxiv_id = Column(String(50), nullable=True)

    journal = Column(String(500), nullable=True)
    publication_date = Column(Date, nullable=True)
    volume = Column(String(50), nullable=True)
    issue = Column(String(50), nullable=True)
    pages = Column(String(50), nullable=True)

    authors = Column(JSONB, nullable=False, default=list)

    keywords = Column(JSONB, default=list)
    mesh_terms = Column(JSONB, default=list)

    is_open_access = Column(Boolean, default=False)
    pdf_url = Column(Text, nullable=True)
    full_text_url = Column(Text, nullable=True)
    full_text = Column(Text, nullable=True)

    citation_count = Column(Integer, default=0)
    impact_factor = Column(Numeric(6, 3), nullable=True)

    article_type = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)

    quality_score = Column(Numeric(3, 2), nullable=True)
    peer_reviewed = Column(Boolean, default=True)

    uploaded_by = Column(UUID(as_uuid=True), nullable=True)
    upload_notes = Column(Text, nullable=True)

    verification_status = Column(
        Enum(VerificationStatus, name="verification_status", create_type=False),
        default=VerificationStatus.UNVERIFIED,
    )
    verified_by = Column(UUID(as_uuid=True), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_fetched = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    plant_associations = relationship(
        "ArticlePlantAssociation",
        back_populates="article",
        cascade="all, delete-orphan",
    )
    compound_associations = relationship(
        "ArticleCompoundAssociation",
        back_populates="article",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<ScientificArticle(id={self.id}, doi={self.doi})>"


class ArticlePlantAssociation(Base):
    __tablename__ = "article_plant_associations"
    __table_args__ = (
        UniqueConstraint("article_id", "plant_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    article_id = Column(
        UUID(as_uuid=True),
        ForeignKey("scientific_articles.id", ondelete="CASCADE"),
        nullable=False,
    )
    plant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("plants.id", ondelete="CASCADE"),
        nullable=False,
    )

    relevance_score = Column(Numeric(3, 2), nullable=True)
    mentioned_in_abstract = Column(Boolean, default=False)
    mentioned_in_title = Column(Boolean, default=False)

    key_findings = Column(Text, nullable=True)
    extracted_data = Column(JSONB, nullable=True)

    created_by = Column(UUID(as_uuid=True), nullable=True)
    is_automated = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    article = relationship("ScientificArticle", back_populates="plant_associations")
    plant = relationship("Plant")

    def __repr__(self) -> str:
        return f"<ArticlePlantAssociation(article={self.article_id}, plant={self.plant_id})>"


class ArticleCompoundAssociation(Base):
    __tablename__ = "article_compound_associations"
    __table_args__ = (
        UniqueConstraint("article_id", "compound_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    article_id = Column(
        UUID(as_uuid=True),
        ForeignKey("scientific_articles.id", ondelete="CASCADE"),
        nullable=False,
    )
    compound_id = Column(
        UUID(as_uuid=True),
        ForeignKey("chemical_compounds.id", ondelete="CASCADE"),
        nullable=False,
    )

    relevance_score = Column(Numeric(3, 2), nullable=True)
    key_findings = Column(Text, nullable=True)

    created_by = Column(UUID(as_uuid=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    article = relationship("ScientificArticle", back_populates="compound_associations")
    compound = relationship("ChemicalCompound")

    def __repr__(self) -> str:
        return f"<ArticleCompoundAssociation(article={self.article_id}, compound={self.compound_id})>"
