from loguru import logger
from src.db.connection import SessionLocal
from src.db.models import RawNegativeSignal

# Нерелевантные научные статьи — общие ML/NLP/CV, без конкретной технологии
IRRELEVANT_NEGATIVE = [
    # Общие ML
    ("Latent Dynamics Models for Stable Long-Horizon Rollout", "Общая ML-статья, не слабый сигнал"),
    ("Rationale-Augmented Dual-Expert Interaction Model", "Общая ML-статья, не слабый сигнал"),
    ("Neural Ordinary Differential Equations", "Зрелый ML-метод"),
    ("Graph Neural Networks for Relational Reasoning", "Зрелый ML-метод"),
    ("Variational Autoencoders for Representation Learning", "Зрелый ML-метод"),
    ("Contrastive Learning for Self-Supervised Representation", "Зрелый ML-метод"),
    ("Masked Language Modeling", "Зрелый ML-метод"),
    ("Causal Inference with Deep Learning", "Общая ML-статья"),
    ("Meta-Learning for Few-Shot Classification", "Зрелый ML-метод"),
    ("Multi-Task Learning with Shared Representations", "Зрелый ML-метод"),
    ("Attention Is All You Need", "Зрелая архитектура"),
    ("Deep Residual Learning for Image Recognition", "Зрелая архитектура"),
    ("Generative Adversarial Networks", "Зрелая архитектура"),
    ("Variational Autoencoders", "Зрелая архитектура"),
    ("Graph Convolutional Networks", "Зрелая архитектура"),
    ("Recurrent Neural Networks", "Зрелая архитектура"),
    ("Long Short-Term Memory Networks", "Зрелая архитектура"),
    ("Gated Recurrent Units", "Зрелая архитектура"),
    ("Convolutional Neural Networks", "Зрелая архитектура"),
    ("Transformer Networks", "Зрелая архитектура"),

    # Общие NLP
    ("Named Entity Recognition with BERT", "Зрелый NLP-метод"),
    ("Sentiment Analysis with Transformers", "Зрелый NLP-метод"),
    ("Machine Translation with Attention", "Зрелый NLP-метод"),
    ("Question Answering with BERT", "Зрелый NLP-метод"),
    ("Text Summarization with Transformers", "Зрелый NLP-метод"),
    ("Text Classification with Deep Learning", "Зрелый NLP-метод"),
    ("Word Embeddings with Word2Vec", "Зрелый NLP-метод"),
    ("GloVe Global Vectors", "Зрелый NLP-метод"),
    ("FastText for Text Classification", "Зрелый NLP-метод"),
    ("ELMo Embeddings", "Зрелый NLP-метод"),

    # Общие CV
    ("Image Classification with ResNet", "Зрелый CV-метод"),
    ("Object Detection with YOLO", "Зрелый CV-метод"),
    ("Semantic Segmentation with U-Net", "Зрелый CV-метод"),
    ("Instance Segmentation with Mask R-CNN", "Зрелый CV-метод"),
    ("Pose Estimation with OpenPose", "Зрелый CV-метод"),
    ("Face Recognition with FaceNet", "Зрелый CV-метод"),
    ("Optical Flow with FlowNet", "Зрелый CV-метод"),
    ("Depth Estimation with MiDaS", "Зрелый CV-метод"),
    ("Style Transfer with Neural Networks", "Зрелый CV-метод"),
    ("Image Generation with GANs", "Зрелый CV-метод"),

    # Общие RL
    ("Deep Q-Learning", "Зрелый RL-метод"),
    ("Proximal Policy Optimization", "Зрелый RL-метод"),
    ("Trust Region Policy Optimization", "Зрелый RL-метод"),
    ("Soft Actor-Critic", "Зрелый RL-метод"),
    ("Twin Delayed DDPG", "Зрелый RL-метод"),
    ("A3C Asynchronous Advantage Actor-Critic", "Зрелый RL-метод"),
    ("DDPG Deep Deterministic Policy Gradient", "Зрелый RL-метод"),
    ("Monte Carlo Tree Search", "Зрелый RL-метод"),
    ("AlphaZero Reinforcement Learning", "Зрелая RL-система"),
    ("MuZero Reinforcement Learning", "Зрелая RL-система"),

    # Общие финтех-статьи (не weak)
    ("Вариационные квантовые алгоритмы для оптимизации портфеля кредитов", "Квантовые алгоритмы, не банковский сигнал"),
    ("Квантовые вычисления для финансового моделирования", "Квантовые вычисления, не банковский сигнал"),
    ("Machine Learning for Credit Scoring", "Зрелый ML-метод в финансах"),
    ("Fraud Detection with Random Forest", "Зрелый ML-метод в финансах"),
    ("Time Series Forecasting with ARIMA", "Зрелый статистический метод"),
    ("Time Series Forecasting with LSTM", "Зрелый ML-метод"),
    ("Risk Management with Monte Carlo", "Зрелый статистический метод"),
    ("Portfolio Optimization with Markowitz", "Зрелая теория"),
    ("Black-Scholes Option Pricing", "Зрелая теория"),
    ("Value at Risk Models", "Зрелый финансовый метод"),

    # Общие обзоры
    ("A Survey of Deep Learning Methods", "Обзор без конкретной технологии"),
    ("A Review of Machine Learning in Finance", "Обзор без конкретной технологии"),
    ("Systematic Review of NLP Methods", "Обзор без конкретной технологии"),
    ("Literature Review on Graph Neural Networks", "Обзор без конкретной технологии"),
    ("Meta-Analysis of Reinforcement Learning", "Обзор без конкретной технологии"),

    # Общие статьи про методы
    ("Feature Engineering for Machine Learning", "Зрелый ML-метод"),
    ("Hyperparameter Optimization", "Зрелый ML-метод"),
    ("Cross-Validation Techniques", "Зрелый ML-метод"),
    ("Ensemble Methods", "Зрелый ML-метод"),
    ("Bagging and Boosting", "Зрелый ML-метод"),
    ("Gradient Boosting Machines", "Зрелый ML-метод"),
    ("Random Forest Algorithm", "Зрелый ML-метод"),
    ("Support Vector Machines", "Зрелый ML-метод"),
    ("Logistic Regression", "Зрелый статистический метод"),
    ("Linear Regression", "Зрелый статистический метод"),
    ("Principal Component Analysis", "Зрелый статистический метод"),
    ("t-SNE Dimensionality Reduction", "Зрелый ML-метод"),
    ("UMAP Dimensionality Reduction", "Зрелый ML-метод"),
    ("K-Means Clustering", "Зрелый ML-метод"),
    ("DBSCAN Clustering", "Зрелый ML-метод"),
]


def add():
    db = SessionLocal()
    saved = 0
    skipped = 0
    try:
        for name, desc in IRRELEVANT_NEGATIVE:
            if db.query(RawNegativeSignal).filter(RawNegativeSignal.name == name).first():
                skipped += 1
                continue
            db.add(RawNegativeSignal(
                name=name,
                description=desc,
                source="irrelevant_negative",
                year=2020,
            ))
            saved += 1
        db.commit()
        logger.info(f"[irrelevant_negative] saved {saved}, skipped {skipped}, total {len(IRRELEVANT_NEGATIVE)}")
    except Exception as e:
        db.rollback()
        logger.error(f"[irrelevant_negative] {e}")
    finally:
        db.close()


if __name__ == "__main__":
    add()