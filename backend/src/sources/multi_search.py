import asyncio
import re
import httpx
from typing import List, Dict
from loguru import logger
from bs4 import BeautifulSoup

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0 Safari/537.36"
)


def _is_cyrillic(text: str) -> bool:
    return bool(re.search(r"[а-яА-ЯёЁ]", text))


def _mk(doc_id, title, abstract, url, source_name, language, trust):
    return {
        "doc_id": doc_id,
        "title": (title or "")[:500],
        "abstract": (abstract or "")[:4000],
        "url": url or "",
        "source_name": source_name,
        "language": language,
        "trust_level": trust,
    }


# ============================================================
# 1. DuckDuckGo HTML
# ============================================================
async def search_duckduckgo(query: str, max_results: int = 20) -> List[Dict]:
    url = "https://html.duckduckgo.com/html/"
    docs = []
    try:
        async with httpx.AsyncClient(timeout=30.0, headers={"User-Agent": USER_AGENT}, follow_redirects=True) as client:
            r = await client.post(url, data={"q": query})
            if r.status_code != 200:
                logger.warning(f"[ddg] status {r.status_code}")
                return []
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.select(".result__a")[:max_results]:
                title = a.get_text(strip=True)
                href = a.get("href", "")
                m = re.search(r"uddg=([^&]+)", href)
                if m:
                    from urllib.parse import unquote
                    href = unquote(m.group(1))
                if not title or not href:
                    continue
                docs.append(_mk(href, title, "", href, "duckduckgo",
                                "en" if not _is_cyrillic(title) else "ru", 5))
    except Exception as e:
        logger.warning(f"[ddg] failed: {e}")
    return docs


# ============================================================
# 2. Startpage HTML
# ============================================================
async def search_startpage(query: str, max_results: int = 20) -> List[Dict]:
    docs = []
    try:
        async with httpx.AsyncClient(timeout=30.0, headers={"User-Agent": USER_AGENT}, follow_redirects=True) as client:
            r = await client.get("https://www.startpage.com/sp/search", params={"query": query})
            if r.status_code != 200:
                logger.warning(f"[startpage] status {r.status_code}")
                return []
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.select("a.result-link, .w-gl__result-title a")[:max_results]:
                title = a.get_text(strip=True)
                href = a.get("href", "")
                if not title or not href.startswith("http"):
                    continue
                docs.append(_mk(href, title, "", href, "startpage",
                                "en" if not _is_cyrillic(title) else "ru", 5))
    except Exception as e:
        logger.warning(f"[startpage] failed: {e}")
    return docs


# ============================================================
# 3. Mojeek HTML
# ============================================================
async def search_mojeek(query: str, max_results: int = 20) -> List[Dict]:
    docs = []
    try:
        async with httpx.AsyncClient(timeout=30.0, headers={"User-Agent": USER_AGENT}, follow_redirects=True) as client:
            r = await client.get("https://www.mojeek.com/search", params={"q": query})
            if r.status_code != 200:
                logger.warning(f"[mojeek] status {r.status_code}")
                return []
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.select("a.title, .results-standard a")[:max_results]:
                title = a.get_text(strip=True)
                href = a.get("href", "")
                if not title or not href.startswith("http"):
                    continue
                docs.append(_mk(href, title, "", href, "mojeek",
                                "en" if not _is_cyrillic(title) else "ru", 5))
    except Exception as e:
        logger.warning(f"[mojeek] failed: {e}")
    return docs


# ============================================================
# 4. Marginalia
# ============================================================
async def search_marginalia(query: str, max_results: int = 20) -> List[Dict]:
    docs = []
    try:
        async with httpx.AsyncClient(timeout=30.0, headers={"User-Agent": USER_AGENT}, follow_redirects=True) as client:
            r = await client.get("https://search.marginalia.nu/search", params={"query": query})
            if r.status_code != 200:
                logger.warning(f"[marginalia] status {r.status_code}")
                return []
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.select("a.result-title, h2 a, .card a")[:max_results]:
                title = a.get_text(strip=True)
                href = a.get("href", "")
                if not href.startswith("http") or not title:
                    continue
                docs.append(_mk(href, title, "", href, "marginalia", "en", 4))
    except Exception as e:
        logger.warning(f"[marginalia] failed: {e}")
    return docs


