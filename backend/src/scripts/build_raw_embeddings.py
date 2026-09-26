from loguru import logger
from src.db.connection import SessionLocal
from src.db.models import RawWeakSignal, RawNegativeSignal, RawJunkSignal
from src.embeddings.model import get_model


def _text_weak(w: RawWeakSignal) -> str:
    return w.name or ""


def _text_negative(n: RawNegativeSignal) -> str:
    return n.name or ""


def _text_junk(j: RawJunkSignal) -> str:
    return j.name or ""


def build():
    model = get_model()
    db = SessionLocal()
    try:
        # Сбрасываем старые эмбеддинги
        db.query(RawWeakSignal).update({RawWeakSignal.embedding: None})
        db.query(RawNegativeSignal).update({RawNegativeSignal.embedding: None})
        db.query(RawJunkSignal).update({RawJunkSignal.embedding: None})
        db.commit()

        for cls, text_fn in [
            (RawWeakSignal, _text_weak),
            (RawNegativeSignal, _text_negative),
            (RawJunkSignal, _text_junk),
        ]:
            items = db.query(cls).all()
            logger.info(f"{cls.__name__}: {len(items)} items")
            for item in items:
                text = text_fn(item)
                vec = model.encode(text, normalize_embeddings=True)
                item.embedding = vec.tolist()
            db.commit()
    finally:
        db.close()
    logger.info("Done")


if __name__ == "__main__":
    build()