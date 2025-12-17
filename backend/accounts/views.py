from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from .forms import UserRegisterForm


import json
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.utils.html import strip_tags

User = get_user_model()



def register_view(request):
    print("Incoming")
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
    print("Here0", request.method)
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)
    try:
        print("Here1", settings.DEFAULT_FROM_EMAIL)
        data = json.loads(request.body)
        print(f"Received signup data: {data}")  
        form = UserRegisterForm({
            "name": data.get("name", ""),
            "email": data.get("email", ""),
            "password1": data.get("password", ""),
            "password2": data.get("password", ""),
            "country": data.get("country", ""),
        })
        print("Here2")
        if form.is_valid():
            print("Here3")
            user = form.save()

            
            verification_url = request.build_absolute_uri(
                f"/accounts/api/verify-email/{user.verification_token}/"
            )

            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {  font-family: Arial, sans-serif; line-height: 1.6; color: #333; } 
                    .container {  max-width: 600px; margin: 0 auto; padding: 20px; } 
                    .header {  background-color: #1A4D2E; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; } 
                    .content {  background-color: #f9f9f9; padding: 30px; border: 1px solid #ddd; } 
                    .button {  display: inline-block; padding: 12px 30px; background-color: #1A4D2E; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; } 
                    .footer {  text-align: center; padding: 20px; color: #666; font-size: 12px; } 
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Welcome to ZaraiLink!</h1>
                    </div>
                    <div class="content">
                        <h2>Hi {user.first_name},</h2>
                        <p>Thank you for registering with ZaraiLink - Your Agri-Trade Intelligence Platform!</p>
                        <p>To complete your registration and activate your account, please verify your email address by clicking the button below:</p>
                        <div style="text-align: center;">
                            <a href="{verification_url}" class="button">Verify Email Address</a>
                        </div>
                        <p>Or copy and paste this link into your browser:</p>
                        <p style="word-break: break-all; color: #1A4D2E;">{verification_url}</p>
                        <p><strong>This verification link will expire in 24 hours.</strong></p>
                        <p>If you didn't create an account with ZaraiLink, please ignore this email.</p>
                    </div>
                    <div class="footer">
                        <p>&copy; 2025 ZaraiLink. All rights reserved.</p>
                        <p>Optimize Data. Empower Tomorrow.</p>
                    </div>
                </div>
            </body>
            </html>
            """

            
            text_content = f"""
            Welcome to ZaraiLink!

            Hi {user.first_name},

            Thank you for registering with ZaraiLink - Your Agri-Trade Intelligence Platform!

            To complete your registration and activate your account, please verify your email address by clicking the link below:

            {verification_url}

            This verification link will expire in 24 hours.

            If you didn't create an account with ZaraiLink, please ignore this email.

            © 2025 ZaraiLink. All rights reserved.
            Optimize Data. Empower Tomorrow.
            """

            
            try:
                email = EmailMultiAlternatives(
                    subject="Verify your ZaraiLink Account",
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[user.email]
                )
                email.attach_alternative(html_content, "text/html")
                email.send(fail_silently=False)
                print(f"Verification email sent to {user.email}")
            except Exception as email_error:
                print(f"Failed to send verification email: {email_error}")
                

            return JsonResponse({
                "success": True,
                "message": "Account created! Please check your email to verify your account.",
                "email": user.email
            })
        else:
            print("Here4")
            print(f"Form errors: {form.errors}")  
            return JsonResponse({"errors": form.errors}, status=400)
    except Exception as e:
        print(f"Signup exception: {str(e)}")  
        import traceback
        traceback.print_exc()
        return JsonResponse({"error": "Invalid request", "details": str(e)}, status=400)


@csrf_exempt
def api_login(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)
    try:
        data = json.loads(request.body)
        email = data.get("email")
        password = data.get("password")

        
        try:
            user_check = User.objects.get(email=email)
            if not user_check.email_verified:
                return JsonResponse({
                    "error": "Please verify your email address before logging in. Check your inbox for the verification link.",
                    "email_not_verified": True
                }, status=403)
        except User.DoesNotExist:
            pass

        user = authenticate(request, email=email, password=password)
        if user:
            if not user.email_verified:
                return JsonResponse({
                    "error": "Please verify your email address before logging in.",
                    "email_not_verified": True
                }, status=403)

            login(request, user)
            return JsonResponse({
                "success": True,
                "user": {
                    "name": f"{user.first_name} {user.last_name}".strip(),
                    "email": user.email,
                    "email_verified": user.email_verified,
                    "token_balance": user.token_balance
                }
            })
        else:
            return JsonResponse({"error": "Invalid email or password"}, status=401)
    except Exception as e:
        return JsonResponse({"error": "Invalid request"}, status=400)


@csrf_exempt
def api_logout(request):
    logout(request)
    return JsonResponse({"success": True})


def api_check_auth(request):
    """
    Check if user is authenticated and return user info
    """
    if request.user.is_authenticated:
        return JsonResponse({
            "authenticated": True,
            "user": {
                "name": f"{request.user.first_name} {request.user.last_name}".strip(),
                "email": request.user.email,
                "email_verified": request.user.email_verified,
                "token_balance": request.user.token_balance
            }
        })
    else:
        return JsonResponse({"authenticated": False})


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


def api_verify_email(request, token):
    """
    Verify user's email using the token sent via email.
    Redirects to frontend after verification.
    """
    try:
        user = User.objects.get(verification_token=token)

        if user.email_verified:
            
            frontend_url = f"{settings.FRONTEND_URL}/verify-email/{token}?status=already_verified"
            return HttpResponseRedirect(frontend_url)

        if not user.is_verification_token_valid():
            
            frontend_url = f"{settings.FRONTEND_URL}/verify-email/{token}?status=expired"
            return HttpResponseRedirect(frontend_url)

        
        user.email_verified = True
        user.is_active = True
        user.save(update_fields=['email_verified', 'is_active'])

        
        frontend_url = f"{settings.FRONTEND_URL}/verify-email/{token}?status=verified"
        return HttpResponseRedirect(frontend_url)

    except User.DoesNotExist:
        
        frontend_url = f"{settings.FRONTEND_URL}/verify-email/{token}?status=invalid"
        return HttpResponseRedirect(frontend_url)


@csrf_exempt
def api_resend_verification(request):
    """
    Resend verification email to the user
    """
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        data = json.loads(request.body)
        email = data.get("email")

        if not email:
            return JsonResponse({"error": "Email is required"}, status=400)

        try:
            user = User.objects.get(email=email)

            if user.email_verified:
                return JsonResponse({
                    "error": "Email is already verified",
                    "already_verified": True
                }, status=400)

            
            user.regenerate_verification_token()

            
            verification_url = request.build_absolute_uri(
                f"/accounts/api/verify-email/{user.verification_token}/"
            )

            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {  font-family: Arial, sans-serif; line-height: 1.6; color: #333; } 
                    .container {  max-width: 600px; margin: 0 auto; padding: 20px; } 
                    .header {  background-color: #1A4D2E; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; } 
                    .content {  background-color: #f9f9f9; padding: 30px; border: 1px solid #ddd; } 
                    .button {  display: inline-block; padding: 12px 30px; background-color: #1A4D2E; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; } 
                    .footer {  text-align: center; padding: 20px; color: #666; font-size: 12px; } 
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>ZaraiLink Email Verification</h1>
                    </div>
                    <div class="content">
                        <h2>Hi {user.first_name},</h2>
                        <p>You requested a new verification link for your ZaraiLink account.</p>
                        <p>Please verify your email address by clicking the button below:</p>
                        <div style="text-align: center;">
                            <a href="{verification_url}" class="button">Verify Email Address</a>
                        </div>
                        <p>Or copy and paste this link into your browser:</p>
                        <p style="word-break: break-all; color: #1A4D2E;">{verification_url}</p>
                        <p><strong>This verification link will expire in 24 hours.</strong></p>
                        <p>If you didn't request this email, please ignore it.</p>
                    </div>
                    <div class="footer">
                        <p>&copy; 2025 ZaraiLink. All rights reserved.</p>
                        <p>Optimize Data. Empower Tomorrow.</p>
                    </div>
                </div>
            </body>
            </html>
            """

            
            text_content = f"""
            ZaraiLink Email Verification

            Hi {user.first_name},

            You requested a new verification link for your ZaraiLink account.

            Please verify your email address by clicking the link below:

            {verification_url}

            This verification link will expire in 24 hours.

            If you didn't request this email, please ignore it.

            © 2025 ZaraiLink. All rights reserved.
            Optimize Data. Empower Tomorrow.
            """

            
            try:
                email = EmailMultiAlternatives(
                    subject="Verify your ZaraiLink Account",
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[user.email]
                )
                email.attach_alternative(html_content, "text/html")
                email.send(fail_silently=False)
                print(f"Verification email resent to {user.email}")
            except Exception as email_error:
                print(f"Failed to resend verification email: {email_error}")
                

            return JsonResponse({
                "success": True,
                "message": "Verification email resent successfully!"
            })

        except User.DoesNotExist:
            
            return JsonResponse({
                "success": True,
                "message": "If that email is registered, a verification email has been sent."
            })

    except Exception as e:
        return JsonResponse({"error": "Invalid request", "details": str(e)}, status=400)