# ============================================================
# 5. OpenAlex
# ============================================================
async def search_openalex(query: str, max_results: int = 20) -> List[Dict]:
    docs = []
    try:
        async with httpx.AsyncClient(timeout=30.0, headers={"User-Agent": USER_AGENT}) as client:
            r = await client.get(
                "https://api.openalex.org/works",
                params={"search": query, "per-page": max_results, "mailto": "weaksignals@example.com"},
            )
            if r.status_code != 200:
                logger.warning(f"[openalex] status {r.status_code}")
                return []
            data = r.json()
            for w in data.get("results", []):
                title = w.get("title") or ""
                abstract = ""
                inv = w.get("abstract_inverted_index")
                if inv:
                    positions = {}
                    for word, idxs in inv.items():
                        for i in idxs:
                            positions[i] = word
                    abstract = " ".join(positions[i] for i in sorted(positions))[:2000]
                doi = w.get("doi") or w.get("id", "")
                if not title or not doi:
                    continue
                docs.append(_mk(doi, title, abstract, doi, "openalex", "en", 9))
    except Exception as e:
        logger.warning(f"[openalex] failed: {e}")
    return docs


# ============================================================
# 6. Crossref
# ============================================================
async def search_crossref(query: str, max_results: int = 20) -> List[Dict]:
    docs = []
    try:
        async with httpx.AsyncClient(timeout=30.0, headers={"User-Agent": USER_AGENT}) as client:
            r = await client.get(
                "https://api.crossref.org/works",
                params={"query": query, "rows": max_results, "mailto": "weaksignals@example.com"},
            )
            if r.status_code != 200:
                logger.warning(f"[crossref] status {r.status_code}")
                return []
            data = r.json()
            for it in data.get("message", {}).get("items", []):
                titles = it.get("title") or []
                title = titles[0] if titles else ""
                doi = it.get("DOI", "")
                url = f"https://doi.org/{doi}" if doi else ""
                abstract = re.sub(r"<[^>]+>", " ", it.get("abstract", "") or "")[:2000]
                if not title or not url:
                    continue
                docs.append(_mk(url, title, abstract, url, "crossref", "en", 9))
    except Exception as e:
        logger.warning(f"[crossref] failed: {e}")
    return docs


# ============================================================
# 7. Semantic Scholar
# ============================================================
async def search_semanticscholar(query: str, max_results: int = 20) -> List[Dict]:
    docs = []
    try:
        async with httpx.AsyncClient(timeout=30.0, headers={"User-Agent": USER_AGENT}) as client:
            r = await client.get(
                "https://api.semanticscholar.org/graph/v1/paper/search",
                params={"query": query, "limit": max_results, "fields": "title,abstract,year,url"},
            )
            if r.status_code != 200:
                logger.warning(f"[s2] status {r.status_code}")
                return []
            data = r.json()
            for p in data.get("data", []):
                title = p.get("title") or ""
                url = p.get("url") or ""
                abstract = p.get("abstract") or ""
                if not title or not url:
                    continue
                docs.append(_mk(url, title, abstract, url, "semantic_scholar", "en", 8))
    except Exception as e:
        logger.warning(f"[s2] failed: {e}")
    return docs


