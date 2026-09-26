import asyncio
from loguru import logger

from src.sources.orchestrator import get_orchestrator_with_rss


async def main():
    orch = get_orchestrator_with_rss()
    logger.info(f"Orchestrator ready: {len(orch.parsers)} RSS parsers")

    docs = await orch.search_all(
        query="AI",
        max_results_per_source=5,
        max_concurrent=5,
    )

    logger.info(f"\n=== TOTAL: {len(docs)} documents ===")
    for d in docs[:10]:
        logger.info(f"[{d.region}] {d.title[:80]} ({d.source_domain})")
        logger.info(f"  published: {d.published_at}")
        logger.info(f"  url: {d.url[:80]}")


if __name__ == "__main__":
    asyncio.run(main())