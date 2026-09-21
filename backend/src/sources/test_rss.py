import asyncio
import json
from pathlib import Path

from src.sources.rss import load_rss_sources, fetch_rss
from src.db.repository import save_documents


async def main():
    sources = load_rss_sources()

    all_documents = []
    for source in sources:
        documents = await fetch_rss(source, max_items=5)
        all_documents.extend(documents)

    print(f"\nВсего получено документов: {len(all_documents)}\n")

    for doc in all_documents[:10]:
        print(f"[{doc['region']}] {doc['title'][:80]}")
        print(f"  Источник: {doc['raw']['source_name']}")
        print(f"  Дата: {doc['published_at']}")
        print()

    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "rss_sample.jsonl"

    with output_file.open("w", encoding="utf-8") as f:
        for doc in all_documents:
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")

    print(f"Сохранено в: {output_file}")

    saved = save_documents(all_documents)
    print(f"Сохранено в БД: {saved}")


if __name__ == "__main__":
    asyncio.run(main())