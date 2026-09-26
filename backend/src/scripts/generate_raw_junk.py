import json
import re
from loguru import logger
from src.db.connection import SessionLocal
from src.db.models import RawJunkSignal
from src.llm.client import get_llm

CATEGORIES = {
    "philosophy": "философские концепции, теории сознания, природа реальности, смысл жизни, онтология, метафизика",
    "pseudoscience": "псевдонаучные концепции: торсионные поля, биополе, квантовый ум, телепатия, экстрасенсорика, психотроника",
    "esoteric": "эзотерика: астрология, нумерология, магия, оккультизм, алхимия, спиритизм",
    "hype": "маркетинговый хайп: Metaverse, Web3, AI girlfriend apps, Superintelligence claims, AGI-2025, сингулярность",
    "reviews": "обзоры без конкретной технологии: 'Обзор литературы по X', 'Систематический обзор Y', 'Мета-анализ Z'",
    "pseudo_tech": "псевдо-технологии: вечный двигатель, холодный синтез, свободная энергия, машина времени, антигравитация",
    "marketing": "маркетинговые клише: 'Революционная платформа', 'Убийца ChatGPT', 'Прорыв в AI', 'Уникальное решение'",
    "conspiracy": "конспирология: рептилоиды, плоская земля, химтрейлы, рептилоидные элиты, тайное правительство",
    "ufo": "уфология: НЛО, пришельцы, похищения, зона 51, круги на полях",
    "homeopathy": "гомеопатия и альтернативная медицина: гомеопатические средства, акупунктура без доказательств, уринотерапия",
}

PROMPT_TEMPLATE = """Сгенерируй {n} примеров {category}.
Формат: JSON-массив объектов {{"name": "...", "description": "..."}}.
Только JSON, без пояснений и без markdown. Не используй переносы строк внутри строк."""


def _safe_parse(raw: str):
    """Устойчивый парсинг JSON от LLM."""
    if not raw:
        return []
    # убираем markdown-обёртки
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?", "", raw).strip()
        raw = re.sub(r"```$", "", raw).strip()
    # ищем первый [ ... ]
    m = re.search(r"\[.*\]", raw, re.DOTALL)
    if not m:
        return []
    text = m.group(0)
    # убираем control characters
    text = re.sub(r"[\x00-\x1f\x7f]", " ", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # пробуем починить одинарные кавычки и лишние запятые
        text = re.sub(r",\s*]", "]", text)
        text = re.sub(r",\s*}", "}", text)
        try:
            return json.loads(text)
        except Exception:
            return []


def generate():
    llm = get_llm()
    db = SessionLocal()
    saved = 0
    try:
        for cat, desc in CATEGORIES.items():
            prompt = PROMPT_TEMPLATE.format(n=50, category=desc)
            try:
                raw = llm.chat("Ты генератор примеров мусора. Отвечай только JSON.", prompt)
                items = _safe_parse(raw)
                if not items:
                    logger.warning(f"[junk] {cat}: не удалось распарсить")
                    continue
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    name = (item.get("name") or "").strip()
                    if not name:
                        continue
                    if db.query(RawJunkSignal).filter(RawJunkSignal.name == name).first():
                        continue
                    db.add(RawJunkSignal(
                        name=name[:500],
                        description=(item.get("description") or "")[:2000],
                        category=cat,
                    ))
                    saved += 1
                db.commit()
                logger.info(f"[junk] {cat}: saved {len(items)}")
            except Exception as e:
                logger.warning(f"[junk] {cat}: {e}")
    finally:
        db.close()
    logger.info(f"[junk] total saved: {saved}")


if __name__ == "__main__":
    generate()