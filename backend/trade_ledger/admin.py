from django.contrib import admin
from .models import ProductCategory, TradeCompany, TradeProduct, TradePartner, TradeTrend


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'hs_code')
    search_fields = ('name', 'hs_code')


@admin.register(TradeCompany)
class TradeCompanyAdmin(admin.ModelAdmin):
    list_display = ('company', 'estimated_revenue', 'trade_volume', 'is_exporter', 'is_importer')
    list_filter = ('is_exporter', 'is_importer')
    search_fields = ('company__name',)
    readonly_fields = ('company',)


@admin.register(TradeProduct)
class TradeProductAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'company', 'category', 'avg_price', 'volume', 'yoy_growth')
    list_filter = ('category', 'currency', 'unit')
    search_fields = ('product_name', 'company__company__name')


@admin.register(TradePartner)
class TradePartnerAdmin(admin.ModelAdmin):
    list_display = ('company', 'country', 'port_name', 'trade_volume', 'percentage_share', 'is_export')
    list_filter = ('country', 'is_export')
    search_fields = ('company__company__name', 'country', 'port_name')


@admin.register(TradeTrend)
class TradeTrendAdmin(admin.ModelAdmin):
    list_display = ('company', 'product', 'month', 'year', 'volume', 'avg_price')
    list_filter = ('year', 'month')
    search_fields = ('company__company__name', 'product__product_name')
