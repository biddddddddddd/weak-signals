import asyncio
import httpx
from typing import List, Dict, Optional
from loguru import logger

from src.preprocessing.filters import is_valid
from src.db.repository import save_documents


OPENALEX_API = "https://api.openalex.org/works"
OPENALEX_EMAIL = "weaksignals@example.com"


async def search_openalex(
    query: str,
    max_results: int = 50,
    email: Optional[str] = None,
    max_retries: int = 3,
) -> List[Dict]:
    """
    Ищет статьи в OpenAlex по запросу. Retry при 429.
    """
    params = {
        "search": query,
        "per-page": min(max_results, 200),
        "sort": "publication_date:desc",
        "mailto": email or OPENALEX_EMAIL,
    }

    headers = {
        "User-Agent": "WeakSignals/0.1 (mailto:weaksignals@example.com)",
    }

    logger.info(f"OpenAlex search: query='{query}', max_results={max_results}")

    response = None
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=30.0, headers=headers, follow_redirects=True) as client:
                response = await client.get(OPENALEX_API, params=params)

                if response.status_code == 429:
                    wait = 30 * (attempt + 1)
                    logger.warning(f"OpenAlex 429, waiting {wait}s... (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(wait)
                    continue

                response.raise_for_status()
                break
        except Exception as e:
            logger.warning(f"OpenAlex error: {e}")
            if attempt == max_retries - 1:
                return []
            await asyncio.sleep(10)

    if response is None or response.status_code == 429:
        logger.warning(f"OpenAlex exhausted retries for query='{query}'")
        return []

    data = response.json()
    results = data.get("results", [])
    logger.info(f"OpenAlex returned {len(results)} entries")

    documents = []
    for work in results:
        doc = _parse_work(work)
        if is_valid(doc):
            documents.append(doc)

    logger.info(f"OpenAlex passed filters: {len(documents)} entries")

    saved = save_documents(documents)
    logger.info(f"OpenAlex saved {saved} documents to DB")

    return documents


def _parse_work(work: Dict) -> Dict:
    authors = [
        a["author"]["display_name"]
        for a in work.get("authorships", [])
        if a.get("author")
    ]

    organizations = []
    for a in work.get("authorships", []):
        for inst in a.get("institutions", []):
            name = inst.get("display_name")
            if name and name not in organizations:
                organizations.append(name)

    countries = []
    for a in work.get("authorships", []):
        for inst in a.get("institutions", []):
            cc = inst.get("country_code")
            if cc and cc not in countries:
                countries.append(cc)

    region = _detect_region(countries)

    return {
        "doc_id": work.get("id", ""),
        "source_domain": "openalex.org",
        "source_type": "science",
        "region": region,
        "language": work.get("language", "en"),
        "title": work.get("title", "") or "",
        "abstract": _reconstruct_abstract(work.get("abstract_inverted_index")),
        "authors": authors,
        "organizations": organizations,
        "published_at": work.get("publication_date", "") or "",
        "url": work.get("doi") or work.get("id", ""),
        "raw": {
            "cited_by_count": work.get("cited_by_count", 0),
            "concepts": [
                c["display_name"] for c in work.get("concepts", [])[:10]
            ],
            "countries": countries,
            "type": work.get("type", ""),
            "open_access": work.get("open_access", {}).get("is_oa", False),
        },
    }


def _reconstruct_abstract(inverted_index: Optional[Dict]) -> str:
    if not inverted_index:
        return ""

    words_with_positions = []
    for word, positions in inverted_index.items():
        for pos in positions:
            words_with_positions.append((pos, word))

    words_with_positions.sort(key=lambda x: x[0])
    return " ".join(word for _, word in words_with_positions)


def _detect_region(countries: List[str]) -> str:
    if not countries:
        return "Global"

    if "US" in countries:
        return "USA"
    if "CN" in countries:
        return "China"

    europe = {"GB", "DE", "FR", "NL", "NO", "SE", "CH", "IT", "ES", "PL", "BE", "AT", "DK", "FI"}
    if any(c in europe for c in countries):
        return "Europe"

    if "JP" in countries:
        return "Japan"
    if "IN" in countries:
        return "India"
    if "RU" in countries:
        return "Russia"

    return "Global"