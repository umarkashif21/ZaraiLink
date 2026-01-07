from rest_framework import serializers
from .models import TradeLensProduct, TradeLensTransaction


class TradeLensProductSerializer(serializers.ModelSerializer):
    transaction_count = serializers.SerializerMethodField()
    total_value = serializers.SerializerMethodField()

    class Meta:
        model = TradeLensProduct
        fields = ['id', 'name', 'hs_code', 'category', 'image_url', 
                  'description', 'transaction_count', 'total_value']

    def get_transaction_count(self, obj):
        return obj.transactions.count()

    def get_total_value(self, obj):
        from django.db.models import Sum
        result = obj.transactions.aggregate(total=Sum('total_value_usd'))
        return float(result['total'] or 0)


class TradeLensTransactionSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = TradeLensTransaction
        fields = ['id', 'product', 'product_name', 'trade_date', 'price_usd', 
                  'quantity_mt', 'total_value_usd', 'buyer_name', 'seller_name',
                  'buyer_country', 'seller_country', 'port', 'province', 
                  'trade_type', 'hs_code']


class OverviewStatsSerializer(serializers.Serializer):
    avg_price = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_quantity = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_value = serializers.DecimalField(max_digits=18, decimal_places=2)
    transaction_count = serializers.IntegerField()
    export_count = serializers.IntegerField()
    import_count = serializers.IntegerField()
    provinces = serializers.ListField()
    ports = serializers.ListField()
    price_trend = serializers.ListField()
    supply_chain_flow = serializers.ListField()


class SummaryStatsSerializer(serializers.Serializer):
    total_quantity = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_value = serializers.DecimalField(max_digits=18, decimal_places=2)
    avg_price = serializers.DecimalField(max_digits=12, decimal_places=2)
    top_buyers = serializers.ListField()
    top_sellers = serializers.ListField()
    monthly_trend = serializers.ListField()


class ComparisonStatsSerializer(serializers.Serializer):
    price_trends = serializers.ListField()
    country_comparison = serializers.ListField()
    trade_type_breakdown = serializers.DictField()


class GlobalViewSerializer(serializers.Serializer):
    countries = serializers.ListField()
    total_export_value = serializers.DecimalField(max_digits=18, decimal_places=2)
    total_import_value = serializers.DecimalField(max_digits=18, decimal_places=2)
