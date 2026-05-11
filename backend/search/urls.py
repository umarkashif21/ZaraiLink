from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SearchViewSet

router = DefaultRouter()
router.register(r'', SearchViewSet, basename='search')

urlpatterns = [
    path('supplier-detail/', SearchViewSet.as_view({'get': 'supplier_detail'}), name='supplier-detail'),
    path('supplier-transactions/', SearchViewSet.as_view({'get': 'supplier_transactions'}), name='supplier-transactions'),
    path('', include(router.urls)),
]
