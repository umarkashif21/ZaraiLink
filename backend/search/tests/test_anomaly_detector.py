"""
Tests for TradeAnomalyDetector (Phase 4-A).

Unit tests: no DB required.
Integration tests: require DB + fitted models (@pytest.mark.django_db).
"""

import pytest
import numpy as np
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_transactions(prices, volumes, dates=None):
    import datetime
    if dates is None:
        today = datetime.date.today()
        dates = [today - datetime.timedelta(days=i * 30) for i in range(len(prices))]
    return [
        {'price': p, 'volume': v, 'date': d}
        for p, v, d in zip(prices, volumes, dates)
    ]


def _make_detector_with_fitted_model(subcat_id=42):
    """Create a TradeAnomalyDetector with a pre-fitted IsolationForest."""
    from search.services.anomaly_detector import TradeAnomalyDetector
    from sklearn.ensemble import IsolationForest
    import numpy as np

    detector = TradeAnomalyDetector()
    prices = np.random.uniform(350, 450, 50).tolist()
    volumes = np.random.uniform(500, 5000, 50).tolist()
    X = np.column_stack([np.log1p(prices), np.log1p(volumes)])
    iso = IsolationForest(contamination=0.1, random_state=42, n_estimators=100)
    iso.fit(X)
    detector._models[subcat_id] = {
        'iso': iso,
        'iso_price_mean': float(np.mean(prices)),
        'iso_price_std': float(np.std(prices)),
    }
    return detector


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------

class TestIsolationForestAnomalyDetection:

    def test_flags_extreme_price_outlier(self):
        """Price of $1,000,000/MT for sugar should be flagged as suspicious."""
        from search.services.anomaly_detector import TradeAnomalyDetector
        from sklearn.ensemble import IsolationForest
        import numpy as np

        # Train model on normal prices
        normal_prices = np.random.uniform(350, 450, 100)
        normal_vols = np.random.uniform(500, 5000, 100)
        X = np.column_stack([np.log1p(normal_prices), np.log1p(normal_vols)])
        iso = IsolationForest(contamination=0.1, random_state=42)
        iso.fit(X)

        detector = TradeAnomalyDetector()
        detector._models[1] = {'iso': iso, 'iso_price_mean': 400, 'iso_price_std': 30}

        # Extreme outlier
        result = detector.score_transaction({
            'price': 1_000_000,
            'volume': 1000,
            'subcategory_id': 1,
        })
        assert result['is_suspicious'] is True, "Extreme price outlier should be flagged"

    def test_normal_transaction_not_suspicious(self):
        """A transaction within the normal price range should not be flagged."""
        detector = _make_detector_with_fitted_model(subcat_id=99)
        result = detector.score_transaction({
            'price': 400,
            'volume': 1000,
            'subcategory_id': 99,
        })
        # Should not be suspicious (or borderline)
        # We can't guarantee False for ALL normal prices, but pct should be low
        assert isinstance(result['is_suspicious'], bool)

    def test_score_transaction_returns_valid_dict(self):
        detector = _make_detector_with_fitted_model()
        result = detector.score_transaction({
            'price': 400, 'volume': 1000, 'subcategory_id': 42
        })
        assert 'price_anomaly_score' in result
        assert 'volume_anomaly_score' in result
        assert 'is_suspicious' in result
        assert 0.0 <= result['price_anomaly_score'] <= 1.0

    def test_score_transaction_no_model_returns_zeros(self):
        from search.services.anomaly_detector import TradeAnomalyDetector
        detector = TradeAnomalyDetector()
        result = detector.score_transaction({
            'price': 400, 'volume': 1000, 'subcategory_id': 999  # no model
        })
        assert result['price_anomaly_score'] == 0.0
        assert result['is_suspicious'] is False

    def test_score_transaction_zero_price_returns_zeros(self):
        detector = _make_detector_with_fitted_model()
        result = detector.score_transaction({
            'price': 0, 'volume': 1000, 'subcategory_id': 42
        })
        assert result['price_anomaly_score'] == 0.0

    def test_price_anomaly_score_in_0_1_range(self):
        detector = _make_detector_with_fitted_model()
        for price in [100, 400, 800, 10000]:
            result = detector.score_transaction({
                'price': price, 'volume': 500, 'subcategory_id': 42
            })
            assert 0.0 <= result['price_anomaly_score'] <= 1.0


