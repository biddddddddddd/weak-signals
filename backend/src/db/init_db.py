from loguru import logger
from src.db.connection import Base, engine
from src.db.models import (  # noqa: F401 — важно для регистрации
    Source,
    Document,
    WeakSignal,
    NegativeSignal,
    ScoredDocument,
    RawWeakSignal,
    RawNegativeSignal,
    RawJunkSignal,
)


def init_db():
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created (or already existed)")


if __name__ == "__main__":
    init_db()