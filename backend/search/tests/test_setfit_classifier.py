"""
Tests for SetFitIntentClassifier (Phase 3-C/3-D).

Unit tests use a mocked SetFit model — no trained model needed.
Integration tests marked @pytest.mark.slow require the trained model.
"""

import pytest
import numpy as np
from unittest.mock import MagicMock, patch


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_classifier(loaded=True):
    """Return a fresh SetFitIntentClassifier with load bypassed."""
    import importlib
    import search.services.setfit_classifier as m
    # Reset singleton and class state
    m._classifier_instance = None
    from search.services.setfit_classifier import SetFitIntentClassifier
    clf = SetFitIntentClassifier()
    clf.__class__._load_attempted = True   # prevent real _load()
    clf.__class__._loaded = loaded
    if loaded:
        clf.__class__._labels = [
            'BUY', 'F3_VOLUME', 'F4_PRICE', 'F5_TIME',
            'F6_TOPK', 'F7_COMPARE', 'F8_EVIDENCE', 'SELL'
        ]
        clf.__class__._model = MagicMock()
    else:
        clf.__class__._model = None
    return clf


def _set_proba(clf, probs: list):
    """Make clf._model.predict_proba return a specific probability row."""
    arr = np.array([probs], dtype=np.float32)
    clf._model.predict_proba.return_value = arr


# ── Unit tests ────────────────────────────────────────────────────────────────

class TestSetFitClassifierUnit:

    def test_predict_returns_tuple(self):
        clf = _make_classifier()
        probs = [0.9, 0.02, 0.02, 0.02, 0.01, 0.01, 0.01, 0.01]
        _set_proba(clf, probs)
        label, conf = clf.predict("who sells dextrose")
        assert isinstance(label, str)
        assert isinstance(conf, float)

    def test_predict_buy_high_confidence(self):
        clf = _make_classifier()
        # BUY is index 0 in labels list
        probs = [0.95, 0.01, 0.01, 0.01, 0.01, 0.0, 0.0, 0.01]
        _set_proba(clf, probs)
        label, conf = clf.predict("find sugar importers")
        assert label == 'BUY'
        assert conf == pytest.approx(0.95, abs=1e-5)

    def test_predict_sell_high_confidence(self):
        clf = _make_classifier()
        # SELL is index 7
        probs = [0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.93]
        _set_proba(clf, probs)
        label, conf = clf.predict("find buyers for our cotton")
        assert label == 'SELL'
        assert conf == pytest.approx(0.93, abs=1e-5)

    def test_predict_f6_topk(self):
        clf = _make_classifier()
        # F6_TOPK is index 4
        probs = [0.02, 0.02, 0.02, 0.02, 0.88, 0.02, 0.01, 0.01]
        _set_proba(clf, probs)
        label, conf = clf.predict("top 5 dextrose suppliers")
        assert label == 'F6_TOPK'
        assert conf >= 0.85

    def test_predict_not_loaded_returns_unknown(self):
        clf = _make_classifier(loaded=False)
        label, conf = clf.predict("any query")
        assert label == 'UNKNOWN'
        assert conf == 0.0

    def test_predict_model_exception_returns_unknown(self):
        clf = _make_classifier()
        clf._model.predict_proba.side_effect = RuntimeError("mock error")
        label, conf = clf.predict("sugar suppliers")
        assert label == 'UNKNOWN'
        assert conf == 0.0

    def test_is_ready_true_when_loaded(self):
        clf = _make_classifier(loaded=True)
        assert clf.is_ready() is True

    def test_is_ready_false_when_not_loaded(self):
        clf = _make_classifier(loaded=False)
        assert clf.is_ready() is False

    def test_singleton_returns_same_instance(self):
        import search.services.setfit_classifier as m
        m._classifier_instance = None
        from search.services.setfit_classifier import get_setfit_classifier
        c1 = get_setfit_classifier()
        c2 = get_setfit_classifier()
        assert c1 is c2
        m._classifier_instance = None

    def test_labels_coverage(self):
        """All SETFIT_TO_FAMILY keys should be valid labels."""
        from search.services.setfit_classifier import SETFIT_TO_FAMILY
        expected = {'BUY', 'SELL', 'F3_VOLUME', 'F4_PRICE', 'F5_TIME',
                    'F6_TOPK', 'F7_COMPARE', 'F8_EVIDENCE'}
        assert set(SETFIT_TO_FAMILY.keys()) == expected

    def test_setfit_to_family_mapping(self):
        from search.services.setfit_classifier import SETFIT_TO_FAMILY
        assert SETFIT_TO_FAMILY['BUY']        == ('BUY',  1)
        assert SETFIT_TO_FAMILY['SELL']       == ('SELL', 2)
        assert SETFIT_TO_FAMILY['F3_VOLUME']  == ('BUY',  3)
        assert SETFIT_TO_FAMILY['F4_PRICE']   == ('BUY',  4)
        assert SETFIT_TO_FAMILY['F5_TIME']    == ('BUY',  5)
        assert SETFIT_TO_FAMILY['F6_TOPK']    == ('BUY',  6)
        assert SETFIT_TO_FAMILY['F7_COMPARE'] == ('BUY',  7)
        assert SETFIT_TO_FAMILY['F8_EVIDENCE']== ('BUY',  8)

    def test_missing_model_dir_does_not_raise(self):
        """If model dir doesn't exist, _load should handle gracefully."""
        import search.services.setfit_classifier as m
        original_dir = m._MODEL_DIR
        m._MODEL_DIR = '/nonexistent/path/setfit_model'
        from search.services.setfit_classifier import SetFitIntentClassifier
        clf = SetFitIntentClassifier()
        clf.__class__._load_attempted = False
        clf.__class__._loaded = False
        clf.__class__._model = None
        # Should not raise
        clf._load()
        assert clf._loaded is False
        m._MODEL_DIR = original_dir

    def test_confidence_threshold_value(self):
        from search.services.setfit_classifier import CONFIDENCE_THRESHOLD
        assert CONFIDENCE_THRESHOLD == pytest.approx(0.70, abs=1e-5)


