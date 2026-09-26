import numpy as np
import joblib
from pathlib import Path
from loguru import logger

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, f1_score, accuracy_score
from sklearn.preprocessing import StandardScaler

DATASETS = Path("/app/data/datasets")
MODELS = Path("/app/data/models")
MODELS.mkdir(parents=True, exist_ok=True)

LABELS = ["weak", "negative", "junk"]


def train():
    X_train = np.load(DATASETS / "X_train.npy")
    y_train = np.load(DATASETS / "y_train.npy")
    X_val = np.load(DATASETS / "X_val.npy")
    y_val = np.load(DATASETS / "y_val.npy")
    X_test = np.load(DATASETS / "X_test.npy")
    y_test = np.load(DATASETS / "y_test.npy")

    logger.info(f"Train: {X_train.shape}, Val: {X_val.shape}, Test: {X_test.shape}")

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_val_s = scaler.transform(X_val)
    X_test_s = scaler.transform(X_test)

    clf = LogisticRegression(
        class_weight="balanced",
        max_iter=3000,
        C=1.0,
        solver="lbfgs",
        multi_class="multinomial",
    )
    clf.fit(X_train_s, y_train)

    # Validation
    y_val_pred = clf.predict(X_val_s)
    logger.info("=" * 60)
    logger.info("VALIDATION")
    logger.info("=" * 60)
    logger.info(f"Accuracy: {accuracy_score(y_val, y_val_pred):.3f}")
    logger.info(f"F1 macro: {f1_score(y_val, y_val_pred, average='macro'):.3f}")
    logger.info(f"\n{classification_report(y_val, y_val_pred, target_names=LABELS)}")
    logger.info(f"Confusion matrix:\n{confusion_matrix(y_val, y_val_pred)}")

    # Test
    y_test_pred = clf.predict(X_test_s)
    logger.info("=" * 60)
    logger.info("TEST")
    logger.info("=" * 60)
    logger.info(f"Accuracy: {accuracy_score(y_test, y_test_pred):.3f}")
    logger.info(f"F1 macro: {f1_score(y_test, y_test_pred, average='macro'):.3f}")
    logger.info(f"\n{classification_report(y_test, y_test_pred, target_names=LABELS)}")
    logger.info(f"Confusion matrix:\n{confusion_matrix(y_test, y_test_pred)}")

    joblib.dump(clf, MODELS / "classifier.pkl")
    joblib.dump(scaler, MODELS / "scaler.pkl")
    logger.info(f"Saved: {MODELS / 'classifier.pkl'}")


if __name__ == "__main__":
    train()