from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict
from loguru import logger


@dataclass
class Document:
    """Единый формат документа для всех источников."""
    doc_id: str
    source_domain: str
    source_type: str          # science | patent | media | social | gov | funding | code | aggregator
    region: str               # USA | China | Europe | Japan | India | Russia | Global
    language: str             # en | ru | zh | ja | ...
    title: str
    abstract: str = ""
    authors: List[str] = field(default_factory=list)
    organizations: List[str] = field(default_factory=list)
    published_at: str = ""
    url: str = ""
    raw: Dict = field(default_factory=dict)


class BaseParser(ABC):
    """
    Абстрактный парсер. Все конкретные парсеры наследуют этот класс.

    Каждый парсер обрабатывает один источник (или группу однотипных источников,
    как RSSParser с конфигом).
    """

    def __init__(
        self,
        source_id: str,
        source_domain: str,
        source_type: str,
        region: str,
        language: str,
        trust_level: str = "medium",
    ):
        self.source_id = source_id
        self.source_domain = source_domain
        self.source_type = source_type
        self.region = region
        self.language = language
        self.trust_level = trust_level
        logger.info(f"Initialized parser: {source_id} ({source_type}, {region})")

    @abstractmethod
    async def search(self, query: str, max_results: int = 20) -> List[Document]:
        """
        Ищет документы по запросу.
        Возвращает список Document.
        """
        raise NotImplementedError

    async def get_stats(self, query: str) -> Optional[Dict]:
        """
        Опциональный метод: возвращает статистику по теме.
        Например, число работ, число свежих работ.
        По умолчанию не поддерживается.
        """
        return None

    def _make_doc_id(self, raw_id: str) -> str:
        """Уникальный ID в формате source:raw_id."""
        return f"{self.source_id}:{raw_id}"

    def _parse_date(self, date_str: str) -> str:
        """Приводит дату к ISO-формату. Возвращает как есть при ошибке."""
        if not date_str:
            return ""
        try:
            for fmt in (
                "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d",
                "%a, %d %b %Y %H:%M:%S %z",
                "%a, %d %b %Y %H:%M:%S %Z",
            ):
                try:
                    return datetime.strptime(date_str, fmt).isoformat()
                except ValueError:
                    continue
            return datetime.fromisoformat(date_str.replace("Z", "+00:00")).isoformat()
        except Exception:
            return date_str