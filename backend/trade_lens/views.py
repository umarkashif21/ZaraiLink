from django.db.models import Avg, Sum, Count, F, Q, Case, When, DecimalField, IntegerField
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

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        # Apply Filters
        search = request.query_params.get('search')
        category = request.query_params.get('category')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        trade_type = request.query_params.get('trade_type')
        
        tx_filters = Q()
        if start_date:
            tx_filters &= Q(transactions__trade_date__gte=start_date)
        if end_date:
            tx_filters &= Q(transactions__trade_date__lte=end_date)
            
        if trade_type and trade_type.upper() in ['IMPORT', 'EXPORT']:
            tx_filters &= Q(transactions__trade_type=trade_type.upper())

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(hs_code__icontains=search)
            )
        if category:
            queryset = queryset.filter(category=category)

        # Annotate product data
        queryset = queryset.annotate(
            import_quantity=Sum(
                Case(When(Q(transactions__trade_type='IMPORT') & tx_filters, then=F('transactions__quantity_mt')), default=0, output_field=DecimalField())
            ),
            export_quantity=Sum(
                Case(When(Q(transactions__trade_type='EXPORT') & tx_filters, then=F('transactions__quantity_mt')), default=0, output_field=DecimalField())
            ),
            import_value=Sum(
                Case(When(Q(transactions__trade_type='IMPORT') & tx_filters, then=F('transactions__total_value_usd')), default=0, output_field=DecimalField())
            ),
            export_value=Sum(
                Case(When(Q(transactions__trade_type='EXPORT') & tx_filters, then=F('transactions__total_value_usd')), default=0, output_field=DecimalField())
            ),
            import_transactions=Count(
                Case(When(Q(transactions__trade_type='IMPORT') & tx_filters, then=F('transactions__id')), output_field=IntegerField())
            ),
            export_transactions=Count(
                Case(When(Q(transactions__trade_type='EXPORT') & tx_filters, then=F('transactions__id')), output_field=IntegerField())
            ),
        )

        global_stats = queryset.aggregate(
            total_imported_products=Count('id', filter=Q(import_quantity__gt=0)),
            total_exported_products=Count('id', filter=Q(export_quantity__gt=0)),
            total_import_value=Sum('import_value'),
            total_export_value=Sum('export_value'),
            total_import_transactions=Sum('import_transactions'),
            total_export_transactions=Sum('export_transactions'),
        )
        
        categories_count = queryset.values('category').distinct().count()

        summary = {
            "total_products": queryset.count(),
            "total_imported_products": global_stats.get('total_imported_products') or 0,
            "total_exported_products": global_stats.get('total_exported_products') or 0,
            "total_import_value": float(global_stats.get('total_import_value') or 0),
            "total_export_value": float(global_stats.get('total_export_value') or 0),
            "total_transactions": (global_stats.get('total_import_transactions') or 0) + (global_stats.get('total_export_transactions') or 0),
            "categories": categories_count
        }

        # Build product list
        products = []
        for p in queryset:
            products.append({
                "id": p.id,
                "name": p.name,
                "hs_code": p.hs_code,
                "category": p.category,
                "description": p.description,
                "import_quantity": float(p.import_quantity or 0),
                "export_quantity": float(p.export_quantity or 0),
                "import_value": float(p.import_value or 0),
                "export_value": float(p.export_value or 0),
                "import_transactions": p.import_transactions,
                "export_transactions": p.export_transactions
            })

        return Response({
            "summary": summary,
            "products": products
        })

    @action(detail=True, methods=['get'])
    def overview(self, request, pk=None):
        """Overview: massive DB aggregations, explicit percentage flow mapping"""
        product = self.get_object()
        transactions = product.transactions.all()
        
        trade_type = request.query_params.get('trade_type')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if trade_type and trade_type.upper() in ['IMPORT', 'EXPORT', 'BOTH']:
            if trade_type.upper() != 'BOTH':
                transactions = transactions.filter(trade_type=trade_type.upper())
        if start_date:
            transactions = transactions.filter(trade_date__gte=start_date)
        if end_date:
            transactions = transactions.filter(trade_date__lte=end_date)
            
        # 1. Summary Block
        stats = transactions.aggregate(
            total_quantity=Sum('quantity_mt'),
            total_trade_value_usd=Sum('total_value_usd'),
            total_transactions=Count('id'),
            import_quantity=Sum('quantity_mt', filter=Q(trade_type='IMPORT')),
            export_quantity=Sum('quantity_mt', filter=Q(trade_type='EXPORT')),
        )
        
        qty = float(stats['total_quantity'] or 0)
        usd = float(stats['total_trade_value_usd'] or 0)
        weighted_avg = (usd / qty) if qty > 0 else 0
        
        summary = {
            "total_quantity": qty,
            "total_trade_value_usd": usd,
            "total_trade_value_pkr": usd * 280,
            "weighted_avg_price": weighted_avg,
            "total_transactions": stats['total_transactions'] or 0,
            "import_quantity": float(stats['import_quantity'] or 0),
            "export_quantity": float(stats['export_quantity'] or 0)
        }
        
        # 2. Price Trend (Weighted Avg by Month)
        monthly_trend = list(transactions.annotate(
            month=TruncMonth('trade_date')
        ).values('month').annotate(
            total_value_usd=Sum('total_value_usd'),
            total_quantity_mt=Sum('quantity_mt')
        ).order_by('month'))
        
        price_trend = []
        for item in monthly_trend:
            m = item['month'].strftime('%b-%y') if item['month'] else 'Unknown'
            q = float(item['total_quantity_mt'] or 0)
            v = float(item['total_value_usd'] or 0)
            avg = (v / q) if q > 0 else 0
            price_trend.append({"month": m, "avg_price": avg})
            
        # 3. Supply Chain Flow routes (Source -> Target)
        flow_data = list(transactions.values('seller_country', 'buyer_country').annotate(
            value=Sum('quantity_mt')
        ).order_by('-value')[:10])
        
        supply_chain_flow = []
        for flow in flow_data:
            supply_chain_flow.append({
                "source": flow['seller_country'] or 'Unknown',
                "target": flow['buyer_country'] or 'Unknown',
                "value": float(flow['value'] or 0)
            })

        return Response({
            'product': TradeLensProductSerializer(product).data,
            'summary': summary,
            'price_trend': price_trend,
            'supply_chain_flow': supply_chain_flow
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
        """Comparison: exact weighted avg price trends, country comparisons"""
        product = self.get_object()
        
        compare_with_str = request.query_params.get('compare_with', '')
        compare_ids = []
        if compare_with_str:
            try:
                compare_ids = [int(i.strip()) for i in compare_with_str.split(',') if i.strip()]
            except ValueError:
                pass
                
        if compare_ids:
            return self._comparison_multi_product(request, product, compare_ids)
            
        transactions = product.transactions.all()
        
        trade_type = request.query_params.get('trade_type')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        buyer = request.query_params.get('buyer')
        seller = request.query_params.get('seller')
        country = request.query_params.get('country')
        
        if trade_type and trade_type.upper() in ['IMPORT', 'EXPORT']:
            transactions = transactions.filter(trade_type=trade_type.upper())
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
                Q(buyer_country__icontains=country) | Q(seller_country__icontains=country)
            )

        # 1. Monthly Avg Price
        price_trends = list(transactions.annotate(
            month=TruncMonth('trade_date')
        ).values('month', 'trade_type').annotate(
            total_value=Sum('total_value_usd'),
            total_qty=Sum('quantity_mt')
        ).order_by('month', 'trade_type'))
        
        monthly_map = {}
        for item in price_trends:
            m = item['month'].strftime('%Y-%m') if item['month'] else 'Unknown'
            if m not in monthly_map:
                monthly_map[m] = {"month": m, "import_avg": None, "export_avg": None}
                
            qty = float(item['total_qty'] or 0)
            val = float(item['total_value'] or 0)
            avg = (val / qty) if qty > 0 else 0
            
            if item['trade_type'] == 'IMPORT':
                monthly_map[m]['import_avg'] = avg
            elif item['trade_type'] == 'EXPORT':
                monthly_map[m]['export_avg'] = avg
                
        monthly_avg_price = sorted(list(monthly_map.values()), key=lambda x: x['month'])

        # 2. Extract Top Countries Globally by Quantity
        transactions = transactions.annotate(
            target_country=Case(
                When(trade_type='IMPORT', then=F('seller_country')),
                default=F('buyer_country')
            )
        )
        
        top_countries = list(
            transactions.filter(target_country__isnull=False)
            .exclude(target_country='')
            .values('target_country')
            .annotate(overall_qty=Sum('quantity_mt'))
            .order_by('-overall_qty')[:10]
        )
        
        target_country_names = [c['target_country'] for c in top_countries]

        # 3. Country-Level Breakdown (Avg Price and Qty)
        country_breakdown = list(
            transactions.filter(target_country__in=target_country_names)
            .values('target_country', 'trade_type')
            .annotate(
                total_value=Sum('total_value_usd'),
                total_qty=Sum('quantity_mt')
            )
        )

        country_map = {}
        for c in target_country_names:
            country_map[c] = {
                "country": c, 
                "import_avg": None, "export_avg": None,
                "import_qty_mt": 0, "export_qty_mt": 0
            }

        for item in country_breakdown:
            c = item['target_country']
            qty = float(item['total_qty'] or 0)
            val = float(item['total_value'] or 0)
            avg = (val / qty) if qty > 0 else 0
            
            if item['trade_type'] == 'IMPORT':
                country_map[c]['import_avg'] = avg
                country_map[c]['import_qty_mt'] = qty
            elif item['trade_type'] == 'EXPORT':
                country_map[c]['export_avg'] = avg
                country_map[c]['export_qty_mt'] = qty

        avg_price_by_country = []
        quantity_by_country = []
        
        for c in target_country_names:
            avg_price_by_country.append({
                "country": c,
                "import_avg": country_map[c]['import_avg'],
                "export_avg": country_map[c]['export_avg']
            })
            quantity_by_country.append({
                "country": c,
                "import_qty_mt": country_map[c]['import_qty_mt'],
                "export_qty_mt": country_map[c]['export_qty_mt']
            })

        return Response({
            'product': TradeLensProductSerializer(product).data,
            'is_multi': False,
            'monthly_avg_price': monthly_avg_price,
            'avg_price_by_country': avg_price_by_country,
            'quantity_by_country': quantity_by_country
        })

    def _comparison_multi_product(self, request, main_product, compare_ids):
        """Comparison for multiple products: grouped by month/product and country/product"""
        product_ids = [main_product.id] + compare_ids
        products = TradeLensProduct.objects.filter(id__in=product_ids)

        transactions = TradeLensTransaction.objects.filter(product_id__in=product_ids)
        
        trade_type = request.query_params.get('trade_type')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        buyer = request.query_params.get('buyer')
        seller = request.query_params.get('seller')
        country = request.query_params.get('country')
        
        if trade_type and trade_type.upper() in ['IMPORT', 'EXPORT']:
            transactions = transactions.filter(trade_type=trade_type.upper())
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
                Q(buyer_country__icontains=country) | Q(seller_country__icontains=country)
            )

        # 1. Monthly Avg Price by Product
        price_trends = list(transactions.annotate(
            month=TruncMonth('trade_date')
        ).values('month', 'product_id').annotate(
            total_value=Sum('total_value_usd'),
            total_qty=Sum('quantity_mt')
        ).order_by('month', 'product_id'))
        
        monthly_map = {}
        for item in price_trends:
            m = item['month'].strftime('%Y-%m') if item['month'] else 'Unknown'
            if m not in monthly_map:
                monthly_map[m] = {"month": m}
                
            qty = float(item['total_qty'] or 0)
            val = float(item['total_value'] or 0)
            avg = (val / qty) if qty > 0 else 0
            
            monthly_map[m][str(item['product_id'])] = avg

        monthly_avg_price = sorted(list(monthly_map.values()), key=lambda x: x['month'])

        # 2. Extract Top Countries Globally by Quantity across chosen products
        transactions = transactions.annotate(
            target_country=Case(
                When(trade_type='IMPORT', then=F('seller_country')),
                default=F('buyer_country')
            )
        )
        
        top_countries = list(
            transactions.filter(target_country__isnull=False)
            .exclude(target_country='')
            .values('target_country')
            .annotate(overall_qty=Sum('quantity_mt'))
            .order_by('-overall_qty')[:10]
        )
        target_country_names = [c['target_country'] for c in top_countries]

        # 3. Country-Level Breakdown (Avg Price and Qty) by Product
        country_breakdown = list(
            transactions.filter(target_country__in=target_country_names)
            .values('target_country', 'product_id')
            .annotate(
                total_value=Sum('total_value_usd'),
                total_qty=Sum('quantity_mt')
            )
        )

        country_qty_map = {}
        country_price_map = {}
        for c in target_country_names:
            country_qty_map[c] = {"country": c}
            country_price_map[c] = {"country": c}

        for item in country_breakdown:
            c = item['target_country']
            pid = str(item['product_id'])
            qty = float(item['total_qty'] or 0)
            val = float(item['total_value'] or 0)
            avg = (val / qty) if qty > 0 else 0
            
            country_qty_map[c][pid] = qty
            country_price_map[c][pid] = avg

        avg_price_by_country = [country_price_map[c] for c in target_country_names]
        quantity_by_country = [country_qty_map[c] for c in target_country_names]
        
        compared_products = [{"id": str(p.id), "name": p.name} for p in products]

        return Response({
            'product': TradeLensProductSerializer(main_product).data,
            'is_multi': True,
            'compared_products': compared_products,
            'monthly_avg_price': monthly_avg_price,
            'avg_price_by_country': avg_price_by_country,
            'quantity_by_country': quantity_by_country
        })

    @action(detail=True, methods=['get'])
    def details(self, request, pk=None):
        """Details: paginated transaction table with sidebar aggregations"""
        product = self.get_object()
        transactions = product.transactions.all()
        
        trade_type = request.query_params.get('trade_type')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        buyer = request.query_params.get('buyer')
        seller = request.query_params.get('seller')
        country = request.query_params.get('country')
        
        if trade_type and trade_type.upper() in ['IMPORT', 'EXPORT']:
            transactions = transactions.filter(trade_type=trade_type.upper())
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
                Q(buyer_country__icontains=country) | Q(seller_country__icontains=country)
            )
            
        # Global Summary (post-filters)
        summary_stats = transactions.aggregate(
            total_transactions=Count('id'),
            total_import_quantity=Sum('quantity_mt', filter=Q(trade_type='IMPORT')),
            total_export_quantity=Sum('quantity_mt', filter=Q(trade_type='EXPORT')),
            total_import_value=Sum('total_value_usd', filter=Q(trade_type='IMPORT')),
            total_export_value=Sum('total_value_usd', filter=Q(trade_type='EXPORT'))
        )
        
        summary = {
            "total_transactions": summary_stats['total_transactions'] or 0,
            "total_import_quantity": float(summary_stats['total_import_quantity'] or 0),
            "total_export_quantity": float(summary_stats['total_export_quantity'] or 0),
            "total_import_value": float(summary_stats['total_import_value'] or 0),
            "total_export_value": float(summary_stats['total_export_value'] or 0),
        }

        # Sidebar Analytics: Top 10 by Quantity
        top_buyers = list(
            transactions.filter(buyer_name__isnull=False)
            .exclude(buyer_name='')
            .values('buyer_name')
            .annotate(quantity_mt=Sum('quantity_mt'), avg_price=Avg('price_usd'))
            .order_by('-quantity_mt')[:10]
        )
        
        top_sellers = list(
            transactions.filter(seller_name__isnull=False)
            .exclude(seller_name='')
            .values('seller_name')
            .annotate(quantity_mt=Sum('quantity_mt'), avg_price=Avg('price_usd'))
            .order_by('-quantity_mt')[:10]
        )
        
        mapped_top_buyers = [
            {"buyer": b['buyer_name'], "quantity_mt": float(b['quantity_mt'] or 0), "avg_price": float(b['avg_price'] or 0)} 
            for b in top_buyers
        ]
        
        mapped_top_sellers = [
            {"seller": s['seller_name'], "quantity_mt": float(s['quantity_mt'] or 0), "avg_price": float(s['avg_price'] or 0)} 
            for s in top_sellers
        ]
        
        # Paginated results mapped exact to wireframe schema
        paginator = StandardPagination()
        page = paginator.paginate_queryset(transactions.order_by('-trade_date'), request)
        
        results = []
        for tx in page:
            results.append({
                "id": tx.id,
                "buyer": tx.buyer_name,
                "seller": tx.seller_name,
                "country": tx.seller_country if tx.trade_type == 'IMPORT' else tx.buyer_country,
                "quantity_mt": float(tx.quantity_mt),
                "avg_price_usd_mt": float(tx.price_usd),
                "total_value_usd": float(tx.total_value_usd),
                "date": tx.trade_date.strftime('%Y-%m-%d') if tx.trade_date else None,
                "trade_type": tx.trade_type
            })

        response = paginator.get_paginated_response(results)
        response.data['summary'] = summary
        response.data['top_buyers'] = mapped_top_buyers
        response.data['top_sellers'] = mapped_top_sellers
        
        return response

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
