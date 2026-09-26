import numpy as np
import joblib
from pathlib import Path
from functools import lru_cache
from typing import Dict, Any
from loguru import logger

MODELS = Path("/app/data/models")

LABELS = {0: "weak", 1: "negative", 2: "junk"}


@lru_cache(maxsize=1)
def _load():
    clf_path = MODELS / "classifier.pkl"
    scaler_path = MODELS / "scaler.pkl"
    if not clf_path.exists() or not scaler_path.exists():
        logger.error(f"Модель не найдена: {clf_path} / {scaler_path}")
        return None, None
    clf = joblib.load(clf_path)
    scaler = joblib.load(scaler_path)
    logger.info(f"Classifier loaded from {clf_path}")
    return clf, scaler


def classify(embedding: list) -> Dict[str, Any]:
    clf, scaler = _load()
    if clf is None or scaler is None:
        return {
            "label": "unknown",
            "probs": {},
            "confidence": 0.0,
            "available": False,
        }

    X = np.array([embedding], dtype=np.float32)
    X_s = scaler.transform(X)
    probs = clf.predict_proba(X_s)[0]
    pred = int(np.argmax(probs))
    return {
        "label": LABELS[pred],
        "probs": {LABELS[i]: float(probs[i]) for i in range(len(probs))},
        "confidence": float(probs[pred]),
        "available": True,
    }


def classify_text(text: str) -> Dict[str, Any]:
    from src.embeddings.model import get_model
    model = get_model()
    emb = model.encode(text, normalize_embeddings=True).tolist()
    return classify(emb)