import json
import re
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from loguru import logger

from src.embeddings.retrieval import find_similar
from src.embeddings.model import get_model
from src.llm.client import get_llm
from src.ml.classifier import classify
from src.db.models import ScoredDocument


SYSTEM_PROMPT = """Ты — аналитик, который ищет «слабые сигналы» в научно-технологических отраслях.

Слабый сигнал — это ранний, разрозненный, неочевидный индикатор зарождающейся технологии.
Это НЕ массовая технология, НЕ зрелый тренд, НЕ маркетинговый хайп, НЕ отраслевой стандарт.

Ты получаешь:
1. Запрос пользователя (технологическое направление).
2. Текст новости или публикации.
3. Похожие примеры слабых сигналов (эталон).
4. Похожие примеры зрелых технологий/хайпа (антипримеры).

Твоя задача — решить, является ли технология из текста слабым сигналом ПО ЗАПРОСУ ПОЛЬЗОВАТЕЛЯ.

КРИТИЧНО ВАЖНО:
- Если запрос содержит отрасль (банки, финтех, ИИ, кибербезопасность), НЕ ограничивай поиск только этой отраслью.
- Ищи ЛЮБЫЕ зарождающиеся технологии, которые могут быть ПРИМЕНИМЫ в этой отрасли или СВЯЗАНЫ с ней.
- Пример: для запроса «слабые сигналы в банкинге» подходят ИИ для KYC, защита от дипфейков, биометрия, постквантовая криптография, Open Banking, RegTech, цифровой рубль, токенизация, агентные системы, объяснимый ИИ, ончейн-скоринг.
- Если запрос общий («слабые сигналы», «новые технологии») — ищи ЛЮБЫЕ конкретные технологии.
- Оценивай технологию по СМЫСЛУ, а не по отрасли.
- Если в тексте нет конкретной технологии, а только общие слова — is_weak_signal=false.

НЕ считай слабым сигналом:
- общие научные статьи без конкретной технологии (например, «метод резки табачного листа», «смазочные материалы»);
- полностью нерелевантные запросу статьи;
- маркетинговый хайп: Metaverse, Web3, NFT, DAO, Superintelligence, Singularity, Digital immortality, Consciousness upload;
- псевдонауку: торсионные поля, биополе, гомеопатия, астрология, сфиральные нейроны, гравитационные экраны, вечный двигатель, холодный синтез, антигравитация, машина времени;
- зрелые технологии: Kubernetes, Docker, PostgreSQL, Redis, GPT-4, TensorFlow, PyTorch, CRISPR-Cas9, mRNA vaccines, AlphaFold, SWIFT, Visa, AWS, Snowflake, Databricks;
- если технология не подтверждена рецензируемыми источниками.

ВАЖНО про поле "technology":
- Это КОНКРЕТНАЯ технология, а не направление и не область.
- НЕ "нейроморфные вычисления", НЕ "квантовое сжатие", НЕ "федеративное обучение" (это направления).
- ДА "Сегнетоэлектрические нейроморфные транзисторы на HfO2", ДА "Фотонные тензорные процессоры".
- Минимум 3 слова, максимум 200 символов.

Другие правила:
- stage: "Исследование" | "Прототип" | "Пилот" | "Раннее внедрение"
- trend: "Стабильный" | "Растёт" | "Растёт быстро"

Отвечай строго в формате JSON без пояснений. Обязательные поля:
{
  "is_weak_signal": true/false,
  "confidence": 0.0-1.0,
  "technology": "конкретное название технологии",
  "description": "что это за технология, 2-3 предложения",
  "advantage": "потенциальное преимущество, 1-2 предложения",
  "case_example": "пример применения, 1-2 предложения",
  "why_weak_signal": "почему это слабый сигнал, а не зрелый тренд",
  "why_this_score": "почему такая уверенность",
  "stage": "Исследование | Прототип | Пилот | Раннее внедрение",
  "trend": "Стабильный | Растёт | Растёт быстро",
  "excluded_trends": ["какие зрелые тренды похожи, но исключены"]
}
"""


def _build_user_prompt(query: str, text: str, weak_examples: List[Dict], neg_examples: List[Dict]) -> str:
    weak_block = "\n".join(
        f"- {w['name']} (сходство {w['score']:.2f}). Почему слабый сигнал: {w['payload'].get('why_weak_signal', '')[:300]}"
        for w in weak_examples
    )
    neg_block = "\n".join(
        f"- {n['name']} (сходство {n['score']:.2f})"
        for n in neg_examples
    )
    return f"""ЗАПРОС ПОЛЬЗОВАТЕЛЯ: {query}

ТЕКСТ:
{text[:4000]}

ПОХОЖИЕ СЛАБЫЕ СИГНАЛЫ (эталон):
{weak_block}

ПОХОЖИЕ ЗРЕЛЫЕ ТЕХНОЛОГИИ / ХАЙП (антипримеры):
{neg_block}

Оцени, является ли технология из текста слабым сигналом по запросу пользователя.
Помни:
1. Если запрос содержит отрасль — не ограничивайся только этой отраслью, ищи смежные технологии.
2. Если запрос общий — ищи любые конкретные технологии.
3. technology — это КОНКРЕТНАЯ технология, а не направление.
Ответ — только JSON."""


