import time
import requests
import json
from loguru import logger

API = "http://localhost:8000/api/search"

# ============================================================
# ТЕСТОВЫЕ ЗАПРОСЫ — 100 штук
# ============================================================

TESTS = {
    "WEAK (реальные слабые сигналы)": {
        "expected_min_signals": 15,
        "expected_max_forbidden": 3,
        "queries": [
            "нейроморфные вычисления",
            "квантовые вычисления",
            "оптические процессоры",
            "федеративное обучение",
            "конфиденциальные вычисления",
            "агентные ИИ-системы",
            "роботы-инспекторы",
            "децентрализованный инференс",
            "спинтроника",
            "мемристоры",
            "фотоника для AI",
            "нейроморфные чипы",
            "квантовое сжатие",
            "федеративное обучение для AML",
            "ончейн-скоринг",
            "орбитальные дата-центры",
            "малые модульные реакторы",
            "телеоперационные данные",
            "дехтерные кисти",
            "тактильные VLA-модели",
        ],
    },
    "NEGATIVE (зрелые технологии)": {
        "expected_min_signals": 0,
        "expected_max_forbidden": 3,
        "queries": [
            "Kubernetes",
            "Docker",
            "PostgreSQL",
            "Redis",
            "TensorFlow",
            "GPT-4",
            "Transformer architecture",
            "CRISPR-Cas9",
            "mRNA vaccines",
            "AlphaFold",
            "SWIFT payments",
            "Visa payment network",
            "AWS EC2",
            "Snowflake",
            "Databricks",
            "React.js",
            "PyTorch",
            "MLflow",
            "Kubeflow",
            "Prometheus",
        ],
    },
    "JUNK (псевдонаука и философия)": {
        "expected_min_signals": 0,
        "expected_max_forbidden": 1,
        "queries": [
            "торсионные поля",
            "биополе человека",
            "квантовый ум",
            "гомеопатия",
            "астрология",
            "нумерология",
            "телепатия",
            "экстрасенсорика",
            "сфиральные нейроны",
            "гравитационные экраны",
            "вечный двигатель",
            "холодный синтез",
            "антигравитация",
            "машина времени",
            "теория сознания",
            "природа реальности",
            "смысл жизни",
            "метафизика",
            "диалектика",
            "онтология",
        ],
    },
    "HYPE (маркетинговый хайп)": {
        "expected_min_signals": 0,
        "expected_max_forbidden": 1,
        "queries": [
            "Metaverse",
            "Web3",
            "NFT marketplace",
            "DAO governance",
            "AGI-2025",
            "Superintelligence",
            "Singularity",
            "Consciousness upload",
            "Digital immortality",
            "Brain-computer interface",
            "Industry 4.0",
            "Smart cities",
            "Digital transformation",
            "Internet of Things",
            "Cloud computing",
            "Big Data",
            "Machine learning",
            "Quantum supremacy claims",
            "AI girlfriend apps",
            "ChatGPT killer apps",
        ],
    },
    "MIXED (реальные запросы жюри)": {
        "expected_min_signals": 12,
        "expected_max_forbidden": 2,
        "queries": [
            "технологии в искусственном интеллекте",
            "перспективные решения в финтехе",
            "слабые сигналы в кибербезопасности",
            "новые технологии в робототехнике",
            "инновации в биотехе",
            "перспективы квантовых вычислений",
            "слабые сигналы в энергетике",
            "новые материалы",
            "edge computing",
            "агентные системы",
            "приватность и безопасность",
            "децентрализованные системы",
            "новые методы обучения",
            "инфраструктура для AI",
            "финтех-инновации",
            "биотех-стартапы",
            "роботы в промышленности",
            "квантовые сенсоры",
            "нейроинтерфейсы",
            "экзотические вычисления",
        ],
    },
}

# Запрещённые ключевые слова (junk + хайп + negative)
FORBIDDEN = [
    # junk
    "сфираль", "торсион", "биополе", "гомеопат", "астролог",
    "нумеролог", "телепат", "экстрасенс", "квантовый ум",
    "квантовое сознание", "гравитационн", "вечный двигатель",
    "холодный синтез", "антигравитац", "машина времени",
    # хайп
    "metaverse", "web3", "nft", "dao", "agi-2025",
    "superintelligence", "singularity", "consciousness upload",
    "digital immortality", "smart cities", "industry 4.0",
    # negative
    "kubernetes", "docker", "gpt-4", "tensorflow", "pytorch",
    "postgresql", "redis", "kafka", "crispr-cas9", "mrna vaccines",
]


