import json
import time
from pathlib import Path
from typing import Dict
import httpx
from loguru import logger


OPENALEX_API = "https://api.openalex.org/works"
CACHE_PATH = Path("data/processed/topic_stats.json")
EMAIL = "weaksignals@example.com"


def _fetch_count(search_query: str, extra_filter: str = "", max_retries: int = 5) -> int:
    """
    Возвращает meta.count из OpenAlex — число работ по запросу.
    0 при неудаче. С увеличенными паузами при 429.
    """
    params = {
        "search": search_query,
        "per-page": 1,
        "mailto": EMAIL,
    }
    if extra_filter:
        params["filter"] = extra_filter

    headers = {"User-Agent": f"WeakSignals/0.1 (mailto:{EMAIL})"}

    for attempt in range(max_retries):
        try:
            response = httpx.get(
                OPENALEX_API,
                params=params,
                headers=headers,
                timeout=30.0,
                follow_redirects=True,
            )

            if response.status_code == 429:
                wait = 60 * (attempt + 1)
                logger.warning(f"OpenAlex 429, waiting {wait}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait)
                continue

            response.raise_for_status()
            data = response.json()
            total = data.get("meta", {}).get("count", 0)
            return int(total) if total else 0

        except Exception as e:
            logger.warning(f"OpenAlex error (attempt {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                return 0
            time.sleep(10)

    return 0


def fetch_topic_stats(query: str) -> Dict:
    """
    2 запроса к OpenAlex:
    1. Всего работ по теме.
    2. Работ за последние ~2 года (с 2024-09-01).
    С паузами 1.5 сек между запросами.
    """
    total_all = _fetch_count(query)
    time.sleep(1.5)

    total_recent = _fetch_count(
        query,
        extra_filter="from_publication_date:2024-09-01",
    )
    time.sleep(1.5)

    return {
        "total": total_all,
        "recent": total_recent,
    }


def fetch_all_topics(queries: list, cache_path: Path = CACHE_PATH) -> Dict:
    """
    Скачивает stats для списка queries. Кэширует в JSON.
    Если файл есть — использует его (продолжает с места обрыва).
    """
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    stats = {}
    if cache_path.exists():
        logger.info(f"Loading cached topic stats from {cache_path}")
        with cache_path.open("r", encoding="utf-8") as f:
            stats = json.load(f)
        logger.info(f"Loaded {len(stats)} cached entries")

    logger.info(f"Fetching OpenAlex stats for {len(queries)} queries (already have {len(stats)})...")

    for i, q in enumerate(queries, 1):
        if q in stats:
            continue

        logger.info(f"[{i}/{len(queries)}] {q[:70]}")
        stats[q] = fetch_topic_stats(q)

        # Polite pause: 2 sec between queries
        time.sleep(2.0)

        if i % 10 == 0:
            with cache_path.open("w", encoding="utf-8") as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
            logger.info(f"  Cache saved ({len(stats)} queries total)")

    with cache_path.open("w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved {len(stats)} topic stats to {cache_path}")
    return stats


def add_topic_features(df, stats: Dict):
    """Добавляет 3 topic-признака в DataFrame."""
    import math

    total_list = []
    recent_list = []
    ratio_list = []

    for q in df["source_query"]:
        s = stats.get(q, {"total": 0, "recent": 0})
        total = s.get("total", 0) or 0
        recent = s.get("recent", 0) or 0

        total_list.append(math.log1p(total))
        recent_list.append(math.log1p(recent))
        ratio_list.append(recent / total if total > 0 else 0.0)

    df = df.copy()
    df["topic_total_log"] = total_list
    df["topic_recent_log"] = recent_list
    df["topic_recent_ratio"] = ratio_list
    return df