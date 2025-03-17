from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed
from ..models import UserSession

class TokenExpirationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if request has an authenticated user via token
        if hasattr(request, 'auth') and isinstance(request.auth, Token):
            try:
                # Find the session for this token
                session = UserSession.objects.get(
                    token=request.auth.key, 
                    is_active=True
                )
                
                # Check if token is expired
                if timezone.now() >= session.expires_at:
                    # Deactivate session
                    session.is_active = False
                    session.save()
                    
                    # Optionally delete the token
                    # request.auth.delete()
                    
                    # Raise authentication error
                    raise AuthenticationFailed('Token has expired')
                    
            except UserSession.DoesNotExist:
                # No session found for this token
                pass
                
        response = self.get_response(request)
        return response