from django.contrib import admin
from django.urls import path, include, re_path
from django.http import HttpResponse
from django.views.generic import TemplateView

def favicon(request):
    return HttpResponse(status=204)

urlpatterns = [
    path('favicon.ico', favicon),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('api/subscriptions/', include('subscriptions.urls')),
    path('api/', include('companies.urls')),  

    path('api/search/', include('search.urls')), # Unified Search
    path("ckeditor5/", include('django_ckeditor_5.urls')),
    path('api-auth/', include('rest_framework.urls')), # DRF Login
    re_path(r'^.*$', TemplateView.as_view(template_name='index.html')),
]