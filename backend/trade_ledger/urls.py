from django.urls import path
from . import views  
from .pdf_export_view import export_comparison_pdf

urlpatterns = [
    path('explorer/', views.explorer_api, name='explorer_api'),
    path('company/<str:company_name>/overview/', views.company_overview_api),
    path('company/<str:company_name>/products/', views.company_products_api),
    path('company/<str:company_name>/partners/', views.company_partners_api),
    path('company/<str:company_name>/trends/', views.company_trends_api),
    path('compare/', views.compare_companies_api),
    path('export-comparison-pdf/', export_comparison_pdf, name='export_comparison_pdf'),
    
    
    path('company/<str:company_name>/similar/', views.similar_companies_api),
    path('company/<str:company_name>/potential-partners/', views.potential_partners_api),
    path('company/<str:company_name>/network-influence/', views.network_influence_api),
    path('product-clusters/', views.product_clusters_api),
    
    
    path('predict/sellers/<str:buyer_name>/', views.predict_sellers_api, name='predict_sellers'),
    path('predict/buyers/<str:seller_name>/', views.predict_buyers_api, name='predict_buyers'),
    path('predict/methods/', views.link_prediction_methods_api, name='link_prediction_methods'),
]