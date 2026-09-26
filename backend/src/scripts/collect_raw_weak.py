import asyncio
import httpx
import feedparser
import re
from typing import List, Dict
from loguru import logger
from src.db.connection import SessionLocal
from src.db.models import RawWeakSignal

MAILTO = "weaksignals@example.com"
USER_AGENT = "WeakSignalsBot/0.1 (mailto:weaksignals@example.com)"

WEAK_KEYWORDS = ["emerging", "early-stage", "novel", "prototype", "first demonstration", "proof of concept"]
CATEGORIES = ["cs.AI", "cs.LG", "cs.RO", "cs.CR", "cs.CL", "cs.CV"]


def _save(records: List[Dict], source: str):
    if not records:
        return 0
    db = SessionLocal()
    saved = 0
    try:
        for rec in records:
            name = (rec.get("name") or "").strip()
            if not name or len(name) < 10:
                continue
            exists = db.query(RawWeakSignal).filter(RawWeakSignal.name == name).first()
            if exists:
                continue
            db.add(RawWeakSignal(
                name=name[:500],
                description=(rec.get("description") or "")[:4000],
                source=source,
                url=(rec.get("url") or "")[:500],
                year=rec.get("year"),
            ))
            saved += 1
        db.commit()
        logger.info(f"[{source}] saved {saved}")
    except Exception as e:
        db.rollback()
        logger.error(f"[{source}] save failed: {e}")
    finally:
        db.close()
    return saved


async def collect_arxiv(max_results: int = 100):
    docs = []
    for cat in CATEGORIES:
        for kw in WEAK_KEYWORDS[:3]:
            try:
                query = f"cat:{cat}+AND+all:{kw}"
                url = f"http://export.arxiv.org/api/query?search_query={query}&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"
                async with httpx.AsyncClient(timeout=60.0, headers={"User-Agent": USER_AGENT}) as client:
                    r = await client.get(url)
                    if r.status_code != 200:
                        continue
                    feed = feedparser.parse(r.text)
                    for entry in feed.entries:
                        title = (entry.get("title") or "").strip()
                        summary = (entry.get("summary") or "").strip()
                        if not title or len(title) < 15:
                            continue
                        docs.append({
                            "name": title,
                            "description": summary[:2000],
                            "url": entry.get("link", ""),
                            "year": int((entry.get("published", "2024") or "2024")[:4]),
                        })
                await asyncio.sleep(3.5)  # лимит arXiv
            except Exception as e:
                logger.warning(f"[arxiv] {e}")
                continue
    _save(docs, "arxiv")
    return len(docs)


async def collect_openalex(max_results: int = 200):
    docs = []
    for kw in WEAK_KEYWORDS:
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                r = await client.get(
                    "https://api.openalex.org/works",
                    params={
                        "search": kw,
                        "filter": "publication_year:2024-2026,cited_by_count:<10",
                        "per-page": min(max_results, 200),
                        "mailto": MAILTO,
                    },
                )
                if r.status_code != 200:
                    continue
                for w in r.json().get("results", []):
                    title = w.get("title") or ""
                    if not title or len(title) < 15:
                        continue
                    doi = w.get("doi") or w.get("id", "")
                    docs.append({
                        "name": title[:500],
                        "description": (w.get("abstract_inverted_index") and " ".join(
                            w["abstract_inverted_index"].keys()
                        ) or "")[:2000],
                        "url": doi,
                        "year": w.get("publication_year"),
                    })
            await asyncio.sleep(0.3)  # polite pool
        except Exception as e:
            logger.warning(f"[openalex] {e}")
    _save(docs, "openalex")
    return len(docs)


async def collect_crossref(max_results: int = 200):
    docs = []
    for kw in WEAK_KEYWORDS:
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                r = await client.get(
                    "https://api.crossref.org/works",
                    params={
                        "query": kw,
                        "filter": "from-pub-date:2024-01-01,until-pub-date:2026-12-31",
                        "rows": min(max_results, 200),
                        "mailto": MAILTO,
                    },
                )
                if r.status_code != 200:
                    continue
                for it in r.json().get("message", {}).get("items", []):
                    titles = it.get("title") or []
                    title = titles[0] if titles else ""
                    if not title or len(title) < 15:
                        continue
                    doi = it.get("DOI", "")
                    docs.append({
                        "name": title[:500],
                        "description": re.sub(r"<[^>]+>", " ", it.get("abstract", "") or "")[:2000],
                        "url": f"https://doi.org/{doi}" if doi else "",
                        "year": (it.get("published", {}).get("date-parts", [[None]])[0][0] if it.get("published") else None),
                    })
            await asyncio.sleep(0.3)
        except Exception as e:
            logger.warning(f"[crossref] {e}")
    _save(docs, "crossref")
    return len(docs)


async def main():
    await collect_arxiv(200)
    await collect_openalex(300)
    await collect_crossref(300)


if __name__ == "__main__":
    asyncio.run(main())