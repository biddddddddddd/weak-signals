import asyncio
import json
from pathlib import Path

from loguru import logger

from src.sources.rss_parser import RSSParser


CONFIG_PATH = Path("config/rss_sources.json")


def load_sources():
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)["sources"]


async def main():
    sources = load_sources()
    logger.info(f"Loaded {len(sources)} sources")

    test_query = "quantum computing"
    logger.info(f"Test query: '{test_query}'")

    total = 0
    per_source = {}

    for src in sources:
        parser = RSSParser(
            source_id=src["name"],
            source_domain=src["domain"],
            region=src["region"],
            language=src["language"],
            trust_level=str(src["trust"]),
            feed_url=src["url"],
            source_type=src.get("source_type", "media"),
        )
        docs = await parser.search(test_query, max_results=10)
        per_source[src["name"]] = len(docs)
        total += len(docs)

        if docs:
            logger.info(f"[{src['name']}] {len(docs)} matched")
            for d in docs[:3]:
                logger.info(f"    {d.title[:90]}")
        else:
            logger.info(f"[{src['name']}] 0 matched")

    logger.info("=" * 60)
    logger.info(f"TOTAL matched for '{test_query}': {total}")
    logger.info("=" * 60)

    # Показать топ и мёртвых
    zero = [k for k, v in per_source.items() if v == 0]
    logger.info(f"Zero-match sources: {len(zero)}/{len(sources)}")
    for z in zero:
        logger.info(f"    {z}")


if __name__ == "__main__":
    asyncio.run(main())