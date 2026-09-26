import httpx
import os
import json
from loguru import logger
from src.db.connection import SessionLocal
from src.db.models import RawWeakSignal

PH_TOKEN = os.getenv("PRODUCT_HUNT_TOKEN", "").strip()
ENDPOINT = "https://api.producthunt.com/v2/api/graphql"

QUERY = """
query($topic: String!, $first: Int!) {
  posts(topic: $topic, first: $first, order: NEWEST) {
    edges {
      node {
        name
        tagline
        description
        url
        createdAt
        votesCount
      }
    }
  }
}
"""

TOPICS = ["artificial-intelligence", "robotics", "fintech", "cybersecurity", "biotech"]


def collect():
    if not PH_TOKEN:
        logger.error("PRODUCT_HUNT_TOKEN не задан")
        return
    headers = {"Authorization": f"Bearer {PH_TOKEN}", "Content-Type": "application/json"}
    docs = []
    with httpx.Client(timeout=30.0, headers=headers) as client:
        for topic in TOPICS:
            try:
                r = client.post(ENDPOINT, json={
                    "query": QUERY,
                    "variables": {"topic": topic, "first": 50},
                })
                if r.status_code != 200:
                    logger.warning(f"[ph] {topic}: {r.status_code}")
                    continue
                data = r.json().get("data", {}).get("posts", {}).get("edges", [])
                for edge in data:
                    node = edge.get("node", {})
                    votes = node.get("votesCount", 0)
                    if votes > 500:
                        continue  # хайп
                    docs.append({
                        "name": node.get("name", ""),
                        "description": (node.get("tagline") or "") + ". " + (node.get("description") or ""),
                        "url": node.get("url", ""),
                        "year": int(node.get("createdAt", "2024")[:4]) if node.get("createdAt") else None,
                    })
            except Exception as e:
                logger.warning(f"[ph] {topic}: {e}")

    db = SessionLocal()
    saved = 0
    try:
        for rec in docs:
            name = (rec.get("name") or "").strip()
            if not name:
                continue
            if db.query(RawWeakSignal).filter(RawWeakSignal.name == name).first():
                continue
            db.add(RawWeakSignal(
                name=name[:500],
                description=(rec.get("description") or "")[:4000],
                source="producthunt",
                url=(rec.get("url") or "")[:500],
                year=rec.get("year"),
            ))
            saved += 1
        db.commit()
        logger.info(f"[producthunt] saved {saved}")
    except Exception as e:
        db.rollback()
        logger.error(f"[producthunt] {e}")
    finally:
        db.close()


if __name__ == "__main__":
    collect()