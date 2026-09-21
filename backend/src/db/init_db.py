from loguru import logger

from src.db.connection import Base, engine
from src.db.models import Source, Document  # noqa: F401 — важно для регистрации


def init_db():
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created (or already existed)")


if __name__ == "__main__":
    init_db()