"""
train_intent.py - SetFit Intent Classifier Training
=====================================================
Trains a few-shot BUY/SELL intent classifier using:
  Backbone : BAAI/bge-small-en-v1.5 (SOTA small encoder, SetFit-compatible)
  Framework: SetFit (contrastive fine-tuning, no need for large labelled sets)

NOTE: We originally planned to use answerdotai/ModernBERT-base, but it requires
transformers>=4.48 which conflicts with SetFit 1.1.x (needs transformers<4.42).
BAAI/bge-small-en-v1.5 is a production-grade replacement — faster, smaller, and
consistently top-ranked on the MTEB leaderboard for retrieval/classification tasks.

Labels:
  0 - BUY  (user wants to find a supplier / import goods)
  1 - SELL (user wants to find a buyer  / export goods)

Output: models/intent_model/  (Hugging-Face-compatible directory)

Usage:
    cd backend
    .venv\\Scripts\\activate
    pip install setfit
    python -m search.services.train_intent
"""

import os
import logging
from datasets import Dataset
from setfit import SetFitModel, Trainer, TrainingArguments

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 0. Output path
# ---------------------------------------------------------------------------
MODEL_OUTPUT = os.path.join(os.path.dirname(__file__), "..", "models", "intent_model")
os.makedirs(MODEL_OUTPUT, exist_ok=True)

# ---------------------------------------------------------------------------
# 1. Seed Training Data  (8-12 examples per class is enough for SetFit)
# ---------------------------------------------------------------------------
TRAIN_TEXTS = [
    # ── BUY (label 0) ──────────────────────────────────────────────────────
    "Looking for sugar suppliers from Brazil",
    "I want to buy refined sugar",
    "Find me importers of rice from Vietnam",
    "Purchase lactose from abroad",
    "We need to import crude palm oil",
    "Who are the top suppliers of dextrose monohydrate?",
    "Source cotton from India",
    "Looking to procure fertilizers from China",
    "Import leather from Italy below $800",
    "Find top 5 wheat suppliers from Australia",
    "I am interested in buying soybean meal",
    "Best importers of edible salt worldwide",
    "Need to buy synthetic yarn with monthly shipments",
    "Which countries export the most basmati rice?",
    "Looking for reliable polyethylene suppliers",
    # ── SELL (label 1) ─────────────────────────────────────────────────────
    "Looking for rice buyers in Dubai",
    "Find buyers for our pink Himalayan salt",
    "I want to export cotton to the UAE",
    "Who is importing Pakistani mangoes?",
    "We have 500 MT of raw sugar to sell",
    "Seeking buyers for our Basmati rice in Europe",
    "Export our leather goods to buyers in Germany",
    "Find me companies that buy surgical instruments",
    "I want to sell synthetic fibre internationally",
    "Market for Pakistani Kinnow in Russia",
    "Looking for cement buyers in Africa",
    "Identify importers of Pakistani textile",
    "We produce rock salt and need international buyers",
    "Who buys halal meat from Pakistan?",
    "Find demand for our engineering goods in Europe",
]

TRAIN_LABELS = (
    [0] * 15  # BUY
    + [1] * 15  # SELL
)

# ---------------------------------------------------------------------------
# 2. Evaluation Data (held-out)
# ---------------------------------------------------------------------------
EVAL_TEXTS = [
    "source chemicals from China",          # BUY
    "I need to import machinery",           # BUY
    "find buyers for our wheat",            # SELL
    "export Pakistani dates to UK",         # SELL
]
EVAL_LABELS = [0, 0, 1, 1]

# ---------------------------------------------------------------------------
# 3. Build HuggingFace Datasets
# ---------------------------------------------------------------------------
train_ds = Dataset.from_dict({"text": TRAIN_TEXTS, "label": TRAIN_LABELS})
eval_ds  = Dataset.from_dict({"text": EVAL_TEXTS,  "label": EVAL_LABELS})

# ---------------------------------------------------------------------------
# 4. Load SetFit Model (body only first)
# ---------------------------------------------------------------------------
logger.info("Loading SetFit backbone: BAAI/bge-small-en-v1.5 ...")
model = SetFitModel.from_pretrained(
    "BAAI/bge-small-en-v1.5",
    labels=["BUY", "SELL"],
)

# ---------------------------------------------------------------------------
# 5. Training Arguments (contrastive body training only)
# ---------------------------------------------------------------------------
args = TrainingArguments(
    output_dir=MODEL_OUTPUT,
    num_epochs=3,
    batch_size=8,
    num_iterations=20,
    eval_strategy="no",       # skip eval to avoid Trainer head complications
    save_strategy="no",       # we handle saving ourselves
)

# ---------------------------------------------------------------------------
# 6. Train the body (SentenceTransformer fine-tuning via contrastive pairs)
# ---------------------------------------------------------------------------
trainer = Trainer(
    model=model,
    args=args,
    train_dataset=train_ds,
)

logger.info("Starting SetFit contrastive training ...")
trainer.train()

# ---------------------------------------------------------------------------
# 7. Manually fit the sklearn head on full training embeddings
#    and persist everything explicitly.
# ---------------------------------------------------------------------------
import joblib
import torch

logger.info("Fitting classification head on training embeddings ...")

# Generate embeddings using the trained body
with torch.no_grad():
    train_embeddings = model.model_body.encode(TRAIN_TEXTS, batch_size=16, convert_to_numpy=True)

# Fit the sklearn head
model.model_head.fit(train_embeddings, TRAIN_LABELS)
logger.info("Head fitted.")

# Save the SentenceTransformer body
model.model_body.save(MODEL_OUTPUT)
logger.info(f"Body saved to: {MODEL_OUTPUT}")

# Explicitly save the sklearn head
head_path = os.path.join(MODEL_OUTPUT, "model_head.pkl")
joblib.dump(model.model_head, head_path)
logger.info(f"Head saved to: {head_path}")

# Also save model config so SetFitModel.from_pretrained() can read it
import json as _json
config_path = os.path.join(MODEL_OUTPUT, "config_setfit.json")
with open(config_path, "w") as f:
    _json.dump({"id2label": {0: "BUY", 1: "SELL"}, "label2id": {"BUY": 0, "SELL": 1}}, f)

# ---------------------------------------------------------------------------
# 8. Quick smoke test
# ---------------------------------------------------------------------------
smoke = [
    "I want to buy sugar from Vietnam",
    "Looking for buyers for our rice",
    "Find top suppliers of palm oil",
    "Export leather goods to Germany",
]
with torch.no_grad():
    smoke_embeddings = model.model_body.encode(smoke, batch_size=16, convert_to_numpy=True)
preds = model.model_head.predict(smoke_embeddings)
print("\n-- Smoke Test --")
for text, pred in zip(smoke, preds):
    label = "BUY" if int(pred) == 0 else "SELL"
    print(f"  [{label}] {text}")
print("Training complete! model_head.pkl saved.")

