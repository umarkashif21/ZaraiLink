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
    
    if not code_str:
        return Response({
            'status': 'error',
            'message': 'Please enter a redeem code'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Find the code
        code = RedeemCode.objects.select_for_update().get(code=code_str)
        
        # Attempt to redeem
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
