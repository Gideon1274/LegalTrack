# core/signals.py
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from .models import AuditLog
import json
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser

@receiver(user_logged_in)
def log_user_login(sender, user, request, **kwargs):
    AuditLog.objects.create(
        actor=user,
        action='login',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        details={'method': 'email/password'}
    )

@receiver(user_logged_out)
def log_user_logout(sender, user, request, **kwargs):
    AuditLog.objects.create(
        actor=user,
        action='logout',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        details={}
    )

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