# ── Query parser integration ──────────────────────────────────────────────────

class TestQueryParserSetFitIntegration:
    """Tests that query_parser.py correctly uses SetFit output."""

    def _make_interpreter(self):
        import django
        import os
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
        try:
            django.setup()
        except RuntimeError:
            pass
        from search.services.query_parser import QueryInterpreter
        return QueryInterpreter()

    def test_setfit_overrides_family_when_high_confidence(self):
        """When SetFit returns confidence >= 0.70, it should override family."""
        interpreter = self._make_interpreter()
        with patch('search.services.query_parser._USE_SETFIT', True):
            with patch('search.services.setfit_classifier.get_setfit_classifier') as mock_get:
                mock_clf = MagicMock()
                mock_clf.is_ready.return_value = True
                mock_clf.predict.return_value = ('F6_TOPK', 0.92)
                mock_get.return_value = mock_clf

                result = interpreter.parse("top 5 sugar suppliers")

        assert result['family'] == 6
        assert result['intent'] == 'BUY'
        assert result['classifier_confidence'] == pytest.approx(0.92, abs=1e-5)

    def test_setfit_ignored_when_low_confidence(self):
        """When SetFit confidence < 0.70, regex result should be preserved."""
        interpreter = self._make_interpreter()
        with patch('search.services.query_parser._USE_SETFIT', True):
            with patch('search.services.setfit_classifier.get_setfit_classifier') as mock_get:
                mock_clf = MagicMock()
                mock_clf.is_ready.return_value = True
                mock_clf.predict.return_value = ('F6_TOPK', 0.50)
                mock_get.return_value = mock_clf

                result = interpreter.parse("find dextrose suppliers")

        # Regex-only result should stand (family=1 for a basic BUY query)
        assert result['family'] != 6 or result.get('classifier_confidence', 0) < 0.70
        assert result['classifier_confidence'] == pytest.approx(0.50, abs=1e-5)

    def test_classifier_confidence_field_always_present(self):
        """classifier_confidence key must always be in result."""
        interpreter = self._make_interpreter()
        result = interpreter.parse("who sells dextrose")
        assert 'classifier_confidence' in result

    def test_setfit_not_called_when_disabled(self):
        """When _USE_SETFIT=False, classifier should not be called."""
        interpreter = self._make_interpreter()
        with patch('search.services.query_parser._USE_SETFIT', False):
            with patch('search.services.setfit_classifier.get_setfit_classifier') as mock_get:
                result = interpreter.parse("sugar suppliers")
        mock_get.assert_not_called()
        assert result.get('classifier_confidence', 0.0) == 0.0

    def test_setfit_failure_does_not_break_pipeline(self):
        """If SetFit raises, pipeline must still return a valid result."""
        interpreter = self._make_interpreter()
        with patch('search.services.query_parser._USE_SETFIT', True):
            with patch('search.services.setfit_classifier.get_setfit_classifier') as mock_get:
                mock_get.side_effect = RuntimeError("setfit broken")
                result = interpreter.parse("find palm oil suppliers")
        assert 'intent' in result
        assert 'family' in result


# ── Integration tests (require trained model) ─────────────────────────────────

@pytest.mark.slow
class TestSetFitClassifierIntegration:

    def test_predict_buy_query(self):
        from search.services.setfit_classifier import SetFitIntentClassifier
        clf = SetFitIntentClassifier()
        clf.__class__._load_attempted = False
        if not clf.is_ready():
            pytest.skip("SetFit model not trained yet")
        label, conf = clf.predict("find sugar importers")
        assert label in ('BUY', 'SELL', 'F3_VOLUME', 'F4_PRICE',
                         'F5_TIME', 'F6_TOPK', 'F7_COMPARE', 'F8_EVIDENCE')
        assert 0.0 <= conf <= 1.0

    def test_predict_topk_query(self):
        from search.services.setfit_classifier import SetFitIntentClassifier
        clf = SetFitIntentClassifier()
        clf.__class__._load_attempted = False
        if not clf.is_ready():
            pytest.skip("SetFit model not trained yet")
        label, conf = clf.predict("top 5 dextrose anhydrous suppliers")
        assert label == 'F6_TOPK'
        assert conf >= 0.70
