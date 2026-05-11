import numpy as np
import datetime
import logging
import os
import json
import pickle

try:
    import lightgbm as lgb
except ImportError:
    lgb = None

# Heuristic pseudo-label weights per query family.
FAMILY_WEIGHTS = {
    1: {  # Discovery / Generic
        'volume_fit': 1.5, 'log_volume': 1.0, 'shipment_freq': 1.0, 'inv_recency': 1.0, 'country_match': 1.0
    },
    2: {  # Country-Filtered
        'country_match': 3.0, 'volume_fit': 1.0, 'log_volume': 1.0, 'inv_recency': 0.5
    },
    3: {  # Volume-Aware
        'volume_fit': 3.0, 'log_volume': 1.0, 'inv_recency': 0.5
    },
    4: {  # Price-Constrained
        'price_fit': 3.0, 'log_price': -1.0, 'volume_fit': 1.0
    },
    5: {  # Time-Constrained
        'inv_recency': 3.0, 'shipment_freq': 1.5, 'volume_fit': 1.0
    },
    9: {  # Hybrid / Default
        'volume_fit': 1.0, 'log_volume': 1.0, 'inv_recency': 1.0, 'shipment_freq': 1.0, 'country_match': 1.0
    }
}

DEFAULT_WEIGHTS = FAMILY_WEIGHTS[9]

class FeatureExtractor:
    FEATURE_NAMES = [
        'log_volume', 'log_price', 'shipment_freq', 'inv_recency',
        'volume_fit_score', 'scope_match', 'country_match', 'price_fit'
    ]

    def extract(self, candidate, parsed_query):
        vol = candidate.get('total_volume_mt', 0)
        price = candidate.get('avg_price_usd_per_mt', 0)
        freq = candidate.get('num_shipments', 0)

        last_date_str = candidate.get('last_trade_date')
        if last_date_str:
            last_date = datetime.date.fromisoformat(last_date_str)
            days_ago = (datetime.date.today() - last_date).days
            inv_recency = 1.0 / (days_ago + 1.0)
        else:
            days_ago = 9999
            inv_recency = 0.0

        v_fit_str = candidate.get('volume_fit', 'N/A')
        v_fit_map = {'Strong': 3, 'Good': 2, 'Partial': 1, 'Low': 0, 'N/A': 0}
        volume_fit_score = v_fit_map.get(v_fit_str, 0)

        # Constant because retrieval already enforces scope; feature kept for
        # the case where retrieval is relaxed.
        scope_match = 1.0

        q_countries = parsed_query.get('country_filter', [])
        cand_country = candidate.get('country', '')
        if q_countries and cand_country in q_countries:
            country_match = 1.0
        elif not q_countries:
             country_match = 0.5
        else:
            country_match = 0.0

        ceiling = parsed_query.get('price_ceiling')
        if ceiling and price <= ceiling:
            price_fit = 1.0
        elif ceiling:
            price_fit = 0.0
        else:
            price_fit = 0.5

        return [
            np.log1p(vol),
            np.log1p(price),
            float(freq),
            inv_recency,
            float(volume_fit_score),
            scope_match,
            country_match,
            price_fit
        ]

class PseudoLabelGenerator:
    """Generates relevance labels (0-4) for LTR training from heuristics."""
    def generate_label(self, candidate, parsed_query):
        family_id = parsed_query.get('family', 9)
        weights = FAMILY_WEIGHTS.get(family_id, DEFAULT_WEIGHTS)

        extractor = FeatureExtractor()
        features = extractor.extract(candidate, parsed_query)
        feat_dict = dict(zip(FeatureExtractor.FEATURE_NAMES, features))

        score = 0.0
        for fname, val in feat_dict.items():
            w = weights.get(fname, 0.0)
            score += w * val

        if score > 15: return 4
        if score > 10: return 3
        if score > 5: return 2
        if score > 2: return 1
        return 0

class LTRModel:
    def __init__(self, model_path=None):
        if model_path is None:
             self.model_path = os.path.join(os.path.dirname(__file__), '../models/lgbm_ltr.txt')
        else:
            self.model_path = model_path
        self.model = None

    def load(self):
        if lgb and os.path.exists(self.model_path):
            try:
                self.model = lgb.Booster(model_file=self.model_path)
            except Exception as e:
                logging.error(f"Failed to load LTR model: {e}")
                self.model = None
        else:
            logging.warning(f"LTR Model file not found at {self.model_path}. Please run train_ltr.py")
            self.model = None

    def predict(self, features):
        if not lgb:
            return np.zeros(len(features))

        # Return zeros when no model is loaded so RankingEnsemble falls back
        # entirely to heuristics. Avoiding a hard error here keeps search alive
        # in environments where training hasn't run yet.
        if not self.model:
            return np.zeros(len(features))

        return self.model.predict(features)

class RankingEnsemble:
    def __init__(self):
        self.extractor = FeatureExtractor()
        self.ltr_model = LTRModel()
        self.ltr_model.load()

    def rank_candidates(self, candidates, parsed_query):
        if not candidates:
            return []

        X = []
        for c in candidates:
            X.append(self.extractor.extract(c, parsed_query))
        X = np.array(X)

        ltr_scores = self.ltr_model.predict(X)

        h_gen = PseudoLabelGenerator()
        heuristic_scores = []
        for i, c in enumerate(candidates):
            family_id = parsed_query.get('family', 9)
            weights = FAMILY_WEIGHTS.get(family_id, DEFAULT_WEIGHTS)
            feat_dict = dict(zip(FeatureExtractor.FEATURE_NAMES, X[i]))
            s = sum(weights.get(k, 0)*v for k,v in feat_dict.items())
            heuristic_scores.append(s)

        # 70% heuristic / 30% LTR until LTR has enough real labels to dominate.
        final_scores = []
        for i in range(len(candidates)):
            fs = (heuristic_scores[i] * 0.7) + (ltr_scores[i] * 0.3)
            final_scores.append(fs)

        for i, c in enumerate(candidates):
            c['ranking_score'] = round(final_scores[i], 3)
            c['match_features'] = {
                'vol': candidates[i].get('total_volume_mt'),
                'fit': candidates[i].get('volume_fit')
            }

        ranked = sorted(candidates, key=lambda x: x['ranking_score'], reverse=True)
        return ranked
