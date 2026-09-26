import httpx
import os
from loguru import logger
from src.db.connection import SessionLocal
from src.db.models import RawWeakSignal

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()
HEADERS = {"Accept": "application/vnd.github+json"}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"

TOPICS = ["ai", "machine-learning", "robotics", "fintech", "cybersecurity", "biotech"]


def save(records):
    db = SessionLocal()
    saved = 0
    try:
        for rec in records:
            name = (rec.get("name") or "").strip()
            if not name:
                continue
            exists = db.query(RawWeakSignal).filter(RawWeakSignal.name == name).first()
            if exists:
                continue
            db.add(RawWeakSignal(
                name=name[:500],
                description=(rec.get("description") or "")[:4000],
                source="github",
                url=(rec.get("url") or "")[:500],
                year=rec.get("year"),
            ))
            saved += 1
        db.commit()
        logger.info(f"[github] saved {saved}")
    except Exception as e:
        db.rollback()
        logger.error(f"[github] save failed: {e}")
    finally:
        db.close()


def collect():
    docs = []
    with httpx.Client(timeout=30.0, headers=HEADERS) as client:
        for topic in TOPICS:
            try:
                r = client.get(
                    "https://api.github.com/search/repositories",
                    params={
                        "q": f"topic:{topic} created:>2024-01-01 stars:<1000",
                        "sort": "stars",
                        "order": "desc",
                        "per_page": 50,
                    },
                )
                if r.status_code != 200:
                    logger.warning(f"[github] {topic}: {r.status_code}")
                    continue
                for it in r.json().get("items", []):
                    docs.append({
                        "name": it.get("full_name", ""),
                        "description": it.get("description") or "",
                        "url": it.get("html_url", ""),
                        "year": int(it.get("created_at", "2024")[:4]) if it.get("created_at") else None,
                    })
            except Exception as e:
                logger.warning(f"[github] {topic}: {e}")
    save(docs)


if __name__ == "__main__":
    collect()