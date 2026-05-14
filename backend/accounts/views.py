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

            user.email_verified = True
            user.is_active = True
            user.save()

            return JsonResponse({
                "success": True,
                "message": "Account created! You are now ready to log in.",
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

        
        user = authenticate(request, email=email, password=password)
        if user:

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
        if not email:
            return JsonResponse({"error": "Email is required"}, status=400)
        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_url = f"{settings.FRONTEND_URL.rstrip('/')}/reset-password/{uid}/{token}"

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #1A4D2E; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                    .content {{ background-color: #f9f9f9; padding: 30px; border: 1px solid #ddd; }}
                    .button {{ display: inline-block; padding: 12px 30px; background-color: #1A4D2E; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                    .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header"><h1>ZaraiLink Password Reset</h1></div>
                    <div class="content">
                        <h2>Hi {user.first_name or 'there'},</h2>
                        <p>We received a request to reset your ZaraiLink password.</p>
                        <p>Click the button below to choose a new password:</p>
                        <div style="text-align: center;">
                            <a href="{reset_url}" class="button">Reset Password</a>
                        </div>
                        <p>Or copy and paste this link into your browser:</p>
                        <p style="word-break: break-all; color: #1A4D2E;">{reset_url}</p>
                        <p>If you didn't request this, you can safely ignore this email.</p>
                    </div>
                    <div class="footer">
                        <p>&copy; ZaraiLink. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            text_content = (
                f"Hi {user.first_name or 'there'},\n\n"
                f"We received a request to reset your ZaraiLink password.\n"
                f"Use the link below to choose a new password:\n\n{reset_url}\n\n"
                f"If you didn't request this, you can safely ignore this email."
            )
            try:
                msg = EmailMultiAlternatives(
                    subject="Reset your ZaraiLink password",
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[user.email],
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send(fail_silently=False)
            except Exception as mail_err:
                import logging
                logging.getLogger('zarailink').error(
                    f"Failed to send password reset email: {mail_err}"
                )
        except User.DoesNotExist:
            pass
        return JsonResponse({
            "success": True,
            "message": "If that email is registered, a password reset link has been sent.",
        })
    except Exception:
        return JsonResponse({"error": "Invalid request"}, status=400)


def api_verify_email(request, token):
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


@csrf_exempt
def api_update_profile(request):
    """Update the authenticated user's display name."""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=401)
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)
    try:
        data = json.loads(request.body)
        name = data.get("name", "").strip()
        if not name:
            return JsonResponse({"error": "Name cannot be empty"}, status=400)
        parts = name.split(" ", 1)
        request.user.first_name = parts[0]
        request.user.last_name = parts[1] if len(parts) > 1 else ""
        request.user.save(update_fields=["first_name", "last_name"])
        return JsonResponse({
            "success": True,
            "name": f"{request.user.first_name} {request.user.last_name}".strip()
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
def api_change_password(request):
    """Change the authenticated user's password after verifying the current one."""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=401)
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)
    try:
        data = json.loads(request.body)
        current_password = data.get("current_password", "")
        new_password = data.get("new_password", "")
        if not current_password or not new_password:
            return JsonResponse({"error": "Both current and new password are required"}, status=400)
        if len(new_password) < 8:
            return JsonResponse({"error": "New password must be at least 8 characters"}, status=400)
        user = authenticate(request, email=request.user.email, password=current_password)
        if not user:
            return JsonResponse({"error": "Current password is incorrect"}, status=400)
        user.set_password(new_password)
        user.save()
        # Keep the user logged in after password change
        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(request, user)
        return JsonResponse({"success": True, "message": "Password updated successfully"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
def api_reset_password_confirm(request):
    """Confirm a password reset using the uid + token from the email link."""
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)
    try:
        data = json.loads(request.body)
        uid = data.get("uid")
        token = data.get("token")
        new_password = data.get("new_password", "")

        if not uid or not token or not new_password:
            return JsonResponse(
                {"error": "uid, token and new_password are required"}, status=400
            )

        from django.utils.http import urlsafe_base64_decode
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError

        try:
            user_pk = urlsafe_base64_decode(uid).decode()
            user = User.objects.get(pk=user_pk)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return JsonResponse({"error": "Invalid reset link."}, status=400)

        if not default_token_generator.check_token(user, token):
            return JsonResponse(
                {"error": "Reset link is invalid or has expired."}, status=400
            )

        try:
            validate_password(new_password, user=user)
        except ValidationError as ve:
            return JsonResponse({"error": " ".join(ve.messages)}, status=400)

        user.set_password(new_password)
        user.save()

        # Auto-login on the new password so the React app immediately sees an authed session.
        login(request, user)

        return JsonResponse({
            "success": True,
            "message": "Password reset successful.",
            "user": {
                "name": f"{user.first_name} {user.last_name}".strip(),
                "email": user.email,
                "email_verified": user.email_verified,
                "token_balance": user.token_balance,
            },
        })
    except Exception:
        return JsonResponse({"error": "Invalid request"}, status=400)