def _parse_json(raw: str) -> Dict[str, Any]:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?", "", raw).strip()
        raw = re.sub(r"```$", "", raw).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
    logger.error(f"Не удалось распарсить JSON от LLM: {raw[:200]}")
    return {
        "is_weak_signal": False,
        "confidence": 0.0,
        "technology": "",
        "description": "",
        "advantage": "",
        "case_example": "",
        "why_weak_signal": "Ошибка парсинга ответа LLM.",
        "why_this_score": "",
        "stage": "",
        "trend": "",
        "excluded_trends": [],
    }


def _get_cached(db: Session, doc_id: str) -> Optional[ScoredDocument]:
    return db.query(ScoredDocument).filter(ScoredDocument.doc_id == doc_id).first()


def _save_cache(
    db: Session,
    doc_id: str,
    title: str,
    url: str,
    source_name: str,
    language: str,
    trust_level: int,
    result: Dict[str, Any],
) -> None:
    cached = _get_cached(db, doc_id)
    if cached:
        return
    record = ScoredDocument(
        doc_id=doc_id,
        title=title,
        url=url,
        source_name=source_name,
        language=language,
        trust_level=trust_level,
        is_weak_signal=1 if result.get("is_weak_signal") else 0,
        confidence=float(result.get("confidence", 0)),
        technology=result.get("technology"),
        description=result.get("description"),
        advantage=result.get("advantage"),
        case_example=result.get("case_example"),
        why_weak_signal=result.get("why_weak_signal"),
        why_this_score=result.get("why_this_score"),
        stage=result.get("stage"),
        trend=result.get("trend"),
        excluded_trends=result.get("excluded_trends", []),
        retrieval_weak=result.get("retrieval_weak", []),
        retrieval_negative=result.get("retrieval_negative", []),
    )
    db.add(record)
    try:
        db.commit()
    except Exception:
        db.rollback()


def score_text(
    db: Session,
    text: str,
    query: str = "",
    top_k: int = 5,
    doc_id: Optional[str] = None,
    title: str = "",
    url: str = "",
    source_name: str = "",
    language: str = "",
    trust_level: int = 5,
    use_classifier: bool = True,
) -> Dict[str, Any]:
    if doc_id:
        cached = _get_cached(db, doc_id)
        if cached:
            return {
                "is_weak_signal": bool(cached.is_weak_signal),
                "confidence": cached.confidence,
                "technology": cached.technology,
                "description": cached.description,
                "advantage": cached.advantage,
                "case_example": cached.case_example,
                "why_weak_signal": cached.why_weak_signal,
                "why_this_score": cached.why_this_score,
                "stage": cached.stage,
                "trend": cached.trend,
                "excluded_trends": cached.excluded_trends or [],
                "retrieval_weak": cached.retrieval_weak or [],
                "retrieval_negative": cached.retrieval_negative or [],
                "trust_level": cached.trust_level or 5,
                "from_cache": True,
            }

    cls_result: Dict[str, Any] = {}
    if use_classifier:
        try:
            model = get_model()
            emb = model.encode(text, normalize_embeddings=True).tolist()
            cls_result = classify(emb)
        except Exception as e:
            logger.warning(f"Classifier failed: {e}")
            cls_result = {"label": "unknown", "available": False, "confidence": 0.0, "probs": {}}

        if cls_result.get("available"):
            label = cls_result["label"]
            conf = cls_result["confidence"]
            if label == "junk" and conf > 0.9:
                result = {
                    "is_weak_signal": False,
                    "confidence": conf,
                    "technology": "",
                    "description": "",
                    "advantage": "",
                    "case_example": "",
                    "why_weak_signal": f"Классификатор: junk (уверенность {conf:.2f})",
                    "why_this_score": f"probs={cls_result['probs']}",
                    "stage": "",
                    "trend": "",
                    "excluded_trends": [],
                    "retrieval_weak": [],
                    "retrieval_negative": [],
                    "trust_level": trust_level,
                    "from_cache": False,
                    "classifier": cls_result,
                    "skipped_llm": True,
                }
                if doc_id:
                    _save_cache(db, doc_id, title, url, source_name, language, trust_level, result)
                    result["doc_id"] = doc_id
                return result

    similar = find_similar(db, text, top_k=top_k, include_negatives=True)
    weak_examples = [s for s in similar if s["type"] == "weak"][:top_k]
    neg_examples = [s for s in similar if s["type"] == "negative"][:top_k]

    llm = get_llm()
    user_prompt = _build_user_prompt(query, text, weak_examples, neg_examples)
    raw = llm.chat(SYSTEM_PROMPT, user_prompt)
    result = _parse_json(raw)

    result["retrieval_weak"] = [
        {"id": w["id"], "name": w["name"], "score": w["score"]} for w in weak_examples
    ]
    result["retrieval_negative"] = [
        {"id": n["id"], "name": n["name"], "score": n["score"]} for n in neg_examples
    ]
    result["from_cache"] = False
    result["classifier"] = cls_result
    result["skipped_llm"] = False
    result["trust_level"] = trust_level

    if doc_id:
        _save_cache(db, doc_id, title, url, source_name, language, trust_level, result)
        result["doc_id"] = doc_id

    return result