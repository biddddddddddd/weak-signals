from src.scoring.scorer import score_text
from src.db.connection import SessionLocal
from loguru import logger

TEXT = """Latent Dynamics Models for Stable Long-Horizon Rollout

We propose a novel approach to modeling latent dynamics for stable long-horizon rollout in reinforcement learning. Our method combines variational inference with sequence models to learn compact latent representations. We demonstrate improved stability on benchmark tasks including robotic control and navigation. The approach shows promise for long-horizon planning but requires further validation."""

db = SessionLocal()
result = score_text(db, TEXT, query="слабые сигналы в банкинге", top_k=5, use_classifier=False)
db.close()

print("=" * 80)
print("LLM РЕЗУЛЬТАТ для Latent Dynamics Models")
print("=" * 80)
for k, v in result.items():
    if k in ("retrieval_weak", "retrieval_negative"):
        continue
    print(f"  {k}: {v}")
print()
print("retrieval_weak:", result.get("retrieval_weak"))
print("retrieval_negative:", result.get("retrieval_negative"))