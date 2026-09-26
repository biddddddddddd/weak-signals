from datetime import datetime, timezone
from typing import Dict, Optional
import math
from loguru import logger


SOURCE_PROPERTIES = {
    "arxiv.org": {"trust": 0.75, "lead_time": 0.95, "specificity": 0.9, "independence": 0.9, "impact": 0.5},
    "openalex.org": {"trust": 0.8, "lead_time": 0.85, "specificity": 0.85, "independence": 0.9, "impact": 0.6},
    "techcrunch.com": {"trust": 0.6, "lead_time": 0.4, "specificity": 0.5, "independence": 0.7, "impact": 0.5},
    "eetimes.com": {"trust": 0.75, "lead_time": 0.55, "specificity": 0.7, "independence": 0.75, "impact": 0.6},
    "therobotreport.com": {"trust": 0.7, "lead_time": 0.55, "specificity": 0.7, "independence": 0.7, "impact": 0.55},
    "tech.eu": {"trust": 0.7, "lead_time": 0.55, "specificity": 0.65, "independence": 0.75, "impact": 0.55},
    "thenextweb.com": {"trust": 0.7, "lead_time": 0.55, "specificity": 0.6, "independence": 0.75, "impact": 0.5},
    "arstechnica.com": {"trust": 0.75, "lead_time": 0.55, "specificity": 0.75, "independence": 0.8, "impact": 0.6},
    "technode.com": {"trust": 0.7, "lead_time": 0.6, "specificity": 0.7, "independence": 0.7, "impact": 0.55},
    "pandaily.com": {"trust": 0.65, "lead_time": 0.6, "specificity": 0.7, "independence": 0.65, "impact": 0.5},
    "japan.cnet.com": {"trust": 0.7, "lead_time": 0.55, "specificity": 0.65, "independence": 0.7, "impact": 0.5},
    "yourstory.com": {"trust": 0.65, "lead_time": 0.55, "specificity": 0.6, "independence": 0.7, "impact": 0.5},
    "cnews.ru": {"trust": 0.6, "lead_time": 0.5, "specificity": 0.6, "independence": 0.65, "impact": 0.5},
}

DEFAULT_PROPERTIES = {
    "trust": 0.5, "lead_time": 0.5, "specificity": 0.5, "independence": 0.5, "impact": 0.5,
}


def get_source_features(domain: str) -> Dict:
    return SOURCE_PROPERTIES.get(domain, DEFAULT_PROPERTIES)


def compute_freshness(published_at: str, half_life_days: int = 365) -> float:
    if not published_at:
        return 0.5
    dt = _parse_date(published_at)
    if dt is None:
        return 0.5

    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    age_days = max(0, (now - dt).days)
    return round(math.exp(-age_days / half_life_days), 4)


def _parse_date(date_str: str) -> Optional[datetime]:
    if not date_str:
        return None
    formats = [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except Exception:
        return None


def extract_features(doc: Dict) -> Dict:
    """
    Извлекает признаки из документа.
    doc — словарь с ключами source_domain, title, abstract, published_at, region, organizations.
    """
    domain = doc.get("source_domain", "")
    props = get_source_features(domain)
    freshness = compute_freshness(doc.get("published_at", ""))

    title = doc.get("title", "") or ""
    abstract = doc.get("abstract", "") or ""
    text = f"{title} {abstract}"

    return {
        "trust": props["trust"],
        "lead_time": props["lead_time"],
        "specificity": props["specificity"],
        "independence": props["independence"],
        "impact": props["impact"],
        "freshness": freshness,
        "title_length": len(title),
        "abstract_length": len(abstract),
        "text_length": len(text),
        "has_organizations": 1 if doc.get("organizations") else 0,
        "region": doc.get("region", "Global") or "Global",
    }