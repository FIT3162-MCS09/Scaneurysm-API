from django.db import models
from django.utils import timezone
from django.conf import settings
from rest_framework.authtoken.models import Token
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid
from src.models.user import User

class UserSession(models.Model):
    """Track user sessions for additional security"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    token = models.CharField(max_length=64, unique=True)  # For REST API auth token
    session_key = models.CharField(max_length=40, blank=True, null=True)  # For browser sessions
    device_info = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Session for {self.user.username}"
    
    def is_expired(self):
        return timezone.now() >= self.expires_at
    
    class Meta:
        db_table = 'user_sessions'


# Signal to create auth token for new users
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)