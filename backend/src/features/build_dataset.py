import pandas as pd
from pathlib import Path
from loguru import logger

from src.db.connection import SessionLocal
from src.db.models import Document, Source
from src.features.source_features import extract_features
from src.features.text_features import compute_idf_map, extract_text_features
from src.features.topic_stats import fetch_all_topics, add_topic_features


OUTPUT_DIR = Path("data/processed")


def load_documents_with_labels():
    db = SessionLocal()
    try:
        rows = (
            db.query(Document, Source.domain)
            .join(Source, Document.source_id == Source.id)
            .filter(Document.label.isnot(None))
            .all()
        )
        logger.info(f"Loaded {len(rows)} documents with labels")
        return rows
    finally:
        db.close()


def build_dataframe(rows):
    logger.info("Building IDF map across all documents...")
    all_texts = [f"{doc.title or ''} {doc.abstract or ''}" for doc, _ in rows]
    idf_map = compute_idf_map(all_texts)

    records = []
    for doc, domain in rows:
        doc_dict = {
            "source_domain": domain,
            "title": doc.title or "",
            "abstract": doc.abstract or "",
            "published_at": doc.published_at or "",
            "region": doc.region or "Global",
            "organizations": doc.organizations or "",
        }

        features = extract_features(doc_dict)
        text_feats = extract_text_features(
            title=doc_dict["title"],
            abstract=doc_dict["abstract"],
            idf_map=idf_map,
            published_at=doc_dict["published_at"],
        )
        features.update(text_feats)
        features["label"] = int(doc.label)
        features["doc_id"] = doc.doc_id
        features["source_query"] = doc.source_query or f"unknown_{doc.id}"
        records.append(features)

    df = pd.DataFrame(records)
    logger.info(f"Built DataFrame: shape={df.shape}")
    return df


def add_region_onehot(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["region_usa"] = (df["region"] == "USA").astype(int)
    df["region_china"] = (df["region"] == "China").astype(int)
    df["region_europe"] = (df["region"] == "Europe").astype(int)
    df["region_japan"] = (df["region"] == "Japan").astype(int)
    df["region_india"] = (df["region"] == "India").astype(int)
    df["region_russia"] = (df["region"] == "Russia").astype(int)
    df["region_global"] = (df["region"] == "Global").astype(int)
    df = df.drop(columns=["region"])
    return df


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 60)
    logger.info("BUILD DATASET (with text features + source_query + topic stats)")
    logger.info("=" * 60)

    rows = load_documents_with_labels()
    if not rows:
        logger.error("No labeled documents in DB. Run collect_dataset first.")
        return

    df = build_dataframe(rows)
    df = add_region_onehot(df)

    unique_queries = sorted(df["source_query"].dropna().unique().tolist())
    logger.info(f"Unique queries: {len(unique_queries)}")

    logger.info("Fetching topic statistics from arXiv (cached after first run)...")
    stats = fetch_all_topics(unique_queries)
    df = add_topic_features(df, stats)

    parquet_path = OUTPUT_DIR / "train_data.parquet"
    csv_path = OUTPUT_DIR / "train_data.csv"

    df.to_parquet(parquet_path, index=False)
    df.to_csv(csv_path, index=False, encoding="utf-8")

    logger.info("=" * 60)
    logger.info(f"Saved parquet: {parquet_path}")
    logger.info(f"Saved csv:     {csv_path}")
    logger.info(f"Rows:          {len(df)}")
    logger.info(f"Columns:       {len(df.columns)}")
    logger.info("=" * 60)

    logger.info(f"Label distribution:\n{df['label'].value_counts().to_string()}")

    feature_cols = [c for c in df.columns if c not in ("label", "doc_id", "source_query")]
    logger.info(f"Feature columns ({len(feature_cols)}): {feature_cols}")


if __name__ == "__main__":
    main()