import json
import re
import time
import hashlib
from typing import List, Dict, Optional
from loguru import logger

from src.db.connection import SessionLocal
from src.db.models import WeakSignal, NegativeSignal, RawWeakSignal, RawNegativeSignal, RawJunkSignal
from src.llm.client import get_llm


# ============ ПРОМПТЫ ============

WEAK_SYSTEM = """Ты — аналитик, который создаёт примеры «слабых сигналов» в научно-технологических отраслях.

Слабый сигнал — это ранний, разрозненный, неочевидный индикатор зарождающейся технологии.
Это НЕ массовая технология, НЕ зрелый тренд, НЕ маркетинговый хайп, НЕ отраслевой стандарт.

Признаки слабого сигнала:
- ранняя стадия (исследование / прототип / пилот)
- мало игроков (стартапы, единичные компании)
- нишевое покрытие (профильные издания, а не массовые СМИ)
- конкретная технология, а не общее направление

Отвечай строго JSON-массивом без пояснений и без markdown."""

WEAK_PROMPT = """Вот эталон слабого сигнала:
Название: {name}
Область: {area}
Компании: {companies}
Почему слабый: {why_weak_signal}
Стадия: {stage}
Тренд: {trend}

Сгенерируй {n} НОВЫХ слабых сигналов по этому паттерну.
Требования:
- каждый — конкретная технология, не общее направление
- ранняя стадия, мало игроков
- НЕ копируй эталон, придумай другие названия и компании
- разные отрасли и формулировки

Формат ответа — JSON-массив:
[
  {{"name": "...", "area": "...", "companies": "...", "why_weak_signal": "...", "stage": "...", "trend": "..."}}
]

Только JSON, без markdown."""


NEG_SYSTEM = """Ты — аналитик, который создаёт примеры «зрелых технологий» (не слабых сигналов).

Зрелая технология — это массовая, устоявшаяся технология с сформированным рынком.
Это НЕ слабый сигнал.

Признаки зрелой технологии:
- массовое внедрение
- много игроков и лидеров рынка
- отраслевой стандарт или де-факто стандарт
- широкая база пользователей
- стадия: зрелость

Отвечай строго JSON-массивом без пояснений и без markdown."""

NEG_PROMPT = """Вот эталон зрелой технологии:
Название: {name}

Сгенерируй {n} НОВЫХ зрелых технологий по этому паттерну.
Требования:
- массовое внедрение, сформированный рынок
- лидеры рынка, отраслевой стандарт
- НЕ копируй эталон
- разные отрасли

Формат ответа — JSON-массив:
[
  {{"name": "...", "description": "..."}}
]

Только JSON, без markdown."""


JUNK_CATEGORIES = [
    ("philosophy", "философские концепции: теории сознания, природа реальности, смысл жизни, онтология, метафизика", 200),
    ("pseudoscience", "псевдонаука: торсионные поля, биополе, квантовый ум, телепатия, экстрасенсорика, психотроника", 200),
    ("hype", "маркетинговый хайп: Metaverse, Web3, AI girlfriend apps, Superintelligence claims, AGI-2025, сингулярность", 150),
    ("reviews", "обзоры без конкретной технологии: 'Обзор литературы по X', 'Систематический обзор Y', 'Мета-анализ Z'", 100),
    ("pseudo_tech", "псевдо-технологии: вечный двигатель, холодный синтез, свободная энергия, машина времени, антигравитация", 100),
    ("marketing", "маркетинговые клише: 'Революционная платформа', 'Убийца ChatGPT', 'Прорыв в AI', 'Уникальное решение'", 50),
]

JUNK_SYSTEM = "Ты генератор примеров мусора. Отвечай только JSON-массивом без markdown."

JUNK_PROMPT = """Сгенерируй {n} примеров {category}.
Формат: JSON-массив объектов {{"name": "...", "description": "..."}}.
Только JSON, без markdown и без переносов строк внутри строк."""


# ============ ПАРСИНГ ============

