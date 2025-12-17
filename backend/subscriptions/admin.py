from django.contrib import admin
from django.utils.html import format_html
from .models import SubscriptionPlan, UserSubscription, TokenPurchase, RedeemCode


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('plan_name', 'tokens_included', 'price_display', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('plan_name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('plan_name', 'description')
        }),
        ('Pricing', {
            'fields': ('price', 'currency', 'tokens_included')
        }),
        ('Features', {
            'fields': ('features',),
            'description': 'Enter features as JSON, e.g., {"feature1": true, "feature2": "value"}'
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def price_display(self, obj):
        return f"{obj.currency} {obj.price}"
    price_display.short_description = 'Price'


@admin.register(RedeemCode)
class RedeemCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'plan', 'status_badge', 'created_at', 'redeemed_by', 'redeemed_at')
    list_filter = ('status', 'plan', 'created_at')
    search_fields = ('code', 'redeemed_by__email')
    readonly_fields = ('created_at', 'redeemed_at', 'redeemed_by')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {
            'fields': ('code', 'plan', 'status')
        }),
        ('Redemption Info', {
            'fields': ('redeemed_by', 'redeemed_at', 'expires_at'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'active': 'green',
            'redeemed': 'gray',
            'expired': 'red'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.status.upper()
        )
    status_badge.short_description = 'Status'
    
    
    actions = [
        'generate_codes_500', 'generate_codes_5k', 'generate_codes_15k',
        'generate_codes_6k_annual', 'generate_codes_60k_annual', 'generate_codes_900k_annual'
    ]
    
    @admin.action(description='🎁 Generate 15 codes for 500 Credits Plan')
    def generate_codes_500(self, request, queryset):
        self._generate_codes(request, '500 Credits', 15)
    
    @admin.action(description='🎁 Generate 15 codes for 5K Credits Plan')
    def generate_codes_5k(self, request, queryset):
        self._generate_codes(request, '5K Credits', 15)
    
    @admin.action(description='🎁 Generate 15 codes for 15K Credits Plan')
    def generate_codes_15k(self, request, queryset):
        self._generate_codes(request, '15K Credits', 15)

    @admin.action(description='🎁 Generate 15 codes for 6000 Credits Annually')
    def generate_codes_6k_annual(self, request, queryset):
        self._generate_codes(request, '6000 Credits Annually', 15)

    @admin.action(description='🎁 Generate 15 codes for 60K Credits Annually')
    def generate_codes_60k_annual(self, request, queryset):
        self._generate_codes(request, '60K Credits Annually', 15)

    @admin.action(description='🎁 Generate 15 codes for 900K Credits Annually')
    def generate_codes_900k_annual(self, request, queryset):
        self._generate_codes(request, '900K Credits Annually', 15)
    
    def _generate_codes(self, request, plan_name, count):
        try:
            plan = SubscriptionPlan.objects.get(plan_name=plan_name)
            codes = []
            
            for i in range(count):
                while True:
                    code = RedeemCode.generate_code(12)
                    if not RedeemCode.objects.filter(code=code).exists():
                        break
                
                redeem_code = RedeemCode.objects.create(
                    code=code,
                    plan=plan,
                    status='active'
                )
                codes.append(code)
            
            
            codes_display = ', '.join(codes[:5]) + '...' if len(codes) > 5 else ', '.join(codes)
            self.message_user(
                request,
                f'✅ Generated {count} codes for {plan_name}: {codes_display}',
                level='success'
            )
            
        except SubscriptionPlan.DoesNotExist:
            self.message_user(
                request,
                f'❌ Plan "{plan_name}" not found. Please create it first.',
                level='error'
            )


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'status', 'start_date', 'end_date', 'billing_cycle')
    list_filter = ('status', 'billing_cycle', 'start_date')
    search_fields = ('user__email', 'plan__plan_name')
    readonly_fields = ('created_at',)
    date_hierarchy = 'start_date'
    
    fieldsets = (
        (None, {
            'fields': ('user', 'plan', 'status')
        }),
        ('Subscription Period', {
            'fields': ('start_date', 'end_date', 'billing_cycle')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(TokenPurchase)
class TokenPurchaseAdmin(admin.ModelAdmin):
    list_display = ('user', 'tokens_purchased', 'price_display', 'purchased_at')
    list_filter = ('purchased_at',)
    search_fields = ('user__email', 'payment_reference')
    readonly_fields = ('purchased_at',)
    date_hierarchy = 'purchased_at'
    
    def price_display(self, obj):
        return f"{obj.currency} {obj.price}"
    price_display.short_description = 'Price'
