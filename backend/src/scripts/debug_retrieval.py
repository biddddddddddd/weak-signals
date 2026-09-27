from src.embeddings.retrieval import find_similar
from src.db.connection import SessionLocal

TEXT = """Latent Dynamics Models for Stable Long-Horizon Rollout

We propose a novel approach to modeling latent dynamics for stable long-horizon rollout in reinforcement learning. Our method combines variational inference with sequence models to learn compact latent representations."""

db = SessionLocal()
results = find_similar(db, TEXT, top_k=10, include_negatives=True)
db.close()

print("=" * 80)
print("RETRIEVAL для Latent Dynamics Models")
print("=" * 80)
for r in results:
    print(f"  [{r['type']:8}] {r['score']:.3f}  {r['name'][:70]}")