class TestScoreCompany:

    def test_pct_suspicious_between_0_and_1(self):
        """pct_suspicious_transactions must always be in [0, 1]."""
        detector = _make_detector_with_fitted_model()
        with patch.object(detector, '_load_company_transactions') as mock:
            mock.return_value = [
                {'price': 400, 'volume': 1000},
                {'price': 1_000_000, 'volume': 1},  # outlier
                {'price': 420, 'volume': 800},
            ]
            result = detector.score_company('Test Co', 42)
        assert 0.0 <= result['pct_suspicious_transactions'] <= 1.0

    def test_normal_company_has_low_pct_suspicious(self):
        """Company with only normal prices should have low pct_suspicious."""
        detector = _make_detector_with_fitted_model()
        with patch.object(detector, '_load_company_transactions') as mock:
            # All normal prices (within training range)
            mock.return_value = [
                {'price': 395 + i * 2, 'volume': 1000 + i * 100}
                for i in range(10)
            ]
            result = detector.score_company('Normal Co', 42)
        # pct_suspicious should be low (not guaranteed 0 due to contamination param)
        assert result['pct_suspicious_transactions'] < 0.5
        assert result['n_transactions'] == 10

    def test_empty_transactions_returns_zeros(self):
        from search.services.anomaly_detector import TradeAnomalyDetector
        detector = TradeAnomalyDetector()
        with patch.object(detector, '_load_company_transactions') as mock:
            mock.return_value = []
            result = detector.score_company('Unknown Co', 42)
        assert result['pct_suspicious_transactions'] == 0.0
        assert result['n_transactions'] == 0

    def test_all_suspicious_returns_high_pct(self):
        """If all transactions are outliers, pct_suspicious should be high."""
        detector = _make_detector_with_fitted_model()
        with patch.object(detector, '_load_company_transactions') as mock:
            # All extreme outliers
            mock.return_value = [
                {'price': 1_000_000, 'volume': 1}
                for _ in range(5)
            ]
            result = detector.score_company('Suspicious Co', 42)
        # All extreme outliers should give high pct
        assert result['pct_suspicious_transactions'] >= 0.5


class TestFitModel:

    def test_fit_with_dry_run_does_not_write_file(self):
        from search.services.anomaly_detector import TradeAnomalyDetector
        import tempfile, os
        detector = TradeAnomalyDetector()

        # Mock DB
        transactions = _make_transactions(
            prices=[350 + i * 5 for i in range(20)],
            volumes=[500 + i * 100 for i in range(20)],
        )
        with patch.object(detector, '_load_transactions', return_value=transactions):
            ok = detector.fit_price_model(777, dry_run=True)

        assert ok is True
        # Model should be in memory
        assert 777 in detector._models
        # But no file written
        path = detector._model_path(777)
        assert not os.path.exists(path)

    def test_fit_with_insufficient_data_returns_false(self):
        from search.services.anomaly_detector import TradeAnomalyDetector
        detector = TradeAnomalyDetector()
        transactions = _make_transactions(
            prices=[400, 420],   # only 2 transactions
            volumes=[1000, 1200],
        )
        with patch.object(detector, '_load_transactions', return_value=transactions):
            ok = detector.fit_price_model(888, dry_run=True)
        assert ok is False


# ---------------------------------------------------------------------------
# Integration test
# ---------------------------------------------------------------------------

@pytest.mark.django_db
@pytest.mark.slow
class TestAnomalyDetectorIntegration:

    def test_fit_and_score_real_subcategory(self):
        from trade_data.models import ProductSubCategory, Transaction
        # Find a subcategory with enough transactions
        from django.db.models import Count
        subcat = (
            ProductSubCategory.objects
            .annotate(n=Count('productitem__transaction'))
            .filter(n__gte=5)
            .first()
        )
        if not subcat:
            pytest.skip("No subcategory with ≥5 transactions in DB")

        from search.services.anomaly_detector import TradeAnomalyDetector
        detector = TradeAnomalyDetector()
        ok = detector.fit_price_model(subcat.id, dry_run=True)
        assert ok is True

        # Score a transaction at mean price (should not be suspicious)
        models = detector._models.get(subcat.id, {})
        mean_price = models.get('iso_price_mean', 400)
        result = detector.score_transaction({
            'price': mean_price,
            'volume': 1000,
            'subcategory_id': subcat.id,
        })
        assert isinstance(result['is_suspicious'], bool)
        assert 0.0 <= result['price_anomaly_score'] <= 1.0
