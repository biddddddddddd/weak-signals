import numpy as np
from loguru import logger
from src.db.connection import SessionLocal
from src.db.models import RawWeakSignal, RawNegativeSignal, RawJunkSignal

THRESHOLD = 0.95


def _dedup(db, cls):
    items = db.query(cls).filter(cls.embedding.isnot(None)).all()
    logger.info(f"{cls.__name__}: {len(items)} items")
    if not items:
        return 0

    embeddings = np.array([it.embedding for it in items], dtype=np.float32)
    # нормализуем (на случай если не нормализованы)
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1
    embeddings = embeddings / norms

    keep = []
    removed = 0
    for i in range(len(items)):
        is_dup = False
        for j in keep:
            sim = float(np.dot(embeddings[i], embeddings[j]))
            if sim > THRESHOLD:
                is_dup = True
                break
        if is_dup:
            db.delete(items[i])
            removed += 1
        else:
            keep.append(i)

    db.commit()
    logger.info(f"{cls.__name__}: removed {removed}, kept {len(keep)}")
    return len(keep)


def dedup():
    db = SessionLocal()
    try:
        _dedup(db, RawWeakSignal)
        _dedup(db, RawNegativeSignal)
        _dedup(db, RawJunkSignal)
    finally:
        db.close()


if __name__ == "__main__":
    dedup()