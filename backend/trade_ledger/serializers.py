from rest_framework import serializers
from .models import ProductCategory, TradeCompany, TradeProduct, TradePartner, TradeTrend
from companies.serializers import CompanyListSerializer


class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ['id', 'name', 'hs_code', 'description']


class TradeProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = TradeProduct
        fields = [
            'id', 'product_name', 'category', 'category_name', 'hs_code',
            'description', 'avg_price', 'currency', 'volume', 'unit', 'yoy_growth'
        ]


class TradePartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradePartner
        fields = [
            'id', 'country', 'port_name', 'trade_volume',
            'percentage_share', 'is_export'
        ]


class TradeTrendSerializer(serializers.ModelSerializer):
    month_name = serializers.CharField(source='get_month_display', read_only=True)
    product_name = serializers.CharField(source='product.product_name', read_only=True)
    
    class Meta:
        model = TradeTrend
        fields = [
            'id', 'month', 'month_name', 'year', 'product', 'product_name',
            'volume', 'avg_price', 'yoy_volume_growth', 'yoy_price_growth'
        ]


class TradeCompanyListSerializer(serializers.ModelSerializer):
    """Serializer for trade company list view"""
    company = CompanyListSerializer(read_only=True)
    top_products = serializers.SerializerMethodField()
    
    class Meta:
        model = TradeCompany
        fields = [
            'id', 'company', 'estimated_revenue', 'trade_volume',
            'active_since', 'is_exporter', 'is_importer', 'top_products'
        ]
    
    def get_top_products(self, obj):
        """Get top 3 products by volume"""
        top_products = obj.products.order_by('-volume')[:3]
        return TradeProductSerializer(top_products, many=True).data


class TradeCompanyDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single company view"""
    company = CompanyListSerializer(read_only=True)
    products = TradeProductSerializer(many=True, read_only=True)
    partners = TradePartnerSerializer(many=True, read_only=True)
    trends = TradeTrendSerializer(many=True, read_only=True)
    
    # Computed fields
    total_products = serializers.SerializerMethodField()
    total_partners = serializers.SerializerMethodField()
    partner_diversity_score = serializers.SerializerMethodField()
    
    class Meta:
        model = TradeCompany
        fields = [
            'id', 'company', 'estimated_revenue', 'trade_volume',
            'active_since', 'is_exporter', 'is_importer',
            'products', 'partners', 'trends',
            'total_products', 'total_partners', 'partner_diversity_score'
        ]
    
    def get_total_products(self, obj):
        return obj.products.count()
    
    def get_total_partners(self, obj):
        return obj.partners.values('country').distinct().count()
    
    def get_partner_diversity_score(self, obj):
        """Calculate diversity score based on number of countries and distribution"""
        partners_count = obj.partners.values('country').distinct().count()
        # Simple formula: more countries = higher score, max 100
        return min(partners_count * 10, 100)
