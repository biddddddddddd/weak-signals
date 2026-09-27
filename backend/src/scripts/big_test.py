import time
import requests
from loguru import logger

API = "http://localhost:8000/api/search"

QUERIES = {
    "ФИНТЕХ (14)": [
        "Биометрическая аутентификация",
        "Постквантовая криптография",
        "Open Banking",
        "RegTech",
        "RegTech для автоматизации комплаенса",
        "Цифровой рубль",
        "Программируемые деньги",
        "Агентные системы для автоматизации банковских процессов",
        "Агентные системы в банкинге",
        "Объяснимый ИИ в банкинге",
        "Объяснимый ИИ в кредитном скоринге",
        "Ончейн-скоринг",
        "Ончейн-скоринг для кредитования",
        "Встроенные финансы",
    ],
    "МЕДТЕХ (14)": [
        "Биопечать",
        "Биофабрикатор",
        "Передовая робототехника в медицине",
        "Квантовые точки",
        "Наносенсоры",
        "CRISPR",
        "Редактирование генома",
        "Телемедицина",
        "Удалённый мониторинг пациентов",
        "Смарт-импланты",
        "Нейроинтерфейсы",
        "Биоразлагаемая электроника",
        "Органоиды",
        "Носимые медицинские устройства",
    ],
    "IT (14)": [
        "Агентный ИИ",
        "MCP протокол",
        "Федеративное обучение",
        "Дифференциальная приватность",
        "Квантовые вычисления",
        "Edge AI",
        "Объяснимый ИИ",
        "Синтетические данные",
        "ИИ-чипы",
        "Нейроморфные чипы",
        "Постквантовая криптография",
        "Децентрализованный инференс",
        "Оптические процессоры",
        "Мемристоры",
    ],
}


def run_query(query, category):
    t0 = time.time()
    try:
        r = requests.post(API, json={"query": query, "limit": 15}, timeout=900)
    except Exception as e:
        return {"query": query, "count": 0, "error": str(e), "category": category}

    elapsed = time.time() - t0
    if r.status_code != 200:
        return {"query": query, "count": 0, "error": f"status {r.status_code}", "category": category}

    d = r.json()
    signals = d.get("signals", [])
    return {
        "query": query,
        "query_en": d.get("query_en", ""),
        "count": len(signals),
        "candidates": d.get("candidates_found", 0),
        "elapsed": elapsed,
        "category": category,
        "signals": signals[:5],
    }


def main():
    print()
    print("╔" + "═" * 78 + "╗")
    print("║" + "  БОЛЬШОЙ ТЕСТ (42 запроса)".center(78) + "║")
    print("╚" + "═" * 78 + "╝")

    all_results = []

    for category, queries in QUERIES.items():
        print()
        print("=" * 80)
        print(f"  {category}")
        print("=" * 80)

        cat_counts = []
        for q in queries:
            res = run_query(q, category)
            all_results.append(res)

            if "error" in res:
                print(f"  ❌ {q[:45]:45} ОШИБКА: {res['error'][:30]}")
                continue

            count = res["count"]
            cat_counts.append(count)
            status = "✅" if count >= 5 else ("⚠️" if count >= 2 else "❌")
            print(f"  {status} {q[:45]:45} signals: {count:2}  candidates: {res['candidates']:3}  en: {res['query_en'][:30]}")

            for sig in res["signals"]:
                print(f"       - {sig.get('score', 0):.2f} {sig.get('technology', '')[:65]}")

        if cat_counts:
            print(f"  --- среднее: {sum(cat_counts)/len(cat_counts):.1f}, "
                  f"макс: {max(cat_counts)}, мин: {min(cat_counts)} ---")

    print()
    print("╔" + "═" * 78 + "╗")
    print("║" + "  ИТОГИ".center(78) + "║")
    print("╚" + "═" * 78 + "╝")
    print()
    print(f"  {'ЗАПРОС':<45} {'СИГНАЛОВ':>10} {'КАНДИДАТОВ':>12}")
    print("  " + "-" * 78)
    for r in all_results:
        if "error" in r:
            print(f"  {r['query'][:45]:<45} {'ERR':>10}")
        else:
            print(f"  {r['query'][:45]:<45} {r['count']:>10} {r['candidates']:>12}")

    counts = [r["count"] for r in all_results if "error" not in r]
    if counts:
        print()
        print(f"  Всего запросов:          {len(counts)}")
        print(f"  Среднее сигналов:        {sum(counts)/len(counts):.1f}")
        print(f"  Максимум:                {max(counts)}")
        print(f"  Минимум:                 {min(counts)}")
        print(f"  Запросов с ≥ 5:          {len([c for c in counts if c >= 5])}/{len(counts)}")
        print(f"  Запросов с ≥ 2:          {len([c for c in counts if c >= 2])}/{len(counts)}")
        print(f"  Запросов с 0:            {len([c for c in counts if c == 0])}/{len(counts)}")


if __name__ == "__main__":
    main()