import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from loguru import logger

from sklearn.model_selection import StratifiedKFold, GroupKFold, cross_validate
from sklearn.metrics import f1_score, roc_auc_score
import lightgbm as lgb


INPUT_PATH = Path("data/processed/train_data.parquet")
MODEL_PATH = Path("data/processed/lightgbm_model.pkl")

FEATURE_COLUMNS = [
    # Source features
    "trust", "lead_time", "specificity", "independence", "impact",
    "freshness",
    # Length features
    "title_length", "abstract_length", "text_length",
    "has_organizations",
    # Text features
    "novelty", "max_idf", "hype_ratio", "academic_markers",
    "uppercase_ratio", "digit_ratio", "avg_word_length", "unique_word_ratio",
    "year", "month",
    # Region one-hot
    "region_usa", "region_china", "region_europe", "region_japan",
    "region_india", "region_russia", "region_global",
    # Topic-level features from arXiv (NEW)
    "topic_total_log", "topic_recent_log", "topic_recent_ratio",
]


def load_data():
    df = pd.read_parquet(INPUT_PATH)
    logger.info(f"Loaded {len(df)} rows from {INPUT_PATH}")

    missing = [c for c in FEATURE_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    if "source_query" not in df.columns:
        raise ValueError("Missing 'source_query' column. Rebuild dataset first.")

    X = df[FEATURE_COLUMNS].values
    y = df["label"].values
    groups = df["source_query"].values

    logger.info(f"X shape: {X.shape}, y shape: {y.shape}")
    logger.info(f"Class balance: {np.bincount(y)}")
    logger.info(f"Unique groups (queries): {len(set(groups))}")
    return X, y, groups, df


def get_model():
    return lgb.LGBMClassifier(
        num_leaves=15,
        max_depth=5,
        learning_rate=0.05,
        n_estimators=300,
        min_child_samples=5,
        class_weight="balanced",
        objective="binary",
        metric="binary_logloss",
        random_state=42,
        verbose=-1,
    )


def cross_validate_stratified(X, y):
    logger.info("=" * 60)
    logger.info("STRATIFIED 5-FOLD (baseline, завышено из-за утечки)")
    logger.info("=" * 60)

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    model = get_model()

    scoring = ["precision", "recall", "f1", "roc_auc"]
    results = cross_validate(model, X, y, cv=cv, scoring=scoring, n_jobs=1)

    for i in range(5):
        logger.info(
            f"  Fold {i+1}: "
            f"precision={results['test_precision'][i]:.4f}  "
            f"recall={results['test_recall'][i]:.4f}  "
            f"f1={results['test_f1'][i]:.4f}  "
            f"roc_auc={results['test_roc_auc'][i]:.4f}"
        )

    logger.info("-" * 60)
    logger.info(f"MEAN f1: {results['test_f1'].mean():.4f}")
    logger.info(f"MEAN precision: {results['test_precision'].mean():.4f}")
    logger.info(f"MEAN recall: {results['test_recall'].mean():.4f}")
    logger.info(f"MEAN roc_auc: {results['test_roc_auc'].mean():.4f}")
    logger.info("=" * 60)

    return results


def cross_validate_grouped(X, y, groups):
    logger.info("=" * 60)
    logger.info("GROUP 5-FOLD by source_query (честная оценка)")
    logger.info("=" * 60)

    cv = GroupKFold(n_splits=5)
    model = get_model()

    scoring = ["precision", "recall", "f1", "roc_auc"]
    results = cross_validate(
        model, X, y,
        cv=cv,
        groups=groups,
        scoring=scoring,
        n_jobs=1,
    )

    for i in range(5):
        logger.info(
            f"  Fold {i+1}: "
            f"precision={results['test_precision'][i]:.4f}  "
            f"recall={results['test_recall'][i]:.4f}  "
            f"f1={results['test_f1'][i]:.4f}  "
            f"roc_auc={results['test_roc_auc'][i]:.4f}"
        )

    logger.info("-" * 60)
    logger.info(f"MEAN f1: {results['test_f1'].mean():.4f}")
    logger.info(f"MEAN precision: {results['test_precision'].mean():.4f}")
    logger.info(f"MEAN recall: {results['test_recall'].mean():.4f}")
    logger.info(f"MEAN roc_auc: {results['test_roc_auc'].mean():.4f}")
    logger.info("=" * 60)

    return results


def train_final_model(X, y):
    logger.info("Training final model on full dataset...")
    model = get_model()
    model.fit(X, y)

    y_pred = model.predict(X)
    y_proba = model.predict_proba(X)[:, 1]
    logger.info(f"Train F1: {f1_score(y, y_pred):.4f}")
    logger.info(f"Train ROC-AUC: {roc_auc_score(y, y_proba):.4f}")
    return model


def show_feature_importance(model):
    logger.info("=" * 60)
    logger.info("FEATURE IMPORTANCE")
    logger.info("=" * 60)
    pairs = sorted(
        zip(FEATURE_COLUMNS, model.feature_importances_),
        key=lambda x: x[1],
        reverse=True,
    )
    for name, importance in pairs:
        logger.info(f"  {name:25} {importance}")
    logger.info("=" * 60)


def save_model(model):
    joblib.dump(model, MODEL_PATH)
    logger.info(f"Model saved to {MODEL_PATH}")


def main():
    X, y, groups, df = load_data()

    stratified_results = cross_validate_stratified(X, y)
    grouped_results = cross_validate_grouped(X, y, groups)

    model = train_final_model(X, y)
    show_feature_importance(model)
    save_model(model)

    logger.info("=" * 60)
    logger.info("FINAL SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Stratified CV F1: {stratified_results['test_f1'].mean():.4f}")
    logger.info(f"Grouped CV F1:    {grouped_results['test_f1'].mean():.4f}")
    logger.info(f"Разница (утечка): {stratified_results['test_f1'].mean() - grouped_results['test_f1'].mean():.4f}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()