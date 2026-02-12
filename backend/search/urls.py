from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SearchViewSet

router = DefaultRouter()
# The base URL is /api/search/ (from project urls.py)
# We register '' so that the viewset maps to /api/search/
# This makes 'list' -> /api/search/ and 'supplier_detail' -> /api/search/supplier-detail/
# However, the frontend currently calls /api/search/query/?q=... so we need to keep 'query' or adjust frontend
# Wait, frontend calls:
# 1. /api/search/query/?q=...   (This hits list, handled by router.register('query', ...))
# 2. /api/search/supplier-detail/ (This FAILS because it would be /api/search/query/supplier-detail/)

# FIX: We can register the same ViewSet at the root 'api/search' to handle the detail action
# OR registers it at '' and use the `list` action as the query endpoint.
# But `list` is cleaner as just GET /api/search/?q=...

router = DefaultRouter()
# Option A: Register at root. 
# GET /api/search/?q=...  -> list()
# GET /api/search/supplier-detail/ -> supplier_detail()
router.register(r'', SearchViewSet, basename='search')

urlpatterns = [
    path('', include(router.urls)),
]
