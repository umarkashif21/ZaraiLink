"""
Tests for Phase 3-G LTR feature extractor (15 features).
"""

import pytest
import datetime
import numpy as np


def _make_candidate(**kwargs):
    defaults = {
        'name': 'Test Co',
        'country': 'China',
        'total_volume': 5000,
        'avg_price': 400,
        'shipment_count': 10,
        'last_shipment_date': datetime.date.today() - datetime.timedelta(days=90),
        'volume_fit': 'Good',
    }
    defaults.update(kwargs)
    return defaults


def _make_parsed_query(**kwargs):
    defaults = {'family': 1, 'country_filter': [], 'price_ceiling': None, 'price_floor': None}
    defaults.update(kwargs)
    return defaults


class TestFeatureExtractorV2:

    def _extractor(self):
        from search.services.ranking_ltr import FeatureExtractor
        return FeatureExtractor()

    def test_returns_15_features(self):
        fe = self._extractor()
        features = fe.extract(_make_candidate(), _make_parsed_query())
        assert len(features) == 15

    def test_all_features_are_floats(self):
        fe = self._extractor()
        features = fe.extract(_make_candidate(), _make_parsed_query())
        for i, f in enumerate(features):
            assert isinstance(f, (int, float)) and not np.isnan(f), \
                f"Feature {i} ({fe.FEATURE_NAMES[i]}) is NaN or non-numeric: {f}"

    def test_no_nan_with_none_values(self):
        """All features produce non-NaN values for a candidate with None fields."""
        fe = self._extractor()
        c = {k: None for k in ['name', 'country', 'total_volume', 'avg_price',
                                'shipment_count', 'last_shipment_date', 'volume_fit']}
        features = fe.extract(c, _make_parsed_query())
        for i, f in enumerate(features):
            assert not np.isnan(f), f"Feature {i} ({fe.FEATURE_NAMES[i]}) is NaN"

    # --- recency_decay_volume (feature 9) ---

    def test_recency_decay_volume_higher_for_recent(self):
        """Same volume, but recent company should have higher recency_decay_volume."""
        fe = self._extractor()
        recent = _make_candidate(total_volume=1000,
                                  last_shipment_date=datetime.date.today() - datetime.timedelta(days=10))
        old = _make_candidate(total_volume=1000,
                               last_shipment_date=datetime.date.today() - datetime.timedelta(days=1000))
        f_recent = fe.extract(recent, _make_parsed_query())
        f_old = fe.extract(old, _make_parsed_query())
        # Index 8 = recency_decay_volume
        assert f_recent[8] > f_old[8]

    def test_recency_decay_volume_no_date(self):
        """recency_decay_volume should be 0 when no date provided."""
        fe = self._extractor()
        c = _make_candidate(total_volume=1000, last_shipment_date=None)
        features = fe.extract(c, _make_parsed_query())
        assert features[8] == 0.0

    # --- trade_diversity_score (feature 10) ---

    def test_trade_diversity_higher_for_diverse(self):
        fe = self._extractor()
        diverse = _make_candidate(trade_diversity=10)
        less_diverse = _make_candidate(trade_diversity=1)
        f_diverse = fe.extract(diverse, _make_parsed_query())
        f_less = fe.extract(less_diverse, _make_parsed_query())
        assert f_diverse[9] > f_less[9]

    def test_trade_diversity_zero_when_missing(self):
        fe = self._extractor()
        c = _make_candidate()  # no trade_diversity field
        features = fe.extract(c, _make_parsed_query())
        # log1p(0) = 0.0
        assert features[9] == pytest.approx(0.0)

    # --- country_diversity_score (feature 11) ---

    def test_country_diversity_score(self):
        fe = self._extractor()
        diverse = _make_candidate(country_diversity=5)
        singleton = _make_candidate(country_diversity=1)
        f_d = fe.extract(diverse, _make_parsed_query())
        f_s = fe.extract(singleton, _make_parsed_query())
        assert f_d[10] > f_s[10]

    # --- bm25_score (feature 12) ---

    def test_bm25_score_passthrough(self):
        fe = self._extractor()
        c = _make_candidate(bm25_score=7.5)
        features = fe.extract(c, _make_parsed_query())
        assert features[11] == pytest.approx(7.5)

    def test_bm25_score_defaults_to_zero(self):
        fe = self._extractor()
        features = fe.extract(_make_candidate(), _make_parsed_query())
        assert features[11] == 0.0

    # --- dense_similarity (feature 13) ---

    def test_dense_similarity_passthrough(self):
        fe = self._extractor()
        c = _make_candidate(dense_similarity=0.87)
        features = fe.extract(c, _make_parsed_query())
        assert features[12] == pytest.approx(0.87)

    # --- entity_confidence (feature 14) ---

    def test_entity_confidence_resolved(self):
        fe = self._extractor()
        c = _make_candidate(entity_confidence=1.0)
        features = fe.extract(c, _make_parsed_query())
        assert features[13] == pytest.approx(1.0)

    def test_entity_confidence_defaults_to_half(self):
        """Default entity_confidence for singletons is 0.5."""
        fe = self._extractor()
        features = fe.extract(_make_candidate(), _make_parsed_query())
        assert features[13] == pytest.approx(0.5)

    # --- volume_trend (feature 15) ---

    def test_volume_trend_positive_for_growing(self):
        fe = self._extractor()
        growing = _make_candidate(volume_6mo=2000, volume_prev_6mo=1000)
        features = fe.extract(growing, _make_parsed_query())
        assert features[14] > 0.0

    def test_volume_trend_negative_for_declining(self):
        fe = self._extractor()
        declining = _make_candidate(volume_6mo=500, volume_prev_6mo=1000)
        features = fe.extract(declining, _make_parsed_query())
        assert features[14] < 0.0

    def test_volume_trend_clamped_to_minus2_plus2(self):
        fe = self._extractor()
        extreme_growth = _make_candidate(volume_6mo=1_000_000, volume_prev_6mo=1)
        features = fe.extract(extreme_growth, _make_parsed_query())
        assert features[14] <= 2.0

        extreme_drop = _make_candidate(volume_6mo=0, volume_prev_6mo=1_000_000)
        features2 = fe.extract(extreme_drop, _make_parsed_query())
        assert features2[14] >= -2.0

    def test_volume_trend_zero_when_no_data(self):
        fe = self._extractor()
        features = fe.extract(_make_candidate(), _make_parsed_query())
        assert features[14] == 0.0

    # --- Original features still work ---

    def test_country_match_with_filter(self):
        fe = self._extractor()
        c = _make_candidate(country='China')
        pq = _make_parsed_query(country_filter=['China'])
        features = fe.extract(c, pq)
        assert features[6] == 1.0  # country_match

    def test_price_fit_under_ceiling(self):
        fe = self._extractor()
        c = _make_candidate(avg_price=350)
        pq = _make_parsed_query(price_ceiling=400)
        features = fe.extract(c, pq)
        assert features[7] == 1.0  # price_fit

    def test_feature_names_count(self):
        from search.services.ranking_ltr import FeatureExtractor
        assert len(FeatureExtractor.FEATURE_NAMES) == 15