# ============================================================
# 8. PubMed
# ============================================================
async def search_pubmed(query: str, max_results: int = 20) -> List[Dict]:
    docs = []
    try:
        async with httpx.AsyncClient(timeout=30.0, headers={"User-Agent": USER_AGENT}) as client:
            r = await client.get(
                "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
                params={"db": "pubmed", "term": query, "retmax": max_results, "retmode": "json"},
            )
            if r.status_code != 200:
                logger.warning(f"[pubmed] status {r.status_code}")
                return []
            ids = r.json().get("esearchresult", {}).get("idlist", [])
            if not ids:
                return []
            r2 = await client.get(
                "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
                params={"db": "pubmed", "id": ",".join(ids), "retmode": "json"},
            )
            data = r2.json().get("result", {})
            for pid in ids:
                item = data.get(pid, {})
                title = item.get("title", "")
                if not title:
                    continue
                url = f"https://pubmed.ncbi.nlm.nih.gov/{pid}/"
                docs.append(_mk(url, title, "", url, "pubmed", "en", 10))
    except Exception as e:
        logger.warning(f"[pubmed] failed: {e}")
    return docs


# ============================================================
# 9. Europe PMC
# ============================================================
async def search_europepmc(query: str, max_results: int = 20) -> List[Dict]:
    docs = []
    try:
        async with httpx.AsyncClient(timeout=30.0, headers={"User-Agent": USER_AGENT}) as client:
            r = await client.get(
                "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
                params={"query": query, "format": "json", "pageSize": max_results},
            )
            if r.status_code != 200:
                logger.warning(f"[epmc] status {r.status_code}")
                return []
            data = r.json()
            for it in data.get("resultList", {}).get("result", []):
                title = it.get("title", "")
                url = f"https://europepmc.org/article/{it.get('source','MED')}/{it.get('id','')}"
                abstract = it.get("abstractText", "") or ""
                if not title:
                    continue
                docs.append(_mk(url, title, abstract, url, "europepmc", "en", 9))
    except Exception as e:
        logger.warning(f"[epmc] failed: {e}")
    return docs


# ============================================================
# 10. DOAJ
# ============================================================
async def search_doaj(query: str, max_results: int = 20) -> List[Dict]:
    docs = []
    try:
        async with httpx.AsyncClient(timeout=30.0, headers={"User-Agent": USER_AGENT}) as client:
            r = await client.get(
                "https://doaj.org/api/search/articles/" + query,
                params={"pageSize": max_results},
            )
            if r.status_code != 200:
                logger.warning(f"[doaj] status {r.status_code}")
                return []
            data = r.json()
            for it in data.get("results", []):
                bib = it.get("bibjson", {})
                title = bib.get("title", "")
                links = bib.get("link", [])
                url = links[0].get("url", "") if links else ""
                abstract = bib.get("abstract", "") or ""
                if not title or not url:
                    continue
                docs.append(_mk(url, title, abstract, url, "doaj", "en", 9))
    except Exception as e:
        logger.warning(f"[doaj] failed: {e}")
    return docs


# ============================================================
# 11. Zenodo
# ============================================================
async def search_zenodo(query: str, max_results: int = 20) -> List[Dict]:
    docs = []
    try:
        async with httpx.AsyncClient(timeout=30.0, headers={"User-Agent": USER_AGENT}) as client:
            r = await client.get(
                "https://zenodo.org/api/records",
                params={"q": query, "size": max_results},
            )
            if r.status_code != 200:
                logger.warning(f"[zenodo] status {r.status_code}")
                return []
            data = r.json()
            for it in data.get("hits", {}).get("hits", []):
                meta = it.get("metadata", {})
                title = meta.get("title", "")
                url = it.get("links", {}).get("self_html", "") or it.get("doi_url", "")
                abstract = re.sub(r"<[^>]+>", " ", meta.get("description", "") or "")[:2000]
                if not title or not url:
                    continue
                docs.append(_mk(url, title, abstract, url, "zenodo", "en", 8))
    except Exception as e:
        logger.warning(f"[zenodo] failed: {e}")
    return docs


