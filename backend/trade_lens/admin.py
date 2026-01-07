from django.contrib import admin
from .models import TradeLensProduct, TradeLensTransaction


@admin.register(TradeLensProduct)
class TradeLensProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'hs_code', 'category', 'created_at')
    list_filter = ('category',)
    search_fields = ('name', 'hs_code')
    ordering = ('name',)


@admin.register(TradeLensTransaction)
class TradeLensTransactionAdmin(admin.ModelAdmin):
    list_display = ('product', 'trade_date', 'trade_type', 'buyer_name', 
                    'seller_name', 'quantity_mt', 'price_usd', 'total_value_usd')
    list_filter = ('trade_type', 'product', 'buyer_country', 'seller_country', 'province', 'port')
    search_fields = ('buyer_name', 'seller_name', 'product__name')
    date_hierarchy = 'trade_date'
    ordering = ('-trade_date',)
