from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from django.db import transaction
from django.db.models import Q
from .models import (
    Company, KeyContact, KeyContactUnlock,
    Sector, CompanyRole, CompanyType
)
from .serializers import (
    CompanyListSerializer, CompanyDetailSerializer,
    KeyContactSerializer, SectorSerializer,
    CompanyRoleSerializer, CompanyTypeSerializer
)


class CompanyViewSet(viewsets.ReadOnlyModelViewSet):
    """API for browsing companies"""
    queryset = Company.objects.filter(verification_status='verified')
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return CompanyListSerializer
        return CompanyDetailSerializer
    
    def get_queryset(self):
        """Filter companies based on query params"""
        queryset = self.queryset
        
        # Apply filters
        search = self.request.query_params.get('search', '').strip()
        region = self.request.query_params.get('region', '').strip()
        sector = self.request.query_params.get('sector', '').strip()
        company_type = self.request.query_params.get('type', '').strip()
        role = self.request.query_params.get('role', '').strip()
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        if region:
            queryset = queryset.filter(province=region)
        if sector:
            queryset = queryset.filter(sector_id=sector)
        if company_type:
            queryset = queryset.filter(company_type_id=company_type)
        if role:
            queryset = queryset.filter(company_role_id=role)
        
        return queryset.select_related(
            'sector', 'company_role', 'company_type'
        ).prefetch_related('products', 'key_contacts')
    
    @action(detail=False, methods=['get'])
    def regions(self, request):
        """Get available regions dynamically"""
        regions = Company.objects.filter(
            verification_status='verified',
            province__isnull=False
        ).values_list('province', flat=True).distinct().order_by('province')
        return Response(list(regions))


class KeyContactViewSet(viewsets.ReadOnlyModelViewSet):
    """API for key contacts"""
    queryset = KeyContact.objects.all()
    serializer_class = KeyContactSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter contacts by company if specified"""
        queryset = self.queryset
        company = self.request.query_params.get('company')
        if company:
            queryset = queryset.filter(company_id=company)
        return queryset.select_related('company')
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    @transaction.atomic
    def unlock(self, request, pk=None):
        """Unlock a contact using tokens"""
        contact = self.get_object()
        user = request.user
        
        # Check if already unlocked
        already_unlocked = KeyContactUnlock.objects.filter(
            user=user, 
            key_contact=contact
        ).exists()
        
        if already_unlocked:
            return Response({
                'status': 'already_unlocked',
                'message': 'You have already unlocked this contact',
                'contact': KeyContactSerializer(contact, context={'request': request}).data
            })
        
        # Check if public (free)
        if contact.is_public:
            # Create unlock record but don't charge
            KeyContactUnlock.objects.create(user=user, key_contact=contact)
            return Response({
                'status': 'success',
                'message': 'Contact unlocked (public contact)',
                'tokens_charged': 0,
                'remaining_balance': user.token_balance,
                'contact': KeyContactSerializer(contact, context={'request': request}).data
            })
        
        # Check token balance
        if not user.has_tokens(1):
            return Response({
                'status': 'insufficient_tokens',
                'message': 'Not enough tokens. Please purchase more.',
                'current_balance': user.token_balance,
                'required': 1
            }, status=status.HTTP_402_PAYMENT_REQUIRED)
        
        # Deduct token and unlock
        success = user.deduct_tokens(1)
        if success:
            KeyContactUnlock.objects.create(user=user, key_contact=contact)
            
            return Response({
                'status': 'success',
                'message': 'Contact unlocked successfully',
                'tokens_charged': 1,
                'remaining_balance': user.token_balance,
                'contact': KeyContactSerializer(contact, context={'request': request}).data
            })
        else:
            return Response({
                'status': 'error',
                'message': 'Failed to deduct tokens'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SectorListView(APIView):
    """List all sectors"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        sectors = Sector.objects.all().order_by('name')
        serializer = SectorSerializer(sectors, many=True)
        return Response(serializer.data)


class CompanyTypeListView(APIView):
    """List all company types"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        types = CompanyType.objects.all().order_by('name')
        serializer = CompanyTypeSerializer(types, many=True)
        return Response(serializer.data)


class CompanyRoleListView(APIView):
    """List all company roles"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        roles = CompanyRole.objects.all().order_by('name')
        serializer = CompanyRoleSerializer(roles, many=True)
        return Response(serializer.data)
