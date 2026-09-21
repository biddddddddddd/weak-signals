from typing import List, Dict
from loguru import logger
from sqlalchemy.orm import Session

from src.db.connection import SessionLocal
from src.db.models import Source, Document


def save_documents(documents: List[Dict]) -> int:
    """
    Сохраняет список документов в БД.
    Автоматически создаёт source, если его ещё нет.
    Возвращает число сохранённых документов.
    """
    if not documents:
        return 0

    db: Session = SessionLocal()
    saved = 0

    try:
        for doc in documents:
            source = _get_or_create_source(db, doc)
            if source is None:
                continue

            exists = db.query(Document).filter(Document.doc_id == doc["doc_id"]).first()
            if exists:
                continue

            document = Document(
                doc_id=doc["doc_id"],
                source_id=source.id,
                title=doc.get("title", ""),
                abstract=doc.get("abstract", ""),
                authors=", ".join(doc.get("authors", [])),
                organizations=", ".join(doc.get("organizations", [])),
                published_at=doc.get("published_at", ""),
                url=doc.get("url", ""),
                language=doc.get("language", ""),
                region=doc.get("region", ""),
            )
            db.add(document)
            saved += 1

        db.commit()
        logger.info(f"Saved {saved} new documents to DB")

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save documents: {e}")
        raise
    finally:
        db.close()

    return saved


def _get_or_create_source(db: Session, doc: Dict) -> Source:
    """Находит source по домену или создаёт новый."""
    domain = doc.get("source_domain")
    if not domain:
        return None

    source = db.query(Source).filter(Source.domain == domain).first()
    if source:
        return source

    raw = doc.get("raw", {})
    source = Source(
        domain=domain,
        name=raw.get("source_name", domain),
        source_type=doc.get("source_type", "unknown"),
        region=doc.get("region", "Global"),
        language=doc.get("language", "en"),
        trust=raw.get("trust", 0.5),
    )
    db.add(source)
    db.flush()
    return source