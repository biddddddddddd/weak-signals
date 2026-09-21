import json
from pathlib import Path
from typing import List, Dict
from datetime import datetime

import httpx
import feedparser
from loguru import logger

from src.preprocessing.filters import is_valid


_CONFIG_PATH = Path("config/rss_sources.json")


def load_rss_sources() -> List[Dict]:
    with _CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)["sources"]


async def fetch_rss(source: Dict, max_items: int = 20) -> List[Dict]:
    """
    Забирает RSS-ленту и возвращает список документов в единой схеме.
    """
    logger.info(f"RSS fetch: {source['name']} ({source['url']})")

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; WeakSignalsBot/0.1)",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0, headers=headers, follow_redirects=True) as client:
            response = await client.get(source["url"])
            response.raise_for_status()
    except Exception as e:
        logger.warning(f"RSS fetch failed for {source['name']}: {e}")
        return []

    feed = feedparser.parse(response.text)
    documents = []

    for entry in feed.entries[:max_items]:
        doc = _parse_entry(entry, source)
        if doc and is_valid(doc):
            documents.append(doc)

    logger.info(f"RSS {source['name']}: {len(documents)} documents passed filters")
    return documents


def _parse_entry(entry, source: Dict) -> Dict:
    """
    Превращает запись RSS в документ единой схемы.
    """
    title = entry.get("title", "").strip()
    summary = entry.get("summary", "") or entry.get("description", "")
    summary = _clean_html(summary)

    published = entry.get("published", "") or entry.get("updated", "")

    return {
        "doc_id": entry.get("link", ""),
        "source_domain": source["domain"],
        "source_type": source["source_type"],
        "region": source["region"],
        "language": source["language"],
        "title": title,
        "abstract": summary,
        "authors": [],
        "organizations": [],
        "published_at": published,
        "url": entry.get("link", ""),
        "raw": {
            "source_name": source["name"],
            "trust": source["trust"],
            "tags": [t.get("term", "") for t in entry.get("tags", [])],
        },
    }


def _clean_html(text: str) -> str:
    """
    Убирает HTML-теги из описания RSS.
    """
    import re
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()