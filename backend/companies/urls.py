from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CompanyViewSet, KeyContactViewSet,
    SectorListView, CompanyTypeListView, CompanyRoleListView
)

app_name = 'companies'

router = DefaultRouter()
router.register('companies', CompanyViewSet, basename='company')
router.register('key-contacts', KeyContactViewSet, basename='keycontact')

urlpatterns = [
    path('', include(router.urls)),
    path('sectors/', SectorListView.as_view(), name='sectors'),
    path('company-types/', CompanyTypeListView.as_view(), name='company-types'),
    path('company-roles/', CompanyRoleListView.as_view(), name='company-roles'),
]
