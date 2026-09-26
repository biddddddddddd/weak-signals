import uuid
import asyncio
import re
from typing import Dict, List
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from loguru import logger

from src.db.connection import get_db
from src.db.models import Document, Source, WeakSignal, ScoredDocument
from src.scoring.scorer import score_text
from src.ml.classifier import classify
from src.embeddings.model import get_model

app = FastAPI(title="Weak Signals API", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_search_cache: Dict[str, dict] = {}


class SearchRequest(BaseModel):
    query: str
    limit: int = 15


def _collect_live(query: str, max_per_source: int = 20) -> list:
    from src.sources.multi_search import search_all_sources
    try:
        docs = asyncio.run(search_all_sources(query, max_per_source=max_per_source))
        return docs
    except Exception as e:
        logger.warning(f"multi_search failed: {e}")
        return []


def _normalize_tech(name: str) -> str:
    if not name:
        return ""
    s = name.lower().strip()
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s)
    for prefix in ("the ", "a ", "an "):
        if s.startswith(prefix):
            s = s[len(prefix):]
    return s.strip()


def _group_signals(signals: List[Dict]) -> List[Dict]:
    groups: Dict[str, Dict] = {}
    for sig in signals:
        key = _normalize_tech(sig.get("technology", ""))
        if not key:
            continue
        if key not in groups:
            groups[key] = {
                "id": sig["id"],
                "technology": sig["technology"],
                "score": sig["score"],
                "status": sig.get("status", "medium"),
                "key_predictors": sig.get("key_predictors", []),
                "why_weak_signal": sig.get("why_weak_signal", ""),
                "trend_stage": sig.get("trend_stage", ""),
                "sources": [{
                    "url": sig.get("source_url", ""),
                    "name": sig.get("source_name", ""),
                    "trust_level": sig.get("trust_level", 5),
                }],
                "sources_count": 1,
                "trust_level": sig.get("trust_level", 5),
                "from_cache": sig.get("from_cache", False),
            }
        else:
            g = groups[key]
            g["sources"].append({
                "url": sig.get("source_url", ""),
                "name": sig.get("source_name", ""),
                "trust_level": sig.get("trust_level", 5),
            })
            g["sources_count"] += 1
            if sig["score"] > g["score"]:
                g["score"] = sig["score"]
                g["why_weak_signal"] = sig.get("why_weak_signal", g["why_weak_signal"])
                g["trend_stage"] = sig.get("trend_stage", g["trend_stage"])
                g["key_predictors"] = sig.get("key_predictors", g["key_predictors"])
                g["status"] = sig.get("status", g["status"])
            if sig.get("trust_level", 5) > g["trust_level"]:
                g["trust_level"] = sig["trust_level"]

    result = list(groups.values())
    result.sort(key=lambda x: (x["score"], x["trust_level"], x["sources_count"]), reverse=True)
    return result


@app.get("/")
def root():
    return {"status": "ok", "service": "Weak Signals API", "version": "1.1.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    return {
        "total_candidates": db.query(WeakSignal).count(),
        "processed_sources": db.query(Source).count(),
        "signals_above_75": db.query(ScoredDocument).filter(
            ScoredDocument.is_weak_signal == 1,
            ScoredDocument.confidence >= 0.75,
        ).count(),
        "total_documents": db.query(Document).count(),
        "scored_documents": db.query(ScoredDocument).count(),
    }


