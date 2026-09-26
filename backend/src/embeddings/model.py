from functools import lru_cache
from sentence_transformers import SentenceTransformer

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    """Загружает модель один раз на процесс."""
    return SentenceTransformer(MODEL_NAME)