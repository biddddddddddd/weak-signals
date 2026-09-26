import re
import math
from typing import List, Dict, Optional
from collections import Counter
from datetime import datetime
from loguru import logger


HYPE_WORDS = {
    "revolutionary", "breakthrough", "disruptive", "game-changer", "game changer",
    "unprecedented", "world-class", "cutting-edge", "state-of-the-art",
    "next-generation", "paradigm shift", "killer", "unrivaled", "unparalleled",
    "groundbreaking", "revolutionizing", "transformative",
}

ACADEMIC_MARKERS = {
    "we prove", "we show", "we demonstrate", "theorem", "lemma", "corollary",
    "experiment", "experiments", "methodology", "benchmark", "benchmarks",
    "evaluation", "empirical", "hypothesis", "analysis", "study", "research",
    "proposed", "propose", "novel", "framework", "algorithm", "dataset",
}

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "this", "that", "these", "those", "it", "its", "as", "we", "our", "us",
    "they", "their", "you", "your", "he", "she", "his", "her", "i", "me",
    "my", "mine", "you", "yours", "not", "no", "do", "does", "did", "can",
    "could", "will", "would", "should", "may", "might", "must", "have",
    "has", "had", "so", "if", "then", "than", "such", "into", "also", "any",
    "each", "which", "who", "whom", "what", "when", "where", "why", "how",
    "all", "some", "more", "most", "other", "many", "very", "here", "there",
}


def tokenize(text: str) -> List[str]:
    """Простая токенизация: буквы, цифры, дефисы."""
    text = text.lower()
    tokens = re.findall(r"[a-zа-яё][a-zа-яё\-]{2,}", text)
    return [t for t in tokens if t not in STOPWORDS]


def compute_idf_map(texts: List[str]) -> Dict[str, float]:
    """
    Считает IDF для каждого слова по корпусу.
    idf(word) = log(N / (1 + df(word))) + 1
    """
    n_docs = len(texts)
    df = Counter()

    for text in texts:
        tokens = set(tokenize(text))
        for token in tokens:
            df[token] += 1

    idf_map = {}
    for token, count in df.items():
        idf_map[token] = math.log(n_docs / (1 + count)) + 1.0

    logger.info(f"IDF map built: {len(idf_map)} unique terms across {n_docs} docs")
    return idf_map


def compute_novelty(text: str, idf_map: Dict[str, float]) -> float:
    """
    Средний IDF терминов документа.
    Чем выше — тем более редкие (новые) слова.
    """
    tokens = tokenize(text)
    if not tokens:
        return 0.0

    scores = [idf_map.get(t, 5.0) for t in tokens]
    return round(sum(scores) / len(scores), 4)


def compute_max_idf(text: str, idf_map: Dict[str, float]) -> float:
    """Максимальный IDF среди терминов документа."""
    tokens = tokenize(text)
    if not tokens:
        return 0.0
    return round(max(idf_map.get(t, 5.0) for t in tokens), 4)


def compute_hype_ratio(text: str) -> float:
    """Доля хайп-слов от общего числа слов."""
    tokens = tokenize(text)
    if not tokens:
        return 0.0
    hype_count = sum(1 for t in tokens if t in HYPE_WORDS)
    return round(hype_count / len(tokens), 4)


def compute_academic_markers(text: str) -> float:
    """Доля академических маркеров (bigram + unigram)."""
    text_lower = " " + text.lower() + " "
    tokens = tokenize(text)
    if not tokens:
        return 0.0

    count = 0
    for token in tokens:
        if token in ACADEMIC_MARKERS:
            count += 1

    for marker in ACADEMIC_MARKERS:
        if " " in marker and marker in text_lower:
            count += 1

    return round(count / len(tokens), 4)


def compute_uppercase_ratio(text: str) -> float:
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    return round(sum(1 for c in letters if c.isupper()) / len(letters), 4)


def compute_digit_ratio(text: str) -> float:
    if not text:
        return 0.0
    return round(sum(1 for c in text if c.isdigit()) / len(text), 4)


def compute_avg_word_length(text: str) -> float:
    tokens = tokenize(text)
    if not tokens:
        return 0.0
    return round(sum(len(t) for t in tokens) / len(tokens), 4)


def compute_unique_ratio(text: str) -> float:
    tokens = tokenize(text)
    if not tokens:
        return 0.0
    return round(len(set(tokens)) / len(tokens), 4)


def parse_year_month(published_at: str) -> tuple:
    """Возвращает (year, month) или (None, None)."""
    if not published_at:
        return None, None
    try:
        for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(published_at, fmt)
                return dt.year, dt.month
            except ValueError:
                continue
        dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        return dt.year, dt.month
    except Exception:
        return None, None


def extract_text_features(
    title: str,
    abstract: str,
    idf_map: Dict[str, float],
    published_at: str = "",
) -> Dict:
    """Возвращает все текстовые признаки для одного документа."""
    text = f"{title} {abstract}"

    year, month = parse_year_month(published_at)
    year = year if year else 2026

    return {
        "novelty": compute_novelty(text, idf_map),
        "max_idf": compute_max_idf(text, idf_map),
        "hype_ratio": compute_hype_ratio(text),
        "academic_markers": compute_academic_markers(text),
        "uppercase_ratio": compute_uppercase_ratio(text),
        "digit_ratio": compute_digit_ratio(text),
        "avg_word_length": compute_avg_word_length(text),
        "unique_word_ratio": compute_unique_ratio(text),
        "year": year,
        "month": month if month else 6,
    }