@app.post("/api/search")
def create_search(request: SearchRequest, db: Session = Depends(get_db)):
    query = request.query.strip()
    if not query:
        return {"search_id": None, "query": query, "status": "failed", "signals": []}

    logger.info(f"Live search: {query}")
    candidates = _collect_live(query, max_per_source=20)
    logger.info(f"Candidates collected: {len(candidates)}")

    model = get_model()
    prefiltered = []
    for cand in candidates:
        text = f"{cand.get('title', '')}. {cand.get('abstract', '')}".strip()
        if len(text) < 30:
            continue
        try:
            emb = model.encode(text, normalize_embeddings=True).tolist()
            cls = classify(emb)
        except Exception as e:
            logger.warning(f"Classifier failed for {cand.get('doc_id')}: {e}")
            continue

        if not cls.get("available"):
            cand["_classifier"] = cls
            cand["_text"] = text
            prefiltered.append(cand)
            continue

        label = cls.get("label")
        conf = cls.get("confidence", 0.0)

        if label == "junk" and conf > 0.9:
            continue

        cand["_classifier"] = cls
        cand["_text"] = text
        prefiltered.append(cand)

    logger.info(f"After junk filter: {len(prefiltered)} candidates")

    prefiltered.sort(
        key=lambda c: (
            c["_classifier"].get("probs", {}).get("weak", 0),
            c["_classifier"].get("probs", {}).get("negative", 0),
        ),
        reverse=True,
    )
    prefiltered = prefiltered[:30]

    logger.info(f"Scoring top-{len(prefiltered)} via LLM...")

    signals = []
    for cand in prefiltered:
        try:
            result = score_text(
                db,
                cand["_text"],
                query=query,
                top_k=5,
                doc_id=cand["doc_id"],
                title=cand.get("title", ""),
                url=cand.get("url", ""),
                source_name=cand.get("source_name", ""),
                language=cand.get("language", ""),
                trust_level=int(cand.get("trust_level", 5)),
                use_classifier=False,
            )
        except Exception as e:
            logger.warning(f"Score failed for {cand.get('doc_id')}: {e}")
            continue

        if not result.get("is_weak_signal"):
            continue
        if result.get("confidence", 0) < 0.6:
            continue

        tech = (result.get("technology") or "").strip()
        if not tech:
            continue

        signals.append({
            "id": cand["doc_id"],
            "technology": tech,
            "score": result["confidence"],
            "status": "high" if result["confidence"] >= 0.85 else "medium",
            "key_predictors": [result.get("stage", ""), result.get("trend", "")],
            "why_weak_signal": result.get("why_weak_signal", ""),
            "sources_count": 1,
            "trend_stage": result.get("stage", ""),
            "source_url": cand.get("url", ""),
            "source_name": cand.get("source_name", ""),
            "trust_level": int(cand.get("trust_level", 5)),
            "from_cache": result.get("from_cache", False),
        })

    logger.info(f"Raw signals before grouping: {len(signals)}")

    grouped = _group_signals(signals)
    logger.info(f"After grouping: {len(grouped)} signals")

    grouped = grouped[: request.limit]

    search_id = str(uuid.uuid4())
    result = {
        "search_id": search_id,
        "query": query,
        "status": "completed",
        "signals": grouped,
        "processed_sources": len(candidates),
        "candidates_found": len(candidates),
        "confirmed_signals": len(grouped),
        "high_confidence_75plus": len([s for s in grouped if s["score"] >= 0.75]),
    }
    _search_cache[search_id] = result
    return result


@app.get("/api/search/{search_id}")
def get_search(search_id: str):
    if search_id not in _search_cache:
        raise HTTPException(status_code=404, detail="Search not found")
    return _search_cache[search_id]


@app.get("/api/insight/{doc_id:path}")
def get_insight(doc_id: str, db: Session = Depends(get_db)):
    cached = db.query(ScoredDocument).filter(ScoredDocument.doc_id == doc_id).first()
    if cached:
        return {
            "id": cached.doc_id,
            "technology": cached.technology,
            "score": cached.confidence,
            "status": "high" if cached.confidence >= 0.85 else "medium",
            "description": cached.description or "",
            "advantage": cached.advantage or "",
            "case_examples": [cached.case_example] if cached.case_example else [],
            "analytical_estimates": [],
            "why_weak_signal": cached.why_weak_signal or "",
            "why_this_score": cached.why_this_score or "",
            "excluded_trends": cached.excluded_trends or [],
            "trust_level": cached.trust_level or 5,
            "sources": [{
                "id": cached.doc_id,
                "name": cached.source_name or "",
                "url": cached.url or "",
                "publication_date": None,
                "type": "web",
                "language": cached.language or "",
                "trust_level": cached.trust_level or 5,
                "trust_reason": None,
                "original_title": cached.title,
                "summary_ru": None,
                "translation_note": None,
            }],
        }

    doc = db.query(Document).filter(Document.doc_id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    source = db.query(Source).filter(Source.id == doc.source_id).first()
    result = score_text(
        db,
        f"{doc.title}. {doc.abstract or ''}",
        query="",
        doc_id=doc.doc_id,
        title=doc.title,
        url=doc.url or "",
        source_name=source.name if source else "",
        language=doc.language or "",
        trust_level=5,
    )
    return {
        "id": doc.doc_id,
        "technology": result.get("technology") or doc.title[:200],
        "score": result.get("confidence", 0.0),
        "status": "high" if result.get("confidence", 0) >= 0.85 else "medium",
        "description": result.get("description") or doc.abstract or "",
        "advantage": result.get("advantage", ""),
        "case_examples": [result["case_example"]] if result.get("case_example") else [],
        "analytical_estimates": [],
        "why_weak_signal": result.get("why_weak_signal", ""),
        "why_this_score": result.get("why_this_score", ""),
        "excluded_trends": result.get("excluded_trends", []),
        "trust_level": result.get("trust_level", 5),
        "sources": [{
            "id": str(source.id) if source else "unknown",
            "name": source.name if source else "",
            "url": doc.url or "",
            "publication_date": doc.published_at,
            "type": source.source_type if source else "unknown",
            "language": doc.language or "",
            "trust_level": result.get("trust_level", 5),
            "trust_reason": None,
            "original_title": doc.title,
            "summary_ru": None,
            "translation_note": None,
        }],
    }