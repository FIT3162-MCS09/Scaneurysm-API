from rest_framework import serializers
from ..service.auth import AuthService

class SignInSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        if username and password:
            user = AuthService.authenticate(username=username, password=password)
            if user is None:
                raise serializers.ValidationError("Invalid username or password")
        else:
            raise serializers.ValidationError("Must include 'username' and 'password'")

        data['user'] = user
        return data