# ============================================================
# 12. HAL
# ============================================================
async def search_hal(query: str, max_results: int = 20) -> List[Dict]:
    docs = []
    try:
        async with httpx.AsyncClient(timeout=30.0, headers={"User-Agent": USER_AGENT}) as client:
            r = await client.get(
                "https://api.archives-ouvertes.fr/search/",
                params={"q": query, "rows": max_results, "wt": "json", "fl": "title_s,abstract_s,uri_s"},
            )
            if r.status_code != 200:
                logger.warning(f"[hal] status {r.status_code}")
                return []
            data = r.json()
            for it in data.get("response", {}).get("docs", []):
                title = (it.get("title_s") or [""])[0]
                abstract = (it.get("abstract_s") or [""])[0]
                url = it.get("uri_s", "")
                if not title or not url:
                    continue
                docs.append(_mk(url, title, abstract, url, "hal", "fr", 8))
    except Exception as e:
        logger.warning(f"[hal] failed: {e}")
    return docs


# ============================================================
# 13. bioRxiv
# ============================================================
async def search_biorxiv(query: str, max_results: int = 20) -> List[Dict]:
    docs = []
    try:
        async with httpx.AsyncClient(timeout=30.0, headers={"User-Agent": USER_AGENT}) as client:
            r = await client.get(
                "https://api.biorxiv.org/details/biorxiv/2024-01-01/2026-12-31/0",
            )
            if r.status_code != 200:
                return []
            data = r.json()
            q_low = query.lower()
            words = [w for w in re.findall(r"\w+", q_low) if len(w) >= 4]
            for it in data.get("collection", [])[:1000]:
                title = it.get("title", "")
                abstract = it.get("abstract", "") or ""
                text = (title + " " + abstract).lower()
                if not any(w in text for w in words):
                    continue
                doi = it.get("doi", "")
                url = f"https://doi.org/{doi}" if doi else ""
                if not title or not url:
                    continue
                docs.append(_mk(url, title, abstract, url, "biorxiv", "en", 8))
                if len(docs) >= max_results:
                    break
    except Exception as e:
        logger.warning(f"[biorxiv] failed: {e}")
    return docs


# ============================================================
# 14. Hacker News
# ============================================================
async def search_hackernews(query: str, max_results: int = 20) -> List[Dict]:
    docs = []
    try:
        async with httpx.AsyncClient(timeout=30.0, headers={"User-Agent": USER_AGENT}) as client:
            r = await client.get(
                "https://hn.algolia.com/api/v1/search",
                params={"query": query, "hitsPerPage": max_results},
            )
            if r.status_code != 200:
                logger.warning(f"[hn] status {r.status_code}")
                return []
            data = r.json()
            for h in data.get("hits", []):
                title = h.get("title") or h.get("story_title") or ""
                url = h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}"
                if not title or not url:
                    continue
                docs.append(_mk(url, title, "", url, "hackernews", "en", 5))
    except Exception as e:
        logger.warning(f"[hn] failed: {e}")
    return docs


# ============================================================
# 15. GitHub Search
# ============================================================
async def search_github(query: str, max_results: int = 20) -> List[Dict]:
    docs = []
    try:
        async with httpx.AsyncClient(
            timeout=30.0,
            headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"},
        ) as client:
            r = await client.get(
                "https://api.github.com/search/repositories",
                params={"q": query, "sort": "stars", "order": "desc", "per_page": max_results},
            )
            if r.status_code != 200:
                logger.warning(f"[github] status {r.status_code}")
                return []
            data = r.json()
            for it in data.get("items", []):
                title = it.get("full_name") or ""
                url = it.get("html_url") or ""
                desc = it.get("description") or ""
                if not title or not url:
                    continue
                docs.append(_mk(url, title, desc, url, "github", "en", 6))
    except Exception as e:
        logger.warning(f"[github] failed: {e}")
    return docs


