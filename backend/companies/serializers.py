from rest_framework import serializers
from .models import (
    Company, CompanyProduct, KeyContact, KeyContactUnlock,
    Sector, CompanyRole, CompanyType
)
from django.contrib.auth import get_user_model

User = get_user_model()


class SectorSerializer(serializers.ModelSerializer):
    """Sector/Product category serializer"""
    class Meta:
        model = Sector
        fields = ['id', 'name', 'description']


class CompanyRoleSerializer(serializers.ModelSerializer):
    """Company role serializer"""
    class Meta:
        model = CompanyRole
        fields = ['id', 'name', 'description']


class CompanyTypeSerializer(serializers.ModelSerializer):
    """Company type serializer"""
    class Meta:
        model = CompanyType
        fields = ['id', 'name', 'description']


class CompanyProductSerializer(serializers.ModelSerializer):
    """Company product serializer"""
    class Meta:
        model = CompanyProduct
        fields = ['id', 'name', 'description', 'variety', 'value_added', 'hsn_code']


class KeyContactSerializer(serializers.ModelSerializer):
    """
    Dynamic serializer that hides/shows contact info based on unlock status
    """
    is_unlocked = serializers.SerializerMethodField()
    
    class Meta:
        model = KeyContact
        fields = ['id', 'name', 'designation', 'phone', 'email', 
                  'whatsapp', 'is_public', 'is_unlocked']
    
    def get_is_unlocked(self, obj):
        """Check if current user has unlocked this contact"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return KeyContactUnlock.objects.filter(
                user=request.user,
                key_contact=obj
            ).exists()
        return False
    
    def to_representation(self, instance):
        """Hide sensitive fields if not unlocked"""
        data = super().to_representation(instance)
        
        
        if instance.is_public or data['is_unlocked']:
            return data
        
        
        data['phone'] = "🔒 Locked"
        data['email'] = "🔒 Locked"
        data['whatsapp'] = "🔒 Locked"
        return data


class CompanyListSerializer(serializers.ModelSerializer):
    """Minimal info for company listings"""
    sector_name = serializers.CharField(source='sector.name', read_only=True)
    role_name = serializers.CharField(source='company_role.name', read_only=True)
    type_name = serializers.CharField(source='company_type.name', read_only=True)
    
    class Meta:
        model = Company
        fields = ['id', 'name', 'country', 'province', 'district', 
                  'sector_name', 'role_name', 'type_name', 'verification_status']


class CompanyDetailSerializer(serializers.ModelSerializer):
    """Full company details with products and contacts"""
    sector = SectorSerializer(read_only=True)
    company_role = CompanyRoleSerializer(read_only=True)
    company_type = CompanyTypeSerializer(read_only=True)
    products = serializers.SerializerMethodField()
    key_contacts = serializers.SerializerMethodField()
    
    class Meta:
        model = Company
        fields = [
            'id', 'name', 'legal_name', 'description', 'country', 'province', 
            'district', 'address', 'market_sentiment', 'website', 'contact_email', 'phone',
            'year_established', 'number_of_employees', 'verification_status',
            'sector', 'company_role', 'company_type', 'products', 'key_contacts'
        ]
    
    def get_products(self, obj):
        """Get company products"""
        products = obj.products.all()
        return CompanyProductSerializer(products, many=True).data
    
    def get_key_contacts(self, obj):
        """Get company key contacts with unlock status"""
        contacts = obj.key_contacts.all()
        return KeyContactSerializer(
            contacts, 
            many=True, 
            context=self.context
        ).data
