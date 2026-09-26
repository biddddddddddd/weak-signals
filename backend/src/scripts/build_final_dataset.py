import numpy as np
from pathlib import Path
from loguru import logger
from sklearn.model_selection import train_test_split

from src.db.connection import SessionLocal
from src.db.models import (
    WeakSignal, NegativeSignal,
    RawWeakSignal, RawNegativeSignal, RawJunkSignal,
)
from src.embeddings.model import get_model

OUTPUT_DIR = Path("/app/data/datasets")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _text_weak_golden(w: WeakSignal) -> str:
    return w.name or ""


def _text_neg_golden(n: NegativeSignal) -> str:
    return n.name or ""


def build():
    db = SessionLocal()
    model = get_model()
    X, y, meta = [], [], []

    # Weak: golden + raw
    for w in db.query(WeakSignal).all():
        text = _text_weak_golden(w)
        emb = model.encode(text, normalize_embeddings=True).tolist()
        X.append(emb)
        y.append(0)
        meta.append({"name": w.name, "source": "golden_weak", "label": 0})

    for w in db.query(RawWeakSignal).filter(RawWeakSignal.embedding.isnot(None)).all():
        X.append(w.embedding)
        y.append(0)
        meta.append({"name": w.name, "source": w.source, "label": 0})

    # Negative: golden + raw
    for n in db.query(NegativeSignal).all():
        text = _text_neg_golden(n)
        emb = model.encode(text, normalize_embeddings=True).tolist()
        X.append(emb)
        y.append(1)
        meta.append({"name": n.name, "source": "golden_negative", "label": 1})

    for n in db.query(RawNegativeSignal).filter(RawNegativeSignal.embedding.isnot(None)).all():
        X.append(n.embedding)
        y.append(1)
        meta.append({"name": n.name, "source": n.source, "label": 1})

    # Junk
    for j in db.query(RawJunkSignal).filter(RawJunkSignal.embedding.isnot(None)).all():
        X.append(j.embedding)
        y.append(2)
        meta.append({"name": j.name, "source": "junk", "label": 2})

    X = np.array(X, dtype=np.float32)
    y = np.array(y, dtype=np.int64)

    logger.info(f"Total: {len(y)}, weak: {(y==0).sum()}, negative: {(y==1).sum()}, junk: {(y==2).sum()}")

    X_temp, X_test, y_temp, y_test, meta_temp, meta_test = train_test_split(
        X, y, meta, test_size=0.15, random_state=42, stratify=y
    )
    val_size = 0.15 / 0.85
    X_train, X_val, y_train, y_val, meta_train, meta_val = train_test_split(
        X_temp, y_temp, meta_temp, test_size=val_size, random_state=42, stratify=y_temp
    )

    np.save(OUTPUT_DIR / "X_train.npy", X_train)
    np.save(OUTPUT_DIR / "y_train.npy", y_train)
    np.save(OUTPUT_DIR / "X_val.npy", X_val)
    np.save(OUTPUT_DIR / "y_val.npy", y_val)
    np.save(OUTPUT_DIR / "X_test.npy", X_test)
    np.save(OUTPUT_DIR / "y_test.npy", y_test)

    logger.info(f"Train: {X_train.shape}, Val: {X_val.shape}, Test: {X_test.shape}")
    logger.info(f"Train labels: weak={int((y_train==0).sum())}, neg={int((y_train==1).sum())}, junk={int((y_train==2).sum())}")
    logger.info(f"Val labels: weak={int((y_val==0).sum())}, neg={int((y_val==1).sum())}, junk={int((y_val==2).sum())}")
    logger.info(f"Test labels: weak={int((y_test==0).sum())}, neg={int((y_test==1).sum())}, junk={int((y_test==2).sum())}")

    db.close()


if __name__ == "__main__":
    build()