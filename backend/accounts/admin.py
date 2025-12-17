from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserAlertPreference


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    
    
    
    
    
    
    list_display = ('email', 'first_name', 'last_name', 'email_verified', 'token_balance', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'email_verified', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name', 'phone_number')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'bio', 'phone_number', 'job_title', 'country')}),
        ('Tokens & Verification', {'fields': ('token_balance', 'email_verified')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'token_balance'),
        }),
    )
    
    readonly_fields = ('date_joined', 'last_login')
    
    
    actions = ['add_100_tokens', 'add_1000_tokens', 'verify_users']
    
    @admin.action(description='Add 100 tokens to selected users')
    def add_100_tokens(self, request, queryset):
        for user in queryset:
            user.add_tokens(100)
        self.message_user(request, f'Added 100 tokens to {queryset.count()} users.')
    
    @admin.action(description='Add 1000 tokens to selected users')
    def add_1000_tokens(self, request, queryset):
        for user in queryset:
            user.add_tokens(1000)
        self.message_user(request, f'Added 1000 tokens to {queryset.count()} users.')
    
    @admin.action(description='Mark selected users as verified')
    def verify_users(self, request, queryset):
        queryset.update(email_verified=True)
        self.message_user(request, f'Verified {queryset.count()} users.')


@admin.register(UserAlertPreference)
class UserAlertPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'notify_email', 'notify_in_app', 'frequency', 'updated_at')
    list_filter = ('notify_email', 'notify_in_app', 'frequency')
    search_fields = ('user__email',)
    readonly_fields = ('updated_at',)
