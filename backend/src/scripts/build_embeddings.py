from loguru import logger
from src.db.connection import SessionLocal
from src.db.models import WeakSignal, NegativeSignal
from src.embeddings.model import get_model


def _text_for_weak(w: WeakSignal) -> str:
    # только название + область — этого достаточно для семантического поиска
    parts = [w.name or "", w.area or ""]
    return ". ".join(p for p in parts if p)


def _text_for_negative(n: NegativeSignal) -> str:
    return n.name or ""


def build_embeddings():
    model = get_model()
    db = SessionLocal()
    try:
        # Сбросим старые эмбеддинги, чтобы пересчитать
        db.query(WeakSignal).update({WeakSignal.embedding: None})
        db.query(NegativeSignal).update({NegativeSignal.embedding: None})
        db.commit()

        weak_items = db.query(WeakSignal).all()
        logger.info(f"Building embeddings for {len(weak_items)} weak signals...")
        for w in weak_items:
            vec = model.encode(_text_for_weak(w), normalize_embeddings=True)
            w.embedding = vec.tolist()
        db.commit()

        neg_items = db.query(NegativeSignal).all()
        logger.info(f"Building embeddings for {len(neg_items)} negative signals...")
        for n in neg_items:
            vec = model.encode(_text_for_negative(n), normalize_embeddings=True)
            n.embedding = vec.tolist()
        db.commit()

        logger.info("Embeddings rebuilt successfully.")
    except Exception as e:
        db.rollback()
        logger.error(f"Build embeddings failed: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    build_embeddings()