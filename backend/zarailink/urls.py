"""
URL configuration for zarailink project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# zarailink/urls.py
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

def favicon(request):
    return HttpResponse(status=204)

urlpatterns = [
    path('favicon.ico', favicon),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('api/subscriptions/', include('subscriptions.urls')),
    path('api/', include('trade_ledger.urls')),  # ← Only this line for trade_ledger
    path("companies/", include("companies.urls")),
    path("ckeditor5/", include('django_ckeditor_5.urls')),
]