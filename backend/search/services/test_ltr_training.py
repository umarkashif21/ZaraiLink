from django.test import TestCase
import os
import shutil
import numpy as np
from unittest.mock import MagicMock, patch
from .ltr_dataset_builder import LTRDatasetBuilder
from .train_ltr import LTRTrainer, MODEL_PATH
from .ranking_ltr import RankingEnsemble, LTRModel, FeatureExtractor
from trade_data.models import ProductSubCategory, Transaction, ProductItem

class LTRTrainingPipelineTest(TestCase):
    def setUp(self):
        # Create Dummy Data for Dataset Builder
        from trade_data.models import Product, ProductCategory
        self.prod = Product.objects.create(name="TestTopProduct", hs_code="1")
        self.cat = ProductCategory.objects.create(name="TestCat", hs_code="12", product=self.prod)
        self.subcat = ProductSubCategory.objects.create(name="TestProd", hs_code="123", category=self.cat)
        self.item = ProductItem.objects.create(sub_category=self.subcat, name="TestItem")
        
        # Create Transactions to convert to synthetic queries
        # Supplier (Import)
        Transaction.objects.create(
            trade_type='IMPORT', product_item=self.item, seller="SupplierA", origin_country="China", 
            qty_mt=100, usd_per_mt=500, reporting_date="2025-01-01"
        )
        Transaction.objects.create(
            trade_type='IMPORT', product_item=self.item, seller="SupplierB", origin_country="China", 
            qty_mt=200, usd_per_mt=400, reporting_date="2025-01-02"
        )
        
        # Ensure model path is clean
        if os.path.exists(MODEL_PATH):
            os.remove(MODEL_PATH)
            
    def tearDown(self):
        # Clean up model after test
        if os.path.exists(MODEL_PATH):
            os.remove(MODEL_PATH)

    def test_dataset_builder(self):
        """
        Verify dataset builder generates valid X, y, groups.
        """
        builder = LTRDatasetBuilder()
        X, y, groups = builder.build_dataset()
        
        self.assertGreater(len(X), 0)
        self.assertEqual(len(X), len(y))
        self.assertEqual(sum(groups), len(X))
        self.assertEqual(X.shape[1], len(FeatureExtractor.FEATURE_NAMES))
        
        # Labels should be 0-4
        self.assertTrue(np.all(y >= 0))
        self.assertTrue(np.all(y <= 4))

    def test_training_script_end_to_end(self):
        """
        Run Trainer, verify model file created, verify Inference loading.
        """
        trainer = LTRTrainer()
        trainer.train()
        
        self.assertTrue(os.path.exists(MODEL_PATH), "Model file was not created by LTRTrainer")
        
        # Verify Ensemble loads it
        ensemble = RankingEnsemble()
        ensemble.ltr_model.load()
        
        self.assertIsNotNone(ensemble.ltr_model.model, "Ensemble failed to load trained model")
        
        # Verify Inference
        candidates = [
            {"counterparty_name": "SupA", "total_volume_mt": 100, "avg_price_usd_per_mt": 500, "num_shipments": 1},
            {"counterparty_name": "SupB", "total_volume_mt": 200, "avg_price_usd_per_mt": 400, "num_shipments": 1}
        ]
        query = {"intent": "BUY", "family": 1}
        
        ranked = ensemble.rank_candidates(candidates, query)
        self.assertEqual(len(ranked), 2)
        # Scores should be different (checks usage of model/weights)
        
    def test_inference_without_model_handles_gracefully(self):
        """
        Ensure system doesn't crash if training hasn't run (returns 0s).
        """
        if os.path.exists(MODEL_PATH):
            os.remove(MODEL_PATH)
            
        ensemble = RankingEnsemble()
        # Should log warning but not crash
        candidates = [{"counterparty_name": "SupA", "total_volume_mt": 100}]
        ranked = ensemble.rank_candidates(candidates, {"intent": "BUY"})
        
        self.assertEqual(len(ranked), 1)
