from src.features.topic_stats import fetch_topic_stats
from loguru import logger


def main():
    test_queries = [
        "quantum computing",
        "GPT-4",
        "Bitcoin",
        "CRISPR gene editing",
    ]

    for q in test_queries:
        stats = fetch_topic_stats(q)
        logger.info(f"'{q}': total={stats['total']}, recent={stats['recent']}")


if __name__ == "__main__":
    main()