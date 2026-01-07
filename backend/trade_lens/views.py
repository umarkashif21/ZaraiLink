from django.db.models import Avg, Sum, Count, F
from django.db.models.functions import TruncMonth, ExtractYear, ExtractMonth
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from .models import TradeLensProduct, TradeLensTransaction
from .serializers import (
    TradeLensProductSerializer,
    TradeLensTransactionSerializer,
)


class StandardPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100


class TradeLensProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TradeLensProduct.objects.all()
    serializer_class = TradeLensProductSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['get'])
    def overview(self, request, pk=None):
        """Overview stats: avg price, supply chain flow, provinces, ports"""
        product = self.get_object()
        transactions = product.transactions.all()
        
        stats = transactions.aggregate(
            avg_price=Avg('price_usd'),
            total_quantity=Sum('quantity_mt'),
            total_value=Sum('total_value_usd'),
            transaction_count=Count('id'),
        )
        
        stats['export_count'] = transactions.filter(trade_type='EXPORT').count()
        stats['import_count'] = transactions.filter(trade_type='IMPORT').count()
        
        provinces = list(transactions.values('province').annotate(
            count=Count('id'),
            total_value=Sum('total_value_usd')
        ).order_by('-total_value')[:10])
        
        ports = list(transactions.values('port').annotate(
            count=Count('id'),
            total_value=Sum('total_value_usd')
        ).order_by('-total_value')[:10])
        
        price_trend = list(transactions.annotate(
            month=TruncMonth('trade_date')
        ).values('month').annotate(
            avg_price=Avg('price_usd'),
            total_qty=Sum('quantity_mt')
        ).order_by('month'))
        
        for item in price_trend:
            item['month'] = item['month'].strftime('%Y-%m') if item['month'] else None
            item['avg_price'] = float(item['avg_price']) if item['avg_price'] else 0
            item['total_qty'] = float(item['total_qty']) if item['total_qty'] else 0
        
        supply_chain = []
        export_data = transactions.filter(trade_type='EXPORT').values('seller_country', 'buyer_country').annotate(
            value=Sum('total_value_usd')
        ).order_by('-value')[:15]
        for item in export_data:
            supply_chain.append({
                'source': item['seller_country'],
                'target': item['buyer_country'],
                'value': float(item['value']) if item['value'] else 0
            })
        
        return Response({
            'product': TradeLensProductSerializer(product).data,
            'avg_price': float(stats['avg_price']) if stats['avg_price'] else 0,
            'total_quantity': float(stats['total_quantity']) if stats['total_quantity'] else 0,
            'total_value': float(stats['total_value']) if stats['total_value'] else 0,
            'transaction_count': stats['transaction_count'],
            'export_count': stats['export_count'],
            'import_count': stats['import_count'],
            'provinces': provinces,
            'ports': ports,
            'price_trend': price_trend,
            'supply_chain_flow': supply_chain,
        })

    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        """Summary: filters, total qty, top buyers/sellers"""
        product = self.get_object()
        transactions = product.transactions.all()
        
        trade_type = request.query_params.get('trade_type')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        country = request.query_params.get('country')
        
        if trade_type:
            transactions = transactions.filter(trade_type=trade_type)
        if start_date:
            transactions = transactions.filter(trade_date__gte=start_date)
        if end_date:
            transactions = transactions.filter(trade_date__lte=end_date)
        if country:
            transactions = transactions.filter(
                buyer_country__icontains=country
            ) | transactions.filter(
                seller_country__icontains=country
            )
        
        stats = transactions.aggregate(
            total_quantity=Sum('quantity_mt'),
            total_value=Sum('total_value_usd'),
            avg_price=Avg('price_usd'),
        )
        
        top_buyers = list(transactions.values('buyer_name', 'buyer_country').annotate(
            total_value=Sum('total_value_usd'),
            total_qty=Sum('quantity_mt'),
            transaction_count=Count('id')
        ).order_by('-total_value')[:10])
        
        top_sellers = list(transactions.values('seller_name', 'seller_country').annotate(
            total_value=Sum('total_value_usd'),
            total_qty=Sum('quantity_mt'),
            transaction_count=Count('id')
        ).order_by('-total_value')[:10])
        
        monthly_trend = list(transactions.annotate(
            month=TruncMonth('trade_date')
        ).values('month').annotate(
            total_value=Sum('total_value_usd'),
            total_qty=Sum('quantity_mt'),
            transaction_count=Count('id')
        ).order_by('month'))
        
        for item in monthly_trend:
            item['month'] = item['month'].strftime('%Y-%m') if item['month'] else None
            item['total_value'] = float(item['total_value']) if item['total_value'] else 0
            item['total_qty'] = float(item['total_qty']) if item['total_qty'] else 0
        
        for buyer in top_buyers:
            buyer['total_value'] = float(buyer['total_value']) if buyer['total_value'] else 0
            buyer['total_qty'] = float(buyer['total_qty']) if buyer['total_qty'] else 0
        for seller in top_sellers:
            seller['total_value'] = float(seller['total_value']) if seller['total_value'] else 0
            seller['total_qty'] = float(seller['total_qty']) if seller['total_qty'] else 0
        
        return Response({
            'product': TradeLensProductSerializer(product).data,
            'total_quantity': float(stats['total_quantity']) if stats['total_quantity'] else 0,
            'total_value': float(stats['total_value']) if stats['total_value'] else 0,
            'avg_price': float(stats['avg_price']) if stats['avg_price'] else 0,
            'top_buyers': top_buyers,
            'top_sellers': top_sellers,
            'monthly_trend': monthly_trend,
        })

    @action(detail=True, methods=['get'])
    def comparison(self, request, pk=None):
        """Comparison: price trends, country comparisons"""
        product = self.get_object()
        transactions = product.transactions.all()
        
        price_trends = list(transactions.annotate(
            month=TruncMonth('trade_date')
        ).values('month', 'trade_type').annotate(
            avg_price=Avg('price_usd'),
            total_value=Sum('total_value_usd'),
            total_qty=Sum('quantity_mt')
        ).order_by('month', 'trade_type'))
        
        for item in price_trends:
            item['month'] = item['month'].strftime('%Y-%m') if item['month'] else None
            item['avg_price'] = float(item['avg_price']) if item['avg_price'] else 0
            item['total_value'] = float(item['total_value']) if item['total_value'] else 0
            item['total_qty'] = float(item['total_qty']) if item['total_qty'] else 0
        
        country_exports = list(transactions.filter(trade_type='EXPORT').values(
            'buyer_country'
        ).annotate(
            total_value=Sum('total_value_usd'),
            total_qty=Sum('quantity_mt'),
            avg_price=Avg('price_usd')
        ).order_by('-total_value')[:10])
        
        country_imports = list(transactions.filter(trade_type='IMPORT').values(
            'seller_country'
        ).annotate(
            total_value=Sum('total_value_usd'),
            total_qty=Sum('quantity_mt'),
            avg_price=Avg('price_usd')
        ).order_by('-total_value')[:10])
        
        for item in country_exports:
            item['country'] = item.pop('buyer_country')
            item['total_value'] = float(item['total_value']) if item['total_value'] else 0
            item['total_qty'] = float(item['total_qty']) if item['total_qty'] else 0
            item['avg_price'] = float(item['avg_price']) if item['avg_price'] else 0
        
        for item in country_imports:
            item['country'] = item.pop('seller_country')
            item['total_value'] = float(item['total_value']) if item['total_value'] else 0
            item['total_qty'] = float(item['total_qty']) if item['total_qty'] else 0
            item['avg_price'] = float(item['avg_price']) if item['avg_price'] else 0
        
        export_stats = transactions.filter(trade_type='EXPORT').aggregate(
            total_value=Sum('total_value_usd'),
            total_qty=Sum('quantity_mt')
        )
        import_stats = transactions.filter(trade_type='IMPORT').aggregate(
            total_value=Sum('total_value_usd'),
            total_qty=Sum('quantity_mt')
        )
        
        return Response({
            'product': TradeLensProductSerializer(product).data,
            'price_trends': price_trends,
            'country_exports': country_exports,
            'country_imports': country_imports,
            'trade_type_breakdown': {
                'exports': {
                    'total_value': float(export_stats['total_value'] or 0),
                    'total_qty': float(export_stats['total_qty'] or 0),
                },
                'imports': {
                    'total_value': float(import_stats['total_value'] or 0),
                    'total_qty': float(import_stats['total_qty'] or 0),
                }
            }
        })

    @action(detail=True, methods=['get'])
    def details(self, request, pk=None):
        """Details: paginated transaction table"""
        product = self.get_object()
        transactions = product.transactions.all()
        
        trade_type = request.query_params.get('trade_type')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        buyer = request.query_params.get('buyer')
        seller = request.query_params.get('seller')
        country = request.query_params.get('country')
        
        if trade_type:
            transactions = transactions.filter(trade_type=trade_type)
        if start_date:
            transactions = transactions.filter(trade_date__gte=start_date)
        if end_date:
            transactions = transactions.filter(trade_date__lte=end_date)
        if buyer:
            transactions = transactions.filter(buyer_name__icontains=buyer)
        if seller:
            transactions = transactions.filter(seller_name__icontains=seller)
        if country:
            transactions = transactions.filter(
                buyer_country__icontains=country
            ) | transactions.filter(
                seller_country__icontains=country
            )
        
        paginator = StandardPagination()
        page = paginator.paginate_queryset(transactions, request)
        serializer = TradeLensTransactionSerializer(page, many=True)
        
        return paginator.get_paginated_response(serializer.data)

    @action(detail=True, methods=['get'])
    def global_view(self, request, pk=None):
        """Global view: trade distribution by country for map"""
        product = self.get_object()
        transactions = product.transactions.all()
        
        export_by_country = transactions.filter(trade_type='EXPORT').values(
            'buyer_country'
        ).annotate(
            total_value=Sum('total_value_usd'),
            total_qty=Sum('quantity_mt'),
            transaction_count=Count('id')
        ).order_by('-total_value')
        
        import_by_country = transactions.filter(trade_type='IMPORT').values(
            'seller_country'
        ).annotate(
            total_value=Sum('total_value_usd'),
            total_qty=Sum('quantity_mt'),
            transaction_count=Count('id')
        ).order_by('-total_value')
        
        countries_data = {}
        for item in export_by_country:
            country = item['buyer_country']
            countries_data[country] = {
                'name': country,
                'export_value': float(item['total_value'] or 0),
                'export_qty': float(item['total_qty'] or 0),
                'export_count': item['transaction_count'],
                'import_value': 0,
                'import_qty': 0,
                'import_count': 0,
            }
        
        for item in import_by_country:
            country = item['seller_country']
            if country in countries_data:
                countries_data[country]['import_value'] = float(item['total_value'] or 0)
                countries_data[country]['import_qty'] = float(item['total_qty'] or 0)
                countries_data[country]['import_count'] = item['transaction_count']
            else:
                countries_data[country] = {
                    'name': country,
                    'export_value': 0,
                    'export_qty': 0,
                    'export_count': 0,
                    'import_value': float(item['total_value'] or 0),
                    'import_qty': float(item['total_qty'] or 0),
                    'import_count': item['transaction_count'],
                }
        
        for country_data in countries_data.values():
            country_data['total_value'] = country_data['export_value'] + country_data['import_value']
            country_data['total_qty'] = country_data['export_qty'] + country_data['import_qty']
        
        countries_list = sorted(
            countries_data.values(), 
            key=lambda x: x['total_value'], 
            reverse=True
        )
        
        total_export = sum(c['export_value'] for c in countries_list)
        total_import = sum(c['import_value'] for c in countries_list)
        
        return Response({
            'product': TradeLensProductSerializer(product).data,
            'countries': countries_list,
            'total_export_value': total_export,
            'total_import_value': total_import,
            'total_trade_value': total_export + total_import,
        })
