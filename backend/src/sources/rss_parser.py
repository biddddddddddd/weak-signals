import httpx
import feedparser
import re
from typing import List
from loguru import logger

from src.sources.base_parser import BaseParser, Document

try:
    from simplemma import lemmatize
except Exception:
    lemmatize = None


USER_AGENT = (
    "Mozilla/5.0 (compatible; WeakSignalsBot/0.2; "
    "+https://github.com/weak-signals; mailto:weaksignals@example.com)"
)

STOP_WORDS = {
    "general", "mainstream", "traditional", "standard", "basic", "advanced",
    "concept", "concepts", "system", "systems", "technology", "technologies",
    "platform", "platforms", "industry", "sector", "framework", "ecosystem",
    "approach", "claims", "apps", "tools", "consumers", "consumer",
    "infrastructure", "protocol", "architecture", "design", "processes",
    "and", "for", "the", "with", "from", "into", "over", "using",
    "для", "или", "при", "над", "под", "без", "что", "как", "это",
    "все", "его", "её", "их", "мы", "вы", "они", "она", "оно",
}

MAX_SCAN = 300
MIN_MATCH_RATIO = 0.5
MIN_MATCH_ABS = 2


def _is_cyrillic(text: str) -> bool:
    return bool(re.search(r"[а-яА-ЯёЁ]", text))


def _lemma(word: str, lang: str) -> str:
    word = word.lower().strip()
    if not word:
        return word
    if lemmatize is not None:
        try:
            return lemmatize(word, lang=lang[:2])
        except Exception:
            return word
    return word


class RSSParser(BaseParser):
    """
    Универсальный RSS-парсер. Работает с одной лентой.
    Фильтр: матч по лемматизированным значимым словам через simplemma.
    """

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

    def _keywords(self, query: str) -> List[str]:
        tokens = re.findall(r"\w+", query, flags=re.UNICODE)
        lang = "ru" if _is_cyrillic(query) else "en"
        keywords: List[str] = []
        for tok in tokens:
            low = tok.lower()
            if low in STOP_WORDS:
                continue
            if len(low) < 3 and not (len(low) == 2 and tok.isupper()):
                continue
            lemma = _lemma(low, lang)
            if lemma and lemma not in STOP_WORDS:
                keywords.append(lemma)
        seen = set()
        unique = []
        for k in keywords:
            if k not in seen:
                seen.add(k)
                unique.append(k)
        return unique

    def _lemmatize_text(self, text: str, lang: str) -> str:
        tokens = re.findall(r"\w+", text, flags=re.UNICODE)
        lemmas = []
        for tok in tokens:
            low = tok.lower()
            if len(low) < 2:
                continue
            lemmas.append(_lemma(low, lang))
        return " " + " ".join(lemmas) + " "

    def _matches(self, text: str, query: str) -> bool:
        keywords = self._keywords(query)
        if not keywords:
            return False

        lang = "ru" if _is_cyrillic(query) else "en"
        text_lemmas = self._lemmatize_text(text, lang)

        hits = 0
        for kw in keywords:
            if re.search(rf"\b{re.escape(kw)}", text_lemmas):
                hits += 1

        n = len(keywords)
        if n == 1:
            need = 1
        elif n == 2:
            need = 2
        else:
            need = max(MIN_MATCH_ABS, round(n * MIN_MATCH_RATIO))
        return hits >= need

    async def search(self, query: str, max_results: int = 20) -> List[Document]:
        headers = {"User-Agent": USER_AGENT}

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

        docs: List[Document] = []
        scanned = 0
        for entry in entries[:MAX_SCAN]:
            scanned += 1
            title = (entry.get("title") or "").strip()
            summary = (
                entry.get("summary", "")
                or entry.get("description", "")
                or ""
            )
            summary = self._clean_html(summary)

            text = f"{title} {summary}"
            if not self._matches(text, query):
                continue

            doc = self._build_document(entry, title, summary)
            if doc:
                docs.append(doc)

            if len(docs) >= max_results:
                break

        if scanned and not docs:
            logger.debug(
                f"[{self.source_id}] scanned {scanned}, matched 0 for '{query[:50]}'"
            )

        return docs

    def _build_document(self, entry, title: str, summary: str) -> Document:
        raw_id = entry.get("id") or entry.get("link") or ""
        if not raw_id:
            return None

        published = entry.get("published", "") or entry.get("updated", "") or ""

        return Document(
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
                "tags": [t.get("term", "") for t in entry.get("tags", [])],
            },
        )

    def _clean_html(self, text: str) -> str:
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()