def check_signal(sig):
    problems = []
    tech = sig.get("technology", "")
    if not tech:
        problems.append("нет technology")
    sources = sig.get("sources", [])
    if not sources:
        problems.append("нет sources")
    if not sig.get("why_weak_signal"):
        problems.append("нет why_weak_signal")
    if sig.get("score", 0) < 0.6:
        problems.append(f"score низкий: {sig['score']}")
    return problems


def check_forbidden(signals):
    found = []
    for sig in signals:
        tech = (sig.get("technology") or "").lower()
        for kw in FORBIDDEN:
            if kw in tech:
                found.append(f"{sig['technology'][:50]} (совпало: {kw})")
    return found


def run_query(query, expected_min, expected_max_forbidden):
    try:
        r = requests.post(API, json={"query": query, "limit": 15}, timeout=900)
    except Exception as e:
        return {"query": query, "error": str(e)}

    if r.status_code != 200:
        return {"query": query, "error": f"status {r.status_code}"}

    d = r.json()
    signals = d.get("signals", [])
    forbidden = check_forbidden(signals)
    problems = []
    for sig in signals:
        p = check_signal(sig)
        if p:
            problems.append(f"{sig.get('technology', '')[:40]}: {', '.join(p)}")

    ok = (
        len(signals) >= expected_min
        and len(forbidden) <= expected_max_forbidden
    )

    return {
        "query": query,
        "count": len(signals),
        "forbidden": forbidden,
        "problems": problems,
        "ok": ok,
        "candidates": d.get("candidates_found", 0),
    }


def main():
    print()
    print("╔" + "═" * 78 + "╗")
    print("║" + "  ДЕМО-ТЕСТ СИСТЕМЫ WEAK SIGNALS (100 запросов)".center(78) + "║")
    print("╚" + "═" * 78 + "╝")

    total_queries = 0
    total_ok = 0
    total_forbidden = 0
    total_problems = 0

    for category, cfg in TESTS.items():
        print()
        print("=" * 80)
        print(f"  {category}")
        print(f"  Ожидаем: минимум {cfg['expected_min_signals']} сигналов, "
              f"максимум {cfg['expected_max_forbidden']} запрещённых")
        print("=" * 80)

        cat_ok = 0
        cat_total = 0

        for query in cfg["queries"]:
            cat_total += 1
            total_queries += 1
            res = run_query(query, cfg["expected_min_signals"], cfg["expected_max_forbidden"])

            if "error" in res:
                print(f"  ❌ {query[:50]:50} ОШИБКА: {res['error'][:40]}")
                continue

            status = "✅" if res["ok"] else "⚠️"
            if res["ok"]:
                cat_ok += 1
                total_ok += 1

            print(f"  {status} {query[:45]:45} signals:{res['count']:>2} "
                  f"forbidden:{len(res['forbidden']):>2} "
                  f"candidates:{res['candidates']:>3}")

            if res["forbidden"]:
                total_forbidden += len(res["forbidden"])
                for f in res["forbidden"]:
                    print(f"       └─ ЗАПРЕЩЁН: {f}")

            if res["problems"]:
                total_problems += len(res["problems"])
                for p in res["problems"][:3]:
                    print(f"       └─ {p[:100]}")

        print(f"  --- {cat_ok}/{cat_total} ({100*cat_ok/cat_total:.0f}%) ---")

    print()
    print("╔" + "═" * 78 + "╗")
    print("║" + "  ИТОГИ".center(78) + "║")
    print("╚" + "═" * 78 + "╝")
    print(f"  Всего запросов:       {total_queries}")
    print(f"  Прошло:               {total_ok} ({100*total_ok/total_queries:.1f}%)")
    print(f"  Запрещённых в выдаче: {total_forbidden}")
    print(f"  Проблемных сигналов:  {total_problems}")
    print()


if __name__ == "__main__":
    main()