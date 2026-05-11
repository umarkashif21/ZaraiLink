"""SetFit BUY/SELL intent classifier training.

Backbone: BAAI/bge-small-en-v1.5. We avoid answerdotai/ModernBERT-base because
it requires transformers>=4.48 which conflicts with SetFit 1.1.x.

Labels: 0=BUY, 1=SELL. Output: models/intent_model/.
Run: python -m search.services.train_intent
"""

import os
import logging
from datasets import Dataset
from setfit import SetFitModel, Trainer, TrainingArguments

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_OUTPUT = os.path.join(os.path.dirname(__file__), "..", "models", "intent_model")
os.makedirs(MODEL_OUTPUT, exist_ok=True)

# 15 examples per class is plenty for SetFit's contrastive training.
TRAIN_TEXTS = [
    # BUY (label 0)
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
    # SELL (label 1)
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

EVAL_TEXTS = [
    "source chemicals from China",
    "I need to import machinery",
    "find buyers for our wheat",
    "export Pakistani dates to UK",
]
EVAL_LABELS = [0, 0, 1, 1]

train_ds = Dataset.from_dict({"text": TRAIN_TEXTS, "label": TRAIN_LABELS})
eval_ds  = Dataset.from_dict({"text": EVAL_TEXTS,  "label": EVAL_LABELS})

logger.info("Loading SetFit backbone: BAAI/bge-small-en-v1.5 ...")
model = SetFitModel.from_pretrained(
    "BAAI/bge-small-en-v1.5",
    labels=["BUY", "SELL"],
)

# eval_strategy/save_strategy "no" because we fit the sklearn head and save
# manually after contrastive body training.
args = TrainingArguments(
    output_dir=MODEL_OUTPUT,
    num_epochs=3,
    batch_size=8,
    num_iterations=20,
    eval_strategy="no",
    save_strategy="no",
)

trainer = Trainer(
    model=model,
    args=args,
    train_dataset=train_ds,
)

logger.info("Starting SetFit contrastive training ...")
trainer.train()

import joblib
import torch

logger.info("Fitting classification head on training embeddings ...")

with torch.no_grad():
    train_embeddings = model.model_body.encode(TRAIN_TEXTS, batch_size=16, convert_to_numpy=True)

model.model_head.fit(train_embeddings, TRAIN_LABELS)
logger.info("Head fitted.")

model.model_body.save(MODEL_OUTPUT)
logger.info(f"Body saved to: {MODEL_OUTPUT}")

head_path = os.path.join(MODEL_OUTPUT, "model_head.pkl")
joblib.dump(model.model_head, head_path)
logger.info(f"Head saved to: {head_path}")

import json as _json
config_path = os.path.join(MODEL_OUTPUT, "config_setfit.json")
with open(config_path, "w") as f:
    _json.dump({"id2label": {0: "BUY", 1: "SELL"}, "label2id": {"BUY": 0, "SELL": 1}}, f)

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

