from django.urls import path
from . import views

app_name = 'subscriptions'

urlpatterns = [
    path('plans/', views.list_plans, name='list_plans'),
    path('redeem/', views.redeem_code, name='redeem_code'),
    path('generate-codes/', views.generate_codes_view, name='generate_codes'),
]
