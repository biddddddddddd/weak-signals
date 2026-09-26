from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from src.db.connection import Base


class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    source_type = Column(String(50), nullable=False)
    region = Column(String(50), nullable=False)
    language = Column(String(10), nullable=True)
    trust = Column(Float, nullable=False, default=0.5)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    documents = relationship("Document", back_populates="source", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Source {self.domain}>"


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    doc_id = Column(String(500), unique=True, nullable=False, index=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False)
    title = Column(Text, nullable=False)
    abstract = Column(Text, nullable=True)
    authors = Column(Text, nullable=True)
    organizations = Column(Text, nullable=True)
    published_at = Column(String(50), nullable=True, index=True)
    url = Column(String(500), nullable=True)
    language = Column(String(10), nullable=True)
    region = Column(String(50), nullable=True, index=True)
    label = Column(Integer, nullable=True, index=True)
    source_query = Column(String(500), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    source = relationship("Source", back_populates="documents")

    __table_args__ = (
        Index("ix_documents_source_published", "source_id", "published_at"),
        Index("ix_documents_label_region", "label", "region"),
        Index("ix_documents_label_query", "label", "source_query"),
    )

    def __repr__(self):
        return f"<Document {self.doc_id[:50]}>"


class WeakSignal(Base):
    __tablename__ = "weak_signals"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False)
    area = Column(String(100))
    companies = Column(Text)
    why_weak_signal = Column(Text)
    stage = Column(String(100))
    trend = Column(String(200))
    score = Column(Integer)
    sources = Column(JSON)
    embedding = Column(JSON, nullable=True)


class NegativeSignal(Base):
    __tablename__ = "negative_signals"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    embedding = Column(JSON, nullable=True)


class ScoredDocument(Base):
    __tablename__ = "scored_documents"

    id = Column(Integer, primary_key=True, index=True)
    doc_id = Column(String(500), unique=True, nullable=False, index=True)
    title = Column(Text, nullable=True)
    url = Column(String(500), nullable=True)
    source_name = Column(String(255), nullable=True)
    language = Column(String(10), nullable=True)
    trust_level = Column(Integer, nullable=True, default=5)
    is_weak_signal = Column(Integer, nullable=False, default=0)
    confidence = Column(Float, nullable=False, default=0.0)
    technology = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    advantage = Column(Text, nullable=True)
    case_example = Column(Text, nullable=True)
    why_weak_signal = Column(Text, nullable=True)
    why_this_score = Column(Text, nullable=True)
    stage = Column(String(100), nullable=True)
    trend = Column(String(100), nullable=True)
    excluded_trends = Column(JSON, nullable=True)
    retrieval_weak = Column(JSON, nullable=True)
    retrieval_negative = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class RawWeakSignal(Base):
    __tablename__ = "raw_weak_signals"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    source = Column(String(50), nullable=True)
    url = Column(String(500), nullable=True)
    year = Column(Integer, nullable=True)
    embedding = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class RawNegativeSignal(Base):
    __tablename__ = "raw_negative_signals"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    source = Column(String(50), nullable=True)
    url = Column(String(500), nullable=True)
    year = Column(Integer, nullable=True)
    embedding = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class RawJunkSignal(Base):
    __tablename__ = "raw_junk_signals"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)
    embedding = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)