# ============================================================
# 16. Stack Exchange
# ============================================================
async def search_stackexchange(query: str, max_results: int = 20) -> List[Dict]:
    docs = []
    try:
        async with httpx.AsyncClient(timeout=30.0, headers={"User-Agent": USER_AGENT}) as client:
            r = await client.get(
                "https://api.stackexchange.com/2.3/search/advanced",
                params={"order": "desc", "sort": "relevance", "q": query, "site": "stackoverflow", "pagesize": max_results},
            )
            if r.status_code != 200:
                logger.warning(f"[stack] status {r.status_code}")
                return []
            data = r.json()
            for it in data.get("items", []):
                title = it.get("title", "")
                url = it.get("link", "")
                if not title or not url:
                    continue
                docs.append(_mk(url, title, "", url, "stackexchange", "en", 6))
    except Exception as e:
        logger.warning(f"[stack] failed: {e}")
    return docs


# ============================================================
# 17. Reddit
# ============================================================
async def search_reddit(query: str, max_results: int = 20) -> List[Dict]:
    docs = []
    try:
        async with httpx.AsyncClient(timeout=30.0, headers={"User-Agent": USER_AGENT}) as client:
            r = await client.get(
                "https://www.reddit.com/search.json",
                params={"q": query, "limit": max_results, "sort": "relevance"},
            )
            if r.status_code != 200:
                logger.warning(f"[reddit] status {r.status_code}")
                return []
            data = r.json()
            for child in data.get("data", {}).get("children", []):
                d = child.get("data", {})
                title = d.get("title", "")
                url = "https://reddit.com" + d.get("permalink", "")
                if not title or not url:
                    continue
                docs.append(_mk(url, title, d.get("selftext", "")[:2000], url, "reddit", "en", 4))
    except Exception as e:
        logger.warning(f"[reddit] failed: {e}")
    return docs


# ============================================================
# 18. Dev.to
# ============================================================
async def search_devto(query: str, max_results: int = 20) -> List[Dict]:
    docs = []
    try:
        async with httpx.AsyncClient(timeout=30.0, headers={"User-Agent": USER_AGENT}) as client:
            r = await client.get(
                "https://dev.to/api/articles",
                params={"tag": query, "per_page": max_results},
            )
            if r.status_code != 200:
                logger.warning(f"[devto] status {r.status_code}")
                return []
            data = r.json()
            for it in data:
                title = it.get("title", "")
                url = it.get("url", "")
                desc = it.get("description", "") or ""
                if not title or not url:
                    continue
                docs.append(_mk(url, title, desc, url, "devto", "en", 5))
    except Exception as e:
        logger.warning(f"[devto] failed: {e}")
    return docs


# ============================================================
# 19. Spaceflight News
# ============================================================
async def search_spaceflight(query: str, max_results: int = 20) -> List[Dict]:
    docs = []
    try:
        async with httpx.AsyncClient(timeout=30.0, headers={"User-Agent": USER_AGENT}) as client:
            r = await client.get(
                "https://api.spaceflightnewsapi.net/v4/articles/",
                params={"search": query, "limit": max_results},
            )
            if r.status_code != 200:
                logger.warning(f"[spaceflight] status {r.status_code}")
                return []
            data = r.json()
            for it in data.get("results", []):
                title = it.get("title", "")
                url = it.get("url", "")
                summary = it.get("summary", "") or ""
                if not title or not url:
                    continue
                docs.append(_mk(url, title, summary, url, "spaceflight", "en", 6))
    except Exception as e:
        logger.warning(f"[spaceflight] failed: {e}")
    return docs


# ============================================================
# 20. Habr (RSS best daily)
# ============================================================
async def search_habr(query: str, max_results: int = 20) -> List[Dict]:
    docs = []
    try:
        import feedparser
        async with httpx.AsyncClient(timeout=30.0, headers={"User-Agent": USER_AGENT}, follow_redirects=True) as client:
            r = await client.get("https://habr.com/ru/rss/best/daily/")
            if r.status_code != 200:
                logger.warning(f"[habr] status {r.status_code}")
                return []
            feed = feedparser.parse(r.text)
            q_low = query.lower()
            words = [w for w in re.findall(r"\w+", q_low) if len(w) >= 4]
            for entry in feed.entries[:300]:
                title = (entry.get("title") or "").strip()
                summary = re.sub(r"<[^>]+>", " ", entry.get("summary", "") or "")
                text = (title + " " + summary).lower()
                if not any(w in text for w in words):
                    continue
                url = entry.get("link", "")
                if not url or not title:
                    continue
                docs.append(_mk(url, title, summary, url, "habr", "ru", 6))
                if len(docs) >= max_results:
                    break
    except Exception as e:
        logger.warning(f"[habr] failed: {e}")
    return docs


