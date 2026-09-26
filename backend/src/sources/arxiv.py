import asyncio
import arxiv
import re
from typing import List, Dict
from loguru import logger

try:
    from deep_translator import GoogleTranslator
except Exception:
    GoogleTranslator = None


def _is_cyrillic(text: str) -> bool:
    return bool(re.search(r"[а-яА-ЯёЁ]", text))


def _translate_to_en(query: str) -> str:
    if not _is_cyrillic(query):
        return query
    if GoogleTranslator is None:
        return query
    try:
        translated = GoogleTranslator(source="auto", target="en").translate(query)
        logger.info(f"Translated query: '{query}' → '{translated}'")
        return translated or query
    except Exception as e:
        logger.warning(f"Translate failed: {e}")
        return query


async def search_arxiv(
    query: str,
    max_results: int = 50,
    max_retries: int = 3,
) -> List[Dict]:
    query_en = _translate_to_en(query)
    logger.info(f"arXiv search: query='{query_en}', max_results={max_results}")

    client = arxiv.Client()

    for attempt in range(max_retries):
        try:
            search = arxiv.Search(
                query=query_en,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate,
            )
            results = list(client.results(search))
            documents = [_parse_result(r) for r in results]
            logger.info(f"arXiv returned {len(documents)} entries")
            return documents
        except Exception as e:
            err = str(e)
            if "429" in err:
                wait = 30 * (attempt + 1)
                logger.warning(f"arXiv 429, waiting {wait}s... (attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(wait)
            else:
                logger.warning(f"arXiv error: {e}")
                return []

    logger.warning(f"arXiv exhausted retries for query='{query}'")
    return []


def _parse_result(result) -> Dict:
    return {
        "doc_id": result.entry_id,
        "source_domain": "arxiv.org",
        "source_type": "preprint",
        "region": "Global",
        "language": "en",
        "title": result.title.strip().replace("\n", " "),
        "abstract": result.summary.strip().replace("\n", " "),
        "authors": [author.name for author in result.authors],
        "organizations": [],
        "published_at": result.published.isoformat(),
        "url": result.entry_id,
        "raw": {
            "categories": result.categories,
            "primary_category": result.primary_category,
        },
    }