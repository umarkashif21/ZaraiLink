"""
backend/search/services/setfit_classifier.py

SetFit intent classifier service for Zarailink query classification.

Maps SetFit class labels → (intent, family):
  BUY        → intent='BUY',  family=1
  SELL       → intent='SELL', family=2
  F3_VOLUME  → intent='BUY',  family=3
  F4_PRICE   → intent='BUY',  family=4
  F5_TIME    → intent='BUY',  family=5
  F6_TOPK    → intent='BUY',  family=6
  F7_COMPARE → intent='BUY',  family=7
  F8_EVIDENCE→ intent='BUY',  family=8

Usage:
    from search.services.setfit_classifier import get_setfit_classifier
    clf = get_setfit_classifier()
    label, confidence = clf.predict("top 5 dextrose suppliers")
"""

import os
import logging

logger = logging.getLogger(__name__)

# Path relative to this file: ../../models/setfit_intent_classifier/
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_MODEL_DIR = os.path.join(_THIS_DIR, '..', 'models', 'setfit_intent_classifier')
_MODEL_DIR = os.path.normpath(_MODEL_DIR)

# SetFit class label → (intent, family)
SETFIT_TO_FAMILY = {
    'BUY':        ('BUY',  1),
    'SELL':       ('SELL', 2),
    'F3_VOLUME':  ('BUY',  3),
    'F4_PRICE':   ('BUY',  4),
    'F5_TIME':    ('BUY',  5),
    'F6_TOPK':    ('BUY',  6),
    'F7_COMPARE': ('BUY',  7),
    'F8_EVIDENCE':('BUY',  8),
}

CONFIDENCE_THRESHOLD = 0.70


class SetFitIntentClassifier:
    """
    Lazy-loading SetFit intent classifier.

    predict(query) → (class_label: str, confidence: float)

    Returns ('UNKNOWN', 0.0) when model is not loaded or prediction fails.
    """

    _model = None
    _labels = None
    _loaded = False
    _load_attempted = False

    def _load(self):
        if self._load_attempted:
            return
        self.__class__._load_attempted = True

        if not os.path.isdir(_MODEL_DIR):
            logger.warning(
                f"SetFit model directory not found: {_MODEL_DIR}. "
                "Run training_scripts/train_setfit_intent.py first."
            )
            return

        try:
            from setfit import SetFitModel
            import json

            logger.info(f"Loading SetFit intent classifier from {_MODEL_DIR}")
            self.__class__._model = SetFitModel.from_pretrained(_MODEL_DIR)

            meta_path = os.path.join(_MODEL_DIR, 'metadata.json')
            if os.path.exists(meta_path):
                with open(meta_path) as f:
                    meta = json.load(f)
                self.__class__._labels = meta.get('labels', [])
            else:
                # Fallback label order
                self.__class__._labels = sorted(SETFIT_TO_FAMILY.keys())

            self.__class__._loaded = True
            logger.info(
                f"SetFit classifier ready. Labels: {self._labels}"
            )
        except Exception as e:
            logger.warning(f"SetFit classifier failed to load: {e}")

    def predict(self, query: str):
        """
        Predict intent class and confidence for query.

        Returns:
            (class_label: str, confidence: float)
            Falls back to ('UNKNOWN', 0.0) on any failure.
        """
        if not self._loaded:
            self._load()

        if not self._loaded or self._model is None:
            return ('UNKNOWN', 0.0)

        try:
            import numpy as np

            # predict_proba returns shape (n_samples, n_classes)
            probs = self._model.predict_proba([query])  # shape (1, n_classes)
            probs_row = probs[0]  # shape (n_classes,)

            best_idx = int(np.argmax(probs_row))
            confidence = float(probs_row[best_idx])

            if self._labels and best_idx < len(self._labels):
                label = self._labels[best_idx]
            else:
                label = 'UNKNOWN'

            return (label, confidence)

        except Exception as e:
            logger.warning(f"SetFit predict failed: {e}")
            return ('UNKNOWN', 0.0)

    def is_ready(self) -> bool:
        """Return True if the model is loaded and ready."""
        if not self._load_attempted:
            self._load()
        return self._loaded


# Module-level singleton
_classifier_instance = None


def get_setfit_classifier() -> SetFitIntentClassifier:
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = SetFitIntentClassifier()
    return _classifier_instance