# ============================================================
# 21. arXiv (обёртка)
# ============================================================
async def search_arxiv_multi(query: str, max_results: int = 20) -> List[Dict]:
    docs = []
    try:
        from src.sources.arxiv import search_arxiv
        arxiv_docs = await search_arxiv(query, max_results=max_results) or []
        for d in arxiv_docs:
            docs.append(_mk(
                d.get("doc_id") or d.get("url") or "",
                d.get("title", ""),
                d.get("abstract", ""),
                d.get("url", ""),
                "arxiv.org",
                "en",
                9,
            ))
    except Exception as e:
        logger.warning(f"[arxiv] failed: {e}")
    return docs


# ============================================================
# Общая функция — принимает готовые query_ru и query_en
# ============================================================
async def search_all_sources(query_ru: str, query_en: str, max_per_source: int = 20) -> List[Dict]:
    """
    Принимает готовые запросы — не переводит.
    query_ru — для русскоязычных источников.
    query_en — для англоязычных.
    """
    logger.info(f"Multi-search: ru='{query_ru}', en='{query_en}', max_per_source={max_per_source}")

    tasks_ru = [
        asyncio.create_task(search_duckduckgo(query_ru, max_per_source)),
        asyncio.create_task(search_startpage(query_ru, max_per_source)),
        asyncio.create_task(search_mojeek(query_ru, max_per_source)),
        asyncio.create_task(search_marginalia(query_ru, max_per_source)),
        asyncio.create_task(search_habr(query_ru, max_per_source)),
    ]

    tasks_en = [
        asyncio.create_task(search_arxiv_multi(query_en, max_per_source)),
        asyncio.create_task(search_openalex(query_en, max_per_source)),
        asyncio.create_task(search_crossref(query_en, max_per_source)),
        asyncio.create_task(search_pubmed(query_en, max_per_source)),
        asyncio.create_task(search_europepmc(query_en, max_per_source)),
        asyncio.create_task(search_doaj(query_en, max_per_source)),
        asyncio.create_task(search_semanticscholar(query_en, max_per_source)),
        asyncio.create_task(search_zenodo(query_en, max_per_source)),
        asyncio.create_task(search_hal(query_en, max_per_source)),
        asyncio.create_task(search_biorxiv(query_en, max_per_source)),
        asyncio.create_task(search_hackernews(query_en, max_per_source)),
        asyncio.create_task(search_github(query_en, max_per_source)),
        asyncio.create_task(search_stackexchange(query_en, max_per_source)),
        asyncio.create_task(search_reddit(query_en, max_per_source)),
        asyncio.create_task(search_devto(query_en, max_per_source)),
        asyncio.create_task(search_spaceflight(query_en, max_per_source)),
    ]

    # Если запрос уже на английском — не дублируем русские
    if not _is_cyrillic(query_ru):
        tasks_ru = []
        tasks_en.append(asyncio.create_task(search_duckduckgo(query_en, max_per_source)))

    results = await asyncio.gather(*(tasks_ru + tasks_en), return_exceptions=True)

    seen = set()
    unique: List[Dict] = []
    for res in results:
        if isinstance(res, Exception):
            logger.warning(f"source failed: {res}")
            continue
        for d in res:
            key = d.get("doc_id") or d.get("url")
            if not key or key in seen:
                continue
            seen.add(key)
            unique.append(d)

    unique.sort(key=lambda x: x.get("trust_level", 5), reverse=True)
    logger.info(f"Multi-search total unique: {len(unique)}")
    return unique