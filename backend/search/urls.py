from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SearchViewSet

router = DefaultRouter()
# GET /api/search/?q=...  -> list()
# GET /api/search/supplier-detail/ -> supplier_detail()
router.register(r'', SearchViewSet, basename='search')

urlpatterns = [
    path('', include(router.urls)),
]
