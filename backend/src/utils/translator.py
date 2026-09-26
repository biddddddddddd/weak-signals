import re
import json
import time
from pathlib import Path
from typing import Optional, Dict
from loguru import logger

try:
    from deep_translator import GoogleTranslator
    _TRANSLATOR_AVAILABLE = True
except ImportError:
    _TRANSLATOR_AVAILABLE = False
    logger.warning("deep-translator not installed, translations disabled")


CACHE_PATH = Path("data/cache/translations.json")
MANUAL_PATH = Path("data/seeds/translations.json")
_manual_dict: Optional[Dict[str, str]] = None


def _load_manual() -> Dict[str, str]:
    """Загружает локальный словарь переводов (ручной)."""
    global _manual_dict
    if _manual_dict is None:
        if MANUAL_PATH.exists():
            with MANUAL_PATH.open("r", encoding="utf-8") as f:
                _manual_dict = json.load(f)
            logger.info(f"Manual translations loaded: {len(_manual_dict)} entries")
        else:
            _manual_dict = {}
            logger.warning(f"Manual translations file not found: {MANUAL_PATH}")
    return _manual_dict


def _load_cache() -> Dict[str, str]:
    if CACHE_PATH.exists():
        with CACHE_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_cache(cache: Dict[str, str]):
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CACHE_PATH.open("w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def _has_cyrillic(text: str) -> bool:
    return bool(re.search(r"[а-яё]", text, re.IGNORECASE))


def translate_to_english(text: str) -> str:
    """
    Приоритет:
    1. Локальный словарь (data/seeds/translations.json)
    2. Кэш (data/cache/translations.json)
    3. Google Translate (с retry)
    4. Вернуть как есть
    """
    if not text:
        return text
    if not _has_cyrillic(text):
        return text

    # 1. Локальный словарь
    manual = _load_manual()
    if text in manual:
        return manual[text]

    # 2. Кэш
    cache = _load_cache()
    if text in cache:
        return cache[text]

    # 3. Google Translate
    if not _TRANSLATOR_AVAILABLE:
        return text

    for attempt in range(3):
        try:
            translated = GoogleTranslator(source="auto", target="en").translate(text)
            if translated and translated.strip():
                cache[text] = translated
                _save_cache(cache)
                return translated
            break
        except Exception as e:
            err = str(e).lower()
            if "too many requests" in err or "429" in err:
                wait = 10 * (attempt + 1)
                logger.warning(f"Google rate limit, waiting {wait}s")
                time.sleep(wait)
            else:
                logger.warning(f"Translation failed: {e}")
                break

    return text


def pretranslate_signals(signals: list) -> Dict[str, str]:
    """
    Переводит сигналы.
    Локальный словарь + кэш = мгновенно.
    Если чего-то нет — Google (с паузой 1 сек).
    """
    result = {}
    total = len(signals)
    manual = _load_manual()

    logger.info(f"Pre-translating {total} signals...")

    google_used = 0
    manual_used = 0

    for i, s in enumerate(signals, 1):
        name = s.get("name", "")
        if not name or name in result:
            continue

        if name in manual:
            result[name] = manual[name]
            manual_used += 1
        else:
            result[name] = translate_to_english(name)
            google_used += 1
            time.sleep(1.0)

        if i % 20 == 0:
            logger.info(f"  Translated {i}/{total} signals")

    logger.info(
        f"Translation done: {len(result)} unique signals "
        f"(manual: {manual_used}, google: {google_used})"
    )
    return result