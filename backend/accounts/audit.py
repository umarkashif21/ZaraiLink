from django.db import models
from django.conf import settings
from django.utils import timezone
import json


class AuditLog(models.Model):
    ACTION_TYPES = [
        ('contact_unlock', 'Contact Unlock'),
        ('bulk_unlock', 'Bulk Contact Unlock'),
        ('password_change', 'Password Change'),
        ('subscription_change', 'Subscription Change'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('export', 'Data Export'),
        ('api_key_generated', 'API Key Generated'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs'
    )
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    description = models.TextField(blank=True)
    metadata = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action_type', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user} - {self.action_type} - {self.timestamp}"


def log_action(user, action_type, description='', metadata=None, request=None):
    ip_address = None
    user_agent = ''
    
    if request:
        
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
    
    AuditLog.objects.create(
        user=user,
        action_type=action_type,
        description=description,
        metadata=metadata,
        ip_address=ip_address,
        user_agent=user_agent,
    )


def get_user_activity(user, limit=50, action_types=None):
    queryset = AuditLog.objects.filter(user=user)
    
    if action_types:
        queryset = queryset.filter(action_type__in=action_types)
    
    return queryset[:limit]
