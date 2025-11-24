from django import template
from subscriptions.models import SubscriptionPlan

register = template.Library()

@register.simple_tag
def get_subscription_plans():
    return SubscriptionPlan.objects.all().order_by('price')
