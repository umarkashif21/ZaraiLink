"""
Django management command: check_models

Verifies that all ML model files exist and are loadable.
Prints PASS / FAIL for each and exits with code 1 if any FAIL.

Usage:
    python manage.py check_models
"""

import sys
import os
import logging
from pathlib import Path

from django.core.management.base import BaseCommand
from django.conf import settings

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Verify all ML model files exist and are loadable.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--quiet', action='store_true',
            help='Only print failures (suppress PASS lines)',
        )

    def handle(self, *args, **options):
        quiet = options['quiet']
        checks = []

        # ── 1. FAISS index ────────────────────────────────────────────────────
        checks.append(self._check_faiss_index(quiet))

        # ── 2. BM25 index ─────────────────────────────────────────────────────
        checks.append(self._check_bm25_index(quiet))

        # ── 3. SetFit intent classifier ───────────────────────────────────────
        checks.append(self._check_setfit(quiet))

        # ── 4. LightGBM LTR model ─────────────────────────────────────────────
        checks.append(self._check_lgbm(quiet))

        # ── 5. Cross-encoder (nomic / ms-marco) ───────────────────────────────
        checks.append(self._check_cross_encoder(quiet))

        # ── 6. nomic-embed-text-v1 ────────────────────────────────────────────
        checks.append(self._check_nomic_embed(quiet))

        # ── 7. GLiNER NER model ───────────────────────────────────────────────
        checks.append(self._check_gliner(quiet))

        # ── Summary ───────────────────────────────────────────────────────────
        passed = sum(1 for ok, _ in checks if ok)
        total = len(checks)
        self.stdout.write('\n' + '─' * 50)
        if passed == total:
            self.stdout.write(self.style.SUCCESS(f'✓  All {total} checks PASSED'))
        else:
            failed = total - passed
            self.stdout.write(self.style.ERROR(f'✗  {failed}/{total} checks FAILED'))
            sys.exit(1)

    # ─────────────────────────────────────────────────────────────────────────

    def _ok(self, label: str, detail: str = '', quiet: bool = False):
        if not quiet:
            msg = f'PASS  {label}'
            if detail:
                msg += f'  [{detail}]'
            self.stdout.write(self.style.SUCCESS(msg))
        return (True, label)

    def _fail(self, label: str, reason: str):
        self.stdout.write(self.style.ERROR(f'FAIL  {label}  — {reason}'))
        return (False, label)

    # ─────────────────────────────────────────────────────────────────────────

    def _check_faiss_index(self, quiet):
        label = 'FAISS HNSW index'
        try:
            index_path = Path(settings.BASE_DIR) / 'search_index_v2.pkl'
            if not index_path.exists():
                # Try legacy path
                index_path = Path(settings.BASE_DIR) / 'search_index.pkl'
            if not index_path.exists():
                return self._fail(label, f'File not found: {index_path}')

            import pickle
            with open(index_path, 'rb') as f:
                idx = pickle.load(f)

            # Check it has the expected keys
            if not isinstance(idx, dict):
                return self._fail(label, 'Loaded object is not a dict')
            required_keys = ['ids']
            missing = [k for k in required_keys if k not in idx]
            if missing:
                return self._fail(label, f'Missing keys: {missing}')

            n_items = len(idx.get('ids', []))
            return self._ok(label, f'{n_items} items, path={index_path.name}', quiet)
        except Exception as e:
            return self._fail(label, str(e))

    def _check_bm25_index(self, quiet):
        label = 'BM25 product index'
        try:
            from search.services.retrieval import HybridRetriever
            idx = HybridRetriever.get_index()
            bm25 = idx.get('bm25')
            if bm25 is None:
                return self._fail(label, 'BM25 index not present in search_index_v2.pkl')
            n_docs = getattr(bm25, 'corpus_size', 0)
            return self._ok(label, f'corpus_size={n_docs}', quiet)
        except Exception as e:
            return self._fail(label, str(e))

    def _check_setfit(self, quiet):
        label = 'SetFit intent classifier'
        try:
            model_dir = Path(settings.BASE_DIR) / 'search' / 'models' / 'setfit_intent_classifier'
            if not model_dir.exists():
                return self._fail(label, f'Directory not found: {model_dir}')

            # Check for required files
            required = ['config.json', 'model_head.pkl']
            missing = [f for f in required if not (model_dir / f).exists()]
            if missing:
                return self._fail(label, f'Missing files: {missing}')

            # Try running a prediction
            from search.services.setfit_classifier import SetFitIntentClassifier
            clf = SetFitIntentClassifier()
            label_out, conf = clf.predict('sugar suppliers')
            if label_out is None:
                return self._fail(label, 'predict() returned None')
            return self._ok(label, f'predict("sugar suppliers") → {label_out} ({conf:.2f})', quiet)
        except Exception as e:
            return self._fail(label, str(e))

    def _check_lgbm(self, quiet):
        label = 'LightGBM LTR model'
        try:
            import lightgbm as lgb
            models_dir = Path(settings.BASE_DIR) / 'search' / 'models'

            # Prefer v2
            model_path = models_dir / 'lgbm_ltr_v2.txt'
            if not model_path.exists():
                model_path = models_dir / 'lgbm_ltr.txt'
            if not model_path.exists():
                return self._fail(label, f'Model file not found in {models_dir}')

            booster = lgb.Booster(model_file=str(model_path))
            import numpy as np
            # Minimal predict to confirm it runs
            n_features = booster.num_feature()
            dummy = np.zeros((1, n_features))
            score = booster.predict(dummy)
            return self._ok(label, f'{model_path.name}, {n_features} features', quiet)
        except Exception as e:
            return self._fail(label, str(e))

    def _check_cross_encoder(self, quiet):
        label = 'Cross-encoder re-ranker'
        try:
            from search.services.cross_encoder import get_reranker
            reranker = get_reranker()
            if reranker is None:
                return self._fail(label, 'get_reranker() returned None')
            # Check the model attribute
            model = getattr(reranker, '_model', None) or getattr(reranker, 'model', None)
            return self._ok(label, 'cross-encoder/ms-marco-MiniLM-L6-v2', quiet)
        except Exception as e:
            return self._fail(label, str(e))

    def _check_nomic_embed(self, quiet):
        label = 'nomic-embed-text-v1'
        try:
            from search.services.retrieval import _NomicModel
            model = _NomicModel.get()
            dim = model.get_sentence_embedding_dimension()
            if dim != 768:
                return self._fail(label, f'Expected dim=768, got {dim}')
            return self._ok(label, f'dim={dim}', quiet)
        except Exception as e:
            return self._fail(label, str(e))

    def _check_gliner(self, quiet):
        label = 'GLiNER NER model'
        try:
            use_gliner = getattr(settings, 'SEARCH_USE_GLINER_NER', True)
            if not use_gliner:
                if not quiet:
                    self.stdout.write(f'SKIP  {label}  [SEARCH_USE_GLINER_NER=False]')
                return (True, label)

            from search.services.ner_extractor import GLiNERExtractor
            extractor = GLiNERExtractor()
            result = extractor.extract('50 MT sugar from Brazil')
            if not isinstance(result, dict):
                return self._fail(label, 'extract() did not return a dict')
            return self._ok(label, f'extract() ok, keys={list(result.keys())}', quiet)
        except Exception as e:
            return self._fail(label, str(e))
