from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, Index
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
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    source = relationship("Source", back_populates="documents")

    __table_args__ = (
        Index("ix_documents_source_published", "source_id", "published_at"),
        Index("ix_documents_label_region", "label", "region"),
    )

    def __repr__(self):
        return f"<Document {self.doc_id[:50]}>"