def _safe_parse_json_array(raw: str) -> List[Dict]:
    """Устойчивый парсинг JSON-массива от LLM."""
    if not raw:
        return []
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?", "", raw).strip()
        raw = re.sub(r"```$", "", raw).strip()
    m = re.search(r"\[.*\]", raw, re.DOTALL)
    if not m:
        return []
    text = m.group(0)
    text = re.sub(r"[\x00-\x1f\x7f]", " ", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        text = re.sub(r",\s*]", "]", text)
        text = re.sub(r",\s*}", "}", text)
        try:
            return json.loads(text)
        except Exception:
            return []


def _hash(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


# ============ АУГМЕНТАЦИЯ WEAK ============

def augment_weak(n_per_golden: int = 10):
    db = SessionLocal()
    llm = get_llm()
    saved = 0
    try:
        golden = db.query(WeakSignal).all()
        logger.info(f"[weak] golden: {len(golden)}, target: {len(golden) * n_per_golden}")

        existing_hashes = set()
        for item in db.query(RawWeakSignal).all():
            existing_hashes.add(_hash(item.name))

        for i, g in enumerate(golden, 1):
            prompt = WEAK_PROMPT.format(
                name=g.name,
                area=g.area or "",
                companies=g.companies or "",
                why_weak_signal=(g.why_weak_signal or "")[:500],
                stage=g.stage or "",
                trend=g.trend or "",
                n=n_per_golden,
            )
            try:
                raw = llm.chat(WEAK_SYSTEM, prompt)
                items = _safe_parse_json_array(raw)
                batch = 0
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    name = (item.get("name") or "").strip()
                    if not name or len(name) < 15:
                        continue
                    h = _hash(name)
                    if h in existing_hashes:
                        continue
                    existing_hashes.add(h)
                    db.add(RawWeakSignal(
                        name=name[:500],
                        description=(item.get("why_weak_signal") or "")[:2000],
                        source="augmented",
                        url=None,
                        year=2026,
                    ))
                    batch += 1
                    saved += 1
                db.commit()
                logger.info(f"[weak] {i}/{len(golden)}: +{batch}, total {saved}")
            except Exception as e:
                logger.warning(f"[weak] {i}: {e}")
                db.rollback()
                continue
            time.sleep(0.5)
    finally:
        db.close()
    logger.info(f"[weak] DONE: {saved}")


# ============ АУГМЕНТАЦИЯ NEGATIVE ============

def augment_negative(n_per_golden: int = 3):
    db = SessionLocal()
    llm = get_llm()
    saved = 0
    try:
        golden = db.query(NegativeSignal).all()
        logger.info(f"[negative] golden: {len(golden)}, target: {len(golden) * n_per_golden}")

        existing_hashes = set()
        for item in db.query(RawNegativeSignal).all():
            existing_hashes.add(_hash(item.name))

        for i, g in enumerate(golden, 1):
            prompt = NEG_PROMPT.format(name=g.name, n=n_per_golden)
            try:
                raw = llm.chat(NEG_SYSTEM, prompt)
                items = _safe_parse_json_array(raw)
                batch = 0
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    name = (item.get("name") or "").strip()
                    if not name or len(name) < 5:
                        continue
                    h = _hash(name)
                    if h in existing_hashes:
                        continue
                    existing_hashes.add(h)
                    db.add(RawNegativeSignal(
                        name=name[:500],
                        description=(item.get("description") or "Зрелая технология")[:2000],
                        source="augmented",
                        url=None,
                        year=2020,
                    ))
                    batch += 1
                    saved += 1
                db.commit()
                logger.info(f"[negative] {i}/{len(golden)}: +{batch}, total {saved}")
            except Exception as e:
                logger.warning(f"[negative] {i}: {e}")
                db.rollback()
                continue
            time.sleep(0.5)
    finally:
        db.close()
    logger.info(f"[negative] DONE: {saved}")


# ============ ГЕНЕРАЦИЯ JUNK ============

def generate_junk():
    db = SessionLocal()
    llm = get_llm()
    saved = 0
    try:
        existing_hashes = set()
        for item in db.query(RawJunkSignal).all():
            existing_hashes.add(_hash(item.name))

        for cat, desc, total in JUNK_CATEGORIES:
            logger.info(f"[junk] {cat}: target {total}")
            remaining = total
            batch_size = 50
            while remaining > 0:
                n = min(batch_size, remaining)
                prompt = JUNK_PROMPT.format(n=n, category=desc)
                try:
                    raw = llm.chat(JUNK_SYSTEM, prompt)
                    items = _safe_parse_json_array(raw)
                    batch = 0
                    for item in items:
                        if not isinstance(item, dict):
                            continue
                        name = (item.get("name") or "").strip()
                        if not name:
                            continue
                        h = _hash(name)
                        if h in existing_hashes:
                            continue
                        existing_hashes.add(h)
                        db.add(RawJunkSignal(
                            name=name[:500],
                            description=(item.get("description") or "")[:2000],
                            category=cat,
                        ))
                        batch += 1
                        saved += 1
                    db.commit()
                    logger.info(f"[junk] {cat}: +{batch}, total {saved}")
                    remaining -= n
                except Exception as e:
                    logger.warning(f"[junk] {cat}: {e}")
                    db.rollback()
                    break
                time.sleep(0.5)
    finally:
        db.close()
    logger.info(f"[junk] DONE: {saved}")


# ============ MAIN ============

def main():
    logger.info("=" * 60)
    logger.info("AUGMENTATION START")
    logger.info("=" * 60)

    logger.info("--- WEAK (10x from 100 golden = 1000 new) ---")
    augment_weak(10)

    logger.info("--- NEGATIVE (3x from 250 golden = 750 new) ---")
    augment_negative(3)

    logger.info("--- JUNK (800 total) ---")
    generate_junk()

    logger.info("=" * 60)
    logger.info("AUGMENTATION DONE")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()