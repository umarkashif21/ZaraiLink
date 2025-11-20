from django.urls import path
from . import views
from django.contrib import auth as auth_views

app_name = "accounts"

urlpatterns = [
    # Optional: HTML views for testing
    path("register/", views.register_view, name="register"),
    path("login/", views.register_view, name="login"),

    # --- API endpoints for React ---
    path("api/signup/", views.api_signup, name="api_signup"),
    path("api/login/", views.api_login, name="api_login"),
    path("api/logout/", views.api_logout, name="api_logout"),
    path("api/forgot-password/", views.api_forgot_password, name="api_forgot_password"),

    # --- Password reset (Django built-in, server-rendered) ---
    path('password_reset_confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='registration/password_reset_confirm.html',
             success_url='/accounts/password_reset_complete/'
         ),
         name='password_reset_confirm'),
    path('password_reset_complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='registration/password_reset_complete.html'
         ),
         name='password_reset_complete'),
]