from rest_framework import serializers
from django.contrib.auth import authenticate
from models.user import User

class SignInSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=255, required=True)
    password = serializers.CharField(max_length=128, required=True, write_only=True)
    
    def validate(self, data):
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            raise serializers.ValidationError("Must include 'username' and 'password'")
            
        user = authenticate(username=username, password=password)
        
        if not user:
            # Track failed login attempts if user exists
            try:
                user_obj = User.objects.get(username=username)
                user_obj.increment_failed_login()
            except User.DoesNotExist:
                pass
                
            raise serializers.ValidationError("Invalid username or password")
            
        if not user.is_active:
            raise serializers.ValidationError("User account is disabled")
            
        # Add user to validated data for easy access in the view
        data['user'] = user
        return data