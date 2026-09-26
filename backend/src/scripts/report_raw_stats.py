from loguru import logger
from src.db.connection import SessionLocal
from src.db.models import RawWeakSignal, RawNegativeSignal, RawJunkSignal


def report():
    db = SessionLocal()
    try:
        print("=" * 50)
        print("RAW DATASET STATS")
        print("=" * 50)
        print(f"Weak:     {db.query(RawWeakSignal).count()}")
        print(f"Negative: {db.query(RawNegativeSignal).count()}")
        print(f"Junk:     {db.query(RawJunkSignal).count()}")

        # распределение weak по источникам
        from sqlalchemy import func
        print()
        print("Weak by source:")
        for src, cnt in db.query(RawWeakSignal.source, func.count()).group_by(RawWeakSignal.source).all():
            print(f"  {src}: {cnt}")

        print()
        print("Junk by category:")
        for cat, cnt in db.query(RawJunkSignal.category, func.count()).group_by(RawJunkSignal.category).all():
            print(f"  {cat}: {cnt}")
    finally:
        db.close()


if __name__ == "__main__":
    report()