import requests
from loguru import logger

API = "http://localhost:8000/api/search"
QUERY = "слабые сигналы"


def main():
    print(f"Запрос: {QUERY}")
    print("=" * 80)

    r = requests.post(API, json={"query": QUERY, "limit": 15}, timeout=900)
    d = r.json()

    print(f"Кандидатов: {d.get('candidates_found', 0)}")
    print(f"Сигналов в ТОП: {len(d.get('signals', []))}")
    print()

    for sig in d.get("signals", []):
        print(f"  {sig.get('score', 0):.2f} {sig.get('technology', '')[:70]}")
        print(f"       why: {sig.get('why_weak_signal', '')[:150]}")
        print()


if __name__ == "__main__":
    main()