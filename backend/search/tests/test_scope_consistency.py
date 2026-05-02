from django.test import TestCase
from unittest.mock import patch, MagicMock
from search.services.aggregation import SupplierAggregator
import datetime

class TestSupplierScopeConsistency(TestCase):
    @patch('search.services.aggregation.Transaction.objects')
    @patch('search.services.aggregation.SupplierAggregator._calculate_intelligence')
    def test_supplier_detail_respects_product_item_filter(self, mock_intelligence, mock_objects):
        mock_intelligence.return_value = {}
        # Setup mock behavior
        mock_qs = MagicMock()
        mock_objects.filter.return_value = mock_qs
        mock_qs.order_by.return_value = mock_qs
        mock_qs.exists.return_value = True

        mock_stats = {
            'total_volume': 3125.0,
            'avg_price': 737.0,
            'shipment_count': 124,
            'last_shipment_date': datetime.date(2023, 1, 1),
            'total': 124,
            'recent_count': 50
        }
        mock_qs.aggregate.return_value = mock_stats
        mock_qs.filter.return_value = mock_qs
        mock_qs.exclude.return_value = mock_qs
        
        # Mock annotate chain
        mock_annotate = MagicMock()
        mock_annotate.values.return_value.annotate.return_value.order_by.return_value = []
        mock_qs.annotate.return_value = mock_annotate
        
        mock_qs.values_list.return_value.distinct.return_value.order_by.return_value = ['China']
        mock_qs.values.return_value.distinct.return_value.count.return_value = 5

        aggregator = SupplierAggregator()

        # 1. Search page equivalent (getting suppliers)
        # We mock this just to ensure our expectation
        # (Assuming the search list passed product_item_filter=[101])

        # 2. Detail page call WITH product_item_filter
        product_item_filter = [101]
        subcategory_ids = [50]
        details = aggregator.get_supplier_details("Seawall Enterprise Ltd", subcategory_ids, product_item_filter=product_item_filter)

        # Verify that filter was called with the seller name
        mock_objects.filter.assert_called_with(
            seller__iexact="Seawall Enterprise Ltd"
        )
        
        # The secondary filter should have been applied for the specific variant
        mock_qs.filter.assert_called_with(product_item__id__in=product_item_filter)

        # The shipment count must match what we mocked (124 instead of 169)
        self.assertEqual(details['stats']['shipment_count'], 124)
