import asyncio
import json
import sys
import argparse
from pathlib import Path
from typing import List, Dict
from loguru import logger

from src.sources.arxiv import search_arxiv
from src.sources.orchestrator import get_full_orchestrator
from src.db.connection import SessionLocal
from src.db.models import Source, Document

SEEDS_DIR = Path("data/seeds")
MAX_PER_SOURCE = 50
SLEEP_BETWEEN = 3
RSS_MAX_CONCURRENT = 10

SEED_FILES = {
    ("en", "negative"): SEEDS_DIR / "negative_signals.json",
    ("en", "positive"): SEEDS_DIR / "positive_signals_en.json",
    ("ru", "negative"): SEEDS_DIR / "negative_signals_ru.json",
    ("ru", "positive"): SEEDS_DIR / "positive_signals.json",
}


def load_signals(path: Path) -> List[Dict]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data["signals"]


def save_documents_with_label(documents: List[Dict], label: int, lang: str, query: str) -> int:
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
                    language=lang,
                    trust=raw.get("trust", 0.5),
                )
                db.add(source)
                db.flush()

            exists = db.query(Document).filter(Document.doc_id == doc["doc_id"]).first()
            if exists:
                continue

            document = Document(
                doc_id=doc.get("doc_id", ""),
                source_id=source.id,
                title=doc.get("title", "") or "",
                abstract=doc.get("abstract", "") or "",
                authors=", ".join(doc.get("authors", []) or []),
                organizations=", ".join(doc.get("organizations", []) or []),
                published_at=doc.get("published_at", "") or "",
                url=doc.get("url", "") or "",
                language=lang,
                region=doc.get("region", "") or "",
                label=label,
                source_query=query,
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


def _to_dicts(docs) -> List[Dict]:
    out = []
    for d in docs or []:
        if isinstance(d, dict):
            out.append(d)
        else:
            out.append({
                "doc_id": getattr(d, "doc_id", ""),
                "source_domain": getattr(d, "source_domain", ""),
                "source_type": getattr(d, "source_type", ""),
                "region": getattr(d, "region", ""),
                "language": getattr(d, "language", ""),
                "title": getattr(d, "title", ""),
                "abstract": getattr(d, "abstract", ""),
                "authors": getattr(d, "authors", []) or [],
                "organizations": getattr(d, "organizations", []) or [],
                "published_at": getattr(d, "published_at", ""),
                "url": getattr(d, "url", ""),
                "raw": getattr(d, "raw", {}) or {},
            })
    return out


async def collect_for_query(query: str, label: int, lang: str, rss_orch, use_arxiv: bool) -> int:
    total_saved = 0

    if use_arxiv:
        try:
            arxiv_docs = await search_arxiv(query, max_results=MAX_PER_SOURCE) or []
            saved = save_documents_with_label(arxiv_docs, label, lang, query)
            total_saved += saved
            logger.info(f"    → arXiv saved {saved}")
        except Exception as e:
            logger.warning(f"  arXiv failed: {e}")

    try:
        rss_docs_raw = await rss_orch.search_all(
            query,
            max_results_per_source=MAX_PER_SOURCE,
            max_concurrent=RSS_MAX_CONCURRENT,
        )
        rss_docs = _to_dicts(rss_docs_raw)
        saved = save_documents_with_label(rss_docs, label, lang, query)
        total_saved += saved
        logger.info(f"    → RSS saved {saved}")
    except Exception as e:
        logger.warning(f"  RSS failed: {e}")

    return total_saved


async def run_program(signals: List[Dict], label: int, lang: str, use_arxiv: bool, title: str):
    logger.info("=" * 60)
    logger.info(title)
    logger.info("=" * 60)
    logger.info("Initializing RSS orchestrator...")
    rss_orch = get_full_orchestrator()
    logger.info(f"RSS orchestrator ready: {len(rss_orch.parsers)} parsers")

    total = 0
    for i, signal in enumerate(signals, 1):
        name = signal["name"]
        logger.info(f"[{i}/{len(signals)}] {name[:70]}")
        saved = await collect_for_query(name, label=label, lang=lang, rss_orch=rss_orch, use_arxiv=use_arxiv)
        total += saved
        logger.info(f"    → total for query: {saved}")
        await asyncio.sleep(SLEEP_BETWEEN)

    logger.info(f"TOTAL for {title}: {total}")
    return total


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", choices=["en", "ru"], required=True)
    parser.add_argument("--label", choices=["positive", "negative"], required=True)
    args = parser.parse_args()

    label_int = 1 if args.label == "positive" else 0
    seed_path = SEED_FILES.get((args.lang, args.label))
    if not seed_path or not seed_path.exists():
        logger.error(f"Seed file not found: {seed_path}")
        sys.exit(1)

    signals = load_signals(seed_path)
    logger.info(f"Loaded {len(signals)} signals from {seed_path}")

    use_arxiv = (args.lang == "en")
    title = f"{args.lang.upper()} / {args.label.upper()}"

    await run_program(signals, label=label_int, lang=args.lang, use_arxiv=use_arxiv, title=title)


if __name__ == "__main__":
    asyncio.run(main())