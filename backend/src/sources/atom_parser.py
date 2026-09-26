import httpx
import feedparser
import re
from typing import List
from loguru import logger

from src.sources.base_parser import BaseParser, Document


class AtomParser(BaseParser):
    """Универсальный Atom-парсер с тем же мягким фильтром."""

    def __init__(
        self,
        source_id: str,
        source_domain: str,
        region: str,
        language: str,
        trust_level: str,
        feed_url: str,
        source_type: str = "media",
    ):
        super().__init__(
            source_id=source_id,
            source_domain=source_domain,
            source_type=source_type,
            region=region,
            language=language,
            trust_level=trust_level,
        )
        self.feed_url = feed_url

    def _matches(self, text: str, query: str) -> bool:
        words = re.findall(r"\w+", query.lower())
        keywords = [w for w in words if len(w) >= 5]
        if not keywords:
            return True
        top = sorted(set(keywords), key=len, reverse=True)[:3]
        text_lower = text.lower()
        return any(w in text_lower for w in top)

    async def search(self, query: str, max_results: int = 20) -> List[Document]:
        headers = {"User-Agent": "Mozilla/5.0 (WeakSignals/0.1)"}

        try:
            async with httpx.AsyncClient(
                timeout=30.0,
                headers=headers,
                follow_redirects=True,
            ) as client:
                response = await client.get(self.feed_url)
                response.raise_for_status()
        except Exception as e:
            logger.warning(f"[{self.source_id}] fetch failed: {e}")
            return []

        feed = feedparser.parse(response.text)
        entries = feed.entries or []

        docs = []
        for entry in entries:
            title = (entry.get("title") or "").strip()
            summary = entry.get("summary", "")
            if not summary and entry.get("content"):
                try:
                    summary = entry.content[0].get("value", "")
                except Exception:
                    summary = ""
            summary = self._clean_html(summary)

            text = f"{title} {summary}"
            if not self._matches(text, query):
                continue

            raw_id = entry.get("id") or entry.get("link") or ""
            if not raw_id:
                continue

            published = entry.get("published", "") or entry.get("updated", "") or ""

            docs.append(Document(
                doc_id=self._make_doc_id(raw_id),
                source_domain=self.source_domain,
                source_type=self.source_type,
                region=self.region,
                language=self.language,
                title=title,
                abstract=summary,
                authors=[],
                organizations=[],
                published_at=self._parse_date(published),
                url=entry.get("link", ""),
                raw={
                    "source_id": self.source_id,
                    "trust_level": self.trust_level,
                },
            ))

            if len(docs) >= max_results:
                break

        return docs

    def _clean_html(self, text: str) -> str:
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()