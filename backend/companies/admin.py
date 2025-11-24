from django.contrib import admin
from ckeditor.widgets import CKEditorWidget
from django import forms
from .models import (
    Sector, CompanyRole, CompanyType, Image, Company, 
    CompanyProduct, KeyContact, KeyContactUnlock
)
# Removed AdminAnnouncement, IngestionLog, CompanyMetricsCache as they are NOT in the models.py file I just viewed.
# If they are supposed to be there, they are missing from models.py.
# Based on the error log, the admin was trying to register them, but if they don't exist in models.py, I should remove them from admin.py or add them to models.py.
# The user request said "change the models from backend... and other things".
# But the errors are about fields not existing.
# Let's check if those models exist in companies/models.py.
# I viewed companies/models.py and it ends at KeyContactUnlock.
# So AdminAnnouncement, IngestionLog, CompanyMetricsCache DO NOT EXIST in companies/models.py.
# I will remove them from admin.py to fix the errors.

# Custom form with CKEditor
class CompanyAdminForm(forms.ModelForm):
    description = forms.CharField(widget=CKEditorWidget(), required=False)
    
    class Meta:
        model = Company
        fields = '__all__'


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
    # Removed 'has_trade_data' as it was not in the models.py I viewed (it had is_verified, etc)
    # Let's re-verify Company model fields from the file I viewed.
    # Fields: name, legal_name, sector, company_role, company_type, description, 
    # email, phone, website, address, district, province, country,
    # year_established, number_of_employees, annual_revenue,
    # verification_status, is_directory_profile, created_at, updated_at.
    # 'has_trade_data' is NOT in the model.
    
    list_filter = ('verification_status', 'is_directory_profile', 'sector', 'company_role')
    search_fields = ('name', 'legal_name', 'email', 'website')
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
            'fields': ('email', 'phone', 'website', 'address', 'district', 'province', 'country')
        }),
        ('Business Details', {
            'fields': ('year_established', 'number_of_employees', 'annual_revenue')
        }),
        ('Status & Flags', {
            'fields': ('verification_status', 'is_directory_profile')
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
    readonly_fields = ('unlock_count',)
    
    def unlock_count(self, obj):
        return obj.unlocks.count()
    unlock_count.short_description = 'Times Unlocked'


@admin.register(KeyContactUnlock)
class KeyContactUnlockAdmin(admin.ModelAdmin):
    # Error said: 'list_display[0]' refers to 'contact', which is not a callable...
    # Model has: key_contact (ForeignKey), user, unlocked_at
    # So it should be 'key_contact', not 'contact'
    list_display = ('key_contact', 'user', 'unlocked_at')
    list_filter = ('unlocked_at',)
    search_fields = ('key_contact__name', 'user__email')
    readonly_fields = ('unlocked_at',)
    date_hierarchy = 'unlocked_at'


# Register Image model
admin.site.register(Image)
