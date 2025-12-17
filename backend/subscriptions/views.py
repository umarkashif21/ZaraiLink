from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import SubscriptionPlan, RedeemCode
from django.db import transaction


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
@permission_classes([IsAuthenticated])
@transaction.atomic
def redeem_code(request):
    """Redeem a subscription code"""
    code_str = request.data.get('code', '').strip().upper()
    plan_id = request.data.get('plan_id')
    
    if not code_str:
        return Response({
            'status': 'error',
            'message': 'Please enter a redeem code'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        
        code = RedeemCode.objects.select_for_update().get(code=code_str)
        
        
        if plan_id and code.plan.id != plan_id:
            return Response({
                'status': 'error',
                'message': f'This code is for "{code.plan.plan_name}", not the selected plan'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        
        success, message = code.redeem(request.user)
        
        if success:
            return Response({
                'status': 'success',
                'message': message,
                'tokens_added': code.plan.tokens_included,
                'plan_name': code.plan.plan_name,
                'new_balance': request.user.token_balance
            })
        else:
            return Response({
                'status': 'error',
                'message': message
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except RedeemCode.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Invalid redeem code'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'An error occurred: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



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
