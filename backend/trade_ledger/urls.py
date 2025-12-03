from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TradeCompanyViewSet, ProductCategoryListView

router = DefaultRouter()
router.register(r'companies', TradeCompanyViewSet, basename='trade-company')

urlpatterns = [
    path('', include(router.urls)),
    path('product-categories/', ProductCategoryListView.as_view(), name='product-categories'),
]
