from django.test import TestCase
from unittest.mock import patch, MagicMock
from trade_data.models import Transaction, Product, ProductCategory, ProductSubCategory, ProductItem
from .candidate_retrieval import CandidateRetriever
import datetime

class CandidateRetrievalTest(TestCase):
    def setUp(self):
        # 1. Setup Product Hierarchy
        self.prod = Product.objects.create(name="Chemicals", hs_code="2800")
        self.cat = ProductCategory.objects.create(product=self.prod, name="Organic Chemicals", hs_code="2900")
        self.subcat = ProductSubCategory.objects.create(category=self.cat, name="Dextrose Monohydrate", hs_code="170230")
        self.item = ProductItem.objects.create(sub_category=self.subcat, name="Dextrose Mono Food Grade")
        
        # 2. GLOBAL BUYER SCENARIO (Intent: SELL, Scope: WORLDWIDE) -> Look for EXPORT
        # A Pakistan Exporter selling to a Global Buyer. 
        # User wants to SELL to Worldwide -> Find Buyers -> Look at EXPORTS.
        self.tx_export = Transaction.objects.create(
            trade_type='EXPORT',
            product_item=self.item,
            seller='Pak-Exporter-A', # The supplier (if buying from Pak)
            buyer='Global-Buyer-X',  # The candidate (if selling to Worldwide)
            origin_country='Pakistan',
            destination_country='Germany',
            qty_mt=100,
            usd_per_mt=500,
            reporting_date=datetime.date(2025, 1, 15),
            source_file='test_export.csv',
            tx_reference='EXP001'
        )
        
        # 3. GLOBAL SUPPLIER SCENARIO (Intent: BUY, Scope: WORLDWIDE) -> Look for IMPORT
        # A Global Supplier selling to Pakistan.
        # User wants to BUY from Worldwide -> Find Suppliers -> Look at IMPORTS.
        self.tx_import = Transaction.objects.create(
            trade_type='IMPORT',
            product_item=self.item,
            seller='Global-Supplier-Y', # The candidate (if buying from Worldwide)
            buyer='Pak-Importer-B',     # The buyer (if selling to Pak)
            origin_country='China',
            destination_country='Pakistan',
            qty_mt=200,
            usd_per_mt=450,
            reporting_date=datetime.date(2025, 2, 1),
            source_file='test_import.csv',
            tx_reference='IMP001'
        )

    @patch('search.services.candidate_retrieval.QueryMatcher')
    def test_scope_worldwide_intent_buy(self, MockMatcher):
        """
        User wants to BUY from WORLDWIDE.
        Should find 'Global-Supplier-Y' from IMPORT transactions.
        """
        # Mock NLP to return our subcategory
        matcher_instance = MockMatcher.return_value
        matcher_instance.match.return_value = [{'id': self.subcat.id, 'name': 'Dextrose', 'score': 1.0}]
        
        parsed_query = {
            "intent": "BUY",
            "product": "dextrose",
            "country_filter": [],
            "multi_intent": False
        }
        
        retriever = CandidateRetriever()
        results = retriever.retrieve_candidates(parsed_query, scope='WORLDWIDE')
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['counterparty_name'], 'Global-Supplier-Y')
        self.assertEqual(results[0]['total_volume_mt'], 200.0)
        self.assertEqual(results[0]['avg_price_usd_per_mt'], 450.0)
        
    @patch('search.services.candidate_retrieval.QueryMatcher')
    def test_scope_pakistan_intent_buy(self, MockMatcher):
        """
        User wants to BUY from PAKISTAN.
        Should find 'Pak-Exporter-A' from EXPORT transactions.
        (Logic: We want domestic suppliers. Pak Exporters are the suppliers in EXPORT data).
        """
        matcher_instance = MockMatcher.return_value
        matcher_instance.match.return_value = [{'id': self.subcat.id, 'name': 'Dextrose', 'score': 1.0}]
        
        parsed_query = {
            "intent": "BUY", 
            "product": "dextrose",
            "country_filter": [],
            "multi_intent": False
        }
        
        retriever = CandidateRetriever()
        results = retriever.retrieve_candidates(parsed_query, scope='PAKISTAN')
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['counterparty_name'], 'Pak-Exporter-A')
        self.assertEqual(results[0]['total_volume_mt'], 100.0)
        
    @patch('search.services.candidate_retrieval.QueryMatcher')
    def test_scope_worldwide_intent_sell(self, MockMatcher):
        """
        User wants to SELL to WORLDWIDE.
        Should find 'Global-Buyer-X' from EXPORT transactions.
        """
        matcher_instance = MockMatcher.return_value
        matcher_instance.match.return_value = [{'id': self.subcat.id, 'name': 'Dextrose', 'score': 1.0}]
        
        parsed_query = {
            "intent": "SELL",
            "product": "dextrose", 
            "country_filter": [],
            "multi_intent": False
        }
        
        retriever = CandidateRetriever()
        results = retriever.retrieve_candidates(parsed_query, scope='WORLDWIDE')
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['counterparty_name'], 'Global-Buyer-X')
        
    @patch('search.services.candidate_retrieval.QueryMatcher')
    def test_scope_pakistan_intent_sell(self, MockMatcher):
        """
        User wants to SELL to PAKISTAN.
        Should find 'Pak-Importer-B' from IMPORT transactions.
        (Logic: We want domestic buyers. Pak Importers are the buyers in IMPORT data).
        """
        matcher_instance = MockMatcher.return_value
        matcher_instance.match.return_value = [{'id': self.subcat.id, 'name': 'Dextrose', 'score': 1.0}]
        
        parsed_query = {
            "intent": "SELL",
            "product": "dextrose",
            "country_filter": [],
            "multi_intent": False
        }
        
        retriever = CandidateRetriever()
        results = retriever.retrieve_candidates(parsed_query, scope='PAKISTAN')
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['counterparty_name'], 'Pak-Importer-B')
        
    @patch('search.services.candidate_retrieval.QueryMatcher')
    def test_scope_default_worldwide(self, MockMatcher):
        """
        Ensure default scope is WORLDWIDE if not provided.
        """
        matcher_instance = MockMatcher.return_value
        matcher_instance.match.return_value = [{'id': self.subcat.id, 'name': 'Dextrose', 'score': 1.0}]
        
        parsed_query = {"intent": "BUY", "product": "dextrose"}
        
        retriever = CandidateRetriever()
        results_none = retriever.retrieve_candidates(parsed_query, scope=None)
        results_ww = retriever.retrieve_candidates(parsed_query, scope='WORLDWIDE')
        
        self.assertEqual(results_none, results_ww)
        self.assertEqual(results_none[0]['counterparty_name'], 'Global-Supplier-Y')

    @patch('search.services.candidate_retrieval.QueryMatcher')
    def test_volume_filtering_and_fit(self, MockMatcher):
        """
        Verify volume filtering works (excludes small suppliers)
        and volume_fit score is calculated.
        """
        matcher_instance = MockMatcher.return_value
        matcher_instance.match.return_value = [{'id': self.subcat.id, 'name': 'Dextrose', 'score': 1.0}]
        
        # Scenario: User wants 90MT
        # Pak-Exporter-A has 100MT shipment (Max) -> Should match
        # Create a small supplier to be filtered out
        Transaction.objects.create(
            trade_type='EXPORT',
            product_item=self.item,
            seller='Small-Pak-Seller',
            buyer='Global-Buyer-Z',
            origin_country='Pakistan',
            destination_country='UAE',
            qty_mt=10, # Max shipment 10MT
            usd_per_mt=500,
            reporting_date=datetime.date(2025, 1, 20)
        )
        
        parsed_query = {
            "intent": "BUY",
            "product": "dextrose",
            "volume_mt": 90, # Requirement
            "multi_intent": False
        }
        
        retriever = CandidateRetriever()
        results = retriever.retrieve_candidates(parsed_query, scope='PAKISTAN')
        
        # Should only find Pak-Exporter-A (100MT), Small-Pak-Seller (10MT) should be gone
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['counterparty_name'], 'Pak-Exporter-A')
        # 100MT >= 90MT -> "Good" (Not Strong, Strong needs 1.2x = 108MT)
        self.assertEqual(results[0]['volume_fit'], 'Good')
        
    @patch('search.services.candidate_retrieval.QueryMatcher')
    def test_time_filtering(self, MockMatcher):
        """
        Verify time range filter.
        """
        matcher_instance = MockMatcher.return_value
        matcher_instance.match.return_value = [{'id': self.subcat.id, 'name': 'Dextrose', 'score': 1.0}]
        
        # Create an old transaction (2023)
        Transaction.objects.create(
            trade_type='EXPORT',
            product_item=self.item,
            seller='Old-Seller',
            buyer='Global-Buyer-W',
            origin_country='Pakistan',
            destination_country='Germany',
            qty_mt=100,
            usd_per_mt=500,
            reporting_date=datetime.date(2023, 1, 15)
        )
        
        parsed_query = {
            "intent": "BUY", 
            "product": "dextrose",
            "time_range": "2025", # Should exclude 2023
            "multi_intent": False
        }
        
        retriever = CandidateRetriever()
        results = retriever.retrieve_candidates(parsed_query, scope='PAKISTAN')
        
        # Should only find 'Pak-Exporter-A' (2025-01-15), not 'Old-Seller' (2023)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['counterparty_name'], 'Pak-Exporter-A')

