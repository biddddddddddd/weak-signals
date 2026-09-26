import json
from pathlib import Path
from typing import List, Dict, Optional
from loguru import logger


REGISTRY_PATH = Path("config/sources_registry.json")
_registry_cache: Optional[Dict] = None


def load_registry(path: Path = REGISTRY_PATH) -> Dict:
    """Загружает реестр источников из JSON."""
    global _registry_cache
    if _registry_cache is not None:
        return _registry_cache

    if not path.exists():
        raise FileNotFoundError(f"Registry file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    _registry_cache = data
    logger.info(f"Registry loaded: {len(data['sources'])} sources (version {data.get('version', '?')})")
    return data


def get_all_sources() -> List[Dict]:
    """Возвращает все источники из реестра."""
    return load_registry()["sources"]


def get_active_sources() -> List[Dict]:
    """Только активные источники (active=true)."""
    return [s for s in get_all_sources() if s.get("active", True)]


def get_by_type(source_type: str) -> List[Dict]:
    """Источники по типу: science, media, patent, gov, social, funding, code, aggregator."""
    return [s for s in get_active_sources() if s.get("type") == source_type]


def get_by_region(region: str) -> List[Dict]:
    """Источники по региону."""
    return [s for s in get_active_sources() if s.get("region") == region]


def get_by_protocol(protocol: str) -> List[Dict]:
    """Источники по протоколу: rss, atom, api, html, graphql, xml."""
    return [s for s in get_active_sources() if s.get("protocol") == protocol]


def get_by_priority(max_priority: int = 1) -> List[Dict]:
    """Источники с приоритетом <= max_priority (1 = запускаем сразу)."""
    return [s for s in get_active_sources() if s.get("priority", 99) <= max_priority]


def get_source_by_id(source_id: str) -> Optional[Dict]:
    """Один источник по ID."""
    for s in get_all_sources():
        if s["id"] == source_id:
            return s
    return None


def get_stats_summary() -> Dict:
    """Сводка по реестру — сколько источников по типам, регионам, протоколам."""
    sources = get_active_sources()

    by_type = {}
    by_region = {}
    by_protocol = {}
    by_priority = {}

    for s in sources:
        by_type[s["type"]] = by_type.get(s["type"], 0) + 1
        by_region[s["region"]] = by_region.get(s["region"], 0) + 1
        by_protocol[s["protocol"]] = by_protocol.get(s["protocol"], 0) + 1
        p = s.get("priority", 99)
        by_priority[p] = by_priority.get(p, 0) + 1

    return {
        "total_active": len(sources),
        "by_type": by_type,
        "by_region": by_region,
        "by_protocol": by_protocol,
        "by_priority": by_priority,
    }