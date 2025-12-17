from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from django.db import transaction
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
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

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        
        
        if request.user.is_authenticated:
            try:
                from market_intel.models import UserInteraction
                UserInteraction.objects.create(user=request.user, company=instance, action='view')
            except Exception as e:
                pass 
            
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        """Override list to include AI fallback indicator in response"""
        queryset = self.filter_queryset(self.get_queryset())
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            
            if getattr(self, '_ai_fallback', False):
                response.data['ai_fallback'] = True
            return response

        serializer = self.get_serializer(queryset, many=True)
        data = {'results': serializer.data}
        
        if getattr(self, '_ai_fallback', False):
            data['ai_fallback'] = True
        return Response(data)

    
    def get_queryset(self):
        """Filter companies based on query params"""
        queryset = self.queryset
        
        
        self._ai_fallback = False
        
        
        search = self.request.query_params.get('search', '').strip()
        region = self.request.query_params.get('region', '').strip()
        sector = self.request.query_params.get('sector', '').strip()
        company_type = self.request.query_params.get('type', '').strip()
        role = self.request.query_params.get('role', '').strip()
        
        if company_type:
            queryset = queryset.filter(company_type_id=company_type)
        if role:
            queryset = queryset.filter(company_role_id=role)
            
        
        use_ai = self.request.query_params.get('use_ai', 'false').lower() == 'true'
        if search:
            if use_ai:
                from utils.ai_service import AIService
                from django.db.models import Case, When, IntegerField
                import logging
                logger = logging.getLogger('zarailink')
                
                try:
                    
                    company_data = list(queryset.values('id', 'name', 'province', 'sector__name')[:100])
                    logger.info(f"AI Search: Query='{search}', Companies available={len(company_data)}")
                    
                    company_data_formatted = [
                        {
                            'id': c['id'], 
                            'name': c['name'], 
                            'province': c.get('province', ''),
                            'sector': c.get('sector__name', '')
                        }
                        for c in company_data
                    ]
                    
                    
                    matching_ids = AIService.smart_search(search, company_data_formatted)
                    logger.info(f"AI Search: GPT returned IDs={matching_ids}")
                    
                    if matching_ids:
                        
                        valid_ids = list(queryset.filter(id__in=matching_ids).values_list('id', flat=True))
                        logger.info(f"AI Search: Valid IDs after filter={valid_ids}")
                        
                        if valid_ids:
                            
                            id_positions = {id_val: pos for pos, id_val in enumerate(matching_ids) if id_val in valid_ids}
                            preserved = Case(
                                *[When(pk=pk, then=pos) for pk, pos in id_positions.items()], 
                                output_field=IntegerField()
                            )
                            queryset = queryset.filter(id__in=valid_ids).order_by(preserved)
                        else:
                            
                            logger.warning("AI Search: No valid IDs found, using text fallback")
                            self._ai_fallback = True
                            queryset = queryset.filter(
                                Q(name__icontains=search) | Q(description__icontains=search)
                            )
                    else:
                        
                        logger.warning("AI Search: GPT returned None/empty, using text fallback")
                        self._ai_fallback = True
                        queryset = queryset.filter(
                            Q(name__icontains=search) | Q(description__icontains=search)
                        )
                except Exception as e:
                    
                    logger.error(f"AI Search Error: {e}")
                    self._ai_fallback = True
                    queryset = queryset.filter(
                        Q(name__icontains=search) | Q(description__icontains=search)
                    )
            else:
                queryset = queryset.filter(
                    Q(name__icontains=search) | Q(description__icontains=search)
                )
        
        
        queryset = queryset.select_related('sector', 'company_role', 'company_type')

        if self.action == 'list':
            queryset = queryset.defer(
                'legal_name', 'description', 'address', 'website', 
                'contact_email', 'phone', 'logo_image', 'year_established', 
                'number_of_employees', 'horeca_retail_info', 'ntn_number', 
                'trade_license_number', 'has_trade_data', 'is_directory_profile', 
                'created_at', 'updated_at'
            )
        else:
            
            queryset = queryset.prefetch_related('products', 'key_contacts')

        return queryset
    
    @action(detail=False, methods=['get'])
    def regions(self, request):
        """Get available regions dynamically"""
        regions = Company.objects.filter(
            verification_status='verified',
            province__isnull=False
        ).exclude(province='').values_list('province', flat=True).distinct().order_by('province')
        return Response(list(regions))
    
    @action(detail=False, methods=['get'])
    def hsn_codes(self, request):
        """Get available HSN codes from products"""
        from .models import CompanyProduct
        hsn_codes = CompanyProduct.objects.exclude(
            hsn_code=''
        ).values_list('hsn_code', flat=True).distinct().order_by('hsn_code')
        return Response(list(hsn_codes))


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
    
    @method_decorator(csrf_exempt)
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    @transaction.atomic
    def unlock(self, request, pk=None):
        """Unlock a contact using tokens"""
        contact = self.get_object()
        user = request.user
        
        
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
        
        
        if contact.is_public:
            
            KeyContactUnlock.objects.create(user=user, key_contact=contact)
            return Response({
                'status': 'success',
                'message': 'Contact unlocked (public contact)',
                'tokens_charged': 0,
                'remaining_balance': user.token_balance,
                'contact': KeyContactSerializer(contact, context={'request': request}).data
            })
        
        
        if not user.has_tokens(1):
            return Response({
                'status': 'insufficient_tokens',
                'message': 'Not enough tokens. Please purchase more.',
                'current_balance': user.token_balance,
                'required': 1
            }, status=status.HTTP_402_PAYMENT_REQUIRED)
        
        
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
