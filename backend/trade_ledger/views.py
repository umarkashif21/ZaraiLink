from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from django.db.models import Q, Sum, Avg, Count
from .models import ProductCategory, TradeCompany, TradeProduct, TradePartner, TradeTrend
from .serializers import (
    ProductCategorySerializer, TradeCompanyListSerializer,
    TradeCompanyDetailSerializer, TradeProductSerializer,
    TradePartnerSerializer, TradeTrendSerializer
)


class TradeCompanyViewSet(viewsets.ReadOnlyModelViewSet):
    """API for browsing trade companies"""
    queryset = TradeCompany.objects.select_related('company').prefetch_related(
        'products', 'partners', 'trends'
    )
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return TradeCompanyListSerializer
        return TradeCompanyDetailSerializer
    
    def get_queryset(self):
        """Filter companies based on query params"""
        queryset = self.queryset
        
        # Apply filters
        country = self.request.query_params.get('country', '').strip()
        product = self.request.query_params.get('product', '').strip()
        company_type = self.request.query_params.get('type', '').strip()
        date_from = self.request.query_params.get('date_from', '').strip()
        date_to = self.request.query_params.get('date_to', '').strip()
        
        if country:
            # Filter by partner countries
            queryset = queryset.filter(partners__country__icontains=country).distinct()
        
        if product:
            # Filter by product category
            queryset = queryset.filter(products__category_id=product).distinct()
        
        if company_type == 'exporter':
            queryset = queryset.filter(is_exporter=True)
        elif company_type == 'importer':
            queryset = queryset.filter(is_importer=True)
        
        if date_from:
            queryset = queryset.filter(active_since__gte=date_from)
        if date_to:
            queryset = queryset.filter(active_since__lte=date_to)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def products(self, request, pk=None):
        """Get products for a specific company"""
        company = self.get_object()
        products = company.products.all()
        serializer = TradeProductSerializer(products, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def partners(self, request, pk=None):
        """Get partners for a specific company"""
        company = self.get_object()
        partners = company.partners.all()
        serializer = TradePartnerSerializer(partners, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def trends(self, request, pk=None):
        """Get trends for a specific company"""
        company = self.get_object()
        trends = company.trends.all()
        serializer = TradeTrendSerializer(trends, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get aggregate statistics for filtered companies"""
        queryset = self.get_queryset()
        product_id = request.query_params.get('product', '').strip()
        
        stats = {}
        
        if product_id:
            # Get statistics for specific product
            products = TradeProduct.objects.filter(
                company__in=queryset,
                category_id=product_id
            )
            stats['avg_price'] = products.aggregate(Avg('avg_price'))['avg_price__avg']
            stats['avg_yoy_growth'] = products.aggregate(Avg('yoy_growth'))['yoy_growth__avg']
            stats['total_volume'] = products.aggregate(Sum('volume'))['volume__sum']
        
        stats['total_companies'] = queryset.count()
        
        return Response(stats)


class ProductCategoryListView(APIView):
    """List all product categories"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        categories = ProductCategory.objects.all().order_by('name')
        serializer = ProductCategorySerializer(categories, many=True)
        return Response(serializer.data)
