from django.test import TestCase
import numpy as np
from .ranking_ltr import FeatureExtractor, RankingEnsemble, FAMILY_WEIGHTS

class RankingLTRTest(TestCase):
    def setUp(self):
        self.extractor = FeatureExtractor()
        self.ensemble = RankingEnsemble()
        
        self.sample_candidate = {
            "counterparty_name": "Supplier A",
            "total_volume_mt": 1000.0,
            "avg_price_usd_per_mt": 500.0,
            "num_shipments": 10,
            "last_trade_date": "2025-01-01",
            "volume_fit": "Good",
            "country": "Pakistan"
        }
        
        self.sample_query = {
            "intent": "BUY",
            "family": 1, # Discovery
            "product": "dextrose",
            "country_filter": ["Pakistan"],
            "price_ceiling": 600
        }

    def test_feature_extraction(self):
        """
        Verify feature vector matches expected values.
        """
        feats = self.extractor.extract(self.sample_candidate, self.sample_query)
        names = FeatureExtractor.FEATURE_NAMES
        f_dict = dict(zip(names, feats))
        
        # volume: log1p(1000) ~ 6.9
        self.assertAlmostEqual(f_dict['log_volume'], np.log1p(1000), places=2)
        
        # price: log1p(500) ~ 6.2
        self.assertAlmostEqual(f_dict['log_price'], np.log1p(500), places=2)
        
        # fit: Good -> 2
        self.assertEqual(f_dict['volume_fit_score'], 2.0)
        
        # country: "Pakistan" in ["Pakistan"] -> 1.0
        self.assertEqual(f_dict['country_match'], 1.0)
        
        # price_fit: 500 <= 600 -> 1.0
        self.assertEqual(f_dict['price_fit'], 1.0)

    def test_ranking_ensemble_sorts_correctly(self):
        """
        Verify that better candidates get higher scores.
        """
        # Candidate A: Strong Volume, Recent
        cand_a = {
            "name": "A",
            "total_volume_mt": 5000,
            "num_shipments": 20,
            "last_trade_date": "2025-02-01",
            "volume_fit": "Strong",
             "country": "Pakistan"
        }
        
        # Candidate B: Low Volume, Old
        cand_b = {
            "name": "B",
            "total_volume_mt": 50,
            "num_shipments": 2,
            "last_trade_date": "2023-01-01",
            "volume_fit": "Low",
             "country": "China"
        }
        
        candidates = [cand_b, cand_a] # Wrong order initially
        query = {"family": 3, "intent": "BUY"} # Volume-Aware Family
        
        ranked = self.ensemble.rank_candidates(candidates, query)
        
        self.assertEqual(ranked[0]['name'], "A")
        self.assertEqual(ranked[1]['name'], "B")
        self.assertTrue(ranked[0]['ranking_score'] > ranked[1]['ranking_score'])

    def test_family_weights(self):
        """
        Test that family 4 (Price) prioritizes Price Fit.
        """
        # A: High Price (Bad fit)
        cand_a = {
            "name": "Expensive",
            "total_volume_mt": 1000,
            "avg_price_usd_per_mt": 800, 
            "volume_fit": "Good"
        }
        
        # B: Low Price (Good fit)
        cand_b = {
            "name": "Cheap",
            "total_volume_mt": 1000,
            "avg_price_usd_per_mt": 400,
            "volume_fit": "Good"
        }
        
        query = {
            "family": 4, # Price Constrained
            "price_ceiling": 500
        }
        
        # B fits price (400 < 500), A does not (800 > 500)
        # Weight for price_fit is high in family 4
        
        ranked = self.ensemble.rank_candidates([cand_a, cand_b], query)
        
        self.assertEqual(ranked[0]['name'], "Cheap") 
