import csv
import json
from pathlib import Path
from loguru import logger
from src.db.connection import SessionLocal
from src.db.models import WeakSignal, NegativeSignal

SEEDS = Path("/app/data/seeds")
WEAK_CSV = SEEDS / "weak-signals.csv"
NEG_JSON = SEEDS / "negative_signals.json"


def load_weak_signals():
    if not WEAK_CSV.exists():
        logger.error(f"Не найден {WEAK_CSV}")
        return 0

    db = SessionLocal()
    saved = 0
    try:
        with WEAK_CSV.open("r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            next(reader)  # пропускаем первую строку с общим названием
            headers = next(reader)  # вторая строка — заголовки
            idx_name = headers.index("Технология (слабый сигнал)")
            idx_area = headers.index("Область")
            idx_companies = headers.index("Компании")
            idx_why = headers.index("Почему это слабый сигнал")
            idx_stage = headers.index("Стадия развития")
            idx_trend = headers.index("Тренд упоминаний")
            idx_score = headers.index("Балл (стадия+тренд)")
            idx_sources = headers.index("Источники")

            for row in reader:
                if not row or len(row) <= idx_name:
                    continue
                name = row[idx_name].strip()
                if not name:
                    continue
                exists = db.query(WeakSignal).filter(WeakSignal.name == name).first()
                if exists:
                    continue
                score_val = 0
                try:
                    score_val = int(row[idx_score].strip())
                except (ValueError, IndexError):
                    pass
                signal = WeakSignal(
                    name=name,
                    area=row[idx_area].strip() if idx_area < len(row) else "",
                    companies=row[idx_companies].strip() if idx_companies < len(row) else "",
                    why_weak_signal=row[idx_why].strip() if idx_why < len(row) else "",
                    stage=row[idx_stage].strip() if idx_stage < len(row) else "",
                    trend=row[idx_trend].strip() if idx_trend < len(row) else "",
                    score=score_val,
                    sources=[row[idx_sources].strip()]
                    if idx_sources < len(row) and row[idx_sources].strip()
                    else [],
                )
                db.add(signal)
                saved += 1
        db.commit()
        logger.info(f"Weak signals loaded: {saved}")
    except Exception as e:
        db.rollback()
        logger.error(f"Load weak signals failed: {e}")
    finally:
        db.close()
    return saved


def load_negative_signals():
    if not NEG_JSON.exists():
        logger.error(f"Не найден {NEG_JSON}")
        return 0

    data = json.loads(NEG_JSON.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        signals = data.get("signals", [])
    elif isinstance(data, list):
        signals = data
    else:
        logger.error("Неизвестный формат negative_signals.json")
        return 0

    db = SessionLocal()
    saved = 0
    try:
        for item in signals:
            if isinstance(item, dict):
                name = item.get("name") or item.get("title") or ""
                description = item.get("description") or item.get("text") or ""
            else:
                name = str(item)
                description = ""
            name = name.strip()
            if not name:
                continue
            exists = db.query(NegativeSignal).filter(NegativeSignal.name == name).first()
            if exists:
                continue
            neg = NegativeSignal(name=name, description=description)
            db.add(neg)
            saved += 1
        db.commit()
        logger.info(f"Negative signals loaded: {saved}")
    except Exception as e:
        db.rollback()
        logger.error(f"Load negative signals failed: {e}")
    finally:
        db.close()
    return saved


if __name__ == "__main__":
    load_weak_signals()
    load_negative_signals()