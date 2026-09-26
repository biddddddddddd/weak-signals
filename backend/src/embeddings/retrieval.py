from typing import List, Dict, Any, Tuple
import numpy as np
from sqlalchemy.orm import Session

from src.db.models import WeakSignal, NegativeSignal
from src.embeddings.model import get_model


def _cosine_sim(query_vec: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    return matrix @ query_vec


def find_similar(
    db: Session,
    text: str,
    top_k: int = 5,
    include_negatives: bool = True,
) -> List[Dict[str, Any]]:
    """
    Возвращает до top_k weak и до top_k negative (всего до 2*top_k).
    """
    model = get_model()
    query_vec = model.encode(text, normalize_embeddings=True)
    query_vec = np.asarray(query_vec, dtype=np.float32)

    results: List[Dict[str, Any]] = []

    weak_items = db.query(WeakSignal).filter(WeakSignal.embedding.isnot(None)).all()
    if weak_items:
        matrix = np.asarray([w.embedding for w in weak_items], dtype=np.float32)
        scores = _cosine_sim(query_vec, matrix)
        for idx in np.argsort(-scores)[:top_k]:
            w = weak_items[int(idx)]
            results.append({
                "type": "weak",
                "id": w.id,
                "name": w.name,
                "score": float(scores[int(idx)]),
                "payload": {
                    "area": w.area,
                    "companies": w.companies,
                    "why_weak_signal": w.why_weak_signal,
                    "stage": w.stage,
                    "trend": w.trend,
                    "score_orig": w.score,
                    "sources": w.sources,
                },
            })

    if include_negatives:
        neg_items = db.query(NegativeSignal).filter(NegativeSignal.embedding.isnot(None)).all()
        if neg_items:
            matrix = np.asarray([n.embedding for n in neg_items], dtype=np.float32)
            scores = _cosine_sim(query_vec, matrix)
            for idx in np.argsort(-scores)[:top_k]:
                n = neg_items[int(idx)]
                results.append({
                    "type": "negative",
                    "id": n.id,
                    "name": n.name,
                    "score": float(scores[int(idx)]),
                    "payload": {"description": n.description},
                })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def prefilter_candidate(
    db: Session,
    text: str,
    weak_threshold: float = 0.4,
) -> Tuple[bool, Dict[str, Any]]:
    """
    Ступень 1 — быстрый фильтр без LLM.
    Считает эмбеддинг текста и сравнивает с weak/negative сигналами.

    Возвращает (passed, info), где info содержит:
      top_weak_score, top_weak_id, top_weak_name,
      top_negative_score, top_negative_id, top_negative_name,
      passed_reason.

    Правила:
      - top_weak_score < weak_threshold  → отбрасываем
      - top_negative_score > top_weak_score → отбрасываем (похоже на зрелый тренд/хайп)
      - иначе → пропускаем
    """
    model = get_model()
    query_vec = model.encode(text, normalize_embeddings=True)
    query_vec = np.asarray(query_vec, dtype=np.float32)

    info: Dict[str, Any] = {
        "top_weak_score": 0.0,
        "top_weak_id": None,
        "top_weak_name": None,
        "top_negative_score": 0.0,
        "top_negative_id": None,
        "top_negative_name": None,
        "passed_reason": "",
    }

    weak_items = db.query(WeakSignal).filter(WeakSignal.embedding.isnot(None)).all()
    if weak_items:
        matrix = np.asarray([w.embedding for w in weak_items], dtype=np.float32)
        scores = _cosine_sim(query_vec, matrix)
        best_idx = int(np.argmax(scores))
        info["top_weak_score"] = float(scores[best_idx])
        info["top_weak_id"] = weak_items[best_idx].id
        info["top_weak_name"] = weak_items[best_idx].name

    neg_items = db.query(NegativeSignal).filter(NegativeSignal.embedding.isnot(None)).all()
    if neg_items:
        matrix = np.asarray([n.embedding for n in neg_items], dtype=np.float32)
        scores = _cosine_sim(query_vec, matrix)
        best_idx = int(np.argmax(scores))
        info["top_negative_score"] = float(scores[best_idx])
        info["top_negative_id"] = neg_items[best_idx].id
        info["top_negative_name"] = neg_items[best_idx].name

    if info["top_weak_score"] < weak_threshold:
        info["passed_reason"] = f"top_weak_score {info['top_weak_score']:.3f} < {weak_threshold}"
        return False, info

    if info["top_negative_score"] > info["top_weak_score"]:
        info["passed_reason"] = (
            f"top_negative_score {info['top_negative_score']:.3f} "
            f"> top_weak_score {info['top_weak_score']:.3f}"
        )
        return False, info

    info["passed_reason"] = "ok"
    return True, info