from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import SubscriptionPlan, RedeemCode
from .services import purchase_access as _purchase_access
from django.db import transaction
from rest_framework.authentication import SessionAuthentication

class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # To not perform the CSRF check

@api_view(['GET'])
def list_plans(request):
    """List all available subscription plans"""
    plans = SubscriptionPlan.objects.all()
    plans_data = [{
        'id': plan.id,
        'plan_name': plan.plan_name,
        'price': str(plan.price),
        'currency': plan.currency,
        'tokens_included': plan.tokens_included,
        'description': plan.description,
        'features': plan.features,
    } for plan in plans]
    
    return Response(plans_data)


@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([IsAuthenticated])
@transaction.atomic
def redeem_code(request):
    """Bypass code and just instantly give tokens based on plan (Demo Mode)"""
    plan_id = request.data.get('plan_id')
    
    if not plan_id:
        return Response({
            'status': 'error',
            'message': 'No plan selected.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        plan = SubscriptionPlan.objects.get(id=plan_id)
        
        request.user.token_balance += plan.tokens_included
        request.user.save()
        
        return Response({
            'status': 'success',
            'message': f'Successfully activated {plan.plan_name}. Added {plan.tokens_included} tokens!',
            'tokens_added': plan.tokens_included,
            'plan_name': plan.plan_name,
            'new_balance': request.user.token_balance
        })
            
    except SubscriptionPlan.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Invalid subscription plan.'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'An error occurred: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([IsAuthenticated])
def purchase_access(request):
    """
    Purchase token-based access to a data category or specific product.

    Body:
        access_type  : 'HS_CODE' | 'PRODUCT'
        hscode       : str  (e.g. '1702.3000')
        product_name : str  (required when access_type='PRODUCT')

    Returns:
        success        : bool
        message        : str
        new_balance    : int   (only on success)
        access_state   : 'FULL_ACCESS' | 'PRODUCT_ACCESS' (only on success)
        required_tokens: int   (only on failure)
    """
    from .services import HS_CODE_PRICE, PRODUCT_PRICE

    access_type  = request.data.get('access_type', '').upper()
    hscode       = (request.data.get('hscode') or '').strip()
    subcat_id    = request.data.get('subcat_id')
    product_name = request.data.get('product_name')

    if subcat_id is not None:
        try:
            subcat_id = int(subcat_id)
        except ValueError:
            subcat_id = None
    elif product_name:
        # Fallback for DataDashboard which currently only knows the name
        from trade_data.models import ProductSubCategory
        sub_obj = ProductSubCategory.objects.filter(name=product_name.strip(), hs_code__startswith=hscode).first()
        if not sub_obj:
            sub_obj = ProductSubCategory.objects.filter(name=product_name.strip()).first()
        if sub_obj:
            subcat_id = sub_obj.id

    if not hscode:
        return Response({'success': False, 'message': 'hscode is required.'},
                        status=status.HTTP_400_BAD_REQUEST)

    success, message, new_balance = _purchase_access(
        user=request.user,
        access_type=access_type,
        hscode=hscode,
        subcat_id=subcat_id,
    )

    if success:
        access_state = 'FULL_ACCESS' if access_type == 'HS_CODE' else 'PRODUCT_ACCESS'
        return Response({
            'success': True,
            'message': message,
            'new_balance': new_balance,
            'access_state': access_state,
        })
    else:
        required = HS_CODE_PRICE if access_type == 'HS_CODE' else PRODUCT_PRICE
        http_status = (
            status.HTTP_402_PAYMENT_REQUIRED
            if 'Insufficient' in message
            else status.HTTP_400_BAD_REQUEST
        )
        return Response({
            'success': False,
            'message': message,
            'required_tokens': required,
            'current_balance': request.user.token_balance,
        }, status=http_status)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_data_view(request):
    user = request.user
    from .models import UserAccess, TokenPurchase, RedeemCode
    from trade_data.models import ProductCategory, ProductSubCategory
    
    access_grants = list(UserAccess.objects.filter(user=user).order_by('-purchased_at'))
    
    entitlements = []
    total_tokens_spent = 0
    top_category_counts = {}

    for grant in access_grants:
        total_tokens_spent += grant.tokens_spent
        top_category_counts[grant.hscode] = top_category_counts.get(grant.hscode, 0) + 1
        
        name = f"HS {grant.hscode}"
        access_level = "Full Category Access"
        
        if grant.access_type == 'HS_CODE':
            cat = ProductCategory.objects.filter(hs_code=grant.hscode).first()
            if cat:
                name = cat.name
            else:
                name = f"HS {grant.hscode} Category"
        else:
            access_level = "Product Access"
            if grant.subcat_id:
                subcat = ProductSubCategory.objects.filter(id=grant.subcat_id).first()
                if subcat:
                    name = subcat.name
                else:
                    name = f"Product (ID {grant.subcat_id})"
            else:
                name = f"Product in HS {grant.hscode}"

        entitlements.append({
            "id": f"ent_{grant.id}",
            "name": name,
            "accessLevel": access_level,
            "purchaseDate": grant.purchased_at.strftime("%Y-%m-%d"),
            "tokenCost": grant.tokens_spent,
            "status": "active"
        })
        
    top_category_name = "None"
    if top_category_counts:
        top_hscode = max(top_category_counts, key=top_category_counts.get)
        cat = ProductCategory.objects.filter(hs_code=top_hscode).first()
        if cat:
            top_category_name = f"{top_hscode} ({cat.name})"
        else:
            top_category_name = top_hscode
            
    history = []
    for grant in access_grants:
        name = f"HS {grant.hscode}"
        if grant.access_type == 'HS_CODE':
            cat = ProductCategory.objects.filter(hs_code=grant.hscode).first()
            if cat: name = cat.name
        elif grant.subcat_id:
            subcat = ProductSubCategory.objects.filter(id=grant.subcat_id).first()
            if subcat: name = subcat.name
            
        history.append({
            "id": f"spend_{grant.id}",
            "date": grant.purchased_at.strftime("%Y-%m-%d"),
            "date_obj": grant.purchased_at,
            "action": f"Unlock: {name}",
            "amount": -grant.tokens_spent
        })
        
    purchases = TokenPurchase.objects.filter(user=user)
    for p in purchases:
        history.append({
            "id": f"pur_{p.id}",
            "date": p.purchased_at.strftime("%Y-%m-%d"),
            "date_obj": p.purchased_at,
            "action": f"Token Top-up via {p.payment_provider}",
            "amount": p.tokens_purchased
        })
        
    redeems = RedeemCode.objects.filter(redeemed_by=user)
    for r in redeems:
        if r.redeemed_at:
            history.append({
                "id": f"red_{r.id}",
                "date": r.redeemed_at.strftime("%Y-%m-%d"),
                "date_obj": r.redeemed_at,
                "action": f"Code Redeemed: {r.plan.plan_name if r.plan else 'Offer'}",
                "amount": r.plan.tokens_included if hasattr(r, 'plan') and r.plan else 0
            })
            
    history.sort(key=lambda x: x["date_obj"], reverse=True)
    for h in history:
        del h["date_obj"]

    queries_count = max(0, total_tokens_spent // 10) + 12 if total_tokens_spent > 0 else 0
    products_viewed = max(0, total_tokens_spent // 50) + 5 if total_tokens_spent > 0 else 0

    return Response({
        "entitlements": entitlements,
        "tokenHistory": history,
        "telemetry": {
            "queries": queries_count,
            "productsViewed": products_viewed,
            "tokensSpent": total_tokens_spent,
            "topCategory": top_category_name
        }
    })

from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse

@user_passes_test(lambda u: u.is_staff)
def generate_codes_view(request):
    if request.method == 'POST':
        plan_id = request.POST.get('plan_id')
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
            codes = []
            for _ in range(10):
                while True:
                    code = RedeemCode.generate_code()
                    if not RedeemCode.objects.filter(code=code).exists():
                        break
                
                RedeemCode.objects.create(
                    code=code,
                    plan=plan,
                    status='active'
                )
                codes.append(code)
            
            messages.success(request, f'Successfully generated 10 codes for {plan.plan_name}.')
        except SubscriptionPlan.DoesNotExist:
            messages.error(request, 'Selected plan does not exist.')
        except Exception as e:
            messages.error(request, f'Error generating codes: {str(e)}')
            
    return redirect('admin:index')
