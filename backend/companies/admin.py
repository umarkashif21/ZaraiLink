from django.contrib import admin
from django_ckeditor_5.widgets import CKEditor5Widget
from django import forms
from .models import (
    Sector, CompanyRole, CompanyType, Image, Company, 
    CompanyProduct, KeyContact, KeyContactUnlock
)


class CompanyAdminForm(forms.ModelForm):
    description = forms.CharField(widget=CKEditor5Widget(config_name='extends'), required=False)
    
    class Meta:
        model = Company
        fields = '__all__'



class KeyContactUnlockInline(admin.TabularInline):
    model = KeyContactUnlock
    extra = 0
    readonly_fields = ('user', 'unlocked_at')
    can_delete = True  
    verbose_name = 'Contact Unlock'
    verbose_name_plural = 'Contact Unlocks (Users who unlocked this contact)'


@admin.register(Sector)
class SectorAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(CompanyRole)
class CompanyRoleAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(CompanyType)
class CompanyTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    form = CompanyAdminForm
    list_display = ('name', 'sector', 'company_role', 'verification_status', 'created_at')
    
    
    
    
    
    
    
    
    list_filter = ('verification_status', 'is_directory_profile', 'sector', 'company_role')
    search_fields = ('name', 'legal_name', 'contact_email', 'website')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'legal_name', 'sector', 'company_role', 'company_type')
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('Contact Information', {
            'fields': ('contact_email', 'phone', 'website', 'address', 'district', 'province', 'country')
        }),
        ('Business Details', {
            'fields': ('year_established', 'number_of_employees', 'horeca_retail_info', 'ntn_number', 'trade_license_number')
        }),
        ('Status & Flags', {
            'fields': ('verification_status', 'is_directory_profile', 'has_trade_data')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CompanyProduct)
class CompanyProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'variety', 'value_added')
    list_filter = ('value_added', 'company')
    search_fields = ('name', 'variety', 'company__name')


@admin.register(KeyContact)
class KeyContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'designation', 'is_public', 'unlock_count')
    list_filter = ('is_public', 'company')
    search_fields = ('name', 'designation', 'company__name', 'email', 'phone')
    readonly_fields = ('unlock_count', 'created_at', 'updated_at')
    inlines = [KeyContactUnlockInline]  
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('company', 'name', 'designation')
        }),
        ('Contact Details', {
            'fields': ('phone', 'email', 'whatsapp')
        }),
        ('Visibility', {
            'fields': ('is_public',),
            'description': 'Public contacts are visible to all users without requiring tokens'
        }),
        ('Metadata', {
            'fields': ('unlock_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def unlock_count(self, obj):
        return obj.unlocks.count()
    unlock_count.short_description = 'Times Unlocked'


@admin.register(KeyContactUnlock)
class KeyContactUnlockAdmin(admin.ModelAdmin):
    
    
    
    list_display = ('key_contact', 'user', 'unlocked_at')
    list_filter = ('unlocked_at',)
    search_fields = ('key_contact__name', 'user__email')
    readonly_fields = ('unlocked_at',)
    date_hierarchy = 'unlocked_at'



admin.site.register(Image)
