import asyncio
import json
from pathlib import Path
from typing import List, Dict
from loguru import logger

from src.sources.arxiv import search_arxiv
from src.sources.openalex import search_openalex
from src.db.connection import SessionLocal
from src.db.models import Source, Document


POSITIVE_FILE = Path("data/seeds/positive_signals.json")
NEGATIVE_FILE = Path("data/seeds/negative_signals.json")


def load_signals(path: Path) -> List[Dict]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data["signals"]


def save_documents_with_label(documents: List[Dict], label: int) -> int:
    if not documents:
        return 0

    db = SessionLocal()
    saved = 0

    try:
        for doc in documents:
            domain = doc.get("source_domain")
            if not domain:
                continue

            source = db.query(Source).filter(Source.domain == domain).first()
            if source is None:
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

            exists = db.query(Document).filter(Document.doc_id == doc["doc_id"]).first()
            if exists:
                continue

            document = Document(
                doc_id=doc["doc_id"],
                source_id=source.id,
                title=doc.get("title", "") or "",
                abstract=doc.get("abstract", "") or "",
                authors=", ".join(doc.get("authors", [])),
                organizations=", ".join(doc.get("organizations", [])),
                published_at=doc.get("published_at", "") or "",
                url=doc.get("url", "") or "",
                language=doc.get("language", "") or "",
                region=doc.get("region", "") or "",
                label=label,
            )
            db.add(document)
            saved += 1

        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Save failed: {e}")
    finally:
        db.close()

    return saved


async def collect_for_query(query: str, label: int, max_per_source: int = 10) -> int:
    total_saved = 0

    try:
        arxiv_docs = await search_arxiv(query, max_results=max_per_source) or []
        saved = save_documents_with_label(arxiv_docs, label)
        total_saved += saved
        logger.info(f"    → arXiv saved {saved}")
    except Exception as e:
        logger.warning(f"  arXiv failed: {e}")

    # OpenAlex временно отключён — IP забанен, возвращает 429 на все запросы
    # try:
    #     openalex_docs = await search_openalex(query, max_results=max_per_source) or []
    #     saved = save_documents_with_label(openalex_docs, label)
    #     total_saved += saved
    #     logger.info(f"    → OpenAlex saved {saved}")
    # except Exception as e:
    #     logger.warning(f"  OpenAlex failed: {e}")

    return total_saved


async def main():
    positives = load_signals(POSITIVE_FILE)
    negatives = load_signals(NEGATIVE_FILE)

    logger.info(f"Loaded {len(positives)} positive + {len(negatives)} negative signals")

    total_pos = 0
    total_neg = 0

    logger.info("=" * 60)
    logger.info("COLLECTING POSITIVE")
    logger.info("=" * 60)
    for i, signal in enumerate(positives, 1):
        name = signal["name"]
        logger.info(f"[{i}/{len(positives)}] POS: {name[:70]}")
        saved = await collect_for_query(name, label=1, max_per_source=10)
        total_pos += saved
        logger.info(f"    → total for query: {saved}")
        await asyncio.sleep(4)

    logger.info("=" * 60)
    logger.info("COLLECTING NEGATIVE")
    logger.info("=" * 60)
    for i, signal in enumerate(negatives, 1):
        name = signal["name"]
        logger.info(f"[{i}/{len(negatives)}] NEG: {name[:70]}")
        saved = await collect_for_query(name, label=0, max_per_source=10)
        total_neg += saved
        logger.info(f"    → total for query: {saved}")
        await asyncio.sleep(4)

    logger.info("=" * 60)
    logger.info("DONE")
    logger.info(f"  Positive saved: {total_pos}")
    logger.info(f"  Negative saved: {total_neg}")
    logger.info(f"  Total:          {total_pos + total_neg}")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())