"""
Tafseer source and chunk models.

IMMUTABLE DATA CONTRACT
=======================
Tafseer data is treated as IMMUTABLE once ingested. This ensures:
- Reproducibility: Same version_tag always produces same data
- Auditability: All changes are tracked in IngestionAuditLog
- Integrity: data_hash allows verification of content

MODIFICATION RULES:
1. Tafseer chunks are NEVER modified in-place after ingestion
2. Any content update requires:
   - New version_tag (must differ from previous)
   - New data_hash (recomputed from new content)
   - New IngestionAuditLog record with operation="update"
   - Update to retrieval_timestamp
3. Deletions must be logged with operation="delete" in audit log
4. Re-ingestion of same source requires version_tag change

VIOLATION CONSEQUENCES:
- Silent data drift (users see different content than cited)
- Broken citation references
- Unreproducible RAG responses
- Audit trail corruption

To update tafseer data:
1. Download new version from CDN
2. Verify version_tag differs from current
3. Run seed_tafseer.py with --force flag (creates new audit record)
4. Run verify_provenance.py to validate
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    DateTime,
    ForeignKey,
    Index,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship

from app.db.database import Base


class TafseerSource(Base):
    """
    Tafseer source metadata - tracks different tafseer books/authors.

    Examples: Ibn Kathir, Al-Tabari, Al-Qurtubi, Al-Sa'di

    PROVENANCE REQUIREMENTS:
    - Every source MUST have: cdn_url, version_tag, retrieval_timestamp, license_type
    - Without provenance, source is considered unverified
    """
    __tablename__ = "tafseer_sources"

    id = Column(String(50), primary_key=True)  # e.g., "ibn_kathir", "tabari"
    name_ar = Column(String(200), nullable=False)
    name_en = Column(String(200), nullable=False)

    # Author information
    author_ar = Column(String(200), nullable=True)
    author_en = Column(String(200), nullable=True)
    era = Column(String(50), nullable=True)  # "classical", "modern"
    death_year_hijri = Column(Integer, nullable=True)

    # Methodology
    methodology = Column(String(50), nullable=True)  # "bil_mathur", "bil_ray", "mixed"

    # Language and version
    language = Column(String(10), nullable=False)  # "ar", "en"
    version = Column(String(50), nullable=True)
    source_url = Column(Text, nullable=True)

    # === PROVENANCE FIELDS (MANDATORY FOR REPRODUCIBILITY) ===
    # CDN URL used to fetch this source
    cdn_url = Column(Text, nullable=True)
    # Git commit hash or version tag of the source repository
    version_tag = Column(String(100), nullable=True)
    # When the data was retrieved from the CDN
    retrieval_timestamp = Column(DateTime, nullable=True)
    # SHA256 hash of the downloaded data for integrity verification
    data_hash = Column(String(64), nullable=True)
    # Total ayah count for validation
    ayah_count = Column(Integer, nullable=True)

    # Licensing (MANDATORY - must be explicitly set)
    license_type = Column(String(100), nullable=True)  # "public_domain", "cc_by", "api_tos", etc.
    license = Column(String(200), nullable=True)
    license_url = Column(Text, nullable=True)
    license_verified = Column(Integer, default=0)  # 0=unverified, 1=verified

    # Quality indicators
    reliability_score = Column(Float, default=1.0)  # 0.0-1.0 scholarly consensus
    is_primary_source = Column(Integer, default=1)  # 1=primary, 0=secondary

    # Admin control
    is_enabled = Column(Integer, default=1)  # 1=enabled, 0=disabled for RAG

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    chunks = relationship("TafseerChunk", back_populates="source", lazy="dynamic")

    def __repr__(self):
        return f"<TafseerSource {self.id} ({self.language})>"

    @property
    def has_valid_provenance(self) -> bool:
        """Check if source has complete provenance metadata."""
        return all([
            self.cdn_url,
            self.version_tag,
            self.retrieval_timestamp,
            self.license_type,
        ])


class IngestionAuditLog(Base):
    """
    Audit log for data ingestion events.

    Tracks every ingestion for reproducibility and compliance.
    """
    __tablename__ = "ingestion_audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # What was ingested
    source_id = Column(String(50), ForeignKey("tafseer_sources.id"), nullable=False)
    operation = Column(String(50), nullable=False)  # "download", "seed", "index", "delete"

    # Provenance snapshot at time of ingestion
    cdn_url = Column(Text, nullable=True)
    version_tag = Column(String(100), nullable=True)
    data_hash = Column(String(64), nullable=True)

    # Results
    records_processed = Column(Integer, default=0)
    records_inserted = Column(Integer, default=0)
    records_skipped = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)

    # Status
    status = Column(String(20), nullable=False)  # "success", "partial", "failed"
    error_message = Column(Text, nullable=True)

    # Timing
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)

    # Environment
    hostname = Column(String(100), nullable=True)
    user = Column(String(100), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    source = relationship("TafseerSource")

    def __repr__(self):
        return f"<IngestionAuditLog {self.id}: {self.operation} {self.source_id} ({self.status})>"


class TafseerChunk(Base):
    """
    Tafseer content chunks - stores segmented tafseer content.

    Each chunk is linked to a verse range and contains searchable content.
    Used for RAG retrieval and must have a unique chunk_id for citation.
    """
    __tablename__ = "tafseer_chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chunk_id = Column(String(100), nullable=False, unique=True, index=True)  # Unique ID for citations

    source_id = Column(String(50), ForeignKey("tafseer_sources.id"), nullable=False, index=True)

    # Verse range this chunk explains
    verse_start_id = Column(Integer, ForeignKey("quran_verses.id"), nullable=False)
    verse_end_id = Column(Integer, ForeignKey("quran_verses.id"), nullable=False)

    # Alternative reference (for convenience)
    sura_no = Column(Integer, nullable=False, index=True)
    aya_start = Column(Integer, nullable=False)
    aya_end = Column(Integer, nullable=False)

    # Content
    content_ar = Column(Text, nullable=True)
    content_en = Column(Text, nullable=True)

    # Topics and themes covered
    topics = Column(ARRAY(String), nullable=True)

    # Scholarly consensus indicator
    scholarly_consensus = Column(String(50), nullable=True)  # "agreed", "majority", "disputed"

    # Chunk metadata
    chunk_order = Column(Integer, default=0)  # Order within the verse explanation
    word_count = Column(Integer, nullable=True)
    char_count = Column(Integer, nullable=True)

    # Embedding status
    is_embedded = Column(Integer, default=0)  # 0=not embedded, 1=embedded
    embedding_model = Column(String(100), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    source = relationship("TafseerSource", back_populates="chunks")
    verse_start = relationship("QuranVerse", foreign_keys=[verse_start_id])
    verse_end = relationship("QuranVerse", foreign_keys=[verse_end_id])

    __table_args__ = (
        Index("ix_chunk_source", "source_id"),
        Index("ix_chunk_verse_range", "verse_start_id", "verse_end_id"),
        Index("ix_chunk_sura", "sura_no"),
    )

    def __repr__(self):
        return f"<TafseerChunk {self.chunk_id} ({self.source_id})>"

    @property
    def verse_reference(self) -> str:
        """Get verse reference for this chunk."""
        if self.aya_start == self.aya_end:
            return f"{self.sura_no}:{self.aya_start}"
        return f"{self.sura_no}:{self.aya_start}-{self.aya_end}"

    @property
    def citation(self) -> str:
        """Get citation string for this chunk."""
        return f"[{self.source_id}, {self.verse_reference}]"
