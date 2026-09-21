import asyncio
import json
from pathlib import Path

from src.sources.arxiv import search_arxiv
from src.db.repository import save_documents


async def main():
    documents = await search_arxiv("quantum computing", max_results=10)

    print(f"\nПолучено документов: {len(documents)}\n")
    for doc in documents[:3]:
        print(f"- {doc['title']}")
        print(f"  Авторы: {', '.join(doc['authors'][:3])}")
        print(f"  Дата: {doc['published_at']}")
        print(f"  URL: {doc['url']}")
        print()

    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "arxiv_sample.jsonl"

    with output_file.open("w", encoding="utf-8") as f:
        for doc in documents:
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")

    print(f"Сохранено в: {output_file}")

    saved = save_documents(documents)
    print(f"Сохранено в БД: {saved}")


if __name__ == "__main__":
    asyncio.run(main())