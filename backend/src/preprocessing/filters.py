import json
import re
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger


_CONFIG_PATH = Path("config/filters_config.json")
_config_cache: Optional[Dict] = None


def _load_config() -> Dict:
    global _config_cache
    if _config_cache is None:
        with _CONFIG_PATH.open("r", encoding="utf-8") as f:
            _config_cache = json.load(f)
        logger.info(f"Filters config loaded from {_CONFIG_PATH}")
    return _config_cache


def get_trust_level(domain: str) -> float:
    """
    Возвращает trust_level для домена.
    Если домена нет в конфиге — возвращает default.
    """
    config = _load_config()
    trust_map = config.get("trust_by_domain", {})
    return trust_map.get(domain, trust_map.get("default", 0.5))


def is_valid(doc: Dict) -> bool:
    """
    Проверяет документ на пригодность.
    Возвращает True, если документ проходит все фильтры.
    """
    config = _load_config()

    if not _check_type(doc, config):
        return False

    if not _check_authors(doc, config):
        return False

    if not _check_title(doc, config):
        return False

    if not _check_abstract(doc, config):
        return False

    return True


def _check_type(doc: Dict, config: Dict) -> bool:
    excluded = config.get("excluded_types", [])
    doc_type = doc.get("raw", {}).get("type", "")
    if doc_type in excluded:
        logger.debug(f"Rejected by type: {doc_type} | {doc.get('title', '')[:50]}")
        return False
    return True


def _check_authors(doc: Dict, config: Dict) -> bool:
    patterns = config.get("excluded_author_patterns", [])
    compiled = [re.compile(p, re.IGNORECASE) for p in patterns]

    authors: List[str] = doc.get("authors", [])
    if not authors:
        return True

    for author in authors:
        for pattern in compiled:
            if pattern.search(author):
                logger.debug(f"Rejected by author: {author} | {doc.get('title', '')[:50]}")
                return False
    return True


def _check_title(doc: Dict, config: Dict) -> bool:
    min_len = config.get("min_title_length", 10)
    title = doc.get("title", "")
    if not title or len(title.strip()) < min_len:
        logger.debug(f"Rejected by title length: {len(title)}")
        return False
    return True


def _check_abstract(doc: Dict, config: Dict) -> bool:
    min_len = config.get("min_abstract_length", 50)
    abstract = doc.get("abstract", "")
    if not abstract or len(abstract.strip()) < min_len:
        logger.debug(f"Rejected by abstract length: {len(abstract)}")
        return False
    return True