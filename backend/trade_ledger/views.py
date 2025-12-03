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
    queryset = TradeCompany.objects.select_related('company').prefetch_related(
        'products', 'partners', 'trends'
    )
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return TradeCompanyListSerializer
        return TradeCompanyDetailSerializer
    
    def get_queryset(self):
        qs = self.queryset
        
        country = self.request.query_params.get('country', '').strip()
        prod = self.request.query_params.get('product', '').strip()
        ctype = self.request.query_params.get('type', '').strip()
        d_from = self.request.query_params.get('date_from', '').strip()
        d_to = self.request.query_params.get('date_to', '').strip()
        
        if country:
            qs = qs.filter(partners__country__icontains=country).distinct()
        
        if prod:
            qs = qs.filter(products__category_id=prod).distinct()
        
        if ctype == 'exporter':
            qs = qs.filter(is_exporter=True)
        elif ctype == 'importer':
            qs = qs.filter(is_importer=True)
        
        if d_from:
            qs = qs.filter(active_since__gte=d_from)
        if d_to:
            qs = qs.filter(active_since__lte=d_to)
        
        return qs
    
    @action(detail=True, methods=['get'])
    def products(self, req, pk=None):
        c = self.get_object()
        prods = c.products.all()
        ser = TradeProductSerializer(prods, many=True)
        return Response(ser.data)
    
    @action(detail=True, methods=['get'])
    def partners(self, req, pk=None):
        c = self.get_object()
        parts = c.partners.all()
        ser = TradePartnerSerializer(parts, many=True)
        return Response(ser.data)
    
    @action(detail=True, methods=['get'])
    def trends(self, req, pk=None):
        c = self.get_object()
        trds = c.trends.all()
        ser = TradeTrendSerializer(trds, many=True)
        return Response(ser.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, req):
        qs = self.get_queryset()
        pid = req.query_params.get('product', '').strip()
        
        stats = {}
        
        if pid:
            prods = TradeProduct.objects.filter(company__in=qs, category_id=pid)
            stats['avg_price'] = prods.aggregate(Avg('avg_price'))['avg_price__avg']
            stats['avg_yoy_growth'] = prods.aggregate(Avg('yoy_growth'))['yoy_growth__avg']
            stats['total_volume'] = prods.aggregate(Sum('volume'))['volume__sum']
        
        stats['total_companies'] = qs.count()
        
        return Response(stats)


class ProductCategoryListView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, req):
        cats = ProductCategory.objects.all().order_by('name')
        ser = ProductCategorySerializer(cats, many=True)
        return Response(ser.data)
