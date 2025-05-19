from rest_framework import serializers

class FileSerializer(serializers.Serializer):
    user_id = serializers.CharField(max_length=255, required=True)
    

class FileUploadSerializer(serializers.Serializer):
    user_id = serializers.CharField(max_length=255, required=True)
    file = serializers.FileField()