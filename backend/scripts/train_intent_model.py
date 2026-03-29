"""
train_intent_model.py
=====================
One-time training script for the ZaraiLink intent classifier (SetFit).

Usage (from backend/):
    python scripts/train_intent_model.py

Output:
    backend/models/zarai_intent_model/   (load with SetFitModel.from_pretrained)

DO NOT import this file from Django. It is run once, manually.
"""

import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Resolve paths
# ---------------------------------------------------------------------------
SCRIPT_DIR  = Path(__file__).resolve().parent          # backend/scripts/
BACKEND_DIR = SCRIPT_DIR.parent                        # backend/
CSV_PATH    = SCRIPT_DIR / "training_data.csv"
MODEL_OUT   = BACKEND_DIR / "models" / "zarai_intent_model"

# ---------------------------------------------------------------------------
# Validate input
# ---------------------------------------------------------------------------
if not CSV_PATH.exists():
    print(f"[ERROR] training_data.csv not found at: {CSV_PATH}")
    sys.exit(1)

print(f"[INFO] Loading training data from: {CSV_PATH}")

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
import pandas as pd

df = pd.read_csv(CSV_PATH)

# Normalize: lowercase labels, drop empties
df = df.dropna(subset=["query", "intent"])
df["query"]  = df["query"].astype(str).str.strip()
df["intent"] = df["intent"].astype(str).str.strip().str.lower()

# Map labels to integers: buy -> 0, sell -> 1
label_map = {"buy": 0, "sell": 1}
df["label"] = df["intent"].map(label_map)

unknown = df["label"].isna()
if unknown.any():
    bad = df.loc[unknown, "intent"].unique().tolist()
    print(f"[WARN] Dropping {unknown.sum()} rows with unknown labels: {bad}")
    df = df.dropna(subset=["label"])

df["label"] = df["label"].astype(int)

print(f"[INFO] Total examples: {len(df)}  |  BUY: {(df['label']==0).sum()}  |  SELL: {(df['label']==1).sum()}")

# ---------------------------------------------------------------------------
# Train / test split (80/20, stratified)
# ---------------------------------------------------------------------------
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(
    df["query"].tolist(),
    df["label"].tolist(),
    test_size=0.20,
    random_state=42,
    stratify=df["label"],
)

print(f"[INFO] Train: {len(X_train)}  |  Test: {len(X_test)}")

# ---------------------------------------------------------------------------
# SetFit training
# ---------------------------------------------------------------------------
from datasets import Dataset
from setfit import SetFitModel, Trainer, TrainingArguments

BASE_MODEL = "sentence-transformers/paraphrase-MiniLM-L6-v2"
print(f"[INFO] Loading base model: {BASE_MODEL}")

model = SetFitModel.from_pretrained(BASE_MODEL, labels=["BUY", "SELL"])

train_dataset = Dataset.from_dict({"text": X_train, "label": y_train})
test_dataset  = Dataset.from_dict({"text": X_test,  "label": y_test})

args = TrainingArguments(
    num_epochs=3,
    batch_size=16,
    evaluation_strategy="epoch",
)

trainer = Trainer(
    model=model,
    args=args,
    train_dataset=train_dataset,
    eval_dataset=test_dataset,
    metric="accuracy",
)

print("[INFO] Training SetFit model ...")
trainer.train()

# ---------------------------------------------------------------------------
# Evaluate
# ---------------------------------------------------------------------------
metrics = trainer.evaluate()
print(f"\n[RESULT] Test accuracy: {metrics.get('accuracy', 'N/A'):.4f}")

# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------
MODEL_OUT.mkdir(parents=True, exist_ok=True)
model.save_pretrained(str(MODEL_OUT))
print(f"\n[INFO] Model saved to: {MODEL_OUT}")
print("[INFO] Training complete.")
