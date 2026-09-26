import asyncio
from typing import List, Dict, Set
from loguru import logger

from src.sources.base_parser import BaseParser, Document


class Orchestrator:
    """
    Запускает парсеры, собирает документы, дедуплицирует.
    Не знает, что внутри парсеров — просто вызывает .search() у каждого.
    """

    def __init__(self):
        self.parsers: List[BaseParser] = []

    def register(self, parser: BaseParser):
        """Добавляет парсер в пул."""
        self.parsers.append(parser)
        logger.info(f"Registered parser: {parser.source_id}")

    def register_many(self, parsers: List[BaseParser]):
        for p in parsers:
            self.register(p)

    async def _safe_search(
        self,
        parser: BaseParser,
        query: str,
        max_results: int,
    ) -> List[Document]:
        """Обёртка для безопасного вызова парсера. Не даёт упасть всему сбору."""
        try:
            docs = await parser.search(query, max_results=max_results)
            logger.info(f"  [{parser.source_id}] {len(docs)} docs")
            return docs
        except Exception as e:
            logger.warning(f"  [{parser.source_id}] FAILED: {e}")
            return []

    async def search_all(
        self,
        query: str,
        max_results_per_source: int = 20,
        max_concurrent: int = 5,
    ) -> List[Document]:
        """
        Запускает все парсеры параллельно (но не более max_concurrent одновременно).
        Возвращает дедуплицированный список документов.
        """
        logger.info(f"Search across {len(self.parsers)} parsers: query='{query}'")

        semaphore = asyncio.Semaphore(max_concurrent)

        async def bounded_search(parser: BaseParser) -> List[Document]:
            async with semaphore:
                return await self._safe_search(parser, query, max_results_per_source)

        tasks = [bounded_search(p) for p in self.parsers]
        results = await asyncio.gather(*tasks)

        all_docs: List[Document] = []
        seen: Set[str] = set()

        for docs in results:
            for doc in docs:
                if doc.doc_id in seen:
                    continue
                seen.add(doc.doc_id)
                all_docs.append(doc)

        logger.info(f"Total unique documents: {len(all_docs)} (from {sum(len(r) for r in results)} raw)")
        return all_docs

    async def collect_stats(
        self,
        query: str,
    ) -> Dict[str, Dict]:
        """
        Опрашивает все парсеры, поддерживающие get_stats().
        Возвращает словарь {source_id: stats_dict}.
        """
        logger.info(f"Collecting stats from {len(self.parsers)} parsers: query='{query}'")

        stats = {}
        for parser in self.parsers:
            try:
                s = await parser.get_stats(query)
                if s:
                    stats[parser.source_id] = s
            except Exception as e:
                logger.warning(f"  [{parser.source_id}] stats failed: {e}")

        return stats


def _domain_from_url(url: str) -> str:
    """Извлекает домен из URL."""
    try:
        from urllib.parse import urlparse
        return urlparse(url).netloc
    except Exception:
        return url


def get_orchestrator_with_rss() -> Orchestrator:
    """
    Фабрика: оркестратор только с RSS-парсерами.
    Используется для быстрого теста.
    """
    from src.sources.rss_parser import RSSParser
    from src.sources.registry import get_by_protocol

    orch = Orchestrator()
    rss_sources = get_by_protocol("rss")

    for s in rss_sources:
        parser = RSSParser(
            source_id=s["id"],
            source_domain=_domain_from_url(s["url"]),
            region=s["region"],
            language=s["language"],
            trust_level=s["trust_level"],
            feed_url=s["url"],
            source_type=s["type"],
        )
        orch.register(parser)

    return orch


def get_full_orchestrator() -> Orchestrator:
    """
    Фабрика: полный оркестратор со всеми активными RSS и Atom парсерами.
    API-парсеры подключаются отдельно по source_id.
    """
    from src.sources.rss_parser import RSSParser
    from src.sources.atom_parser import AtomParser
    from src.sources.registry import get_active_sources

    orch = Orchestrator()
    sources = get_active_sources()

    for s in sources:
        try:
            if s["protocol"] == "rss":
                parser = RSSParser(
                    source_id=s["id"],
                    source_domain=_domain_from_url(s["url"]),
                    region=s["region"],
                    language=s["language"],
                    trust_level=s["trust_level"],
                    feed_url=s["url"],
                    source_type=s["type"],
                )
                orch.register(parser)

            elif s["protocol"] == "atom":
                parser = AtomParser(
                    source_id=s["id"],
                    source_domain=_domain_from_url(s["url"]),
                    region=s["region"],
                    language=s["language"],
                    trust_level=s["trust_level"],
                    feed_url=s["url"],
                    source_type=s["type"],
                )
                orch.register(parser)

            # API-парсеры добавятся отдельно по source_id:
            # elif s["id"] == "crossref": ...

        except Exception as e:
            logger.warning(f"Could not register {s['id']}: {e}")

    return orch