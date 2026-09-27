import time
import requests
from loguru import logger

API = "http://localhost:8000/api/search"

# Запросы, которые РЕАЛЬНО будет вводить Газпромбанк
QUERIES = [
    # Финтех
    "инновации в эквайринге",
    "новые платёжные системы",
    "цифровой рубль",
    "Open Banking в России",
    "BNPL и рассрочки",
    "трансграничные платежи",
    # Кибербезопасность
    "новые системы защиты банков",
    "защита от дипфейков в банкинге",
    "биометрическая аутентификация",
    "постквантовая криптография в финансах",
    "мошенничество с ИИ",
    # ИИ в банках
    "ИИ в кредитном скоринге",
    "генеративный ИИ в банках",
    "агентные системы в финтехе",
    "объяснимый ИИ в банках",
    "ИИ в управлении рисками",
    # Инфраструктура
    "импортозамещение в банках",
    "суверенные облака для банков",
    "отказоустойчивость банковских систем",
    "Open Source в банках",
    # Регуляторика
    "регулирование ИИ в финансах",
    "Open API в банках",
    "стандарты ISO 20022",
    "RegTech",
    # Общие
    "технологии в финансовом секторе",
    "инновации в банках",
    "перспективные технологии в финтехе",
    "слабые сигналы в банкинге",
]


def run_query(query):
    print()
    print("=" * 80)
    print(f"  ЗАПРОС: {query}")
    print("=" * 80)

    t0 = time.time()
    try:
        r = requests.post(API, json={"query": query, "limit": 15}, timeout=900)
    except Exception as e:
        print(f"  ❌ ОШИБКА: {e}")
        return {"query": query, "count": 0, "error": str(e)}

    elapsed = time.time() - t0
    if r.status_code != 200:
        print(f"  ❌ Status {r.status_code}")
        return {"query": query, "count": 0, "error": f"status {r.status_code}"}

    d = r.json()
    signals = d.get("signals", [])
    print(f"  Время: {elapsed:.1f} сек")
    print(f"  Кандидатов: {d.get('candidates_found', 0)}")
    print(f"  Сигналов в ТОП: {len(signals)}")
    print()

    for i, sig in enumerate(signals[:15], 1):
        tech = sig.get("technology", "")[:60]
        score = sig.get("score", 0)
        srcs = sig.get("sources_count", 0)
        print(f"    [{i:2}] {score:.2f} (src:{srcs}) {tech}")

    return {"query": query, "count": len(signals), "elapsed": elapsed}


def main():
    print()
    print("╔" + "═" * 78 + "╗")
    print("║" + "  ТЕСТ НА ЗАПРОСАХ ГАЗПРОМБАНКА".center(78) + "║")
    print("╚" + "═" * 78 + "╝")

    results = []
    for q in QUERIES:
        res = run_query(q)
        results.append(res)

    print()
    print("╔" + "═" * 78 + "╗")
    print("║" + "  ИТОГИ".center(78) + "║")
    print("╚" + "═" * 78 + "╝")
    print()
    print(f"  {'ЗАПРОС':<45} {'СИГНАЛОВ':>10} {'ВРЕМЯ':>10}")
    print("  " + "-" * 78)
    for r in results:
        print(f"  {r['query'][:45]:<45} {r['count']:>10} {r.get('elapsed', 0):>9.1f}s")

    # Статистика
    counts = [r["count"] for r in results if "error" not in r]
    if counts:
        print()
        print(f"  Среднее: {sum(counts)/len(counts):.1f}")
        print(f"  Минимум: {min(counts)}")
        print(f"  Максимум: {max(counts)}")
        print(f"  Запросов с ≥ 12 сигналов: {len([c for c in counts if c >= 12])}/{len(counts)}")
        print(f"  Запросов с ≥ 8 сигналов:  {len([c for c in counts if c >= 8])}/{len(counts)}")
        print(f"  Запросов с < 5 сигналов:  {len([c for c in counts if c < 5])}/{len(counts)}")


if __name__ == "__main__":
    main()