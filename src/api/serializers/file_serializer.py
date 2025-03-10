from rest_framework import serializers

class FileSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    

class FileUploadSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    file = serializers.FileField()