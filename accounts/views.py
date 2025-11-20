from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from .forms import UserRegisterForm

# --- NEW API IMPORTS ---
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


# Optional: Keep your existing HTML views (e.g., for testing)
def register_view(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created!")
            return redirect("accounts:login")
    else:
        form = UserRegisterForm()
    return render(request, "accounts/register.html", {"form": form})


@csrf_exempt
def api_signup(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)
    try:
        data = json.loads(request.body)
        form = UserRegisterForm({
            "name": data.get("name", ""),
            "email": data.get("email", ""),
            "password1": data.get("password", ""),
            "password2": data.get("password", ""),
            "country": data.get("country", ""),
        })
        if form.is_valid():
            user = form.save()
            login(request, user)
            return JsonResponse({"success": True})
        else:
            return JsonResponse({"errors": form.errors}, status=400)
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)


@csrf_exempt
def api_login(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)
    try:
        data = json.loads(request.body)
        email = data.get("email")
        password = data.get("password")
        user = authenticate(request, email=email, password=password)
        if user:
            login(request, user)
            return JsonResponse({
                "success": True,
                "user": {
                    "name": f"{user.first_name} {user.last_name}".strip(),
                    "email": user.email
                }
            })
        else:
            return JsonResponse({"error": "Invalid email or password"}, status=401)
    except Exception:
        return JsonResponse({"error": "Invalid request"}, status=400)


def api_logout(request):
    logout(request)
    return JsonResponse({"success": True})


@csrf_exempt
def api_forgot_password(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)
    try:
        data = json.loads(request.body)
        email = data.get("email")
        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_url = request.build_absolute_uri(
                reverse("accounts:password_reset_confirm", args=[uid, token])
            )
            send_mail(
                subject="Reset your ZaraiLink password",
                message=f"Click the link to reset your password: {reset_url}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except User.DoesNotExist:
            pass
        return JsonResponse({"success": True})
    except Exception:
        return JsonResponse({"error": "Invalid request"}, status=400)